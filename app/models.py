from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ─── Request bodies ───────────────────────────────────────────────────────────

class CreateProjectRequest(BaseModel):
    user_id: str | None = None
    language: str = "fa"
    # customer_id: MVP ownership tracking — not real auth.
    # Frontend may generate a UUID; backend generates one if not provided.
    # Never shown to the user.
    customer_id: str | None = None


class SubmitRequestBody(BaseModel):
    raw_text: str = Field(..., min_length=1, description="متن درخواست کاربر")
    input_type: str = "text"
    detected_language: str = "fa"
    attachments: list[Any] = Field(default_factory=list)


class ConfirmUnderstandingRequest(BaseModel):
    understanding_id: UUID
    confirmed: bool


# ─── Row models ───────────────────────────────────────────────────────────────
# Declared before any Response model that references them.

class ProjectRow(BaseModel):
    id: UUID
    user_id: str | None = None
    customer_id: str | None = None  # MVP ownership — generated at project creation
    status: str
    scenario: str | None
    language: str
    current_version_id: UUID | None = None
    final_approval_status: bool = False
    created_at: datetime = None
    updated_at: datetime = None


class UserRequestRow(BaseModel):
    id: UUID
    project_id: UUID
    raw_text: str
    input_type: str
    detected_language: str
    attachments: list[Any]
    created_at: datetime = None


class UnderstandingRow(BaseModel):
    id: UUID
    project_id: UUID
    bullets: list[str] = []
    assumptions: list[str] = []
    clarification_questions: list[str] = []
    user_answers: list[str] = []
    detected_scenario: str | None = None
    confidence: str | None = None
    confirmed_by_user: bool = False
    confirmed_at: datetime | None = None
    created_at: datetime = None
    updated_at: datetime = None

    # ── Rich structured fields (from Claude understanding) ─────────────────────
    # Stored so they survive the round-trip to storage and back into the builder.
    # All optional — mock_pm / older data simply won't populate them.
    website_intent: str | None = None
    product_type: str | None = None
    business_domain: str | None = None
    product_name: str | None = None
    target_users: str | None = None
    primary_goal: str | None = None
    visual_style: str | None = None
    color_palette: dict[str, Any] = {}
    hero_title: str | None = None
    hero_subtitle: str | None = None
    primary_cta: str | None = None
    secondary_cta: str | None = None
    navigation_items: list[str] = []
    required_sections: list[str] = []
    menu_items: list[dict[str, Any]] = []
    benefits: list[dict[str, Any]] = []
    about_text: str | None = None
    user_actions: list[str] = []
    owner_actions: list[str] = []
    suggested_features: list[str] = []
    first_version_scope: str | None = None

    # ── Rich structured fields (Builder v2 / Website Builder) ──────────────────
    # Persisted so Claude's structured understanding survives into generate-preview.
    product_type: str | None = None
    business_domain: str | None = None
    website_intent: str | None = None
    primary_goal: str | None = None
    target_users: str | None = None
    product_name: str | None = None
    visual_style: str | None = None
    color_palette: dict[str, Any] = {}
    hero_title: str | None = None
    hero_subtitle: str | None = None
    primary_cta: str | None = None
    secondary_cta: str | None = None
    navigation_items: list[str] = []
    required_sections: list[str] = []
    user_actions: list[str] = []
    owner_actions: list[str] = []
    suggested_features: list[str] = []
    menu_items: list[dict[str, Any]] = []
    benefits: list[dict[str, Any]] = []
    about_text: str | None = None
    first_version_scope: str | None = None


class BuilderOutputRow(BaseModel):
    id: UUID
    project_id: UUID
    version_id: UUID | None
    output_type: str
    preview_data: dict[str, Any]
    change_summary: list[str]
    known_limitations: list[str]
    created_at: datetime = None


class VersionRow(BaseModel):
    id: UUID
    project_id: UUID
    version_number: int
    version_label: str
    output_id: UUID | None
    review_report_id: UUID | None
    user_visible_preview: dict[str, Any]
    approved_by_user: bool
    created_at: datetime = None


class ReviewReportRow(BaseModel):
    id: UUID
    project_id: UUID
    version_id: UUID | None
    overall_status: str
    issues_found: list[str]
    checklist: list[dict[str, Any]]
    user_friendly_summary: str | None
    internal_notes: str | None
    created_at: datetime = None


class ApprovedVersionRow(BaseModel):
    id: UUID
    project_id: UUID
    version_id: UUID
    approved_at: datetime = None
    user_feedback: str | None = None
    final_summary: str | None = None


class LearningNoteRow(BaseModel):
    id: UUID
    project_id: UUID
    version_id: UUID | None
    scenario: str | None
    product_type: str | None
    what_worked: list[str]
    user_preferences_detected: dict[str, Any]
    reusable_patterns: list[str]
    created_at: datetime = None


class RevisionRequestRow(BaseModel):
    id: UUID
    project_id: UUID
    from_version_id: UUID
    raw_revision_text: str
    interpreted_actions: list[dict[str, Any]]
    status: str
    created_at: datetime = None
    updated_at: datetime = None


class ReusablePatternRow(BaseModel):
    id: UUID
    scenario: str
    pattern_type: str
    source_project_id: UUID | None
    source_version_id: UUID | None
    title: str | None
    pattern_data: dict[str, Any]
    usage_count: int
    approval_count: int
    created_at: datetime = None
    updated_at: datetime = None


# ─── Response bodies ──────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class CreateProjectResponse(BaseModel):
    project_id: UUID
    status: str
    language: str
    customer_id: str  # always present — generated if not supplied


class ProjectSummary(BaseModel):
    """Lightweight project card for the customer workspace list."""
    project_id: UUID
    title: str | None = None          # from latest understanding title if available
    scenario: str | None = None       # internal — used for icon/type label
    status: str                        # internal status — frontend maps to Persian
    updated_at: str
    current_version_id: UUID | None = None


class CustomerProjectsResponse(BaseModel):
    customer_id: str
    projects: list[ProjectSummary]


class SubmitRequestResponse(BaseModel):
    project_id: UUID
    request_id: UUID
    status: str
    raw_text: str


class AnswerDiagnosticRequest(BaseModel):
    understanding_id: UUID
    diagnostic_answer: str = Field(..., min_length=1)


class GenerateUnderstandingResponse(BaseModel):
    project_id: UUID
    understanding_id: UUID
    bullets: list[str]
    assumptions: list[str]
    clarification_questions: list[str]
    detected_scenario: str | None = None
    confidence: str | None = None
    confirmed_by_user: bool = False
    status: str
    # Diagnostic question fields (Phase 1)
    has_diagnostic_question: bool = False
    preamble: str | None = None
    diagnostic_question: str | None = None
    diagnostic_options: list[str] = Field(default_factory=list)


class ConfirmUnderstandingResponse(BaseModel):
    project_id: UUID
    understanding_id: UUID
    confirmed_by_user: bool = False
    status: str


class RetryBuildResponse(BaseModel):
    """
    Response for POST /projects/{id}/retry-build — resets a project stuck
    in 'building'/'reviewing' (e.g. after an internal reviewer rejection
    that reverted it without giving the user any way to retry) back to
    'ready_for_builder' so the normal generate-preview flow can run again.
    """
    project_id: UUID
    status: str


class RevisionCopyResponse(BaseModel):
    """
    Response for POST /projects/{id}/create-revision-copy — creates a new,
    independent, editable project pre-filled with the original raw_text
    from an approved project. The approved project itself is never
    mutated: no status change, no version/approval data touched.
    """
    new_project_id: UUID
    status: str
    raw_text: str


class ReopenForEditResponse(BaseModel):
    """
    Response for POST /projects/{id}/reopen-for-edit — explicitly chosen
    by the founder: an approved project CAN be reopened for direct
    editing (not just copied), but it must go back through the normal
    review + final-approval gate before it counts as approved again.
    This sets status back to 'ready_for_user_review' so the existing
    /revision and /edit-direct flows work unchanged, and /approve
    requires a fresh explicit confirmation to re-lock it.
    """
    project_id: UUID
    status: str


class RecommendationResponse(BaseModel):
    """
    Puzzle 6.6 — the user-facing "پیشنهاد کارخانه" recommendation step.

    Deliberately exposes ONLY simple, human-readable Persian fields —
    never raw ProductBlueprint internals (industry_category,
    confidence_level, recommended_tool_type, etc.). Those stay
    internal/debug-only via the separately-gated /blueprint/draft
    endpoint, which this route does NOT call or depend on.
    """
    project_id: UUID
    understood_summary: str       # "فهمیدم می‌خواهی ..."
    recommended_output_label: str  # human label for what we'll build, e.g. "کاتالوگ محصول و صفحه سفارش ساده"
    reason: str                    # why this fits better than the alternative
    first_output_note: str         # honest note: this is the first available output, not the whole factory
    not_recommended_note: str | None = None  # what we are NOT building first, and why (optional)


class NeedFirstResponse(BaseModel):
    """
    Puzzle: need-first advisor step — shown BEFORE the existing
    website-section diagnostic question (mock_pm/anthropic_pm's
    _DIAGNOSTIC), only when ENABLE_NEED_FIRST_RECOMMENDATION is "true".

    Mirrors RecommendationResponse's style: only simple, human-readable
    Persian fields, never raw internal tool_key values directly (those
    only appear inside `options`, paired with their Persian label, so
    the frontend can echo the chosen option_key back when continuing —
    but nothing here is a confidence_level/industry_category-style debug
    field).
    """
    project_id: UUID
    understood_summary: str            # "فهمیدم مشکل اصلی تو ... است."
    framing_note: str                  # "سایت، بات، ... فقط راه‌حل هستند؛ ..."
    options: list[dict[str, str]] = Field(default_factory=list)   # [{option_key, label}], length 0-3
    factory_recommendation_key: str | None = None
    factory_recommendation_label: str | None = None
    reason: str | None = None
    needs_clarification: bool = False
    clarification_question: str | None = None
    clarification_options: list[str] = Field(default_factory=list)


class GeneratePreviewResponse(BaseModel):
    project_id: UUID
    status: str
    version_id: UUID
    output_id: UUID
    review_report_id: UUID
    preview_data: dict[str, Any]
    review_summary: str


class ApproveVersionRequest(BaseModel):
    version_id: UUID
    user_feedback: str | None = None


class ApproveVersionResponse(BaseModel):
    project_id: UUID
    version_id: UUID
    status: str
    approved_by_user: bool
    learning_note_id: UUID
    message: str


class RevisionRequestBody(BaseModel):
    raw_revision_text: str = Field(..., min_length=1)
    from_version_id: UUID | None = None
    # Contextual editing — populated when the user clicked a specific
    # element/section in the full-site preview before describing the
    # change. All optional: when absent, the AI falls back to guessing
    # from the request text + full section list (the old behavior).
    selected_element_id: str | None = None
    selected_element_type: str | None = None
    selected_element_text: str | None = None
    selected_section_id: str | None = None
    selected_section_type: str | None = None


class SaveHtmlRequest(BaseModel):
    """Save edited HTML from the GrapesJS website editor back onto the current version.

    This is a direct save (no AI re-interpretation) — the user has already
    made their edits visually in the editor; we just persist the result.
    """
    version_id: UUID
    html_preview: str = Field(..., min_length=1)


class SaveHtmlResponse(BaseModel):
    project_id: UUID
    version_id: UUID
    preview_data: dict[str, Any]
    message: str


class DirectEditRequest(BaseModel):
    """
    Apply one or more DIRECT, deterministic edits from the Contextual Edit
    Panel's mini-dashboard (text/color/size fields, card fields, price,
    section background color, section move). No AI involved — this is the
    fix for "direct fields don't apply unless the user also writes a
    natural-language instruction": the panel now calls this endpoint
    straight away, with no dependency on text interpretation.
    """
    version_id: UUID
    selected_section_id: str = Field(..., min_length=1)
    selected_element_id: str | None = None
    # Layer hierarchy — when the clicked element sits inside a box/card
    # (e.g. an icon inside its colored box inside a product card), these
    # carry the resolved ids for the other layers, and target_layer says
    # which one the user actually picked in the "می‌خواهی کدام قسمت را
    # تغییر بدهی؟" selector ("element" | "box" | "card"). Defaults to
    # "element" (the exact clicked thing) when not specified.
    selected_box_id: str | None = None
    selected_card_id: str | None = None
    target_layer: str | None = None      # "element" | "box" | "card"
    # One or more of the following may be set, depending on what the user
    # changed in the mini-dashboard. All optional — only present fields
    # are applied.
    new_text: str | None = None          # updates the element's main text field
    item_index: int | None = None        # required when editing a list item (card title/desc/price)
    field_key: str | None = None         # which content field to update — "title", "name", "desc", "price", "primary_button", ...
    color: str | None = None             # hex color for the element's text/icon
    background_color: str | None = None  # hex color for section background or card/button background
    size: str | None = None              # "small" | "medium" | "large"
    icon: str | None = None              # emoji/icon replacement
    move_section: str | None = None      # "up" | "down" — move the whole selected section


class DirectEditResponse(BaseModel):
    project_id: UUID
    version_id: UUID
    preview_data: dict[str, Any]
    message: str


class GenerateRevisionResponse(BaseModel):
    project_id: UUID
    revision_request_id: UUID
    from_version_id: UUID
    new_version_id: UUID
    output_id: UUID
    review_report_id: UUID
    status: str
    preview_data: dict[str, Any] | None = None
    message: str


class ExportRow(BaseModel):
    id: UUID
    project_id: UUID
    version_id: UUID
    export_type: str
    export_data: dict[str, Any]
    summary: str | None
    created_at: datetime = None


class ExportResponse(BaseModel):
    project_id:         UUID
    version_id:         UUID
    export_id:          UUID
    export_type:        str
    summary:            str
    export_data:        dict[str, Any]   # internal — downstream build use
    delivery_education: dict[str, Any]   # user-facing — clear, non-technical
    message:            str


class ProjectStateResponse(BaseModel):
    project: ProjectRow
    user_requests: list[UserRequestRow]
    understandings: list[UnderstandingRow] = Field(default_factory=list)
    builder_outputs: list[BuilderOutputRow] = Field(default_factory=list)
    versions: list[VersionRow] = Field(default_factory=list)
    review_reports: list[ReviewReportRow] = Field(default_factory=list)
    approved_versions: list[ApprovedVersionRow] = Field(default_factory=list)
    learning_notes: list[LearningNoteRow] = Field(default_factory=list)
    revision_requests: list[RevisionRequestRow] = Field(default_factory=list)
    reusable_patterns: list[ReusablePatternRow] = Field(default_factory=list)
    exports: list[ExportRow] = Field(default_factory=list)
