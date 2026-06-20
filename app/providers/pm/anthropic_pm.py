"""
Anthropic PM Provider — Website Builder Understanding Layer (v3).

Uses Claude with forced tool-use (function calling) to GUARANTEE valid
structured JSON output. Covers both:
  - generate(): Phase 1 — initial understanding + diagnostic question
  - refine():   Phase 2 — incorporate user's diagnostic answer

Falls back to mock only as an emergency path if the API call itself fails
(network error, invalid key, rate limit) — NOT as the normal path.
"""
from __future__ import annotations
from typing import Any


_SYSTEM_PROMPT = """تو مدیر محصول یک کارخانه هوش مصنوعی برای کاربران غیرفنی هستی — تمرکز فعلی فقط روی «ساخت وب‌سایت» است.
وظیفه‌ات: فهم عمیق آنچه یک شخص غیرفنی می‌خواهد بسازد — نه تطبیق با یک قالب از پیش تعریف‌شده.

همیشه به فارسی پاسخ بده.
business_domain باید دقیقاً همان چیزی باشد که کاربر خواسته — نه نزدیک‌ترین قالب.
اگر کاربر درباره آموزش آشپزی پرسید → business_domain = "آموزش آشپزی ایرانی"، نه "آرایشگاه" یا "رزرو نوبت".
اگر کاربر درباره آموزش زبان پرسید → business_domain = "آموزش زبان انگلیسی".
اگر کاربر درباره سفارش غذا پرسید → business_domain = "سفارش غذا".

قانون مهم برای انتخاب detected_scenario:
هر چیزی که شامل «کلاس»، «دوره»، «آموزش» باشد — برای هر موضوعی (آشپزی، زبان، موسیقی، هنر و...) —
باید scenario = general_class باشد، حتی اگر کلمه «ثبت‌نام» یا «برنامه زمانی» هم در متن باشد.
scenario = booking فقط برای رزرو نوبت خدماتی مثل آرایشگاه، کلینیک، تعمیرگاه است — نه کلاس‌های آموزشی.

قانون بسیار مهم برای کافه/رستوران — website_intent باید دقیق انتخاب شود:
کافه می‌تواند چند نوع سایت کاملاً متفاوت باشد. هرگز یک قالب ثابت را به همه فرض نکن.
- اگر کاربر فقط گفت «سایت کافه می‌خوام» بدون جزئیات بیشتر → confidence باید "low" باشد و
  در missing_questions این سؤال دقیق فارسی را بگذار:
  "می‌خواهی سایت کافه بیشتر برای چه کاری باشد؟"
  و این گزینه‌ها را در bullets یا missing_questions به شکل قابل‌فهم پیشنهاد بده:
  معرفی کافه و نمایش منو / رزرو میز / سفارش آنلاین / فروش محصولات قهوه / ترکیبی از چند مورد
- اگر کاربر گفت «معرفی»، «منو»، «گالری» بدون سفارش/فروش → website_intent = "cafe_intro"
- اگر کاربر گفت «رزرو میز» به‌عنوان هدف اصلی → website_intent = "cafe_reservation"
- اگر کاربر گفت «سفارش آنلاین»، «سفارش غذا و نوشیدنی» → website_intent = "cafe_ordering"
- اگر کاربر گفت «فروش قهوه»، «فروش محصولات»، «فروشگاه قهوه» → website_intent = "coffee_ecommerce"
- اگر چند مورد با هم خواسته شد → website_intent = "cafe_hybrid"

برای آموزش:
- آموزش آشپزی → website_intent = "cooking_education"
- آموزش زبان برای کودکان → website_intent = "children_english_education"
- سایر آموزش‌ها → website_intent = "education_website"

برای رزرو نوبت خدماتی (آرایشگاه و مانند آن) → website_intent = "service_booking"
برای هر چیز دیگر → website_intent = "general_website"

اگر اطمینان کافی نداری (مخصوصاً برای کافه مبهم)، حدس قطعی نزن — حتماً سؤال در missing_questions بگذار
و confidence را "low" بگذار.
هرگز سؤال فنی نپرس (API، دیتابیس، بک‌اند، هاستینگ و مانند آن)."""


def _scenario_enum_description() -> str:
    return (
        "Choose the SINGLE best match:\n"
        "- restaurant: cafes, restaurants, food ordering, menus\n"
        "- store: online shops, product sales, e-commerce\n"
        "- booking: appointment/time-slot booking for services like "
        "barbershops, salons, clinics, repair shops — NOT classes or courses\n"
        "- general_class: ANY teaching, courses, classes, workshops, training — "
        "including cooking classes, language classes, online/offline classes, "
        "skill courses, educational programs of any kind. If the user mentions "
        "'کلاس' (class), 'دوره' (course), 'آموزش' (teaching/education) for ANY "
        "subject (cooking, language, music, art, etc.) — always choose general_class, "
        "never booking, even if they also mention scheduling or registration.\n"
        "- telegram_bot: bots, automated messaging assistants\n"
        "- company_landing: business/company intro pages with no specific product\n"
        "- general: anything else"
    )


_WEBSITE_INTENT_ENUM = [
    "cafe_intro", "cafe_reservation", "cafe_ordering", "coffee_ecommerce",
    "cafe_hybrid", "education_website", "cooking_education",
    "children_english_education", "service_booking", "general_website",
]

_WEBSITE_INTENT_DESCRIPTION = (
    "The SPECIFIC website intent — more precise than detected_scenario. "
    "For cafe-related requests, NEVER assume one fixed type — distinguish: "
    "cafe_intro (just showcase + menu), cafe_reservation (table booking focus), "
    "cafe_ordering (online food/drink ordering), coffee_ecommerce (selling coffee "
    "products like a store), cafe_hybrid (combination). "
    "For education: cooking_education, children_english_education, or generic education_website. "
    "service_booking is ONLY for appointment-based services (barbershop, salon, clinic) — "
    "never for classes/courses. If the request is too vague to tell (e.g. just 'سایت کافه می‌خوام' "
    "with no further detail), set confidence to low and ask in missing_questions instead of guessing."
)


def _build_tool_schema(name: str, description: str) -> dict:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": {
                "product_type": {
                    "type": "string",
                    "enum": ["website", "bot", "mobile_app", "dashboard", "unknown"],
                },
                "business_domain": {"type": "string", "description": "Persian — exact business domain"},
                "website_intent": {
                    "type": "string",
                    "enum": _WEBSITE_INTENT_ENUM,
                    "description": _WEBSITE_INTENT_DESCRIPTION,
                },
                "primary_goal": {"type": "string", "description": "Persian — one sentence"},
                "target_users": {"type": "string", "description": "Persian — who will visit this site"},
                "user_actions": {"type": "array", "items": {"type": "string"}},
                "owner_actions": {"type": "array", "items": {"type": "string"}},
                "suggested_features": {"type": "array", "items": {"type": "string"}},
                "bullets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-4 simple Persian bullets for user confirmation",
                },
                "missing_questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Only if truly needed — non-technical, max 1. "
                        "REQUIRED if the cafe/restaurant request is ambiguous about "
                        "intro vs reservation vs ordering vs ecommerce."
                    ),
                },
                "detected_scenario": {
                    "type": "string",
                    "enum": ["restaurant", "store", "booking", "general_class",
                             "telegram_bot", "company_landing", "general"],
                    "description": _scenario_enum_description(),
                },
                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},

                # Rich product spec fields (Builder v2/v3)
                "product_name": {"type": "string", "description": "Persian product name"},
                "visual_style": {"type": "string", "description": "e.g. warm, modern, minimal, playful"},
                "color_palette": {
                    "type": "object",
                    "properties": {
                        "primary": {"type": "string", "description": "hex color"},
                        "secondary": {"type": "string", "description": "hex color"},
                    },
                },
                "hero_title": {"type": "string"},
                "hero_subtitle": {"type": "string"},
                "primary_cta": {"type": "string"},
                "secondary_cta": {"type": "string"},
                "navigation_items": {"type": "array", "items": {"type": "string"}},
                "required_sections": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Persian section names this website needs, based on website_intent",
                },
                "menu_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "icon": {"type": "string"},
                            "name": {"type": "string"},
                            "desc": {"type": "string"},
                            "price": {"type": "string"},
                        },
                    },
                    "description": "Items, courses, services, or products depending on domain",
                },
                "benefits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "icon": {"type": "string"},
                            "title": {"type": "string"},
                            "desc": {"type": "string"},
                        },
                    },
                },
                "about_text": {"type": "string", "description": "Persian — 1-2 sentences about the business"},
                "first_version_scope": {"type": "string", "description": "Persian — what v1 actually builds"},
            },
            "required": ["product_type", "business_domain", "website_intent", "primary_goal",
                         "bullets", "detected_scenario", "confidence"],
        },
    }


_GENERATE_TOOL = _build_tool_schema(
    "submit_understanding",
    "Submit the structured understanding of the user's product request.",
)
_REFINE_TOOL = _build_tool_schema(
    "submit_refined_understanding",
    "Submit the refined structured understanding after incorporating the user's "
    "answer to a clarification question. Resolve any ambiguity using their answer.",
)


def generate(raw_text: str, language: str = "fa",
             api_key: str | None = None) -> dict[str, Any]:
    """Phase 1 — Call Claude with forced tool-use for guaranteed structured output."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            tools=[_GENERATE_TOOL],
            tool_choice={"type": "tool", "name": "submit_understanding"},
            messages=[{"role": "user", "content": raw_text}],
        )
        tool_block = next((b for b in message.content if b.type == "tool_use"), None)
        if tool_block is None:
            raise ValueError("No tool_use block in Claude response")
        data = dict(tool_block.input)
        return _apply_defaults(data)

    except Exception as exc:
        print(f"[anthropic_pm] generate() call failed ({exc}), using mock fallback")
        from app.providers.pm.mock_pm import generate as mock_generate
        return mock_generate(raw_text, language)


def refine(raw_text: str, diagnostic_answer: str,
           detected_scenario: str, language: str = "fa",
           api_key: str | None = None) -> dict[str, Any]:
    """Phase 2 — incorporate the user's diagnostic answer using Claude."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        context = (
            f"درخواست اصلی کاربر: {raw_text}\n"
            f"سناریوی اولیه تشخیص‌داده‌شده: {detected_scenario}\n"
            f"جواب کاربر به سؤال شفاف‌سازی: {diagnostic_answer}\n\n"
            "حالا فهم نهایی و دقیق را بر اساس جواب کاربر بساز. ابهام را با همین جواب رفع کن."
        )
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            tools=[_REFINE_TOOL],
            tool_choice={"type": "tool", "name": "submit_refined_understanding"},
            messages=[{"role": "user", "content": context}],
        )
        tool_block = next((b for b in message.content if b.type == "tool_use"), None)
        if tool_block is None:
            raise ValueError("No tool_use block in Claude refine response")
        data = dict(tool_block.input)
        data["missing_questions"] = []  # Phase 2 never asks again
        return _apply_defaults(data)

    except Exception as exc:
        print(f"[anthropic_pm] refine() call failed ({exc}), using mock fallback")
        from app.providers.pm.mock_pm import refine as mock_refine
        return mock_refine(raw_text, diagnostic_answer, detected_scenario, language)


def _apply_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """Ensure all expected keys exist with safe defaults."""
    data.setdefault("product_type", "website")
    data.setdefault("business_domain", "")
    data.setdefault("website_intent", "general_website")
    data.setdefault("primary_goal", "")
    data.setdefault("target_users", "")
    data.setdefault("user_actions", [])
    data.setdefault("owner_actions", [])
    data.setdefault("suggested_features", [])
    data.setdefault("bullets", [])
    data.setdefault("missing_questions", [])
    data.setdefault("detected_scenario", "general")
    data.setdefault("confidence", "medium")
    # Rich spec defaults
    data.setdefault("product_name", data.get("business_domain") or "محصول شما")
    data.setdefault("visual_style", "modern")
    data.setdefault("color_palette", {})
    data.setdefault("hero_title", data.get("product_name", ""))
    data.setdefault("hero_subtitle", data.get("primary_goal", ""))
    data.setdefault("primary_cta", "شروع کنید")
    data.setdefault("secondary_cta", None)
    data.setdefault("navigation_items", [])
    data.setdefault("required_sections", [])
    data.setdefault("menu_items", [])
    data.setdefault("benefits", [])
    data.setdefault("about_text", "")
    data.setdefault("first_version_scope", "")
    # has_diagnostic_question flag — used by routes to decide whether to show a question
    data["has_diagnostic_question"] = bool(data.get("missing_questions"))
    if data["has_diagnostic_question"]:
        data["diagnostic_question"] = data["missing_questions"][0]
        data["diagnostic_options"] = _options_for_intent(data.get("business_domain", ""))
    return data


def _options_for_intent(business_domain: str) -> list[str]:
    """Best-effort option list for the clarification question (cafe ambiguity)."""
    if any(k in business_domain for k in ["کافه", "رستوران", "کافی‌شاپ"]):
        return [
            "معرفی کافه و نمایش منو",
            "رزرو میز",
            "سفارش آنلاین",
            "فروش محصولات قهوه",
            "ترکیبی از چند مورد",
        ]
    return []
