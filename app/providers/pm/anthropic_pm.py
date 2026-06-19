"""
Anthropic PM Provider — Smart Understanding Layer (v2).

Uses Claude with forced tool-use (function calling) to GUARANTEE valid
structured JSON output — no markdown fences, no prose, no parsing errors.

Falls back to mock only as an emergency path if the API call itself fails
(network error, invalid key, rate limit) — NOT as the normal path.
"""
from __future__ import annotations
from typing import Any


_SYSTEM_PROMPT = """تو مدیر محصول یک کارخانه هوش مصنوعی برای کاربران غیرفنی هستی.
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

اگر اطمینان کافی نداری، یک سؤال ساده و غیرفنی در missing_questions بگذار.
هرگز سؤال فنی نپرس (API، دیتابیس، بک‌اند، هاستینگ و مانند آن)."""


_TOOL_SCHEMA = {
    "name": "submit_understanding",
    "description": "Submit the structured understanding of the user's product request.",
    "input_schema": {
        "type": "object",
        "properties": {
            "product_type": {
                "type": "string",
                "enum": ["website", "bot", "mobile_app", "dashboard", "unknown"],
            },
            "business_domain": {"type": "string", "description": "Persian — exact business domain"},
            "primary_goal": {"type": "string", "description": "Persian — one sentence"},
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
                "description": "Only if truly needed — non-technical, max 1",
            },
            "detected_scenario": {
                "type": "string",
                "enum": ["restaurant", "store", "booking", "general_class",
                         "telegram_bot", "company_landing", "general"],
                "description": (
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
                ),
            },
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},

            # Rich product spec fields (Builder v2)
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
            "sections": {"type": "array", "items": {"type": "string"}},
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
        "required": ["product_type", "business_domain", "primary_goal", "bullets",
                     "detected_scenario", "confidence"],
    },
}


def generate(raw_text: str, language: str = "fa",
             api_key: str | None = None) -> dict[str, Any]:
    """Call Claude with forced tool-use for guaranteed structured output."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            tools=[_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": "submit_understanding"},
            messages=[{"role": "user", "content": raw_text}],
        )

        # Find the tool_use block — guaranteed structured JSON, no parsing needed
        tool_block = next(
            (b for b in message.content if b.type == "tool_use"), None
        )
        if tool_block is None:
            raise ValueError("No tool_use block in Claude response")

        data = dict(tool_block.input)
        return _apply_defaults(data)

    except Exception as exc:
        print(f"[anthropic_pm] API call failed ({exc}), using mock fallback")
        from app.providers.pm.mock_pm import generate as mock_generate
        return mock_generate(raw_text, language)


def _apply_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """Ensure all expected keys exist with safe defaults."""
    data.setdefault("product_type", "unknown")
    data.setdefault("business_domain", "")
    data.setdefault("primary_goal", "")
    data.setdefault("user_actions", [])
    data.setdefault("owner_actions", [])
    data.setdefault("suggested_features", [])
    data.setdefault("bullets", [])
    data.setdefault("missing_questions", [])
    data.setdefault("detected_scenario", "general")
    data.setdefault("confidence", "medium")
    # Rich spec defaults
    data.setdefault("product_name", data.get("business_domain", "محصول شما"))
    data.setdefault("visual_style", "modern")
    data.setdefault("color_palette", {})
    data.setdefault("hero_title", data.get("product_name", ""))
    data.setdefault("hero_subtitle", data.get("primary_goal", ""))
    data.setdefault("primary_cta", "شروع کنید")
    data.setdefault("secondary_cta", None)
    data.setdefault("navigation_items", [])
    data.setdefault("sections", [])
    data.setdefault("menu_items", [])
    data.setdefault("benefits", [])
    data.setdefault("about_text", "")
    data.setdefault("first_version_scope", "")
    return data
