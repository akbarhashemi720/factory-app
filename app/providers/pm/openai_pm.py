"""
OpenAI PM Provider.

Calls GPT-4o-mini to generate a structured understanding.
Falls back to mock provider on any error.

Requires: OPENAI_API_KEY in settings.
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
    """Call OpenAI API and return structured understanding."""
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": _SYSTEM_PROMPT_TEMPLATE.format(language=language)},
                {"role": "user", "content": raw_text},
            ],
            temperature=0.3,
        )
        return _parse(response.choices[0].message.content)
    except Exception as exc:
        print(f"[openai_pm] call failed ({exc}), falling back to mock")
        from app.providers.pm.mock_pm import generate as mock_generate
        return mock_generate(raw_text, language)


def _parse(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Non-JSON from OpenAI: {exc}") from exc
    required = {"bullets", "assumptions", "clarification_questions",
                "detected_scenario", "confidence"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Missing keys: {missing}")
    return data
