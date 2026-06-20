"""
Product Manager Agent — service layer.

Two-phase approach:
  Phase 1: generate_understanding()    — returns one diagnostic question
  Phase 2: refine_understanding()      — takes user's answer, returns bullets

Routes always call this module; they never import provider modules directly.

PM_PROVIDER options:
    mock        → providers/pm/mock_pm.py  (default)
    openai      → providers/pm/openai_pm.py
    anthropic   → providers/pm/anthropic_pm.py
"""
from __future__ import annotations

from typing import Any


def generate_understanding(raw_text: str, language: str = "fa") -> dict[str, Any]:
    """
    Phase 1: detect intent and return one diagnostic question.
    The response will have has_diagnostic_question=True and include
    diagnostic_question + diagnostic_options for the UI.
    """
    from app.config import settings
    provider = settings.pm_provider.lower()

    if provider == "openai":
        from app.providers.pm.openai_pm import generate
        return generate(raw_text, language, api_key=settings.openai_api_key)
    if provider == "anthropic":
        from app.providers.pm.anthropic_pm import generate
        return generate(raw_text, language, api_key=settings.anthropic_api_key)

    from app.providers.pm.mock_pm import generate
    return generate(raw_text, language)


def refine_understanding(raw_text: str, diagnostic_answer: str,
                         detected_scenario: str,
                         language: str = "fa") -> dict[str, Any]:
    """
    Phase 2: incorporate user's diagnostic answer into refined understanding.
    Returns bullets, confirmed scenario, and no further questions.

    Uses the SAME provider as Phase 1 — mock is only an emergency fallback
    inside each provider's own refine(), not the default path here.
    """
    from app.config import settings
    provider = settings.pm_provider.lower()

    if provider == "openai":
        try:
            from app.providers.pm.openai_pm import refine
            return refine(raw_text, diagnostic_answer, detected_scenario, language,
                          api_key=settings.openai_api_key)
        except ImportError:
            from app.providers.pm.mock_pm import refine
            return refine(raw_text, diagnostic_answer, detected_scenario, language)
    if provider == "anthropic":
        from app.providers.pm.anthropic_pm import refine
        return refine(raw_text, diagnostic_answer, detected_scenario, language,
                      api_key=settings.anthropic_api_key)

    from app.providers.pm.mock_pm import refine
    return refine(raw_text, diagnostic_answer, detected_scenario, language)
