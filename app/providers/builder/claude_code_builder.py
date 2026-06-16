"""
Claude Code Builder Provider — PLACEHOLDER.

Future production builder. Not implemented in Sprint 3.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW THIS WILL WORK (future sprint)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Read builder_task from the Shared Factory Repository.
   The task contains: scenario, product_brief, build_mode,
   and any ScenarioPack patterns to start from.

2. Construct a structured prompt using the task + ScenarioPack template.
   Do NOT send raw user text — send structured instructions only.

3. Call Claude Code (or equivalent code-generation API).
   build_mode routing:
     fast_preview    → lightweight scaffold (~60s target)
     production_build → full HTML/CSS/JS (speed improves over time; quality always first)
     revision        → targeted diff applied to existing output
     export          → package approved version for download

4. Receive generated files (HTML, JSON, assets).

5. Return in the standard provider contract:
   {preview_data, change_summary, known_limitations}

6. Write output back to Shared Factory Repository.
   Never hand output directly to the user — PM Agent presents it.

Performance target for common scenarios:
  fast_preview    → < 2 minutes
  production_build → depends on complexity; speed is a long-term optimisation direction
  (measured from builder_task created to builder_output stored)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

To activate (future):
    BUILDER_PROVIDER=claude_code
    CLAUDE_CODE_API_KEY=...  (or via Anthropic SDK)

Interface must match mock_builder.generate exactly.
"""
from __future__ import annotations

from typing import Any


def generate(project: dict, understanding: dict, scenario_pattern: dict | None = None) -> dict[str, Any]:  # noqa: ARG001
    """Not yet implemented. Use BUILDER_PROVIDER=mock for Sprint 3."""
    raise NotImplementedError(
        "Claude Code Builder is a placeholder. "
        "Set BUILDER_PROVIDER=mock to use the simulated builder."
    )
