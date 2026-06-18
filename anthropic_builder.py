"""
Anthropic Builder Provider.

Uses Claude to generate a real product plan as preview_data.
No fixed templates — Claude reads the understanding and builds a proper plan.

Falls back to mock_builder if API key is unavailable.
"""
from __future__ import annotations
import json
from typing import Any


_SYSTEM_PROMPT = """You are the Builder of an AI Factory for non-technical users.
You receive a confirmed understanding of what a user wants to build.
Your job: create a real, useful product plan — not a generic template.

Respond ONLY with valid JSON. No preamble, no markdown fences.

Return this exact structure:
{
  "scenario": "same as detected_scenario from understanding",
  "product_name": "a good Persian name for this product",
  "product_type": "website | bot | app | dashboard",
  "target_users": "who will use this — in Persian",
  "title": "main headline — in Persian",
  "subtitle": "one line description — in Persian",
  "tone": "friendly | professional | calm | energetic",
  "primary_button": "main call to action — in Persian",
  "secondary_button": "secondary action or null",
  "show_contact": true or false,
  "sections": ["list of main pages/sections — in Persian"],
  "features": ["list of key features — in Persian"],
  "user_journey": ["step by step what the end user does — in Persian"],
  "v1_scope": "what version 1 will actually build — one paragraph in Persian",
  "cards": []
}

Rules:
- Make it SPECIFIC to the actual business domain — not generic
- If it is about English teaching → name it something like "مدرسه آنلاین زبان"
- If it is about food ordering → name it with food/restaurant theme
- sections must match the actual product (4-6 sections)
- v1_scope must be honest and clear — what will actually be built first
- All text must be in simple, non-technical Persian
- NEVER use words like API, backend, frontend, database, deployment
- Respond ONLY with the JSON object."""


def generate(
    project: dict,
    understanding: dict,
    scenario_pattern: dict | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Generate a real product plan using Claude."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Build context for Claude
        context = {
            "business_domain": understanding.get("business_domain", ""),
            "product_type": understanding.get("product_type", ""),
            "primary_goal": understanding.get("primary_goal", ""),
            "user_actions": understanding.get("user_actions", []),
            "owner_actions": understanding.get("owner_actions", []),
            "suggested_features": understanding.get("suggested_features", []),
            "confirmed_bullets": understanding.get("bullets", []),
            "detected_scenario": understanding.get("detected_scenario", "general"),
        }

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Build a product plan for this understanding:\n{json.dumps(context, ensure_ascii=False)}"
            }],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        preview_data = json.loads(raw.strip())

        return {
            "preview_data": preview_data,
            "change_summary": [
                f"برنامه محصول برای «{preview_data.get('product_name', '')}» ساخته شد",
                f"نوع محصول: {preview_data.get('product_type', '')}",
                "محتوا بر اساس نیاز واقعی شما طراحی شده",
            ],
            "known_limitations": [
                "این برنامه اولیه است — جزئیات در مرحله اصلاح قابل تغییر است",
                "تصاویر و محتوای نهایی در مراحل بعد اضافه می‌شود",
            ],
        }

    except Exception as exc:
        print(f"[anthropic_builder] API call failed ({exc}), using mock fallback")
        from app.providers.builder.mock_builder import generate as mock_generate
        return mock_generate(project, understanding, scenario_pattern)
