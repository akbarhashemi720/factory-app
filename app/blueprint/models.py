"""
Product Blueprint — data model (Puzzle 1, AI Factory v2 planning).

This file defines the SHAPE of a "Product Blueprint" — the structured
description of what a non-technical user actually needs, what tool best
solves that need, and what should (and should not) be built for them.

This is intentionally a DATA MODEL ONLY. Nothing in the current app
creates, reads, or depends on a ProductBlueprint yet. The existing
Website Preview Builder flow (request -> understanding -> diagnostic
question -> confirm -> generate-preview -> revision/edit-direct ->
approve -> export) is completely unaffected by this file and continues
to use its own existing data shapes (UnderstandingRow, the html_builder
"spec" dict, etc.) exactly as before.

Why this exists:
Today, "understanding" in this codebase answers the narrow question
"what kind of website should this be?" (via `website_intent`). A real
Product Blueprint answers the broader question AI Factory v2 needs to
answer: "what does this person actually need, and what is the best
digital tool for that need — which may or may not be a website?"

Future direction (not implemented by this file):
  User need -> Need Understanding -> Solution Recommendation
  -> Product Blueprint (this model) -> Output Builder -> Launch
  -> Managed Product Layer

Follows the same Pydantic style already used elsewhere in this project
(see app/models.py and app/inspiration/models.py).
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


ConfidenceLevel = Literal["low", "medium", "high"]


class ProductBlueprint(BaseModel):
    """
    A structured description of a user's real need and the recommended
    digital solution for it — the planning artifact that should
    eventually sit between Solution Recommendation and the Output
    Builder in the AI Factory v2 flow.

    Every field is optional (defaults to None / empty) so a partial
    blueprint can exist while the understanding is still being refined,
    the same way the existing UnderstandingRow allows partial data
    during the multi-step understanding flow.
    """

    # ── Core understanding fields ───────────────────────────────────────────
    # What the person actually said, and what we believe they actually need —
    # kept separate from any assumption about which tool solves it.
    raw_user_request: str | None = None
    user_need: str | None = None
    user_type: str | None = None
    business_or_personal_context: str | None = None
    industry_category: str | None = None
    problem_to_solve: str | None = None
    digital_need_category: str | None = None

    # ── Recommendation fields ───────────────────────────────────────────────
    # recommended_tool_type is the best tool for the REAL need — e.g.
    # "order page", "form", "dashboard", "bot", "task agent",
    # "support agent", "website preview", "product catalog", or
    # "booking system". It is not assumed to always be a website.
    recommended_tool_type: str | None = None
    reason_for_recommendation: str | None = None
    recommended_starting_point: str | None = None
    # first_output_type is what gets BUILT first. For now this will
    # usually still be "website_preview" (the only Output Adapter that
    # currently exists), but the model itself makes no such assumption —
    # it is a plain string, not an enum locked to website values.
    first_output_type: str | None = None

    # ── Product structure fields ────────────────────────────────────────────
    core_features: list[str] = Field(default_factory=list)
    future_features: list[str] = Field(default_factory=list)
    launch_requirements: list[str] = Field(default_factory=list)
    managed_product_needs: list[str] = Field(default_factory=list)
    # Possible AI roles that might manage this product later (e.g. "Support
    # Agent", "Sales Agent") — purely descriptive/planning data here, NOT a
    # claim that any such agent exists or runs. No real or fake agent
    # behavior is implied or implemented by listing a name in this field.
    possible_ai_agents: list[str] = Field(default_factory=list)

    # ── Safety / thinking fields ────────────────────────────────────────────
    # These let the factory reason honestly about its own recommendation,
    # including when it should recommend AGAINST something.
    confidence_level: ConfidenceLevel | None = None
    assumptions: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    # not_recommended + reason_not_recommended let the factory say, e.g.,
    # "A mobile app is not recommended for the first version because it
    # is too heavy for a homemade pickle seller."
    not_recommended: list[str] = Field(default_factory=list)
    reason_not_recommended: str | None = None
