"""
Anthropic PM Provider.

Calls Claude Haiku to generate a structured understanding.
Falls back to mock provider on any error.

Requires: ANTHROPIC_API_KEY in settings.
"""
from __future__ import annotations

import json
from typing import Any


_SYSTEM_PROMPT_TEMPLATE = """You are the Product Manager of an AI Factory.
Understand what a non-technical user wants to build.
User language: {language}

Return ONLY valid JSON with these exact keys:
{{
  "bullets": ["3-4 simple bullets in user's language"],
  "assumptions": ["1-2 assumptions, or []"],
  "clarification_questions": ["only if vague, else []"],
  "detected_scenario": "restaurant | dashboard | company_landing | general",
  "confidence": "high | medium | low"
}}
No preamble, no markdown fences. Only the JSON object."""


def generate(raw_text: str, language: str = "fa",
             api_key: str | None = None) -> dict[str, Any]:
    """Call Anthropic API and return structured understanding."""
    try:
        import anthropic  # type: ignore
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=_SYSTEM_PROMPT_TEMPLATE.format(language=language),
            messages=[{"role": "user", "content": raw_text}],
        )
        return _parse(message.content[0].text)
    except Exception as exc:
        print(f"[anthropic_pm] call failed ({exc}), falling back to mock")
        from app.providers.pm.mock_pm import generate as mock_generate
        return mock_generate(raw_text, language)


def _parse(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Non-JSON from Anthropic: {exc}") from exc
    required = {"bullets", "assumptions", "clarification_questions",
                "detected_scenario", "confidence"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Missing keys: {missing}")
    return data
