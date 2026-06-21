"""
Inspiration Bank — data model (Part 1).

Stores DESIGN INSPIRATION METADATA ONLY — never copies a real website's
code, images, text, logos, or brand assets. Each record represents a
"design family" (a reusable pattern: layout shape, color mood, card
style, section order) that the builder can draw from to produce more
visually diverse generated websites, while still being something the
contextual editor can fully understand and edit afterward.

Popularity is intentionally only ONE signal among several in
inspiration_value_score — a popular site is not automatically a good
design reference for a small local business.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class InspirationReference(BaseModel):
    """One design-family reference record. Pure metadata — no scraped assets."""

    # ── Identity ─────────────────────────────────────────────────────────────
    reference_id: str
    job_category: str          # e.g. "website_builder"
    business_type: str         # e.g. "cafe", "clothing_store", "education"
    reference_name: str        # human-readable family name, e.g. "گرم و صمیمی"
    reference_url: str | None = None   # optional, for internal research only —
                                        # NEVER shown to the customer, NEVER scraped/copied

    # ── Design characteristics (what the builder actually uses) ────────────
    visual_style: str          # e.g. "warm_handmade", "minimal_clean", "luxury_premium"
    layout_type: str           # e.g. "hero_grid_menu", "gallery_first", "story_driven"
    color_palette: dict[str, str] = Field(default_factory=dict)   # {"primary": "#...", "secondary": "#...", "accent": "#..."}
    hero_style: str            # e.g. "large_image_overlay", "split_text_image", "centered_minimal"
    navigation_style: str      # e.g. "sticky_simple", "transparent_overlay", "centered_logo"
    card_style: str            # e.g. "rounded_shadow", "flat_bordered", "image_focused"
    section_structure: list[str] = Field(default_factory=list)  # ordered section types for this family
    interaction_style: str     # e.g. "subtle_hover", "scroll_reveal", "minimal_static"

    # ── Guidance for the builder/AI ──────────────────────────────────────────
    best_for: list[str] = Field(default_factory=list)   # intents this family suits, e.g. ["لوکس", "خاص"]
    inspiration_notes: str = ""    # short internal note on what makes this family distinct
    avoid_copying: str = (
        "این فقط یک الگوی طراحی است — هیچ متن، تصویر، لوگو یا کد واقعی از منبع کپی نمی‌شود."
    )
    tags: list[str] = Field(default_factory=list)

    # ── Editability contract (Part 4) ────────────────────────────────────────
    # Declares which editable layers this family's generated sections must
    # expose, so the contextual editor (icon/box/card/section layers,
    # separate text-color vs background-color) keeps working regardless of
    # which inspiration family was used to generate the site.
    editable_layer_requirements: list[str] = Field(
        default_factory=lambda: ["section", "card", "image_box", "icon_image", "title", "description", "price", "button"]
    )

    # ── Scoring inputs ────────────────────────────────────────────────────────
    freshness_score: float = 0.0          # 0-1, how current/modern the pattern feels
    design_quality_score: float = 0.0     # 0-1, internal design-quality judgment
    industry_match_score: float = 0.0     # 0-1, how well it fits this business_type
    uniqueness_score: float = 0.0         # 0-1, how distinct vs other families in the bank
    popularity_score: float = 0.0         # 0-1, derived from the popularity signals below

    # ── Popularity / audience signals (inputs to popularity_score only —
    #    never used alone to pick a family) ───────────────────────────────────
    traffic_rank: int | None = None              # lower is more popular, optional/approximate
    estimated_audience_level: str | None = None   # "niche" | "moderate" | "mainstream"
    brand_popularity: str | None = None           # "emerging" | "known" | "well_known"
    social_presence: str | None = None            # "low" | "medium" | "high"
    review_presence: str | None = None            # "low" | "medium" | "high"
    search_visibility: str | None = None          # "low" | "medium" | "high"

    @property
    def inspiration_value_score(self) -> float:
        """
        30% design_quality + 25% industry_match + 20% freshness
        + 15% popularity + 10% uniqueness.
        Popularity is deliberately weighted low — a popular site is not
        always the best design reference for a given business.
        """
        return round(
            0.30 * self.design_quality_score
            + 0.25 * self.industry_match_score
            + 0.20 * self.freshness_score
            + 0.15 * self.popularity_score
            + 0.10 * self.uniqueness_score,
            4,
        )

    def to_customer_facing_summary(self) -> dict[str, Any]:
        """
        What the customer is allowed to see — human Persian language only.
        Never exposes reference_id, reference_url, technical fields, or
        scoring internals.
        """
        return {
            "name": self.reference_name,
            "description": self.inspiration_notes,
        }
