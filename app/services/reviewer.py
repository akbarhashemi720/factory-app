"""
Reviewer Agent — service layer.

Routes to the configured reviewer provider.
Routes never import provider modules directly — only this file does.

REVIEWER_PROVIDER options:
    rule_based  → providers/reviewer/rule_based_reviewer.py  (default)
    ai          → providers/reviewer/ai_reviewer.py          (placeholder, falls back)
"""
from __future__ import annotations

from typing import Any


def review_preview(preview_data: dict[str, Any],
                   understanding: dict[str, Any]) -> dict[str, Any]:
    """
    Dispatch to the configured reviewer provider.

    All providers share the same interface:
        review(preview_data, understanding) -> dict
    """
    from app.config import settings

    provider = settings.reviewer_provider.lower()

    if provider == "ai":
        from app.providers.reviewer.ai_reviewer import review
        return review(preview_data, understanding)

    # Default: rule_based
    from app.providers.reviewer.rule_based_reviewer import review
    return review(preview_data, understanding)
