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
        "what_delivered":   "پیش‌نمایش اولیه یک ابزار یادآوری و پیگیری کارهای روزانه",
        "helps_you_do":     "کارهایی که نباید فراموش کنی را در یک جا ثبت کنی، وضعیت هر کار را ببینی، و هیچ چیز مهمی از دستت نرود",
        "how_to_use":       "این یک نسخه اولیه قابل بررسی است؛ لیست یادآورهایت را باز کن و ببین آیا همین‌طوری که می‌خواهی هست",
        "included_now":     ["ثبت یادآور جدید", "تعیین زمان یادآوری", "علامت‌گذاری انجام‌شده/انجام‌نشده", "یادداشت کوتاه برای هر کار"],
        "not_yet":          ["ارسال خودکار پیام یادآور به تلگرام یا پیامک (هنوز فعال نیست)", "یادآور زمان‌بندی‌شده پیشرفته (هنوز فعال نیست)"],
        "next_step":        "در مرحله بعد می‌توان این را آنلاین و فعال کرد، و بعداً اتصال به پیام‌رسان‌ها را هم اضافه کرد",
    },
    "family_simple_finance_or_tracking": {
        "what_delivered":   "پیش‌نمایش اولیه یک ابزار ثبت و پیگیری پول روزانه",
        "helps_you_do":     "درآمد و هزینه‌های روزانه‌ات را ثبت کنی، مانده را ببینی، و کنترل بیشتری روی پول کارت داشته باشی",
        "how_to_use":       "این یک نسخه اولیه قابل بررسی است؛ ببین ثبت درآمد/هزینه همان‌طوری که می‌خواهی کار می‌کند یا نه",
        "included_now":     ["ثبت درآمد", "ثبت هزینه", "مشاهده مانده", "جمع‌بندی ساده روزانه"],
        "not_yet":          ["اتصال به حساب بانکی (هنوز فعال نیست)", "گزارش‌های پیشرفته حسابداری (هنوز فعال نیست)", "پرداخت آنلاین (هنوز فعال نیست)"],
        "next_step":        "در مرحله بعد می‌توان این را آنلاین و فعال کرد، و بعداً ثبت طلب و بدهی مشتریان را هم اضافه کرد",
    },
    "family_customer_management": {
        "what_delivered":   "پیش‌نمایش اولیه یک دفترچه برای اطلاعات و پیگیری مشتریان",
        "helps_you_do":     "اطلاعات مشتری‌هایت را در یک جا نگه داری، آخرین تماس را ببینی، و پیگیری‌های بعدی را فراموش نکنی",
        "how_to_use":       "این یک نسخه اولیه قابل بررسی است؛ ببین ساختار کارت مشتری همان‌طوری که می‌خواهی هست",
        "included_now":     ["لیست مشتریان", "اطلاعات تماس", "یادداشت آزاد", "تاریخ آخرین تماس", "یادآور پیگیری"],
        "not_yet":          ["ارسال پیام خودکار به مشتریان (هنوز فعال نیست)", "اتصال به CRM پیشرفته (هنوز فعال نیست)", "گزارش فروش پیشرفته (هنوز فعال نیست)"],
        "next_step":        "در مرحله بعد می‌توان این را آنلاین و فعال کرد، و بعداً سابقه سفارش‌های هر مشتری را هم اضافه کرد",
    },
    "family_internal_admin_tool": {
        "what_delivered":   "پیش‌نمایش اولیه یک ابزار مدیریت وظایف تیم",
        "helps_you_do":     "کارهای تیمت را تعریف کنی، مسئول هر کار را مشخص کنی، و وضعیت پیشرفت را ببینی",
        "how_to_use":       "این یک نسخه اولیه قابل بررسی است؛ ببین تعریف وظیفه و تعیین مسئول همان‌طوری که می‌خواهی هست",
        "included_now":     ["تعریف وظیفه", "تعیین مسئول", "وضعیت انجام/در حال انجام", "چک‌لیست روزانه"],
        "not_yet":          ["سیستم تأیید و گردش کار پیشرفته (هنوز فعال نیست)", "اعلان خودکار به اعضای تیم (هنوز فعال نیست)", "گزارش عملکرد (هنوز فعال نیست)"],
        "next_step":        "در مرحله بعد می‌توان این را آنلاین و فعال کرد، و بعداً فرم‌های ثبت اطلاعات را هم اضافه کرد",
    },
    "family_content_or_marketing": {
        "what_delivered":   "پیش‌نمایش اولیه یک ابزار برنامه‌ریزی و پیش‌نویس محتوا",
        "helps_you_do":     "ایده‌های محتوایت را یادداشت کنی، پیش‌نویس بنویسی، و برنامه هفتگی داشته باشی",
        "how_to_use":       "این یک نسخه اولیه قابل بررسی است؛ ببین ثبت ایده و پیش‌نویس همان‌طوری که می‌خواهی کار می‌کند",
        "included_now":     ["ثبت ایده محتوا", "پیش‌نویس پیام", "برنامه هفتگی", "تأیید قبل از انتشار"],
        "not_yet":          ["انتشار خودکار در اینستاگرام یا تلگرام (هنوز فعال نیست)", "اتصال به شبکه‌های اجتماعی (هنوز فعال نیست)", "تولید خودکار محتوا با هوش مصنوعی (هنوز فعال نیست)"],
        "next_step":        "در مرحله بعد می‌توان این را آنلاین و فعال کرد؛ تا آن زمان، محتوای تأیید‌شده را می‌توانی به‌صورت دستی منتشر کنی",
    },
    "family_business_growth_or_operations": {
        "what_delivered":   "پیش‌نمایش اولیه یک مرکز نمای کلی کسب‌وکار",
        "helps_you_do":     "اهداف اصلی‌ات را ثبت کنی، اولویت‌های روزانه را ببینی، و یک نمای کلی از وضعیت کارت داشته باشی",
        "how_to_use":       "این یک نسخه اولیه قابل بررسی است؛ ببین ثبت اهداف و اولویت‌ها همان‌طوری که می‌خواهی هست",
        "included_now":     ["ثبت اهداف اصلی", "اولویت‌های روزانه", "نمای کلی وضعیت", "گزارش ساده هفتگی"],
        "not_yet":          ["اجرای خودکار کارها توسط هوش مصنوعی (هنوز فعال نیست)", "ایجنت‌های عملیاتی (هنوز فعال نیست)", "اتوماسیون کسب‌وکار (هنوز فعال نیست)"],
        "next_step":        "در مرحله بعد می‌توان این را آنلاین و فعال کرد، و بعداً مشتریان، فروش، یا وظایف تیم را به این مرکز وصل کرد",
    },
    "family_website_or_public_presence": {
        "what_delivered":   "پیش‌نمایش اولیه یک صفحه معرفی برای کسب‌وکارت",
        "helps_you_do":     "کارت را به مشتریان معرفی کنی، خدمات اصلی را نشان بدهی، و راه تماس را واضح کنی",
        "how_to_use":       "این یک نسخه اولیه قابل بررسی است؛ ببین معرفی و اطلاعات تماس همان‌طوری که می‌خواهی نوشته شده — بعد از راه‌اندازی می‌توانی لینک را با مشتریان به اشتراک بگذاری",
        "included_now":     ["معرفی کوتاه کسب‌وکار", "خدمات یا محصولات اصلی", "راه تماس"],
        "not_yet":          ["سفارش آنلاین (هنوز فعال نیست)", "پرداخت آنلاین (هنوز فعال نیست)", "رزرو آنلاین (هنوز فعال نیست)", "اتصال به دامنه اختصاصی (هنوز فعال نیست)"],
        "next_step":        "در مرحله بعد می‌توان این را آنلاین و فعال کرد، و بعداً فرم تماس یا دکمه سفارش را هم اضافه کرد",
    },
    # Tier-1/Tier-2 scenarios
    "restaurant": {
        "what_delivered":   "پیش‌نمایش اولیه یک صفحه معرفی و سفارش برای کافه یا رستوران",
        "helps_you_do":     "مشتریان منوت را ببینند، سفارش بدهند، و با تو تماس بگیرند",
        "how_to_use":       "این یک نسخه اولیه قابل بررسی است؛ بعد از راه‌اندازی می‌توانی لینک را با مشتریانت به اشتراک بگذاری و منو را به‌روز نگه داری",
        "included_now":     ["معرفی کافه/رستوران", "منو با قیمت", "دکمه سفارش", "اطلاعات تماس"],
        "not_yet":          ["پرداخت آنلاین (هنوز فعال نیست)", "رزرو میز آنلاین (هنوز فعال نیست)", "اپلیکیشن موبایل (هنوز فعال نیست)"],
        "next_step":        "در مرحله بعد می‌توان این را آنلاین و فعال کرد، و بعداً سیستم رزرو میز یا پرداخت آنلاین اضافه کرد",
    },
    "store": {
        "what_delivered":   "پیش‌نمایش اولیه فروشگاه",
        "helps_you_do":     "مشتریانت محصولاتت را ببینند و سفارش بدهند",
        "how_to_use":       "این یک نسخه اولیه قابل بررسی است؛ بعد از راه‌اندازی می‌توانی محصولاتت را به‌روز نگه داری و سفارش‌های رسیده را پیگیری کنی",
        "included_now":     ["نمایش محصولات", "دکمه سفارش", "اطلاعات تماس"],
        "not_yet":          ["پرداخت آنلاین خودکار (هنوز فعال نیست)", "انبارداری پیشرفته (هنوز فعال نیست)", "ارسال خودکار (هنوز فعال نیست)"],
        "next_step":        "در مرحله بعد می‌توان این را آنلاین و فعال کرد، و بعداً سیستم پرداخت آنلاین اضافه کرد",
    },
    "booking": {
        "what_delivered":   "پیش‌نمایش اولیه سیستم رزرو",
        "helps_you_do":     "مشتریانت وقت یا خدمات رزرو کنند",
        "how_to_use":       "این یک نسخه اولیه قابل بررسی است؛ بعد از راه‌اندازی می‌توانی زمان‌های آزادت را مشخص کنی و رزروهای رسیده را تأیید کنی",
        "included_now":     ["نمایش زمان‌های آزاد", "فرم رزرو", "اطلاعات تماس"],
        "not_yet":          ["تأیید خودکار رزرو (هنوز فعال نیست)", "پرداخت پیش‌پرداخت (هنوز فعال نیست)", "یادآور خودکار (هنوز فعال نیست)"],
        "next_step":        "در مرحله بعد می‌توان این را آنلاین و فعال کرد، و بعداً تأیید خودکار رزرو اضافه کرد",
    },
    "telegram_bot": {
        "what_delivered":   "طرح اولیه ربات تلگرام",
        "helps_you_do":     "مشتریانت پیام بفرستند، سؤال بپرسند، یا سفارش بدهند",
        "how_to_use":       "این یک طرح اولیه قابل بررسی است، نه یک ربات فعال؛ در مرحله بعد می‌توان آن را در تلگرام راه‌اندازی و فعال کرد",
        "included_now":     ["طرح دریافت پیام", "طرح پاسخ‌های آماده", "طرح هدایت مشتری"],
        "not_yet":          ["فعال‌سازی واقعی ربات در تلگرام (هنوز فعال نیست)", "پاسخ خودکار هوشمند (هنوز فعال نیست)", "اتصال به سیستم سفارش (هنوز فعال نیست)", "پرداخت در تلگرام (هنوز فعال نیست)"],
        "next_step":        "در مرحله بعد می‌توان این را در تلگرام راه‌اندازی و فعال کرد، و بعداً پاسخ‌های خودکار بیشتری تعریف کرد",
    },
    "company_landing": {
        "what_delivered":   "پیش‌نمایش اولیه یک صفحه معرفی برای کسب‌وکارت",
        "helps_you_do":     "کارت را به مشتریان معرفی کنی و راه تماس را واضح کنی",
        "how_to_use":       "این یک نسخه اولیه قابل بررسی است؛ بعد از راه‌اندازی می‌توانی لینک صفحه را به اشتراک بگذاری",
        "included_now":     ["معرفی کسب‌وکار", "خدمات اصلی", "راه تماس"],
        "not_yet":          ["سفارش آنلاین (هنوز فعال نیست)", "پرداخت آنلاین (هنوز فعال نیست)", "دامنه اختصاصی (هنوز فعال نیست)"],
        "next_step":        "در مرحله بعد می‌توان این را آنلاین و فعال کرد، و بعداً دکمه سفارش یا فرم تماس اضافه کرد",
    },
}

_DEFAULT_PROFILE: dict[str, Any] = {
    "what_delivered":   "نسخه اولیه قابل بررسی، متناسب با نیازت",
    "helps_you_do":     "کارت را آنلاین‌تر و منظم‌تر کنی",
    "how_to_use":       "این یک نسخه اولیه قابل بررسی است؛ آن را ببین و اگر همان‌طوری که می‌خواهی نبود، بگو تا تغییرش بدهیم",
    "included_now":     ["ساختار اصلی محصول", "قابلیت‌های پایه"],
    "not_yet":          ["راه‌اندازی و فعال‌سازی آنلاین (هنوز فعال نیست)", "قابلیت‌های پیشرفته‌تر در مراحل بعدی اضافه می‌شوند"],
    "next_step":        "در مرحله بعد می‌توان این را آنلاین و فعال کرد، و بعداً قابلیت‌های بیشتری اضافه کرد",
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
        "title":        "فایل پیش‌نمایش محصول آماده شد",
        "product_name": product_name,
        "sections": {
            "این پیش‌نمایش چیست؟":              profile["what_delivered"],
            "این به چه کاری کمک می‌کند؟":       profile["helps_you_do"],
            "چطور بررسی‌اش کنی؟":               profile["how_to_use"],
            "در نسخه اولیه چه چیزهایی هست؟":   profile["included_now"],
            "چه چیزهایی هنوز فعال نیست؟":       profile["not_yet"],
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

    summary = f"فایل پیش‌نمایش «{export_data['title'] or scenario}» آماده است."

    return {
        "export_type":          "preview_package",
        "export_data":          export_data,       # internal — for downstream build
        "delivery_education":   delivery_education, # user-facing — clear, non-technical
        "summary":              summary,
    }
