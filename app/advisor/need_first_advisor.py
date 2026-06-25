"""
Need-First Advisor (Puzzle: "Add need-first recommendation before
website/detail questions").

This module is the smallest safe layer that lets the factory behave like
a product advisor BEFORE the existing website-section diagnostic question
(app/providers/pm/mock_pm.py's _DIAGNOSTIC) is shown. It does not touch
mock_pm.py, anthropic_pm.py, the builder, or the database — it is a pure,
isolated, rule-based function: raw text in, a recommendation dict out.

Gating: this entire module is only reached when the environment flag
ENABLE_NEED_FIRST_RECOMMENDATION is "true" (checked by the caller in
app/routes/projects.py, mirroring the existing
ENABLE_INTERNAL_BLUEPRINT_ENDPOINT pattern in app/routes/blueprint.py).
When the flag is off, none of this code runs and the old flow is
unchanged.

Design notes:
  - Deliberately rule-based/keyword-driven, not Claude-based — same
    "smallest safe version" spirit as app/blueprint/generator.py.
  - Deliberately NOT importing from app.providers.pm.mock_pm — the
    audit's core complaint was two parallel, disconnected systems
    making decisions about the same request. This advisor is meant to
    run BEFORE that system and short-circuit its website-first
    diagnostic, not become a third disconnected system reusing its
    internals. Some keyword lists are intentionally small and
    self-contained here.
  - Only ever surfaces 2-3 options to the user, even though the
    factory may "consider" more tool types internally.
"""
from __future__ import annotations

from typing import Any


# ── Internal product/tool vocabulary (never shown raw to the user — only
# the human Persian option labels below are user-facing) ────────────────────
_TOOL_LABELS_FA = {
    "digital_menu_order":      "منوی دیجیتال + سفارش ساده",
    "walkin_landing":          "صفحه جذب مشتری حضوری",
    "customer_followup":       "ابزار پیگیری مشتری‌های قبلی",
    "cafe_intro_site":         "سایت معرفی کافه و فضای لوکس",
    "cafe_intro_menu_site":    "سایت معرفی + منوی دیجیتال",
    "special_offer_landing":   "صفحه جذب مشتری با پیشنهاد ویژه",
    "portfolio_request_form":  "صفحه نمونه‌کار + فرم درخواست سفارش",
    "service_price_intro":     "صفحه معرفی خدمات و قیمت حدودی",
    "measurement_booking":     "رزرو وقت اندازه‌گیری",
    "catalog_order":           "کاتالوگ محصول + سفارش ساده",
    "brand_intro_page":        "صفحه معرفی برند خانگی",
    "quick_order_form":        "فرم سفارش سریع",
}


def _opt(tool_key: str) -> dict[str, str]:
    return {"tool_key": tool_key, "label": _TOOL_LABELS_FA[tool_key]}


# ── Need-level clarification options for Test 5 (truly vague requests) ──────
_NEED_CLARIFY_OPTIONS = [
    "فروش بیشتر",
    "مشتری بیشتر",
    "سفارش راحت‌تر",
    "نظم در کارها",
    "دیدن حساب‌ها یا گزارش‌ها",
]


def get_need_first_recommendation(raw_text: str) -> dict[str, Any]:
    """
    Returns a dict with:
      detected_pain_or_goal, business_context, user_named_tool_if_any,
      recommended_options (list of {tool_key, label}, length 2-3),
      factory_recommendation (tool_key), reason_for_recommendation,
      needs_clarification (bool),
      clarification_question / clarification_options (only if needed).

    Kept internal — app/routes/projects.py converts this into the
    user-facing RecommendationResponse-style text; raw tool_key values
    are never shown to the user directly.
    """
    text = (raw_text or "").strip()

    # ── Example 1: کافه + فروش/راحت بودن signal (sales-goal framing, not
    # just "I want a cafe website") ──────────────────────────────────────────
    if any(k in text for k in ["کافه", "رستوران", "کافی‌شاپ", "کافیشاپ"]) and \
       any(k in text for k in ["فروش", "راحت باشه", "بات یا سایت", "بهتر بشه فروش"]):
        return {
            "detected_pain_or_goal": "فروش بیشتر کافه",
            "business_context": "کافه",
            "user_named_tool_if_any": "بات یا سایت" if ("بات" in text and "سایت" in text) else None,
            "recommended_options": [
                _opt("digital_menu_order"),
                _opt("walkin_landing"),
                _opt("customer_followup"),
            ],
            "factory_recommendation": "digital_menu_order",
            "reason_for_recommendation": (
                "چون سریع‌تر از یک سایت معرفی معمولی به فروش وصل می‌شود "
                "و مشتری راحت‌تر انتخاب و سفارش می‌دهد."
            ),
            "needs_clarification": False,
        }

    # ── Example 2: explicit "سایت کافه لوکس" — still advise, don't just build ──
    if any(k in text for k in ["کافه", "رستوران"]) and \
       any(k in text for k in ["سایت", "وبسایت", "وب‌سایت", "صفحه", "لندینگ", "website", "page", "landing"]):
        return {
            "detected_pain_or_goal": "حضور آنلاین برای کافه (با تأکید بر برند/فضا)",
            "business_context": "کافه",
            "user_named_tool_if_any": "سایت",
            "recommended_options": [
                _opt("cafe_intro_site"),
                _opt("cafe_intro_menu_site"),
                _opt("special_offer_landing"),
            ],
            "factory_recommendation": "cafe_intro_menu_site",
            "reason_for_recommendation": (
                "چون برای کافه لوکس، هم حس برند مهم است و هم مشتری باید سریع منو را ببیند."
            ),
            "needs_clarification": False,
        }

    # ── Example 3: tailoring / attracting more customers ───────────────────
    if any(k in text for k in ["خیاط", "خیاطی", "خیاطیم"]) and \
       any(k in text for k in ["مشتری", "جذب"]):
        return {
            "detected_pain_or_goal": "جذب مشتری بیشتر برای خیاطی",
            "business_context": "خیاطی",
            "user_named_tool_if_any": None,
            "recommended_options": [
                _opt("portfolio_request_form"),
                _opt("service_price_intro"),
                _opt("measurement_booking"),
            ],
            "factory_recommendation": "portfolio_request_form",
            "reason_for_recommendation": (
                "چون مشتری قبل از تماس باید کیفیت کارها را ببیند و بعد راحت درخواست بدهد."
            ),
            "needs_clarification": False,
        }

    # ── Example 4: homemade food / pickles — selling a home product ────────
    if any(k in text for k in [
        "ترشی", "خیارشور", "زیتون", "مربا", "غذای خانگی", "غذای آماده",
        "شیرینی خانگی", "کیک خانگی",
    ]):
        return {
            "detected_pain_or_goal": "فروش محصول خانگی",
            "business_context": "فروش محصولات خانگی",
            "user_named_tool_if_any": None,
            "recommended_options": [
                _opt("catalog_order"),
                _opt("brand_intro_page"),
                _opt("quick_order_form"),
            ],
            "factory_recommendation": "catalog_order",
            "reason_for_recommendation": (
                "چون مشتری باید محصول، قیمت و راه سفارش را سریع ببیند."
            ),
            "needs_clarification": False,
        }

    # ── Example 5: truly vague — ask a need-level question, never a
    # website-section question. ─────────────────────────────────────────────
    return {
        "detected_pain_or_goal": None,
        "business_context": None,
        "user_named_tool_if_any": None,
        "recommended_options": [],
        "factory_recommendation": None,
        "reason_for_recommendation": None,
        "needs_clarification": True,
        "clarification_question": (
            "برای اینکه پیشنهاد دقیق‌تری بدهم، اول باید بفهمم منظورت از بهتر شدن چیست."
        ),
        "clarification_options": list(_NEED_CLARIFY_OPTIONS),
    }
