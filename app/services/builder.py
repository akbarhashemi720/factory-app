"""
Builder Agent — service layer.

Stable interface between the route layer and the underlying builder provider.
Routes always call this module; they never import provider modules directly.

To swap the builder provider, change BUILDER_PROVIDER in .env:
    BUILDER_PROVIDER=mock          → providers/builder/mock_builder.py
    BUILDER_PROVIDER=claude_code   → providers/builder/claude_code_builder.py (placeholder)
    (future providers follow the same pattern)
"""
from __future__ import annotations

from typing import Any


def generate_preview(
    project: dict,
    understanding: dict,
    scenario_pattern: dict | None = None,
) -> dict[str, Any]:
    """
    Dispatch to the configured builder provider.

    Args:
        project:          projects row
        understanding:    confirmed understandings row
        scenario_pattern: optional reusable_patterns row from Memory Layer.
                          Used as a soft starting hint — never overrides
                          the current understanding or user request.

    All providers must return:
        {preview_data, change_summary, known_limitations}
    """
    from app.config import settings

    provider = settings.builder_provider.lower()

    if provider == "claude_code":
        from app.providers.builder.claude_code_builder import generate
        return generate(project, understanding, scenario_pattern)

    # Default: mock
    from app.providers.builder.mock_builder import generate
    return generate(project, understanding, scenario_pattern)
