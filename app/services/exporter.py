"""
Exporter Service — with Delivery Education Layer.

Delivery includes education.
The factory must explain the delivered product in clear, confidence-building,
non-technical, and anxiety-free language.

The user should never see:
  JSON, backend, database, API, deployment, GitHub, hosting, server,
  endpoint, auth, token, webhook, scenario, family, template, reviewer.

Future sprints can use export_data as input to:
  - HTML/CSS/JS code generator
  - App generator
  - Download system
  - Demo presenter
"""
from __future__ import annotations

from typing import Any


# ─── Delivery education profiles ──────────────────────────────────────────────
# Each profile explains the delivered product in simple human language.
# Internal scenario/family keys are never shown to the user.
# Examples are reasoning tests, not fixed product definitions.
# A reminder profile works for medicine, plants, customer calls, or daily tasks.

_DELIVERY_PROFILES: dict[str, dict[str, Any]] = {
    "family_reminder_or_routine": {
        "what_delivered":   "یک ابزار ساده یادآوری و پیگیری کارهای روزانه",
        "helps_you_do":     "کارهایی که نباید فراموش کنی را در یک جا ثبت کنی، وضعیت هر کار را ببینی، و هیچ چیز مهمی از دستت نرود",
        "how_to_use":       "لیست یادآورهایت را باز کن، کار جدید اضافه کن، و وقتی انجام شد تیک بزن",
        "included_now":     ["ثبت یادآور جدید", "تعیین زمان یادآوری", "علامت‌گذاری انجام‌شده/انجام‌نشده", "یادداشت کوتاه برای هر کار"],
        "not_yet":          ["ارسال خودکار پیام یادآور به تلگرام یا پیامک", "یادآور زمان‌بندی‌شده پیشرفته"],
        "next_step":        "می‌توانی یادآورهایت را کامل‌تر کنی و بعداً اتصال به پیام‌رسان‌ها را اضافه کنی",
    },
    "family_simple_finance_or_tracking": {
        "what_delivered":   "یک ابزار ساده ثبت و پیگیری پول روزانه",
        "helps_you_do":     "درآمد و هزینه‌های روزانه‌ات را ثبت کنی، مانده را ببینی، و کنترل بیشتری روی پول کارت داشته باشی",
        "how_to_use":       "هر بار پول گرفتی یا خرج کردی وارد کن، جمع‌بندی روزانه را ببین",
        "included_now":     ["ثبت درآمد", "ثبت هزینه", "مشاهده مانده", "جمع‌بندی ساده روزانه"],
        "not_yet":          ["اتصال به حساب بانکی", "گزارش‌های پیشرفته حسابداری", "پرداخت آنلاین"],
        "next_step":        "می‌توانی ثبت طلب و بدهی مشتریان را هم اضافه کنی",
    },
    "family_customer_management": {
        "what_delivered":   "یک دفترچه ساده برای اطلاعات و پیگیری مشتریان",
        "helps_you_do":     "اطلاعات مشتری‌هایت را در یک جا نگه داری، آخرین تماس را ببینی، و پیگیری‌های بعدی را فراموش نکنی",
        "how_to_use":       "برای هر مشتری یک کارت بساز، اطلاعات تماس را وارد کن، یادداشت بگذار و تاریخ پیگیری تنظیم کن",
        "included_now":     ["لیست مشتریان", "اطلاعات تماس", "یادداشت آزاد", "تاریخ آخرین تماس", "یادآور پیگیری"],
        "not_yet":          ["ارسال پیام خودکار به مشتریان", "اتصال به CRM پیشرفته", "گزارش فروش پیشرفته"],
        "next_step":        "می‌توانی سابقه سفارش‌های هر مشتری را هم اضافه کنی",
    },
    "family_internal_admin_tool": {
        "what_delivered":   "یک ابزار ساده مدیریت وظایف تیم",
        "helps_you_do":     "کارهای تیمت را تعریف کنی، مسئول هر کار را مشخص کنی، و وضعیت پیشرفت را ببینی",
        "how_to_use":       "وظیفه جدید تعریف کن، مسئول و مهلت مشخص کن، وضعیت را به‌روز کن",
        "included_now":     ["تعریف وظیفه", "تعیین مسئول", "وضعیت انجام/در حال انجام", "چک‌لیست روزانه"],
        "not_yet":          ["سیستم تأیید و گردش کار پیشرفته", "اعلان خودکار به اعضای تیم", "گزارش عملکرد"],
        "next_step":        "می‌توانی فرم‌های ثبت اطلاعات را هم اضافه کنی",
    },
    "family_content_or_marketing": {
        "what_delivered":   "یک ابزار ساده برنامه‌ریزی و پیش‌نویس محتوا",
        "helps_you_do":     "ایده‌های محتوایت را یادداشت کنی، پیش‌نویس بنویسی، و برنامه هفتگی داشته باشی",
        "how_to_use":       "ایده جدید بنویس، پیش‌نویس آماده کن، قبل از انتشار مرور کن",
        "included_now":     ["ثبت ایده محتوا", "پیش‌نویس پیام", "برنامه هفتگی", "تأیید قبل از انتشار"],
        "not_yet":          ["انتشار خودکار در اینستاگرام یا تلگرام", "اتصال به شبکه‌های اجتماعی", "تولید خودکار محتوا با هوش مصنوعی"],
        "next_step":        "می‌توانی محتوای تأیید‌شده را به صورت دستی منتشر کنی",
    },
    "family_business_growth_or_operations": {
        "what_delivered":   "یک مرکز ساده نمای کلی کسب‌وکار",
        "helps_you_do":     "اهداف اصلی‌ات را ثبت کنی، اولویت‌های روزانه را ببینی، و یک نمای کلی از وضعیت کارت داشته باشی",
        "how_to_use":       "هر هفته اهدافت را مرور کن، اولویت‌های امروز را مشخص کن، و پیشرفت را ثبت کن",
        "included_now":     ["ثبت اهداف اصلی", "اولویت‌های روزانه", "نمای کلی وضعیت", "گزارش ساده هفتگی"],
        "not_yet":          ["اجرای خودکار کارها توسط هوش مصنوعی", "agent های عملیاتی", "اتوماسیون کسب‌وکار"],
        "next_step":        "می‌توانی مشتریان، فروش، یا وظایف تیم را به این مرکز وصل کنی",
    },
    "family_website_or_public_presence": {
        "what_delivered":   "یک صفحه معرفی ساده برای کسب‌وکارت",
        "helps_you_do":     "کارت را به مشتریان معرفی کنی، خدمات اصلی را نشان بدهی، و راه تماس را واضح کنی",
        "how_to_use":       "لینک صفحه را با مشتریانت به اشتراک بگذار، اطلاعات تماس را کامل نگه دار",
        "included_now":     ["معرفی کوتاه کسب‌وکار", "خدمات یا محصولات اصلی", "راه تماس"],
        "not_yet":          ["سفارش آنلاین", "پرداخت آنلاین", "رزرو آنلاین", "اتصال به دامنه اختصاصی"],
        "next_step":        "می‌توانی فرم تماس یا دکمه سفارش را اضافه کنی",
    },
    # Tier-1/Tier-2 scenarios
    "restaurant": {
        "what_delivered":   "یک صفحه معرفی و سفارش برای کافه یا رستورانت",
        "helps_you_do":     "مشتریان منوت را ببینند، سفارش بدهند، و با تو تماس بگیرند",
        "how_to_use":       "لینک را با مشتریانت به اشتراک بگذار، منو را به‌روز نگه دار",
        "included_now":     ["معرفی کافه/رستوران", "منو با قیمت", "دکمه سفارش", "اطلاعات تماس"],
        "not_yet":          ["پرداخت آنلاین", "رزرو میز آنلاین", "اپلیکیشن موبایل"],
        "next_step":        "می‌توانی سیستم رزرو میز یا پرداخت آنلاین اضافه کنی",
    },
    "store": {
        "what_delivered":   "یک فروشگاه ساده آنلاین",
        "helps_you_do":     "مشتریانت محصولاتت را ببینند و سفارش بدهند",
        "how_to_use":       "محصولاتت را به‌روز نگه دار، سفارش‌های رسیده را پیگیری کن",
        "included_now":     ["نمایش محصولات", "دکمه سفارش", "اطلاعات تماس"],
        "not_yet":          ["پرداخت آنلاین خودکار", "انبارداری پیشرفته", "ارسال خودکار"],
        "next_step":        "می‌توانی سیستم پرداخت آنلاین اضافه کنی",
    },
    "booking": {
        "what_delivered":   "یک سیستم ساده رزرو",
        "helps_you_do":     "مشتریانت وقت یا خدمات رزرو کنند",
        "how_to_use":       "زمان‌های آزادت را مشخص کن، رزروهای رسیده را تأیید کن",
        "included_now":     ["نمایش زمان‌های آزاد", "فرم رزرو", "اطلاعات تماس"],
        "not_yet":          ["تأیید خودکار رزرو", "پرداخت پیش‌پرداخت", "یادآور خودکار"],
        "next_step":        "می‌توانی تأیید خودکار رزرو اضافه کنی",
    },
    "telegram_bot": {
        "what_delivered":   "یک ربات ساده تلگرام",
        "helps_you_do":     "مشتریانت پیام بفرستند، سؤال بپرسند، یا سفارش بدهند",
        "how_to_use":       "ربات را در تلگرام فعال کن، پیام‌های دریافتی را پاسخ بده",
        "included_now":     ["دریافت پیام", "پاسخ‌های آماده", "هدایت مشتری"],
        "not_yet":          ["پاسخ خودکار هوشمند", "اتصال به سیستم سفارش", "پرداخت در تلگرام"],
        "next_step":        "می‌توانی پاسخ‌های خودکار بیشتری تعریف کنی",
    },
    "company_landing": {
        "what_delivered":   "یک صفحه معرفی ساده برای کسب‌وکارت",
        "helps_you_do":     "کارت را به مشتریان معرفی کنی و راه تماس را واضح کنی",
        "how_to_use":       "لینک صفحه را به اشتراک بگذار، اطلاعات تماس را کامل نگه دار",
        "included_now":     ["معرفی کسب‌وکار", "خدمات اصلی", "راه تماس"],
        "not_yet":          ["سفارش آنلاین", "پرداخت آنلاین", "دامنه اختصاصی"],
        "next_step":        "می‌توانی دکمه سفارش یا فرم تماس اضافه کنی",
    },
}

_DEFAULT_PROFILE: dict[str, Any] = {
    "what_delivered":   "یک محصول دیجیتال ساده متناسب با نیازت",
    "helps_you_do":     "کارت را آنلاین‌تر و منظم‌تر کنی",
    "how_to_use":       "محصول آماده را باز کن و با داده‌های واقعی کارت شروع کن",
    "included_now":     ["ساختار اصلی محصول", "قابلیت‌های پایه"],
    "not_yet":          ["قابلیت‌های پیشرفته‌تر در مراحل بعدی اضافه می‌شوند"],
    "next_step":        "می‌توانی محصول را گسترش بدهی و قابلیت‌های بیشتری اضافه کنی",
}


def _get_delivery_profile(scenario: str) -> dict[str, Any]:
    """Return the delivery education profile for the given scenario.
    Family-prefixed scenarios and Tier-1 scenarios have dedicated profiles.
    Falls back to a generic profile for unknown scenarios.
    """
    return _DELIVERY_PROFILES.get(scenario, _DEFAULT_PROFILE)


def _build_delivery_education(
    scenario: str,
    title: str,
    profile: dict[str, Any],
) -> dict[str, Any]:
    """
    Build the user-facing delivery education summary.
    All fields use clear, confidence-building, non-technical, and anxiety-free language.
    Internal labels (scenario, family_, template, reviewer) are never included.
    """
    product_name = title or profile["what_delivered"]
    return {
        "title":        "تحویل محصول آماده شد",
        "product_name": product_name,
        "sections": {
            "چه چیزی آماده شده؟":              profile["what_delivered"],
            "این محصول به چه کاری کمک می‌کند؟": profile["helps_you_do"],
            "چطور از آن استفاده کنی؟":          profile["how_to_use"],
            "در نسخه اولیه چه چیزهایی هست؟":   profile["included_now"],
            "چه چیزهایی بعداً قابل اضافه شدن است؟": profile["not_yet"],
            "قدم بعدی پیشنهادی":               profile["next_step"],
        },
    }


def create_export_package(
    project: dict,
    version: dict,
    builder_output: dict | None,
) -> dict[str, Any]:
    """
    Produce a clean, exportable package from the approved version.
    Includes a delivery education summary for non-technical users.

    Prefers builder_output.preview_data for richest content;
    falls back to version.user_visible_preview if output is unavailable.
    """
    scenario   = project.get("scenario") or "general"
    version_id = version["id"]
    project_id = project["id"]

    # Choose richest available preview
    preview: dict[str, Any] = {}
    if builder_output and builder_output.get("preview_data"):
        preview = builder_output["preview_data"]
    elif version.get("user_visible_preview"):
        preview = version["user_visible_preview"]

    # Internal export data — never exposed directly to non-technical users
    export_data: dict[str, Any] = {
        "project_id":   project_id,
        "version_id":   version_id,
        "scenario":     scenario,
        "title":        preview.get("title", ""),
        "subtitle":     preview.get("subtitle", ""),
        "preview":      preview,
        "approved":     True,
        "packaged_for": "demo_and_future_build",
    }

    # Add scenario-specific fields for downstream build use
    if scenario == "restaurant":
        export_data["menu_items"]       = preview.get("menu_items", [])
        export_data["primary_button"]   = preview.get("primary_button", "")
        export_data["secondary_button"] = preview.get("secondary_button", "")
    elif scenario in ("dashboard", "family_simple_finance_or_tracking",
                      "family_customer_management", "family_internal_admin_tool",
                      "family_business_growth_or_operations"):
        export_data["cards"]    = preview.get("cards", [])
        export_data["sections"] = preview.get("sections", [])
    elif scenario in ("company_landing", "family_website_or_public_presence",
                      "family_content_or_marketing", "news_site"):
        export_data["sections"]       = preview.get("sections", [])
        export_data["primary_button"] = preview.get("primary_button", "")

    # ── Delivery education layer ───────────────────────────────────────────────
    profile           = _get_delivery_profile(scenario)
    delivery_education = _build_delivery_education(
        scenario=scenario,
        title=preview.get("title", ""),
        profile=profile,
    )

    summary = f"خروجی «{export_data['title'] or scenario}» آماده است."

    return {
        "export_type":          "preview_package",
        "export_data":          export_data,       # internal — for downstream build
        "delivery_education":   delivery_education, # user-facing — clear, non-technical
        "summary":              summary,
    }
