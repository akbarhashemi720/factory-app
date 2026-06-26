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
    # Goal-level second-stage options (Puzzle: goal selection -> product
    # advisor, not website-section questions)
    "new_customer_acquisition":   "جذب مشتری جدید",
    "digital_menu_order_goal":    "منوی دیجیتال + سفارش ساده",
    "returning_customer_tool":    "برگرداندن مشتری‌های قبلی",
    "digital_menu_simple_order":  "منوی دیجیتال + ثبت سفارش ساده",
    "quick_order_form_goal":      "فرم سفارش سریع",
    "simple_order_bot":           "بات سفارش‌گیری ساده",
    "customer_landing_offer":     "صفحه جذب مشتری با عکس، آدرس و پیشنهاد ویژه",
    "digital_menu_fast_decision": "منوی دیجیتال برای تصمیم سریع‌تر",
    "contact_or_booking_form":    "فرم تماس یا رزرو ساده",
    "simple_task_dashboard_goal": "داشبورد ساده کارها",
    "order_request_form":        "فرم ثبت سفارش/درخواست",
    "customer_followup_list":    "لیست پیگیری مشتری‌ها",
    "simple_finance_dashboard":  "داشبورد ساده فروش و هزینه",
    "income_order_log":          "ثبت سفارش‌ها و درآمدها",
    "simple_periodic_report":    "گزارش روزانه/هفتگی ساده",
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
            "preview_archetype": "digital_menu_order_page",
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
            "preview_archetype": "digital_menu_order_page",
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
            "preview_archetype": "service_portfolio_request_page",
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
            "preview_archetype": "product_catalog_order_page",
        }

    # ── Example 4.5: admin/office task & meeting organization — a CLEAR
    # input that should go straight to a dashboard recommendation, never
    # through the generic vague-goal clarification (the gap this puzzle
    # fixes: "برای نظم کارهای اداری ام ... نظم بدم به کارهام و جلساتم"
    # used to fall through to "فروش بیشتر / مشتری بیشتر / ..." options). ──
    if any(k in text for k in ["نظم", "سازمان‌دهی", "مدیریت کارها", "مدیریت کار"]) and \
       any(k in text for k in ["کار", "کارها", "کارهام", "اداری", "جلسات", "جلسه"]):
        return {
            "detected_pain_or_goal": "نظم‌دادن به کارها و جلسات",
            "business_context": "کارهای اداری",
            "user_named_tool_if_any": None,
            "recommended_options": [
                _opt("simple_task_dashboard_goal"),
                _opt("order_request_form"),
                _opt("customer_followup_list"),
            ],
            "factory_recommendation": "simple_task_dashboard_goal",
            "factory_recommendation_combo_label": "داشبورد ساده وظایف + جلسات",
            "reason_for_recommendation": (
                "چون درخواست تو بیشتر درباره نظم‌دادن به کارها و جلسات است، نه ساخت یک سایت تبلیغاتی."
            ),
            "needs_clarification": False,
            "preview_archetype": "task_dashboard_mockup",
            # This is the kind of request where it can genuinely help to
            # know if it's just for the user or a whole team — but ONLY
            # as a button-based follow-up, never a blank textbox (Puzzle
            # requirement #2). Optional: the frontend may choose to ask
            # this before final confirmation; the recommendation itself
            # does not require it to proceed.
            "optional_followup_question": (
                "آیا این سیستم فقط برای استفاده شخصی شماست یا می‌خواهید "
                "تیمی از چند نفر هم از آن استفاده کند؟"
            ),
            "optional_followup_options": [
                "فقط برای خودم",
                "برای تیم چند نفره",
                "هم خودم هم تیم",
                "مطمئن نیستم، پیشنهاد بده",
            ],
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


# ── Goal-level second-stage recommendation ───────────────────────────────────
# Reached AFTER the user answers the Example-5-style clarification question
# (e.g. picks "فروش بیشتر"). This is STILL rule-based and fast — no Claude
# call — and is the fix for the bug where the old code jumped straight
# into the website-section diagnostic ("سایت کافه چه بخش‌هایی داشته
# باشد؟") right after a goal was picked, before any product/tool was
# even recommended.
#
# Each goal maps to 2-3 practical product/tool paths + one explicit
# factory recommendation + a short reason — exactly mirroring the
# pattern used by get_need_first_recommendation() above, just one level
# deeper (goal -> tool, instead of raw text -> goal-or-tool).

_CAFE_GOAL_RECOMMENDATIONS: dict[str, dict[str, Any]] = {
    "فروش بیشتر": {
        "detected_pain_or_goal": "افزایش فروش کافه",
        "recommended_options": [
            {"tool_key": "new_customer_acquisition", "label": _TOOL_LABELS_FA["new_customer_acquisition"],
             "explanation": "برای اینکه افراد بیشتری کافه را ببینند و حضوری بیایند."},
            {"tool_key": "digital_menu_order_goal", "label": _TOOL_LABELS_FA["digital_menu_order_goal"],
             "explanation": "برای اینکه مشتری سریع منو را ببیند و راحت‌تر سفارش بدهد."},
            {"tool_key": "returning_customer_tool", "label": _TOOL_LABELS_FA["returning_customer_tool"],
             "explanation": "برای اینکه کسانی که قبلاً آمده‌اند دوباره برگردند."},
        ],
        "factory_recommendation": "new_customer_acquisition",
        "factory_recommendation_combo_label": "جذب مشتری جدید + منوی دیجیتال",
        "reason_for_recommendation": (
            "چون برای کافه معمولاً اول باید مشتری راحت کافه، فضا، منو، آدرس و پیشنهاد ویژه را ببیند؛ "
            "بعداً می‌شود سفارش یا باشگاه مشتریان اضافه کرد."
        ),
        "preview_archetype": "lead_landing_page",
    },
    "سفارش راحت‌تر": {
        "detected_pain_or_goal": "راحت‌تر کردن سفارش‌گیری کافه",
        "recommended_options": [
            {"tool_key": "digital_menu_simple_order", "label": _TOOL_LABELS_FA["digital_menu_simple_order"], "explanation": None},
            {"tool_key": "quick_order_form_goal", "label": _TOOL_LABELS_FA["quick_order_form_goal"], "explanation": None},
            {"tool_key": "simple_order_bot", "label": _TOOL_LABELS_FA["simple_order_bot"], "explanation": None},
        ],
        "factory_recommendation": "digital_menu_simple_order",
        "factory_recommendation_combo_label": _TOOL_LABELS_FA["digital_menu_simple_order"],
        "reason_for_recommendation": "چون برای شروع سریع‌تر و سبک‌تر از اپلیکیشن یا فروشگاه کامل است.",
        "preview_archetype": "digital_menu_order_page",
    },
    "مشتری بیشتر": {
        "detected_pain_or_goal": "جذب مشتری بیشتر برای کافه",
        "recommended_options": [
            {"tool_key": "customer_landing_offer", "label": _TOOL_LABELS_FA["customer_landing_offer"], "explanation": None},
            {"tool_key": "digital_menu_fast_decision", "label": _TOOL_LABELS_FA["digital_menu_fast_decision"], "explanation": None},
            {"tool_key": "contact_or_booking_form", "label": _TOOL_LABELS_FA["contact_or_booking_form"], "explanation": None},
        ],
        "factory_recommendation": "customer_landing_offer",
        "factory_recommendation_combo_label": "صفحه جذب مشتری + منوی دیجیتال",
        "reason_for_recommendation": (
            "چون قبل از هرچیز باید مشتری جدید کافه را ببیند و سریع تصمیم بگیرد بیاید."
        ),
        "preview_archetype": "lead_landing_page",
    },
    "نظم در کارها": {
        "detected_pain_or_goal": "نظم بیشتر در کارهای روزانه کافه",
        "recommended_options": [
            {"tool_key": "simple_task_dashboard_goal", "label": _TOOL_LABELS_FA["simple_task_dashboard_goal"], "explanation": None},
            {"tool_key": "order_request_form", "label": _TOOL_LABELS_FA["order_request_form"], "explanation": None},
            {"tool_key": "customer_followup_list", "label": _TOOL_LABELS_FA["customer_followup_list"], "explanation": None},
        ],
        "factory_recommendation": "simple_task_dashboard_goal",
        "factory_recommendation_combo_label": _TOOL_LABELS_FA["simple_task_dashboard_goal"],
        "reason_for_recommendation": "چون برای شروع، یک نمای ساده از کارها و وضعیتشان کافی است.",
        "preview_archetype": "task_dashboard_mockup",
    },
    "دیدن حساب‌ها یا گزارش‌ها": {
        "detected_pain_or_goal": "دیدن ساده حساب‌ها و گزارش‌های کافه",
        "recommended_options": [
            {"tool_key": "simple_finance_dashboard", "label": _TOOL_LABELS_FA["simple_finance_dashboard"], "explanation": None},
            {"tool_key": "income_order_log", "label": _TOOL_LABELS_FA["income_order_log"], "explanation": None},
            {"tool_key": "simple_periodic_report", "label": _TOOL_LABELS_FA["simple_periodic_report"], "explanation": None},
        ],
        "factory_recommendation": "simple_finance_dashboard",
        "factory_recommendation_combo_label": _TOOL_LABELS_FA["simple_finance_dashboard"],
        "reason_for_recommendation": "چون برای شروع، یک نمای ساده از درآمد و هزینه کافی است.",
        "preview_archetype": "task_dashboard_mockup",
    },
}

# Generic (business-context-unknown) version of the same 5 goals — used
# when the raw text doesn't mention a recognized business type. Slightly
# more generic wording, same structure.
_GENERIC_GOAL_RECOMMENDATIONS: dict[str, dict[str, Any]] = {
    "فروش بیشتر": {
        "detected_pain_or_goal": "افزایش فروش",
        "recommended_options": [
            {"tool_key": "new_customer_acquisition", "label": _TOOL_LABELS_FA["new_customer_acquisition"], "explanation": None},
            {"tool_key": "catalog_order", "label": _TOOL_LABELS_FA["catalog_order"], "explanation": None},
            {"tool_key": "returning_customer_tool", "label": _TOOL_LABELS_FA["returning_customer_tool"], "explanation": None},
        ],
        "factory_recommendation": "catalog_order",
        "factory_recommendation_combo_label": _TOOL_LABELS_FA["catalog_order"],
        "reason_for_recommendation": "چون مشتری باید محصول یا خدمت و راه سفارش را سریع ببیند.",
        "preview_archetype": "product_catalog_order_page",
    },
    "سفارش راحت‌تر": _CAFE_GOAL_RECOMMENDATIONS["سفارش راحت‌تر"],
    "مشتری بیشتر": {
        "detected_pain_or_goal": "جذب مشتری بیشتر",
        "recommended_options": [
            {"tool_key": "customer_landing_offer", "label": _TOOL_LABELS_FA["customer_landing_offer"], "explanation": None},
            {"tool_key": "portfolio_request_form", "label": _TOOL_LABELS_FA["portfolio_request_form"], "explanation": None},
            {"tool_key": "contact_or_booking_form", "label": _TOOL_LABELS_FA["contact_or_booking_form"], "explanation": None},
        ],
        "factory_recommendation": "customer_landing_offer",
        "factory_recommendation_combo_label": _TOOL_LABELS_FA["customer_landing_offer"],
        "reason_for_recommendation": "چون قبل از هرچیز باید مشتری جدید کارت را ببیند و سریع تصمیم بگیرد.",
        "preview_archetype": "lead_landing_page",
    },
    "نظم در کارها": _CAFE_GOAL_RECOMMENDATIONS["نظم در کارها"],
    "دیدن حساب‌ها یا گزارش‌ها": _CAFE_GOAL_RECOMMENDATIONS["دیدن حساب‌ها یا گزارش‌ها"],
}


def get_goal_based_recommendation(raw_text: str, goal_label: str) -> dict[str, Any]:
    """
    Second-stage, still-rule-based recommendation: given the ORIGINAL
    raw request text (for business context like "کافه") and the goal
    the user just picked (e.g. "فروش بیشتر"), return a practical
    product/tool recommendation — never a website-section question.

    Returns the same shape as get_need_first_recommendation()'s normal
    (non-clarification) branch, so the existing NeedFirstResponse/
    build_need_first_text() presentation layer can render it unchanged.
    """
    text = (raw_text or "").strip()
    is_cafe = any(k in text for k in ["کافه", "رستوران", "کافی‌شاپ", "کافیشاپ"])

    table = _CAFE_GOAL_RECOMMENDATIONS if is_cafe else _GENERIC_GOAL_RECOMMENDATIONS
    entry = table.get(goal_label)

    if entry is None:
        # Unknown goal label (shouldn't normally happen since the UI only
        # sends back labels we ourselves offered) — fail safe into the
        # original clarification question rather than guessing.
        return {
            "detected_pain_or_goal": None,
            "business_context": "کافه" if is_cafe else None,
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

    return {
        "detected_pain_or_goal": entry["detected_pain_or_goal"],
        "business_context": "کافه" if is_cafe else None,
        "user_named_tool_if_any": None,
        "recommended_options": [
            {"tool_key": o["tool_key"], "label": o["label"]} for o in entry["recommended_options"]
        ],
        "recommended_options_explanations": {
            o["tool_key"]: o["explanation"] for o in entry["recommended_options"] if o.get("explanation")
        },
        "factory_recommendation": entry["factory_recommendation"],
        "factory_recommendation_combo_label": entry.get("factory_recommendation_combo_label"),
        "reason_for_recommendation": entry["reason_for_recommendation"],
        "needs_clarification": False,
        "preview_archetype": entry.get("preview_archetype"),
    }
