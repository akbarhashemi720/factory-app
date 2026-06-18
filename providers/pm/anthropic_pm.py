"""
Anthropic PM Provider — Smart Understanding Layer.

Uses Claude to freely understand any user request — not template matching.
Returns structured JSON with product_type, business_domain, goals, features, etc.

Falls back to mock gracefully if API key is missing.
"""
from __future__ import annotations
import json
from typing import Any


_SYSTEM_PROMPT = """You are the Product Manager of an AI Factory for non-technical users.
Your job: deeply understand what a non-technical person wants to build.

The user writes in Persian (Farsi). You must respond in Persian too.
Read their request carefully and return ONLY valid JSON — no preamble, no markdown.

Return this exact JSON structure:
{
  "product_type": "website | bot | mobile_app | dashboard | unknown",
  "business_domain": "free text in Persian — e.g. آموزش زبان انگلیسی، سفارش غذا، رزرو نوبت",
  "primary_goal": "one sentence in Persian — what the owner wants to achieve",
  "user_actions": ["list of what the end user can do — in Persian"],
  "owner_actions": ["list of what the business owner can do — in Persian"],
  "suggested_features": ["3-5 key features in Persian"],
  "bullets": ["3-4 simple bullets summarizing the understanding — in Persian, for user confirmation"],
  "missing_questions": ["only truly important questions, NOT technical — max 1 question, or []"],
  "detected_scenario": "best matching scenario key from: restaurant, store, booking, general_class, general_ordering, telegram_bot, company_landing, general",
  "confidence": "high | medium | low"
}

Rules:
- If confidence is low, add ONE simple Persian question to missing_questions
- NEVER ask technical questions (API, database, backend, hosting, etc.)
- bullets must be simple and human — these will be shown to the user for confirmation
- business_domain must reflect EXACTLY what the user asked for, not a nearby template
- If user asks about English teaching → business_domain = "آموزش زبان انگلیسی", NOT "رستوران"
- If user asks about food ordering → business_domain = "سفارش غذا"
- Respond ONLY with the JSON object. No other text."""


def generate(raw_text: str, language: str = "fa",
             api_key: str | None = None) -> dict[str, Any]:
    """Call Claude API for free-form understanding. Falls back to mock if unavailable."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": raw_text}],
        )
        raw = message.content[0].text
        return _parse(raw)
    except Exception as exc:
        print(f"[anthropic_pm] API call failed ({exc}), using mock fallback")
        # DEMO FALLBACK — not a real understanding, only for when API is unavailable
        from app.providers.pm.mock_pm import generate as mock_generate
        return mock_generate(raw_text, language)


def _parse(raw: str) -> dict[str, Any]:
    """Parse and validate the JSON response from Claude."""
    try:
        # Strip markdown fences if present
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Non-JSON from Claude: {exc}") from exc

    # Ensure required keys exist with defaults
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
    return data
