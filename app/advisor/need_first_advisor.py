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

Legacy Replacement Sprint (Phase 4): every archetype value used in this
module's _TOOL_ARCHETYPES table MUST come from the single central list
in app/contract/product_contract.py. _ASSERT_ALL_ARCHETYPES_VALID below
runs at import time and raises immediately if any value here is not in
that central list — this makes the "two diverging archetype lists"
failure mode impossible to ship silently, without needing a separate
test file.
"""
from __future__ import annotations

from typing import Any

from app.contract.product_contract import VALID_ARCHETYPES


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
    # Puzzle: "Fix selected option propagation" — exact admin/task-org
    # options requested, each with its OWN distinct archetype so picking
    # a different option genuinely produces a different preview.
    "task_dashboard":            "داشبورد کارها و جلسات",
    "client_followup_list":      "لیست پیگیری مشتری‌ها",
    "team_task_board":           "تقسیم وظایف بین افراد",
}

# ── tool_key -> preview_archetype (THE core fix) ─────────────────────────────
# Previously, only the top-level factory_recommendation carried a
# preview_archetype — individual options did not, so picking a
# non-recommended option (e.g. "لیست پیگیری مشتری‌ها") had NO archetype
# at all. The frontend then fell through to the old website-section
# diagnostic flow (mock_pm), which asked unrelated sales/booking
# questions and could render a completely unrelated salon/booking
# preview. Now every tool_key that can appear as a selectable option is
# mapped here, and build_need_first_text()/the frontend attach this
# archetype to EACH option, not just the recommended one.
_TOOL_ARCHETYPES: dict[str, str] = {
    "digital_menu_order": "digital_menu_order_page",
    "walkin_landing": "lead_landing_page",
    "customer_followup": "simple_crm_followup_mockup",
    "cafe_intro_site": "lead_landing_page",
    "cafe_intro_menu_site": "digital_menu_order_page",
    "special_offer_landing": "lead_landing_page",
    "portfolio_request_form": "service_portfolio_request_page",
    "service_price_intro": "service_portfolio_request_page",
    "measurement_booking": "booking_page_mockup",
    "catalog_order": "product_catalog_order_page",
    "brand_intro_page": "lead_landing_page",
    "quick_order_form": "product_catalog_order_page",
    "new_customer_acquisition": "lead_landing_page",
    "digital_menu_order_goal": "digital_menu_order_page",
    "returning_customer_tool": "simple_crm_followup_mockup",
    "digital_menu_simple_order": "digital_menu_order_page",
    "quick_order_form_goal": "product_catalog_order_page",
    "simple_order_bot": "digital_menu_order_page",  # bot not buildable yet; closest honest mockup
    "customer_landing_offer": "lead_landing_page",
    "digital_menu_fast_decision": "digital_menu_order_page",
    "contact_or_booking_form": "booking_page_mockup",
    "simple_task_dashboard_goal": "task_dashboard_mockup",
    "order_request_form": "service_portfolio_request_page",
    "customer_followup_list": "simple_crm_followup_mockup",
    "simple_finance_dashboard": "task_dashboard_mockup",  # closest existing dashboard archetype
    "income_order_log": "task_dashboard_mockup",
    "simple_periodic_report": "task_dashboard_mockup",
    "task_dashboard": "task_dashboard_mockup",
    "client_followup_list": "simple_crm_followup_mockup",
    "team_task_board": "team_task_board_mockup",
}

# Phase 4 structural guard: every archetype value above must exist in the
# central VALID_ARCHETYPES list. This raises at import time (i.e. the
# app fails to start) rather than allowing a silently-diverging list to
# ship — the explicit alternative to a separate test file.
_unknown_archetypes = {v for v in _TOOL_ARCHETYPES.values() if v not in VALID_ARCHETYPES}
if _unknown_archetypes:
    raise RuntimeError(
        f"need_first_advisor._TOOL_ARCHETYPES references archetypes not in "
        f"the central VALID_ARCHETYPES list: {_unknown_archetypes}. "
        f"Update app/contract/product_contract.py or fix this table."
    )


# ── Proposed sections per tool_key (THE fix for "empty fake recommendation
# detail screens") ────────────────────────────────────────────────────────
# Puzzle: "Fix empty fake recommendation detail screens". Previously the
# confirmation screen ("این بخش‌ها را پیشنهاد می‌کنم") showed whatever
# `bullets` happened to come back from the OLD website-section
# understanding call — which is empty for need-first-confirmed options
# that never reach that old flow. Every selectable tool_key now has a
# guaranteed, specific, non-empty list of proposed sections here, scoped
# to exactly what that option means (e.g. "تقسیم وظایف بین افراد" gets
# team/assignment-focused sections, NOT the same list as "داشبورد کارها
# و جلسات", even though both currently share the task_dashboard_mockup
# archetype under the hood).
_PROPOSED_SECTIONS_BY_TOOL_KEY: dict[str, list[str]] = {
    "task_dashboard": [
        "کارهای امروز",
        "جلسات آینده",
        "وضعیت کارها (انجام‌نشده/در حال انجام/انجام‌شده)",
        "تقویم و یادآوری‌ها",
        "افزودن کار یا جلسه",
    ],
    "simple_task_dashboard_goal": [
        "کارهای امروز",
        "وضعیت کارها (انجام‌نشده/در حال انجام/انجام‌شده)",
        "افزودن کار جدید",
    ],
    "team_task_board": [
        "اعضای تیم و مسئول هر کار",
        "لیست کارهای هر نفر",
        "وضعیت انجام کارها",
        "مهلت‌ها و یادآوری‌ها",
        "جلسات مرتبط با تیم",
    ],
    "client_followup_list": [
        "نام مشتری",
        "وضعیت پیگیری",
        "آخرین تماس یا پیام",
        "اقدام بعدی",
        "یادآوری پیگیری",
    ],
    "customer_followup_list": [
        "نام مشتری",
        "وضعیت پیگیری",
        "آخرین تماس یا پیام",
        "اقدام بعدی",
    ],
    "returning_customer_tool": [
        "نام مشتری",
        "آخرین خرید/مراجعه",
        "یادآوری برگشت مشتری",
    ],
    "customer_followup": [
        "نام مشتری",
        "وضعیت پیگیری",
        "یادآوری پیگیری بعدی",
    ],
    "contact_or_booking_form": [
        "نام و شماره تماس",
        "انتخاب خدمت یا موضوع",
        "انتخاب زمان پیشنهادی",
        "پیام کوتاه مشتری",
        "دکمه ارسال درخواست",
    ],
    "measurement_booking": [
        "نام و شماره تماس",
        "انتخاب روز و ساعت اندازه‌گیری",
        "پیام کوتاه مشتری",
        "دکمه ثبت درخواست نوبت",
    ],
    "simple_finance_dashboard": [
        "خلاصه درآمد و هزینه",
        "جمع‌بندی ماهانه",
        "افزودن تراکنش جدید",
    ],
    "income_order_log": [
        "لیست سفارش‌ها",
        "میزان درآمد هر سفارش",
        "جمع‌بندی دوره‌ای",
    ],
    "simple_periodic_report": [
        "گزارش روزانه",
        "گزارش هفتگی",
        "نمودار ساده روند",
    ],
    "catalog_order": [
        "نمایش محصولات با عکس و قیمت",
        "توضیح کوتاه هر محصول",
        "فرم سفارش ساده",
        "راه تماس برای سفارش",
    ],
    "quick_order_form": [
        "نام محصول",
        "تعداد سفارش",
        "اطلاعات تماس",
        "دکمه ارسال سفارش",
    ],
    "brand_intro_page": [
        "معرفی کوتاه برند",
        "نمونه محصولات",
        "راه ارتباط با فروشنده",
    ],
    "digital_menu_order": [
        "دسته‌بندی منو",
        "قیمت هر آیتم",
        "فرم سفارش ساده",
        "راه تماس برای سفارش",
    ],
    "digital_menu_order_goal": [
        "دسته‌بندی منو",
        "قیمت هر آیتم",
        "ثبت سفارش ساده",
    ],
    "digital_menu_simple_order": [
        "دسته‌بندی منو",
        "قیمت هر آیتم",
        "ثبت سفارش ساده",
    ],
    "digital_menu_fast_decision": [
        "دسته‌بندی منو با عکس",
        "قیمت هر آیتم",
        "دکمه تماس سریع",
    ],
    "simple_order_bot": [
        "خوش‌آمدگویی و معرفی منو",
        "انتخاب آیتم سفارش",
        "تأیید نهایی سفارش",
    ],
    "portfolio_request_form": [
        "نمونه‌کارهای قبلی",
        "توضیح کوتاه هر نمونه‌کار",
        "فرم درخواست سفارش",
        "اطلاعات تماس",
    ],
    "service_price_intro": [
        "لیست خدمات",
        "قیمت حدودی هر خدمت",
        "راه تماس",
    ],
    "order_request_form": [
        "نوع درخواست/سفارش",
        "توضیح کوتاه درخواست",
        "اطلاعات تماس",
    ],
    "walkin_landing": [
        "معرفی کوتاه و جذاب",
        "آدرس و نحوه دسترسی",
        "دعوت به حضور",
    ],
    "new_customer_acquisition": [
        "معرفی کوتاه کسب‌وکار",
        "یک دلیل قانع‌کننده برای انتخاب",
        "آدرس و راه تماس",
        "دعوت به اقدام",
    ],
    "special_offer_landing": [
        "معرفی پیشنهاد ویژه",
        "مدت زمان پیشنهاد",
        "دعوت به اقدام",
    ],
    "customer_landing_offer": [
        "عکس و معرفی کوتاه",
        "آدرس",
        "پیشنهاد ویژه",
    ],
    "cafe_intro_site": [
        "معرفی فضای کافه",
        "عکس‌های فضا",
        "آدرس و تماس",
    ],
    "cafe_intro_menu_site": [
        "معرفی کافه",
        "منوی دیجیتال",
        "آدرس و تماس",
    ],
}

# Archetype-level fallback (when a tool_key has no specific entry above,
# but its archetype does) — keeps the guarantee that EVERY selectable
# option produces a non-empty, archetype-appropriate section list.
_PROPOSED_SECTIONS_BY_ARCHETYPE: dict[str, list[str]] = {
    "task_dashboard_mockup": [
        "کارهای امروز",
        "وضعیت کارها",
        "افزودن کار جدید",
    ],
    "simple_crm_followup_mockup": [
        "نام مشتری",
        "وضعیت پیگیری",
        "یادآوری پیگیری بعدی",
    ],
    "booking_page_mockup": [
        "نام و شماره تماس",
        "انتخاب خدمت یا موضوع",
        "انتخاب زمان پیشنهادی",
        "دکمه ارسال درخواست",
    ],
    "product_catalog_order_page": [
        "نمایش محصولات",
        "قیمت و توضیح کوتاه",
        "فرم سفارش ساده",
    ],
    "digital_menu_order_page": [
        "دسته‌بندی منو",
        "قیمت هر آیتم",
        "ثبت سفارش ساده",
    ],
    "service_portfolio_request_page": [
        "نمونه‌کارهای قبلی",
        "فرم درخواست سفارش",
        "اطلاعات تماس",
    ],
    "lead_landing_page": [
        "معرفی کوتاه",
        "دعوت به اقدام",
        "اطلاعات تماس",
    ],
}


def get_proposed_sections(tool_key: str | None, archetype: str | None) -> list[str]:
    """
    Returns a guaranteed non-empty list of proposed sections (3-5 items)
    for a given selected option, or an empty list only if BOTH the
    tool_key and the archetype are unrecognized — in which case the
    caller must show the safe fallback message instead of a confirm
    screen with nothing in it (Puzzle requirement: never let the user
    confirm an empty recommendation).
    """
    if tool_key and tool_key in _PROPOSED_SECTIONS_BY_TOOL_KEY:
        return list(_PROPOSED_SECTIONS_BY_TOOL_KEY[tool_key])
    if archetype and archetype in _PROPOSED_SECTIONS_BY_ARCHETYPE:
        return list(_PROPOSED_SECTIONS_BY_ARCHETYPE[archetype])
    return []


def _opt(tool_key: str) -> dict[str, Any]:
    archetype = _TOOL_ARCHETYPES.get(tool_key)
    return {
        "tool_key": tool_key,
        "label": _TOOL_LABELS_FA[tool_key],
        "archetype": archetype,
        "proposed_sections": get_proposed_sections(tool_key, archetype),
    }


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
            # Puzzle: "Fix selected option propagation" — these 3 options
            # are scoped to internal work management ONLY (no
            # sales/booking/marketing options here), and each carries
            # its OWN archetype (via _opt -> _TOOL_ARCHETYPES) so picking
            # a different one genuinely produces a different preview.
            "recommended_options": [
                _opt("task_dashboard"),
                _opt("client_followup_list"),
                _opt("team_task_board"),
            ],
            "factory_recommendation": "task_dashboard",
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
            {
                "tool_key": o["tool_key"],
                "label": o["label"],
                "archetype": _TOOL_ARCHETYPES.get(o["tool_key"]),
                "proposed_sections": get_proposed_sections(o["tool_key"], _TOOL_ARCHETYPES.get(o["tool_key"])),
            }
            for o in entry["recommended_options"]
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
