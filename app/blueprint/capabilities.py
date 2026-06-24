"""
Output Capability Matrix — static data (Puzzle 7, AI Factory v2 honesty layer).

This file answers one question honestly: for a given recommended output
type (e.g. "product_catalog_order_page", "financial_dashboard_mockup"),
what can the factory ACTUALLY build right now — a real working preview,
a visual mockup only, or nothing at all yet?

This is intentionally DATA + ONE HELPER FUNCTION ONLY — no logic, no AI
calls, no UI, no connection to the builder or the recommendation step.
Nothing in the current app imports or uses this file yet. The existing
Website Preview Builder flow (request -> understanding -> diagnostic
question -> confirm -> recommendation -> generate-preview ->
revision/edit-direct -> approve -> export), `website_intent`,
ProductBlueprint (app/blueprint/models.py), the rule-based generator
(app/blueprint/generator.py), and the recommendation wording
(app/blueprint/recommendation_text.py) are completely unaffected by
this file.

Why this exists:
Without this matrix, the factory has no honest, structured way to know
"can I actually build this, or am I about to overpromise?" — the
recommendation step (Puzzle 6.6) currently writes its own ad-hoc
"not fully supported yet" sentences for non-website outputs. This
matrix is the future single source of truth for that honesty check,
so it can eventually replace those ad-hoc checks instead of duplicating
them per-feature. That wiring is NOT done by this file — only the data
shape and a lookup helper.

Status meanings:
  "supported"            -- a real, working preview can be built today.
  "partially_supported"  -- only a visual mockup can be built; no real
                             backend behavior (booking, accounting,
                             task automation, etc.) exists yet.
  "not_supported"         -- nothing can be built for this yet; this is
                             a future output type only.
"""
from __future__ import annotations

from typing import Any, Literal


CapabilityStatus = Literal["supported", "partially_supported", "not_supported"]


OUTPUT_CAPABILITY_MATRIX: list[dict[str, Any]] = [
    {
        "output_type": "product_catalog_order_page",
        "status": "supported",
        "plain_persian_name": "کاتالوگ محصول و صفحه سفارش",
        "plain_english_name": "Product catalog + order page",
        "what_it_can_do_now": (
            "یک پیش‌نمایش واقعی و کامل از کاتالوگ محصول با عکس/آیکون، قیمت، "
            "توضیح، و یک فرم سفارش ساده — قابل ویرایش با کلیک یا با جمله."
        ),
        "current_limitations": (
            "پرداخت آنلاین واقعی، انبارداری، و ارسال خودکار هنوز وجود ندارد؛ "
            "فرم سفارش فقط یک پیام تأیید نمایشی نشان می‌دهد، چیزی ذخیره/ارسال نمی‌شود."
        ),
        "honest_user_message_fa": (
            "این یک پیش‌نمایش واقعی و کامل از کاتالوگ و صفحه سفارش است — می‌توانی همین حالا آن را ببینی و ویرایش کنی."
        ),
        "honest_user_message_en": (
            "This is a real, complete preview of the catalog and order page — you can see and edit it right now."
        ),
    },
    {
        "output_type": "service_portfolio_request_page",
        "status": "supported",
        "plain_persian_name": "صفحه نمونه‌کار و فرم درخواست",
        "plain_english_name": "Portfolio + service request page",
        "what_it_can_do_now": (
            "یک پیش‌نمایش واقعی و کامل از معرفی خدمات، نمایش نمونه‌کارها، و یک فرم "
            "درخواست/تماس — قابل ویرایش با کلیک یا با جمله."
        ),
        "current_limitations": (
            "پیگیری خودکار وضعیت سفارش، تقویم نوبت‌دهی واقعی، و اعلان خودکار هنوز وجود ندارد."
        ),
        "honest_user_message_fa": (
            "این یک پیش‌نمایش واقعی و کامل از صفحه معرفی و درخواست خدمات است — می‌توانی همین حالا آن را ببینی و ویرایش کنی."
        ),
        "honest_user_message_en": (
            "This is a real, complete preview of the service/portfolio request page — you can see and edit it right now."
        ),
    },
    {
        "output_type": "booking_page_mockup",
        "status": "partially_supported",
        "plain_persian_name": "نمایش اولیه صفحه رزرو",
        "plain_english_name": "Booking page mockup",
        "what_it_can_do_now": (
            "یک نمایش بصری از شکل صفحه رزرو (لیست خدمات، فرم انتخاب زمان) — "
            "ظاهر آن را می‌توان دید و ویرایش کرد."
        ),
        "current_limitations": (
            "هیچ سیستم واقعی رزرو، تقویم زمان‌های آزاد/پر، یا تأیید خودکار نوبت پشت این نمایش وجود ندارد — "
            "فقط ظاهر صفحه است، نه یک سیستم رزرو کارکننده."
        ),
        "honest_user_message_fa": (
            "این فقط یک نمایش اولیه از ظاهر صفحه رزرو است؛ سیستم واقعی رزرو نوبت هنوز ساخته نشده."
        ),
        "honest_user_message_en": (
            "This is only an early visual mockup of the booking page; a real booking system is not built yet."
        ),
    },
    {
        "output_type": "financial_dashboard_mockup",
        "status": "partially_supported",
        "plain_persian_name": "نمایش اولیه داشبورد مالی",
        "plain_english_name": "Financial dashboard mockup",
        "what_it_can_do_now": (
            "یک نمایش بصری از شکل یک داشبورد مالی ساده (مثلاً کارت‌های درآمد/هزینه) — "
            "ظاهر آن را می‌توان دید."
        ),
        "current_limitations": (
            "هیچ پایگاه داده مالی واقعی، محاسبه خودکار، یا اتصال به حساب بانکی پشت این نمایش وجود ندارد — "
            "فقط یک ماکت بصری است، نه یک ابزار حسابداری کارکننده."
        ),
        "honest_user_message_fa": (
            "این فقط یک نمایش اولیه از ظاهر داشبورد مالی است؛ پایگاه داده حسابداری واقعی هنوز ساخته نشده."
        ),
        "honest_user_message_en": (
            "This is only an early visual mockup of the financial dashboard; a real accounting database is not built yet."
        ),
    },
    {
        "output_type": "task_dashboard_mockup",
        "status": "partially_supported",
        "plain_persian_name": "نمایش اولیه داشبورد وظایف",
        "plain_english_name": "Task dashboard mockup",
        "what_it_can_do_now": (
            "یک نمایش بصری از شکل یک داشبورد ساده وظایف (لیست کارها، وضعیت انجام) — "
            "ظاهر آن را می‌توان دید."
        ),
        "current_limitations": (
            "هیچ سیستم واقعی اعلان، تخصیص خودکار وظیفه، یا همگام‌سازی با تیم پشت این نمایش وجود ندارد — "
            "فقط یک ماکت بصری است، نه یک ابزار مدیریت وظایف کارکننده."
        ),
        "honest_user_message_fa": (
            "این فقط یک نمایش اولیه از ظاهر داشبورد وظایف است؛ سیستم واقعی مدیریت وظایف هنوز ساخته نشده."
        ),
        "honest_user_message_en": (
            "This is only an early visual mockup of the task dashboard; a real task-management system is not built yet."
        ),
    },
    {
        "output_type": "support_bot",
        "status": "not_supported",
        "plain_persian_name": "ربات پاسخ‌گویی به مشتری",
        "plain_english_name": "Support bot",
        "what_it_can_do_now": "هیچ — این خروجی هنوز قابل ساخت نیست.",
        "current_limitations": (
            "هیچ موتور گفتگو، اتصال به پیام‌رسان، یا منطق پاسخ‌گویی خودکار هنوز پیاده‌سازی نشده است."
        ),
        "honest_user_message_fa": "این یک خروجی آینده کارخانه است و هنوز قابل ساخت نیست.",
        "honest_user_message_en": "This is a future factory output and cannot be built yet.",
    },
    {
        "output_type": "mobile_app",
        "status": "not_supported",
        "plain_persian_name": "اپلیکیشن موبایل",
        "plain_english_name": "Mobile app",
        "what_it_can_do_now": "هیچ — این خروجی هنوز قابل ساخت نیست.",
        "current_limitations": (
            "هیچ موتور ساخت اپلیکیشن موبایل (iOS/Android) هنوز پیاده‌سازی نشده است."
        ),
        "honest_user_message_fa": "این یک خروجی آینده کارخانه است و هنوز قابل ساخت نیست.",
        "honest_user_message_en": "This is a future factory output and cannot be built yet.",
    },
    {
        "output_type": "managed_ai_agent",
        "status": "not_supported",
        "plain_persian_name": "ایجنت هوشمند مدیریت محصول",
        "plain_english_name": "Managed AI agent",
        "what_it_can_do_now": "هیچ — این خروجی هنوز قابل ساخت نیست.",
        "current_limitations": (
            "هیچ ایجنت واقعی (فروش، پشتیبانی، مدیریت محصول و...) با حافظه یا تصمیم‌گیری مستقل "
            "هنوز پیاده‌سازی نشده است — حتی نمونه‌های فعلی، صرفاً توابع کد معمولی هستند، نه ایجنت."
        ),
        "honest_user_message_fa": "این یک خروجی آینده کارخانه است و هنوز قابل ساخت نیست.",
        "honest_user_message_en": "This is a future factory output and cannot be built yet.",
    },
]


_SAFE_FALLBACK_TEMPLATE: dict[str, Any] = {
    "status": "not_supported",
    "plain_persian_name": "خروجی ناشناخته",
    "plain_english_name": "Unknown output",
    "what_it_can_do_now": "هیچ — این نوع خروجی هنوز در کارخانه تعریف نشده است.",
    "current_limitations": "این نوع خروجی هنوز شناخته‌شده یا پیاده‌سازی‌شده نیست.",
    "honest_user_message_fa": "این نوع خروجی هنوز در کارخانه تعریف نشده و قابل ساخت نیست.",
    "honest_user_message_en": "This output type is not yet defined in the factory and cannot be built.",
}


def get_output_capability(output_type: str) -> dict[str, Any]:
    """
    Look up the capability entry for a given output_type. If the
    output_type is unknown (not in the matrix), returns a safe fallback
    with status "not_supported" — never silently claims support for
    something the factory doesn't recognize.
    """
    for entry in OUTPUT_CAPABILITY_MATRIX:
        if entry["output_type"] == output_type:
            return entry

    fallback = dict(_SAFE_FALLBACK_TEMPLATE)
    fallback["output_type"] = output_type
    return fallback
