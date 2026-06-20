"""
Mock PM Provider — with diagnostic question step.

Two-phase approach:
  Phase 1: generate() — detect intent, return one diagnostic question
  Phase 2: refine()   — take user's answer, return improved understanding bullets

Detection priority rules:
  1. Explicit product-type keywords win when the user clearly names a product type
     (داشبورد, ربات, رزرو, فروشگاه, کافه, سایت خبری...).
  2. Specific goal/action signals are checked next (ordering, contact, showcase, class).
  3. Broad need-family detection handles natural non-technical descriptions
     (یادم بمونه, حساب و کتاب, مشتری‌هام, رشد کسب‌وکار...).
  4. Unknown or vague requests fall back to a simple clarifying question.

The Need Reasoning Layer (priority 3) runs AFTER explicit product keywords,
so if the user says "ربات یادآور" the bot/telegram detection wins.
If the user says "می‌خوام داروم یادم نره" with no product named, family detection wins.

Doctor mind: diagnose before prescribing.
Nurse language: simple, warm, human — never technical.
Product designer: turn answers into product decisions.
"""
from __future__ import annotations

from typing import Any


# ─── Need Reasoning Layer (Tier 0) ────────────────────────────────────────────
# Internal families only — NEVER shown to the user.
# Each family maps to a warm diagnostic question tailored to that kind of need.
# The family is used for routing; the user sees only simple human language.

_NEED_FAMILIES: list[tuple[str, list[str]]] = [
    ("reminder_or_routine", [
        "یادم بمونه", "یادآور", "فراموش نکنم", "دارو", "reminder",
        "یادآوری", "روتین", "هر روز", "تکراری", "وظیفه روزانه", "کارهای روزانه", "نگران فراموشی", "به موقع",
        "یادم می‌ره", "داروم", "داروهام",
    ]),
    ("simple_finance_or_tracking", [
        "حساب و کتاب", "حساب‌وکتاب", "حسابداری", "درآمد و هزینه",
        "پول مغازه", "پول روزانه", "هزینه روزانه", "درآمد روزانه",
        "جمع‌بندی پول", "صندوق", "کش فلو", "ثبت پول",
        "دخل و خرج", "دخل‌وخرج", "بدهی مشتری",
        "پرداخت", "پرداخت‌ها", "پیگیری پرداخت",
        "طلبکاری", "طلب", "فاکتور", "گزارش روزانه",
    ]),
    ("customer_management", [
        "مشتری‌هام", "اطلاعات مشتری", "پیگیری مشتری", "لیست مشتریان",
        "تاریخچه مشتری", "یادداشت مشتری", "crm", "مدیریت مشتری",
        "فراموش نکنم چه گفتیم", "سابقه مشتری",
    ]),
    ("content_or_marketing", [
        "پست بذارم", "محتوا", "اینستاگرام", "شبکه اجتماعی",
        "تبلیغات", "پیام بازاریابی", "کپی‌رایتینگ", "متن تبلیغ",
        "content", "marketing", "سوشال مدیا", "کانال تلگرام",
    ]),
    ("internal_admin_tool", [
        "فرم", "گردش کار", "تأیید", "درخواست داخلی", "پرسنل",
        "گزارش داخلی", "workflow", "approval", "admin", "ادمین",
        "فرآیند اداری", "چک‌لیست",
        "مدیریت کارمند", "کارمندها", "کارمندم", "وظیفه کارمند",
        "تقسیم کار", "تیم",
    ]),
    ("business_growth_or_operations", [
        "کسب‌وکارم رشد کنه", "کارم بهتر بشه", "فروشم بیشتر بشه",
        "رونق", "مدیریت کار", "اداره کسب‌وکار", "خودش بچرخه",
        "بچرخه", "راحت‌تر بچرخه", "کمتر دغدغه داشته باشم",
        "راحت‌تر بشه", "بهره‌وری", "کارم آسون‌تر بشه",
    ]),
    ("website_or_public_presence", [
        "سایت", "وبسایت", "صفحه آنلاین", "پرتفولیو", "نمونه کار",
        "آنلاین باشم", "معرفی آنلاین", "صفحه فرود", "landing",
        "website", "وب",
    ]),
]


def _detect_need_family(text: str) -> str | None:
    """
    Internal Tier 0: detect broad need family from user text.
    Returns family name or None if no match.
    This label is NEVER shown to the user.
    """
    t = text.lower()
    for family, signals in _NEED_FAMILIES:
        if any(s in t for s in signals):
            return family
    return None


# ─── Need-family diagnostic questions ─────────────────────────────────────────
# User sees these — must be warm, simple, and non-technical.

_FAMILY_DIAGNOSTIC: dict[str, dict] = {
    "reminder_or_routine": {
        "preamble":  "فهمیدم. می‌خوای یه ابزار ساده داشته باشی که سر وقت بهت یادآوری کنه. فعلاً فقط مسیر مناسب رو مشخص می‌کنیم؛ اتصال به اپ‌ها در مرحله بعد بررسی می‌شود.",
        "question":  "چطور می‌خوای یادآور بهت بده؟",
        "options":   ["پیام تلگرام یا واتساپ", "پیامک یا تماس", "داخل یه صفحه ساده", "مطمئن نیستم"],
        "decision":  "delivery_channel",
    },
    "simple_finance_or_tracking": {
        "preamble":  "فهمیدم. می‌خوای یه روش ساده داشته باشی که پول روزانه کارت رو ثبت و دنبال کنی، بدون نرم‌افزار پیچیده حسابداری.",
        "question":  "اول می‌خوای چه چیزی رو ثبت کنی؟",
        "options":   ["درآمد", "هزینه‌ها", "طلب و بدهی مشتریان", "همه اینها"],
        "decision":  "tracking_scope",
    },
    "customer_management": {
        "preamble":  "فهمیدم. می‌خوای یه جای ساده داشته باشی که اطلاعات مشتری‌هات رو نگه داری و بدونی چی باید پیگیری بشه.",
        "question":  "مهم‌ترین چیزی که می‌خوای درباره هر مشتری یادت باشه چیه؟",
        "options":   ["سفارش‌هاشون", "اطلاعات تماس", "یادآور پیگیری", "یادداشت و سابقه"],
        "decision":  "crm_focus",
    },
    "content_or_marketing": {
        "preamble":  "فهمیدم. می‌خوای کمک داشته باشی برای محتوا یا پیام‌های کسب‌وکارت.",
        "question":  "کجا می‌خوای این محتوا استفاده بشه؟",
        "options":   ["اینستاگرام", "تلگرام", "واتساپ / پیامک", "چند جا با هم"],
        "decision":  "content_channel",
    },
    "internal_admin_tool": {
        "preamble":  "فهمیدم. می‌خوای یه ابزار داخلی داشته باشی که کارهای اداری یا فرآیندهای تیمت رو منظم‌تر کنه.",
        "question":  "بیشتر به چه چیزی نیاز داری؟",
        "options":   ["فرم و ثبت اطلاعات", "تأیید و گردش کار", "گزارش و چک‌لیست", "همه اینها"],
        "decision":  "admin_scope",
    },
    "business_growth_or_operations": {
        "preamble":  "فهمیدم. می‌خوای کسب‌وکارت راحت‌تر بچرخه و کمتر خودت درگیر جزئیات باشی.",
        "question":  "الان بزرگ‌ترین دغدغه‌ات چیه؟",
        "options":   ["فروش بیشتر", "مدیریت مشتریان", "نظم کارها", "گزارش و اطلاعات"],
        "decision":  "growth_focus",
    },
    "website_or_public_presence": {
        "preamble":  "فهمیدم. می‌خوای یه حضور آنلاین داشته باشی که کارت رو معرفی کنه.",
        "question":  "هدف اصلی این صفحه آنلاین چیه؟",
        "options":   ["معرفی کار و خدمات", "گرفتن سفارش یا رزرو", "نمایش نمونه کار", "تماس و ارتباط"],
        "decision":  "web_goal",
    },
}


# ─── Detection tables ─────────────────────────────────────────────────────────
# Each list is checked in ORDER. First match wins.
# Rules are specific → generic to avoid false positives.

# Tier 1: explicit product-type keywords (highest priority)
_TIER1: list[tuple[str, list[str]]] = [
    ("telegram_bot",   ["ربات", "تلگرام", "bot", "بات"]),
    ("restaurant",     ["کافه", "رستوران", "کافی‌شاپ", "کافیشاپ"]),
    ("booking",        ["رزرو", "نوبت گرفتن", "وقت گرفتن", "ثبت‌نام کلاس",
                        "رزرو بگیرم", "رزرو بگیرند", "appointment"]),
    ("dashboard",      ["داشبورد"]),
    ("store",          ["فروشگاه آنلاین", "فروشگاه", "shop", "store"]),
    ("news_site",      ["سایت خبری", "وب‌سایت خبری", "پورتال خبری",
                        "news site", "news website",
                        "اخبار", "خبر"]),
]

# Tier 2: goal/action signals — context-dependent, use careful mapping or general
# Key insight: these words alone are NOT enough to pick a specific scenario.
# They need a diagnostic question to disambiguate.
_TIER2_GENERAL_SIGNALS: list[str] = [
    "سفارش",      # could be food, product, service
    "محصول",      # could be store or just a showcase
    "مدیریت",     # could be dashboard, booking, or admin
    "آنلاین بشه", # could be anything
    "تماس بگیرن", # contact/leads → company_landing
    "ارتباط",
    "معرفی",      # could be company_landing or product showcase
]

# Tier 2 special: contact/leads signal → company_landing (clear enough)
_CONTACT_SIGNALS: list[str] = [
    "تماس بگیرن", "تماس بگیرند", "باهام تماس", "با من تماس",
    "ارتباط بگیرند", "ارتباط برقرار"
]

# Tier 2 special: ordering without a known venue → general (needs clarification)
_ORDERING_SIGNALS: list[str] = [
    "سفارش بدن", "سفارش بدهند", "سفارش بگیرم", "سفارش بگیرند",
    "راحت‌تر سفارش", "آسان‌تر سفارش",
]

# Tier 2 special: product showcase without selling intent → company_landing
_SHOWCASE_SIGNALS: list[str] = [
    "معرفی کنم", "معرفی کنیم", "محصولام رو معرفی", "محصولامو معرفی",
]

# Tier 2 special: class/education management → general (needs clarification)
_CLASS_SIGNALS: list[str] = [
    "کلاس", "دوره", "آموزش",
]

# Tier 2 special: customer management signals — specific enough for family routing
# These must be checked before generic "مدیریت" catches them
_CUSTOMER_MGMT_SIGNALS: list[str] = [
    "مشتری‌هام", "مشتریام", "مشتریانم", "مشتری‌هایم",
    "اطلاعات مشتری", "پیگیری مشتری", "سابقه مشتری",
    "لیست مشتریان", "یادداشت مشتری",
]

# ─── Diagnostic questions ─────────────────────────────────────────────────────

_DIAGNOSTIC: dict[str, dict] = {
    "restaurant": {
        "preamble":  "فهمیدم. فقط یه چیز تا نسخه درست بسازیم:",
        "question":  "آیا می‌خواهی مشتری از همین صفحه سفارش بدهد، یا فقط کافه را ببیند و بعد تماس بگیرد؟",
        "options":   ["فقط معرفی — تماس می‌گیرند", "سفارش مستقیم از صفحه"],
        "decision":  "ordering_model",
    },
    "store": {
        "preamble":  "فهمیدم. فقط یه چیز تا نسخه درست بسازیم:",
        "question":  "آیا مشتری باید داخل سایت پرداخت کند، یا فقط سفارش بدهد و بعد تو باهاشون تماس می‌گیری؟",
        "options":   ["فقط سفارش — من تماس می‌گیرم", "پرداخت آنلاین داخل سایت"],
        "decision":  "payment_model",
    },
    "booking": {
        "preamble":  "فهمیدم. فقط یه چیز تا نسخه درست بسازیم:",
        "question":  "آیا می‌خواهی مشتری خودش وقت خالی انتخاب کند، یا فقط درخواست بدهد و تو تأیید کنی؟",
        "options":   ["خودش انتخاب کند", "درخواست بدهد — من تأیید کنم"],
        "decision":  "booking_model",
    },
    "dashboard": {
        "preamble":  "فهمیدم. فقط یه چیز تا نسخه درست بسازیم:",
        "question":  "این داشبورد فقط برای دیدن آمار است، یا برای مدیریت سفارش‌ها هم استفاده می‌کنی؟",
        "options":   ["فقط دیدن آمار", "مدیریت سفارش‌ها هم لازم است"],
        "decision":  "dashboard_scope",
    },
    "telegram_bot": {
        "preamble":  "فهمیدم. فقط یه چیز تا نسخه درست بسازیم:",
        "question":  "مشتری با این ربات چه کاری می‌کند؟",
        "options":   ["سفارش می‌دهد", "اطلاعات می‌گیرد", "وقت رزرو می‌کند", "چند کار با هم"],
        "decision":  "bot_function",
    },
    "company_landing": {
        "preamble":  "فهمیدم. فقط یه چیز تا نسخه درست بسازیم:",
        "question":  "آیا یه صفحه ساده برای معرفی و تماس کافی است، یا می‌خواهی مشتری همان‌جا کاری هم انجام بدهد؟",
        "options":   ["فقط معرفی و تماس", "سفارش هم بدهد", "رزرو هم بگیرد"],
        "decision":  "page_goal",
    },
    # Specialized general questions
    "news_site": {
        "preamble":  "فهمیدم. تو یک سایت خبری می‌خوای که تا حد ممکن خودش کار کند.",
        "question":  "اخبار قرار است از کجا بیاید؟",
        "options":   [
            "از منابع خبری مشخص",
            "با کمک هوش مصنوعی تولید/خلاصه شود",
            "فعلاً فقط ظاهر و ساختار سایت را می‌خواهم",
            "مطمئن نیستم",
        ],
        "decision":  "news_source",
    },
    "general_ordering": {
        "preamble":  "فهمیدم. بگذار یه چیز را روشن کنیم:",
        "question":  "این سفارش بیشتر برای چه چیزی است؟",
        "options":   ["غذا یا کافه/رستوران", "محصول", "خدمات", "چیز دیگری"],
        "decision":  "order_type",
    },
    "general_class": {
        "preamble":  "فهمیدم. بگذار یه چیز را روشن کنیم:",
        "question":  "می‌خواهی دانش‌آموزان خودشان ثبت‌نام یا رزرو کنند، یا فقط خودت کلاس‌ها را مدیریت کنی؟",
        "options":   ["دانش‌آموز ثبت‌نام/رزرو کند", "فقط خودم مدیریت کنم", "برنامه کلاس‌ها نمایش داده شود"],
        "decision":  "class_model",
    },
    "general_showcase": {
        "preamble":  "فهمیدم. فقط یه چیز تا نسخه درست بسازیم:",
        "question":  "آیا می‌خواهی مشتری همان‌جا سفارش بدهد، یا فقط محصولات را ببیند و باهات تماس بگیرد؟",
        "options":   ["فقط ببیند و تماس بگیرد", "همان‌جا سفارش بدهد"],
        "decision":  "showcase_vs_store",
    },
    "general": {
        "preamble":  "مشکلی نیست — بگو کسب‌وکارت چیه؟ با هم می‌فهمیم چه چیزی می‌سازیم.",
        "question":  "کارت بیشتر به چه دسته‌ای می‌خورد؟",
        "options":   ["فروش محصول", "معرفی کار/خدمات", "رزرو و وقت‌گیری", "چیز دیگری"],
        "decision":  "product_type",
    },
}


# ─── Scenario detection ───────────────────────────────────────────────────────

def detect_scenario(text: str) -> str:
    """
    Detect scenario with priority rules:
      1. Explicit product-type keywords win when user names a product (tier 1)
      2. Context-specific goal/action signals (tier 2 specials)
      3. Broad need-family detection for non-technical natural descriptions (tier 0 / family_*)
      4. Unknown/vague → general clarifying question

    Returns a scenario key used for routing. Family-based results are prefixed
    with 'family_' so generate() can route them to the right diagnostic.
    """
    t = text.lower()

    # Tier 1: explicit product type — highest priority (user named it)
    for scenario, keywords in _TIER1:
        if any(kw in t for kw in keywords):
            return scenario

    # Tier 2 specials: specific enough to map without tier-1 keyword
    if any(s in t for s in _CONTACT_SIGNALS):
        return "company_landing"
    if any(s in t for s in _SHOWCASE_SIGNALS):
        return "general_showcase"
    if any(s in t for s in _CLASS_SIGNALS):
        return "general_class"
    if any(s in t for s in _ORDERING_SIGNALS):
        return "general_ordering"

    # Tier 2 customer management: before generic signals to avoid مدیریت swallowing them
    if any(s in t for s in _CUSTOMER_MGMT_SIGNALS):
        return "family_customer_management"

    # Tier 2 employee/admin management: specific enough for family routing
    _EMPLOYEE_SIGNALS = ["کارمندام", "کارمندم", "کارکنان", "پرسنلم",
                         "وظیفه تعریف", "وظیفه کارمند", "تقسیم کار تیم"]
    if any(s in t for s in _EMPLOYEE_SIGNALS):
        return "family_internal_admin_tool"

    # Tier 2 generic signals that still need more info
    if any(s in t for s in _TIER2_GENERAL_SIGNALS):
        return "general"

    # Tier 0 (Need Reasoning): broad family detection
    # Checked last so explicit keywords always win
    family = _detect_need_family(t)
    if family:
        return f"family_{family}"  # internal prefix — never shown to user

    return "general"


def _entry_mode(text: str) -> str:
    """'product' if user names a known product type, 'goal' otherwise."""
    t = text.lower()
    for _, keywords in _TIER1:
        if any(kw in t for kw in keywords):
            return "product"
    return "goal"


# ─── Phase 1: generate ────────────────────────────────────────────────────────

def _extract_business_domain(text: str) -> str | None:
    """Best-effort domain extraction for builder spec selection (mock path only).

    Only fires for EDUCATION-flavored text — must see a teaching/class/course
    signal alongside the topic keyword, otherwise "سفارش غذا" (food ordering)
    gets wrongly classified as "آموزش آشپزی" (cooking education) just because
    it contains "غذا".
    """
    edu_signal = ["آموزش", "کلاس", "دوره", "یاد بگیر", "یادگیری", "تدریس"]
    has_edu = any(k in text for k in edu_signal)
    if not has_edu:
        return None

    cooking_kw = ["آشپز", "پخت", "کیک", "شیرینی"]  # "غذا" removed — too broad, matches ordering too
    music_kw   = ["موسیقی", "ساز", "آواز", "گیتار", "پیانو"]
    if any(k in text for k in cooking_kw):
        return "آموزش آشپزی"
    if any(k in text for k in music_kw):
        return "آموزش موسیقی"
    if "زبان" in text or "انگلیسی" in text:
        return "آموزش زبان"
    return None


_CAFE_INTRO_KW      = ["معرفی", "منو", "گالری", "نمایش منو"]
_CAFE_RESERVE_KW    = ["رزرو میز", "رزرو", "میز خالی"]
_CAFE_ORDER_KW      = ["سفارش آنلاین", "سفارش غذا", "سفارش نوشیدنی", "ثبت سفارش"]
_CAFE_ECOMMERCE_KW  = ["فروش قهوه", "فروش محصولات", "فروشگاه قهوه", "فروش دانه قهوه"]


def _detect_website_intent(scenario: str, text: str) -> tuple[str, bool]:
    """
    Return (website_intent, is_ambiguous).
    is_ambiguous=True means the request needs a clarification question
    before generating — used only for the cafe/restaurant family for now.
    """
    if scenario == "restaurant":
        has_intro   = any(k in text for k in _CAFE_INTRO_KW)
        has_reserve = any(k in text for k in _CAFE_RESERVE_KW)
        has_order   = any(k in text for k in _CAFE_ORDER_KW)
        has_eco     = any(k in text for k in _CAFE_ECOMMERCE_KW)

        signals = sum([has_intro, has_reserve, has_order, has_eco])
        if signals >= 2:
            return "cafe_hybrid", False
        if has_eco:
            return "coffee_ecommerce", False
        if has_order:
            return "cafe_ordering", False
        if has_reserve:
            return "cafe_reservation", False
        if has_intro:
            return "cafe_intro", False
        # No specific signal at all → ambiguous, must ask
        return "cafe_intro", True

    if scenario == "general_class":
        domain = _extract_business_domain(text) or ""
        if "آشپز" in domain:
            return "cooking_education", False
        if "زبان" in domain and ("کودک" in text or "بچه" in text):
            return "children_english_education", False
        return "education_website", False

    if scenario == "booking" or scenario == "telegram_bot":
        return "service_booking", False

    return "general_website", False


_CAFE_CLARIFY_OPTIONS = [
    "معرفی کافه و نمایش منو",
    "رزرو میز",
    "سفارش آنلاین",
    "فروش محصولات قهوه",
    "ترکیبی از چند مورد",
]


def generate(raw_text: str, language: str = "fa") -> dict[str, Any]:
    """Public entry point — adds business_domain + website_intent best-effort, then delegates."""
    result = _generate_impl(raw_text, language)
    if "business_domain" not in result or not result.get("business_domain"):
        result["business_domain"] = _extract_business_domain(raw_text)

    scenario = result.get("detected_scenario", "general")
    intent, is_ambiguous = _detect_website_intent(scenario, raw_text)
    result["website_intent"] = intent

    if is_ambiguous:
        # Override with an explicit, non-technical clarification question —
        # don't let the system guess confidently on a vague cafe request.
        result["has_diagnostic_question"] = True
        result["diagnostic_question"] = "می‌خواهی سایت کافه بیشتر برای چه کاری باشد؟"
        result["diagnostic_options"] = _CAFE_CLARIFY_OPTIONS
        result["confidence"] = "low"

    return result


def _generate_impl(raw_text: str, language: str = "fa") -> dict[str, Any]:
    """
    Phase 1 — detect intent, return one warm diagnostic question.
    bullets are empty; populated only after Phase 2 (refine).

    Rich input handling:
    - Reference markers [مرجع سبک و ساختار: ...] are stripped before detection
      but noted for preamble — treated as style guide, not copy.
    - Automation signals (اتوماتیک، خودکار، خودش کار کند) are detected
      and reflected honestly with MVP scope note.
    """
    # ── Strip and detect reference marker ────────────────────────────────────
    has_reference = "[مرجع سبک و ساختار:" in raw_text
    clean_text    = raw_text.split("\n\n[مرجع سبک و ساختار:")[0].strip()

    # ── Detect automation intent ──────────────────────────────────────────────
    auto_signals = ["اتوماتیک", "خودکار", "خودش کار کند", "تمام‌اتوماتیک",
                    "بدون دخالت", "خودش انجام بده", "automated", "automatic"]
    wants_automation = any(s in clean_text for s in auto_signals)

    scenario = detect_scenario(clean_text)
    mode     = _entry_mode(clean_text)

    # ── Route family_ scenarios to their dedicated diagnostic ─────────────────
    if scenario.startswith("family_"):
        family_key = scenario[len("family_"):]  # strip prefix
        fam_diag   = _FAMILY_DIAGNOSTIC.get(family_key, _FAMILY_DIAGNOSTIC.get("business_growth_or_operations"))
        preamble   = fam_diag["preamble"]
        if wants_automation:
            preamble += " نسخه اولیه با یک ساختار ساده شروع می‌کند و اتوماسیون بیشتر بعداً اضافه می‌شود."
        return {
            "bullets":                 [],
            "assumptions":             [],
            "clarification_questions": [],
            "detected_scenario":       scenario,
            "confidence":              "medium",
            "has_diagnostic_question": True,
            "has_reference":           has_reference,
            "wants_automation":        wants_automation,
            "preamble":                preamble,
            "diagnostic_question":     fam_diag["question"],
            "diagnostic_options":      fam_diag["options"],
            "diagnostic_decision":     fam_diag["decision"],
        }

    # ── Standard Tier1/Tier2 routing ─────────────────────────────────────────
    diag_key   = scenario
    diag       = _DIAGNOSTIC.get(diag_key, _DIAGNOSTIC["general"])
    confidence = "high" if scenario not in ("general", "general_ordering",
                                             "general_class", "general_showcase") else "low"

    preamble = diag["preamble"]
    if mode == "product" and "فقط یه چیز" not in preamble:
        preamble = "فهمیدم. فقط یه چیز تا نسخه درست بسازیم:"

    # ── Reflect reference and automation in preamble ──────────────────────────
    extras: list[str] = []
    if has_reference:
        extras.append(
            "نمونه را به‌عنوان مرجع سبک و ساختار در نظر می‌گیرم، نه برای کپی مستقیم."
        )
    if wants_automation:
        extras.append(
            "برای نسخه اولیه، ساختار و تجربه را می‌سازیم. "
            "اتوماسیون کامل مرحله بعدی است و باید منابع، قوانین، و سطح تأیید مشخص شود."
        )
    if extras:
        preamble = preamble + " " + " ".join(extras)

    return {
        "bullets":                 [],
        "assumptions":             [],
        "clarification_questions": [],
        "detected_scenario":       scenario,
        "confidence":              confidence,
        "has_diagnostic_question": True,
        "has_reference":           has_reference,
        "wants_automation":        wants_automation,
        "preamble":                preamble,
        "diagnostic_question":     diag["question"],
        "diagnostic_options":      diag["options"],
        "diagnostic_decision":     diag["decision"],
    }


# ─── Phase 2: refine ─────────────────────────────────────────────────────────

def refine(raw_text: str, diagnostic_answer: str,
           detected_scenario: str, language: str = "fa") -> dict[str, Any]:
    """
    Phase 2 — incorporate user's answer into refined understanding bullets.
    """
    a        = diagnostic_answer.lower()
    scenario = detected_scenario

    bullets = _refined_bullets(scenario, a, raw_text)
    # Resolve general sub-scenarios to a concrete one for builder
    resolved = _resolve_scenario(scenario, a)

    # Resolve website_intent — prefer what the ORIGINAL raw_text already signals
    # (e.g. "فروش قهوه" → coffee_ecommerce) over a generic diagnostic answer like
    # "سفارش مستقیم از صفحه", which only distinguishes ordering vs contact-only
    # and should not silently downgrade a clearer ecommerce/reservation intent.
    original_intent, original_ambiguous = _detect_website_intent(resolved, raw_text)
    website_intent = original_intent

    if resolved == "restaurant" and original_ambiguous:
        # Only let the diagnostic answer decide when the original text was vague
        if "معرفی" in diagnostic_answer or "منو" in diagnostic_answer:
            website_intent = "cafe_intro"
        elif "رزرو" in diagnostic_answer:
            website_intent = "cafe_reservation"
        elif "سفارش" in diagnostic_answer:
            website_intent = "cafe_ordering"
        elif "فروش" in diagnostic_answer or "محصولات قهوه" in diagnostic_answer:
            website_intent = "coffee_ecommerce"
        elif "ترکیبی" in diagnostic_answer:
            website_intent = "cafe_hybrid"

    business_domain = _extract_business_domain(raw_text)

    return {
        "bullets":                 bullets,
        "assumptions":             [],
        "clarification_questions": [],
        "detected_scenario":       resolved,
        "website_intent":          website_intent,
        "business_domain":         business_domain,
        "confidence":              "high",
        "has_diagnostic_question": False,
        "diagnostic_answer":       diagnostic_answer,
    }


def _resolve_scenario(scenario: str, answer: str) -> str:
    """Map general sub-scenarios to a concrete builder scenario after answer."""
    a = answer.lower()
    if scenario == "general_ordering":
        if "غذا" in a or "کافه" in a or "رستوران" in a:
            return "restaurant"
        return "store"
    if scenario == "general_class":
        # NEVER route to booking — classes/courses always stay general_class,
        # even when the answer mentions "ثبت‌نام" or "رزرو" (class registration,
        # not appointment booking). This was the root cause of cooking education
        # becoming a barbershop/booking page.
        return "general_class"
    if scenario == "general_showcase":
        if "سفارش" in a:
            return "store"
        return "company_landing"
    if scenario == "general":
        if "فروش" in a:
            return "store"
        if "رزرو" in a or "وقت" in a:
            return "booking"
        if "معرفی" in a:
            return "company_landing"
    if scenario == "news_site":
        # MVP: news_site maps to company_landing structure for builder
        return "company_landing"
    if scenario.startswith("family_"):
        # Need-family scenarios now have dedicated builder previews.
        # Pass through unchanged so builder uses the correct template.
        # No remapping needed.
        return scenario
    return scenario  # already concrete


def _refined_bullets(scenario: str, answer: str, raw_text: str) -> list[str]:
    """Return tight, specific bullets based on scenario + diagnostic answer."""
    a = answer

    if scenario.startswith("family_"):
        family = scenario[len("family_"):]
        a_lower = a.lower()
        if family == "reminder_or_routine":
            channel = ("تلگرام یا واتساپ" if "تلگرام" in a_lower or "واتساپ" in a_lower
                       else "پیامک" if "پیامک" in a_lower else "یک صفحه ساده")
            return [
                "می‌خواهی یه ابزار ساده داشته باشی که سر وقت بهت یادآوری کنه",
                f"مسیر پیشنهادی یادآوری: {channel}",
                "برای نسخه اولیه، مسیر مناسب را مشخص می‌کنیم؛ اتصال واقعی در مرحله بعد بررسی می‌شود",
            ]
        if family == "simple_finance_or_tracking":
            return [
                "می‌خواهی یه روش ساده داشته باشی که پول روزانه کارت رو ثبت کنی",
                f"اول روی این تمرکز می‌کنیم: {a_lower or 'درآمد و هزینه'}",
                "بدون نرم‌افزار پیچیده — ساده، سریع، قابل فهم",
            ]
        if family == "customer_management":
            return [
                "می‌خواهی یه جای ساده داشته باشی که اطلاعات مشتری‌هات رو نگه داری",
                f"مهم‌ترین چیزی که ثبت می‌کنیم: {a_lower or 'اطلاعات و پیگیری'}",
                "می‌توانی بعداً بیشتر اضافه کنی — اول ساده شروع می‌کنیم",
            ]
        if family == "content_or_marketing":
            return [
                f"می‌خواهی کمک داشته باشی برای محتوا و پیام‌ها در {a_lower or 'شبکه اجتماعی'}",
                "نسخه اولیه ساختار کمک می‌کند — تولید خودکار محتوا مرحله بعدی است",
            ]
        if family == "internal_admin_tool":
            return [
                "می‌خواهی یه ابزار داخلی داشته باشی که کارهای اداری رو منظم‌تر کنه",
                "با فرم‌ها و ثبت اطلاعات شروع می‌کنیم",
                "بعداً می‌توانیم تأیید و گردش کار اضافه کنیم",
            ]
        if family == "business_growth_or_operations":
            return [
                "می‌خواهی کسب‌وکارت راحت‌تر بچرخه و کمتر خودت درگیر جزئیات باشی",
                "با یک نقطه شروع مشخص می‌کنیم — بعداً گسترش می‌دهیم",
            ]
        if family == "website_or_public_presence":
            return [
                f"می‌خواهی یه حضور آنلاین داشته باشی — هدف اصلی: {a_lower or 'معرفی کار'}",
                "ساده، واضح، و قابل استفاده برای مشتریانت",
            ]
        return [
            "نیازت را فهمیدم — یه ابزار ساده می‌سازیم که مشکلت را حل کند",
            "با یک نسخه اولیه شروع می‌کنیم و بعداً گسترش می‌دهیم",
        ]

    if scenario == "news_site":
        a_lower = a.lower()
        base = [
            "یک سایت خبری می‌خواهی که تا حد ممکن خودش کار کند",
            "نسخه اولیه روی ساختار، دسته‌بندی خبرها، صفحه اصلی و تجربه خواندن خبر تمرکز می‌کند",
            "اتوماسیون کامل خبرها فعلاً ساخته نمی‌شود و مرحله بعدی است",
        ]
        if "مرجع سبک" in raw_text or "[مرجع" in raw_text:
            base.append("نمونه داده‌شده فقط مرجع سبک و ساختار است، نه کپی مستقیم")
        if "مطمئن نیستم" in a_lower or "فقط ظاهر" in a_lower:
            base.append("فعلاً روی ساختار و ظاهر سایت تمرکز می‌کنیم — منبع خبر بعداً مشخص می‌شود")
        elif "هوش مصنوعی" in a_lower:
            base.append("تولید خبر با هوش مصنوعی مرحله بعد است — ابتدا ساختار سایت را می‌سازیم")
        elif "منابع خبری" in a_lower:
            base.append("اتصال به منابع خبری خارجی مرحله بعد است — ابتدا ساختار سایت را می‌سازیم")
        return base

    if scenario == "restaurant":
        if "سفارش" in a:
            return [
                "یک صفحه معرفی کافه با امکان سفارش مستقیم می‌خواهی",
                "مشتری منو را ببیند و از همان صفحه سفارش بدهد",
                "نیازی به پرداخت آنلاین فعلاً نیست — سفارش ثبت می‌شود",
                "ظاهر باید گرم، خوش‌خوراک و قابل اعتماد باشد",
            ]
        return [
            "یک صفحه معرفی کافه می‌خواهی",
            "مشتری کافه را ببیند و بعد تماس بگیرد یا بیاید",
            "منو، آدرس و اطلاعات تماس باید واضح باشند",
            "ظاهر باید گرم، خوش‌خوراک و قابل اعتماد باشد",
        ]

    if scenario == "store":
        if "پرداخت" in a:
            return [
                "یک فروشگاه آنلاین با پرداخت داخل سایت می‌خواهی",
                "مشتری محصول انتخاب کند و همان‌جا پرداخت کند",
                "سیستم پرداخت آنلاین لازم است",
            ]
        return [
            "یک فروشگاه آنلاین ساده می‌خواهی",
            "مشتری سفارش بدهد و تو بعداً تماس بگیری",
            "نیازی به پرداخت آنلاین در این مرحله نیست",
            "صفحه محصولات، توضیحات، و فرم سفارش لازم است",
        ]

    if scenario == "booking":
        if "خودش" in a:
            return [
                "می‌خواهی دانش‌آموزها یا شرکت‌کننده‌ها بتوانند برای کلاس‌ها زمان رزرو کنند",
                "کاربر باید زمان‌های آزاد را ساده ببیند و انتخاب کند",
                "هدف این است که هماهنگی کلاس‌ها کمتر دستی و وقت‌گیر شود",
            ]
        return [
            "می‌خواهی شرکت‌کننده‌ها بتوانند درخواست وقت بدهند",
            "زمان پیشنهادی ثبت می‌شود و تو تأیید می‌کنی",
            "ساده‌تر از سیستم رزرو کامل — مناسب برای شروع",
        ]

    if scenario == "dashboard":
        if "سفارش" in a or "مدیریت" in a:
            return [
                "داشبوردی می‌خواهی که هم آمار ببینی هم سفارش‌ها را مدیریت کنی",
                "لیست سفارش‌ها، وضعیت، و گزارش فروش لازم است",
            ]
        return [
            "یک داشبورد برای دیدن آمار فروش می‌خواهی",
            "اعداد و نمودارهای کلیدی باید یک‌جا دیده شوند",
            "فقط برای دیدن خودت — دیگران دسترسی ندارند",
        ]

    if scenario == "telegram_bot":
        if "سفارش" in a:
            return [
                "یک ربات تلگرام برای گرفتن سفارش می‌خواهی",
                "مشتری از طریق ربات سفارش بدهد",
                "سفارش‌ها باید برای تو نمایش داده شوند",
            ]
        if "اطلاعات" in a:
            return [
                "یک ربات اطلاع‌رسانی می‌خواهی",
                "مشتری سؤال بپرسد و ربات جواب بدهد",
            ]
        if "رزرو" in a or "وقت" in a:
            return [
                "یک ربات رزرو وقت می‌خواهی",
                "مشتری از طریق تلگرام وقت انتخاب کند",
            ]
        return [
            "یک ربات تلگرام چندکاره می‌خواهی",
            "امکانات مختلف در یک ربات ترکیب می‌شوند",
        ]

    if scenario == "company_landing":
        if "سفارش" in a:
            return [
                "یک صفحه معرفی با امکان سفارش می‌خواهی",
                "مشتری کار تو را ببیند و از همان‌جا سفارش بدهد",
            ]
        if "رزرو" in a:
            return [
                "یک صفحه معرفی با امکان رزرو وقت می‌خواهی",
                "مشتری خدمات را ببیند و وقت بگیرد",
            ]
        return [
            "یک صفحه معرفی ساده برای کار یا کسب‌وکارت می‌خواهی",
            "مشتری بفهمد چه کاری می‌کنی و باهات تماس بگیرد",
            "شماره تماس، توضیح کوتاه، و دکمه تماس لازم است",
        ]

    if scenario == "general_ordering":
        if "غذا" in a or "کافه" in a or "رستوران" in a:
            return [
                "یک صفحه معرفی و سفارش برای کافه یا رستوران می‌خواهی",
                "مشتری بتواند از همان صفحه سفارش بدهد",
            ]
        return [
            "یک فروشگاه ساده برای سفارش‌گیری می‌خواهی",
            "مشتری باید بتواند محصول‌ها را ببیند و سفارش ثبت کند",
            "فعلاً تمرکز روی ساده شدن سفارش است، نه پیچیدگی‌های اضافی",
            "بعداً می‌توان پرداخت آنلاین یا تماس بعد از سفارش را دقیق‌تر کرد",
        ]

    if scenario == "general_class":
        if "ثبت‌نام" in a or "رزرو" in a:
            return [
                "می‌خواهی دانش‌آموزان به صورت آنلاین ثبت‌نام کنند",
                "سیستم رزرو یا ثبت‌نام کلاس لازم است",
            ]
        if "برنامه" in a or "نمایش" in a:
            return [
                "یک صفحه نمایش برنامه کلاس‌ها می‌خواهی",
                "شرکت‌کننده‌ها جدول کلاس‌ها را ببینند",
            ]
        return [
            "می‌خواهی کلاس‌هات را ساده‌تر مدیریت کنی",
            "ثبت کلاس‌ها، زمان‌ها، و دانش‌آموزان",
        ]

    if scenario == "general_showcase":
        if "سفارش" in a:
            return [
                "یک فروشگاه آنلاین ساده می‌خواهی",
                "مشتری محصول ببیند و سفارش بدهد",
            ]
        return [
            "یک صفحه معرفی محصولات می‌خواهی",
            "مشتری محصولات را ببیند و برای خرید تماس بگیرد",
            "نیازی به فروشگاه کامل نیست — نمایش و تماس کافی است",
        ]

    # general fallback — specific enough to feel understood, broad enough to cover any goal
    a_lower = a
    if "معرفی" in a_lower or "کار" in a_lower or "خدمات" in a_lower:
        return [
            "یک صفحه معرفی ساده برای کارت می‌خواهی",
            "هدف اصلی این است که آدم‌ها بفهمند چه کاری انجام می‌دهی",
            "مشتری باید بتواند راحت با تو تماس بگیرد",
            "لازم نیست فعلاً فروشگاه یا رزرو پیچیده بسازیم",
        ]
    if "تماس" in a_lower or "ارتباط" in a_lower:
        return [
            "یک صفحه ساده می‌خواهی که مشتری بتواند باهات تماس بگیرد",
            "توضیح کوتاهی از کارت و راه تماس کافی است",
            "ساده، واضح، و قابل اعتماد",
        ]
    if "فروش" in a_lower:
        return [
            "یک فروشگاه یا صفحه فروش ساده می‌خواهی",
            "مشتری باید بتواند محصول را ببیند و سفارش بدهد",
        ]
    if "رزرو" in a_lower or "وقت" in a_lower:
        return [
            "یک سیستم رزرو ساده می‌خواهی",
            "مشتری باید بتواند وقت یا خدمات را رزرو کند",
        ]
    return [
        "یک صفحه ساده آنلاین برای کارت می‌خواهی",
        "هنوز جزئیات را با هم روشن می‌کنیم — شروع خوبی است",
    ]
