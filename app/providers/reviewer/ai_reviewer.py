"""
AI Reviewer Provider — PLACEHOLDER.

Future provider that uses a language model to review builder output.
Not implemented in Sprint 3 / 3.1.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTERFACE CONTRACT (same as rule_based_reviewer)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    review(preview_data: dict, understanding: dict) -> dict

    Returns:
        {
            "overall_status":        "passed" | "needs_revision" | "blocked",
            "issues_found":          list[str],
            "checklist":             list[{label, passed, note}],
            "user_friendly_summary": str,
            "internal_notes":        str,
        }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUALITY GATES (future — all reviewers must enforce these)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
quality_gates = [
    "matches_confirmed_understanding",  # output scenario == confirmed scenario
    "required_components_exist",        # title, subtitle, primary CTA present
    "correction_is_visible",            # requested corrections reflected in output
    "user_preview_is_understandable",   # no technical jargon in user-facing content
    "no_internal_technical_details_exposed",  # no IDs, logs, or raw data in preview
]

HOW THIS WILL WORK (future sprint):
  1. Receive preview_data + confirmed understanding.
  2. Build a structured review prompt.
  3. Call an AI model (OpenAI / Anthropic / etc.).
  4. Parse the structured JSON response into checklist + overall_status.
  5. Ensure user_friendly_summary contains no technical terms.
  6. Fall back to rule_based_reviewer on any error.

To activate (future):
    REVIEWER_PROVIDER=ai
    (plus the relevant AI API key)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

from typing import Any


def review(preview_data: dict[str, Any],
           understanding: dict[str, Any]) -> dict[str, Any]:
    """Not yet implemented. Falls back to rule-based reviewer."""
    print("[ai_reviewer] not implemented — falling back to rule_based_reviewer")
    from app.providers.reviewer.rule_based_reviewer import review as rule_review
    return rule_review(preview_data, understanding)
