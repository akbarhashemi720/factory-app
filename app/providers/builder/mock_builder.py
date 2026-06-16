"""
Mock Builder Provider — Sprint 3.

Generates structured preview_data from scenario templates.
No AI call. Pure Python. Default builder for MVP.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRODUCTION EFFICIENCY ROADMAP (not implemented yet)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The factory should evolve from a single-output builder into a
repeatable production system optimised for speed, quality, and reuse.

Future builder modes (build_mode field in builder_task):
  fast_preview    — current sprint: quick JSON scaffold, no assets
  production_build — full HTML/CSS/JS output ready for deployment
  revision        — apply targeted correction to existing output
  export          — package final approved version for download

Future template library (one pack per scenario):
  Each ScenarioPack will define:
    default_sections    — ordered list of page sections
    default_components  — required UI components
    default_copy        — placeholder text fitting the scenario tone
    default_checklist   — reviewer rules specific to this scenario
    reusable_patterns   — patterns learned from approved projects

Long-term performance target:
  For common scenarios (restaurant, dashboard, company landing)
  the factory should produce usable first versions faster over time.
# Speed is a long-term direction — quality, correctness, and UX always come first.
  This requires: template library + parallel-friendly design +
  pattern reuse from Memory Layer.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

from typing import Any


# ─── Scenario Pack stubs ──────────────────────────────────────────────────────
# Each dict documents the intended ScenarioPack structure.
# In a future sprint these will be loaded from a template library
# (database or YAML files) so the builder starts from a proven scaffold
# instead of an empty page.

SCENARIO_PACKS: dict[str, dict] = {
    "restaurant": {
        "default_sections": ["hero", "image", "menu_preview", "contact"],
        "default_components": ["title", "subtitle", "primary_button",
                               "menu_items", "contact_button"],
        "copy_tone": "warm, appetising, simple",
        "required_for_quality": ["title", "subtitle", "primary_button"],
        "reusable_patterns": [],
    },
    "dashboard": {
        "default_sections": ["metric_cards", "chart", "report_list"],
        "default_components": ["title", "subtitle", "metric_cards",
                               "chart_placeholder", "report_rows"],
        "copy_tone": "professional, data-focused, minimal",
        "required_for_quality": ["title", "cards"],
        "reusable_patterns": [],
    },
    "company_landing": {
        "default_sections": ["hero", "value_proposition", "features", "cta"],
        "default_components": ["title", "subtitle", "primary_button", "sections"],
        "copy_tone": "professional, trustworthy, action-oriented",
        "required_for_quality": ["title", "subtitle", "primary_button"],
        "reusable_patterns": [],
    },
    "store": {
        "default_sections": ["product_list", "product_detail", "order_form"],
        "default_components": ["title", "subtitle", "primary_button", "sections"],
        "copy_tone": "friendly, clear, action-oriented",
        "required_for_quality": ["title", "subtitle", "primary_button"],
        "reusable_patterns": [],
    },
    "booking": {
        "default_sections": ["available_slots", "booking_form", "contact"],
        "default_components": ["title", "subtitle", "primary_button", "time_slots"],
        "copy_tone": "calm, reassuring, simple",
        "required_for_quality": ["title", "subtitle", "primary_button"],
        "reusable_patterns": [],
    },
    "telegram_bot": {
        "default_sections": ["bot_intro", "features", "start_button"],
        "default_components": ["title", "subtitle", "primary_button", "sections"],
        "copy_tone": "friendly, concise, helpful",
        "required_for_quality": ["title", "subtitle", "primary_button"],
        "reusable_patterns": [],
    },
    "general_ordering": {
        "default_sections":    ["انتخاب مورد سفارش", "اطلاعات مشتری", "ثبت و پیگیری سفارش"],
        "default_components":  ["title", "subtitle", "primary_button", "sections"],
        "copy_tone":           "friendly, action-oriented",
        "required_for_quality": ["title", "subtitle", "primary_button"],
        "reusable_patterns":   [],
    },
    "general_class": {
        "default_sections":    ["لیست کلاس‌ها", "برنامه زمانی", "ثبت‌نام یا مدیریت شاگردها"],
        "default_components":  ["title", "subtitle", "primary_button", "sections"],
        "copy_tone":           "professional, educational",
        "required_for_quality": ["title", "subtitle", "primary_button"],
        "reusable_patterns":   [],
    },
    "general_showcase": {
        "default_sections":    ["محصولات منتخب", "توضیح کوتاه محصولات", "راه تماس یا سفارش"],
        "default_components":  ["title", "subtitle", "primary_button", "sections"],
        "copy_tone":           "friendly, visual",
        "required_for_quality": ["title", "subtitle", "primary_button"],
        "reusable_patterns":   [],
    },
    "general": {
        "default_sections":    ["معرفی کار", "گرفتن سفارش یا پیام", "رزرو یا تماس"],
        "default_components":  ["title", "subtitle", "primary_button", "sections"],
        "copy_tone":           "neutral",
        "required_for_quality": ["title", "subtitle", "primary_button"],
        "reusable_patterns":   [],
    },
}


# ─── Public interface ────────────────────────────────────────────────────────

def generate(
    project: dict,
    understanding: dict,
    scenario_pattern: dict | None = None,
) -> dict[str, Any]:
    """
    Generate scenario-appropriate preview_data.

    # ── Reusable pattern behaviour (Sprint 6) ──────────────────────────────
    # Reusable patterns are soft defaults, not hard overrides.
    # Confirmed understanding and current project needs always win.
    #
    # Safe to reuse from pattern:  tone, has_contact, sections/cards flags,
    #                               presence of subtitle, title_style
    # NOT safe to reuse:           exact business name, exact copy,
    #                               user-specific content from old projects
    # ────────────────────────────────────────────────────────────────────────

    Interface contract (same for all builder providers):
        Args:
            project:          projects row
            understanding:    confirmed understandings row (confirmed_by_user=True)
            scenario_pattern: optional reusable_patterns row — soft starting hint
        Returns:
            {preview_data, change_summary, known_limitations}
    """
    scenario = (
        understanding.get("detected_scenario")
        or project.get("scenario")
        or "general"
    )

    pack = SCENARIO_PACKS.get(scenario, SCENARIO_PACKS["general"])

    # Build preview from scenario template (always the base)
    builder_fn = _PREVIEW_MAP.get(scenario)
    if builder_fn:
        preview_data = builder_fn()
    else:
        preview_data = _general(scenario)  # preserves the detected scenario

    # ── Apply pattern as soft default ────────────────────────────────────────
    used_pattern = False
    if scenario_pattern:
        pd = scenario_pattern.get("pattern_data", {})

        # Reuse structural/tonal properties — never copy identity fields
        if "tone" in pd and "tone" not in preview_data:
            preview_data["tone"] = pd["tone"]

        if pd.get("has_contact") and not preview_data.get("show_contact"):
            preview_data["show_contact"] = True
            if not preview_data.get("secondary_button"):
                preview_data["secondary_button"] = "تماس"

        # If pattern says there was a subtitle and current template has none, keep
        # our template's subtitle (it already has one from scenario fn — no action)

        used_pattern = True

    change_summary = [
        f"پیش‌نمایش بر اساس سناریوی «{scenario}» ساخته شد",
        "محتوا از روی فهم تأییدشده استخراج شد",
    ]
    if used_pattern:
        change_summary.append("ساختار اولیه از الگوی تأییدشده پروژه‌های مشابه استفاده کرد")

    return {
        "preview_data": preview_data,
        "change_summary": change_summary,
        "known_limitations": [
            "این نسخه اولیه است — هنوز آماده راه‌اندازی نهایی نیست",
            "تصاویر واقعی جایگذاری نشده‌اند",
            "محتوای نهایی در مرحله اصلاح قابل تنظیم است",
        ],
        "_scenario_pack": {k: v for k, v in pack.items() if k != "reusable_patterns"},
    }


# ─── Scenario preview templates ───────────────────────────────────────────────

def _restaurant() -> dict[str, Any]:
    return {
        "scenario": "restaurant",
        "title": "کافه آرام",
        "subtitle": "قهوه تازه، فضای ساده و دلنشین",
        "tone": "calm",
        "show_menu": True,
        "show_contact": True,
        "primary_button": "مشاهده منو",
        "secondary_button": "تماس",
        "menu_items": [
            {"name": "اسپرسو دوپیو", "price": "۴۵٬۰۰۰ تومان"},
            {"name": "کیک شکلاتی",  "price": "۶۰٬۰۰۰ تومان"},
        ],
    }


def _dashboard() -> dict[str, Any]:
    return {
        "scenario": "dashboard",
        "title": "داشبورد مدیریت",
        "subtitle": "نمای کلی وضعیت و گزارش‌ها",
        "tone": "professional",
        "cards": [
            {"label": "فروش امروز",    "value": "۱۲.۴M"},
            {"label": "کاربران فعال", "value": "۲,۴۸۰"},
            {"label": "نرخ رشد",       "value": "۱۸٪"},
        ],
        "show_report_section": True,
    }


def _company_landing() -> dict[str, Any]:
    return {
        "scenario": "company_landing",
        "title": "معرفی کار",
        "subtitle": "راهکاری ساده برای رشد کسب‌وکار شما",
        "tone": "professional",
        "primary_button": "شروع همکاری",
        "sections": ["چرا این کسب‌وکار ارزشمند است", "خدمات اصلی", "دلیل اعتماد مشتریان"],
    }


def _store() -> dict[str, Any]:
    return {
        "scenario": "store",
        "title": "فروشگاه آنلاین",
        "subtitle": "محصولات ما را ببینید و سفارش بدهید",
        "tone": "friendly",
        "primary_button": "ثبت سفارش",
        "secondary_button": "تماس با ما",
        "show_contact": True,
        "sections": ["محصولات منتخب", "توضیح کوتاه هر محصول", "فرم ثبت سفارش"],
    }


def _booking() -> dict[str, Any]:
    return {
        "scenario": "booking",
        "title": "رزرو وقت",
        "subtitle": "زمان مناسب خود را انتخاب کنید",
        "tone": "calm",
        "primary_button": "رزرو وقت",
        "show_contact": True,
        "time_slots": [
            "امروز ۱۰:۰۰",
            "امروز ۱۲:۰۰",
            "فردا ۱۶:۰۰",
        ],
    }


def _telegram_bot() -> dict[str, Any]:
    return {
        "scenario": "telegram_bot",
        "title": "ربات تلگرام",
        "subtitle": "با یک کلیک خدمات ما را دریافت کنید",
        "tone": "friendly",
        "primary_button": "شروع",
        "sections": ["ربات چه کاری انجام می‌دهد", "امکانات اصلی", "شروع استفاده"],
    }


def _general_ordering() -> dict[str, Any]:
    return {
        "scenario": "general_ordering",
        "title": "سیستم سفارش ساده",
        "subtitle": "مشتری سفارش را ثبت می‌کند و تو راحت‌تر پیگیری می‌کنی",
        "tone": "friendly",
        "primary_button": "ثبت سفارش",
        "secondary_button": "تماس",
        "show_contact": True,
        "sections": ["انتخاب مورد سفارش", "اطلاعات مشتری", "ثبت و پیگیری سفارش"],
    }


def _general_class() -> dict[str, Any]:
    return {
        "scenario": "general_class",
        "title": "مدیریت کلاس‌ها",
        "subtitle": "کلاس‌ها، ثبت‌نام و برنامه‌ها را ساده‌تر مدیریت کن",
        "tone": "professional",
        "primary_button": "ثبت‌نام کلاس",
        "secondary_button": "مشاهده برنامه",
        "sections": ["لیست کلاس‌ها", "برنامه زمانی", "ثبت‌نام یا مدیریت شاگردها"],
    }


def _general_showcase() -> dict[str, Any]:
    return {
        "scenario": "general_showcase",
        "title": "معرفی محصولات",
        "subtitle": "محصولاتت را واضح نشان بده و مسیر تماس یا سفارش را ساده کن",
        "tone": "friendly",
        "primary_button": "مشاهده محصولات",
        "secondary_button": "تماس",
        "show_contact": True,
        "sections": ["محصولات منتخب", "توضیح کوتاه محصولات", "راه تماس یا سفارش"],
    }


def _general(scenario_hint: str = "general") -> dict[str, Any]:
    return {
        "scenario": scenario_hint,
        "title": "شروع ساخت محصول",
        "subtitle": "چند مسیر رایج برای آنلاین کردن کارت آماده است",
        "tone": "neutral",
        "primary_button": "ادامه با راهنمایی کارخانه",
        "sections": ["معرفی کار", "گرفتن سفارش یا پیام", "رزرو یا تماس"],
    }


# ─── Need-family preview scaffolds ───────────────────────────────────────────
# These are flexible product shapes for broadly detected need families.
# Internal family names are NEVER shown to the user.
#
# Examples are tests of reasoning behavior, not fixed product definitions.
# A reminder scaffold works for medicine, plants, customer calls, or daily tasks.
# A finance scaffold works for shops, freelancers, or households.
# The shape is determined by the need pattern, not by a specific named product.

def _family_reminder_or_routine() -> dict[str, Any]:
    return {
        "scenario": "family_reminder_or_routine",
        "title": "یادآور ساده",
        "subtitle": "کارهایی که نباید فراموش کنی — همیشه جلوی چشمت",
        "tone": "calm",
        "primary_button": "افزودن یادآور",
        "sections": [
            "یادآورهای امروز",
            "افزودن یادآور جدید",
            "زمان یادآوری",
            "یادداشت کوتاه",
            "وضعیت: انجام شد / انجام نشد",
        ],
        "note": "اتصال به اپ‌های پیام‌رسان در مرحله بعدی بررسی می‌شود.",
    }


def _family_simple_finance_or_tracking() -> dict[str, Any]:
    return {
        "scenario": "family_simple_finance_or_tracking",
        "title": "ثبت روزانه پول",
        "subtitle": "درآمد و هزینه‌هات را ساده ثبت کن و جمع‌بندی ببین",
        "tone": "clean",
        "primary_button": "ثبت ورودی جدید",
        "cards": [
            {"label": "درآمد امروز",   "value": "—"},
            {"label": "هزینه امروز",   "value": "—"},
            {"label": "مانده کل",      "value": "—"},
        ],
        "sections": [
            "درآمد امروز",
            "هزینه‌های امروز",
            "طلب و بدهی مشتریان",
            "جمع‌بندی ساده روزانه",
            "ثبت ورودی جدید",
        ],
    }


def _family_customer_management() -> dict[str, Any]:
    return {
        "scenario": "family_customer_management",
        "title": "مشتری‌هام",
        "subtitle": "یه دفترچه ساده برای یادداشت مشتری‌ها و پیگیری‌ها",
        "tone": "friendly",
        "primary_button": "مشتری جدید",
        "sections": [
            "لیست مشتریان",
            "اطلاعات مشتری",
            "آخرین تماس",
            "پیگیری بعدی",
            "یادداشت‌ها",
            "سابقه سفارش‌ها",
        ],
    }


def _family_internal_admin_tool() -> dict[str, Any]:
    return {
        "scenario": "family_internal_admin_tool",
        "title": "کارهای تیم",
        "subtitle": "وظایف و کارهای جاری را منظم دنبال کن",
        "tone": "professional",
        "primary_button": "وظیفه جدید",
        "sections": [
            "وظایف امروز",
            "مسئول هر کار",
            "وضعیت: در حال انجام / تمام شد",
            "چک‌لیست روزانه",
            "گزارش ساده",
        ],
    }


def _family_content_or_marketing() -> dict[str, Any]:
    return {
        "scenario": "family_content_or_marketing",
        "title": "ایده‌های محتوا",
        "subtitle": "ایده بنویس، پیش‌نویس آماده کن، برنامه هفتگی داشته باش",
        "tone": "creative",
        "primary_button": "ایده جدید",
        "sections": [
            "ایده‌های محتوا",
            "پیش‌نویس پیام",
            "کجا استفاده می‌شود",
            "برنامه هفتگی",
            "تأیید قبل از انتشار",
        ],
        "note": "انتشار خودکار در مرحله بعدی بررسی می‌شود.",
    }


def _family_business_growth_or_operations() -> dict[str, Any]:
    return {
        "scenario": "family_business_growth_or_operations",
        "title": "مرکز کسب‌وکار",
        "subtitle": "نمای کلی کارت — اولویت‌ها، مشتریان، و قدم‌های بعدی",
        "tone": "calm",
        "primary_button": "اولویت‌های امروز",
        "sections": [
            "هدف‌های اصلی",
            "اولویت‌های امروز",
            "مشتریان / فروش / وظایف",
            "قدم‌های پیشنهادی بعدی",
            "گزارش ساده هفتگی",
        ],
        "note": "نسخه اول کمک می‌کند کارت را سازماندهی و بهتر بفهمی.",
    }


def _family_website_or_public_presence() -> dict[str, Any]:
    return {
        "scenario": "family_website_or_public_presence",
        "title": "معرفی کار",
        "subtitle": "یه صفحه ساده که کارت را به مشتریان معرفی کند",
        "tone": "professional",
        "primary_button": "تماس با ما",
        "show_contact": True,
        "sections": [
            "معرفی کوتاه",
            "خدمات یا محصولات اصلی",
            "چرا ما؟",
            "راه تماس",
        ],
    }


_PREVIEW_MAP: dict[str, Any] = {
    "restaurant":      _restaurant,
    "dashboard":       _dashboard,
    "company_landing": _company_landing,
    "store":           _store,
    "booking":         _booking,
    "telegram_bot":    _telegram_bot,
    "general_ordering": _general_ordering,
    "general_class":    _general_class,
    "general_showcase": _general_showcase,
    "general":          lambda: _general("general"),
    # Need-family previews (internal — label never shown to user)
    "family_reminder_or_routine":        _family_reminder_or_routine,
    "family_simple_finance_or_tracking": _family_simple_finance_or_tracking,
    "family_customer_management":        _family_customer_management,
    "family_internal_admin_tool":        _family_internal_admin_tool,
    "family_content_or_marketing":       _family_content_or_marketing,
    "family_business_growth_or_operations": _family_business_growth_or_operations,
    "family_website_or_public_presence": _family_website_or_public_presence,
}
