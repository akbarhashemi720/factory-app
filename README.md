[models (1).py](https://github.com/user-attachments/files/29054772/models.1.py)
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
    customer_id: str | None  # MVP ownership — generated at project creation
    status: str
    scenario: str | None
    language: str
    current_version_id: UUID | None
    final_approval_status: bool = False
    created_at: datetime
    updated_at: datetime


class UserRequestRow(BaseModel):
    id: UUID
    project_id: UUID
    raw_text: str
    input_type: str
    detected_language: str
    attachments: list[Any]
    created_at: datetime


class UnderstandingRow(BaseModel):
    id: UUID
    project_id: UUID
    bullets: list[str]
    assumptions: list[str]
    clarification_questions: list[str]
    user_answers: list[str] = []
    detected_scenario: str | None
    confidence: str | None
    confirmed_by_user: bool
    confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class BuilderOutputRow(BaseModel):
    id: UUID
    project_id: UUID
    version_id: UUID | None
    output_type: str
    preview_data: dict[str, Any]
    change_summary: list[str]
    known_limitations: list[str]
    created_at: datetime


class VersionRow(BaseModel):
    id: UUID
    project_id: UUID
    version_number: int
    version_label: str
    output_id: UUID | None
    review_report_id: UUID | None
    user_visible_preview: dict[str, Any]
    approved_by_user: bool
    created_at: datetime


class ReviewReportRow(BaseModel):
    id: UUID
    project_id: UUID
    version_id: UUID | None
    overall_status: str
    issues_found: list[str]
    checklist: list[dict[str, Any]]
    user_friendly_summary: str | None
    internal_notes: str | None
    created_at: datetime


class ApprovedVersionRow(BaseModel):
    id: UUID
    project_id: UUID
    version_id: UUID
    approved_at: datetime
    user_feedback: str | None
    final_summary: str | None


class LearningNoteRow(BaseModel):
    id: UUID
    project_id: UUID
    version_id: UUID | None
    scenario: str | None
    product_type: str | None
    what_worked: list[str]
    user_preferences_detected: dict[str, Any]
    reusable_patterns: list[str]
    created_at: datetime


class RevisionRequestRow(BaseModel):
    id: UUID
    project_id: UUID
    from_version_id: UUID
    raw_revision_text: str
    interpreted_actions: list[dict[str, Any]]
    status: str
    created_at: datetime
    updated_at: datetime


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
    created_at: datetime
    updated_at: datetime


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
    detected_scenario: str | None
    confidence: str | None
    confirmed_by_user: bool
    status: str
    # Diagnostic question fields (Phase 1)
    has_diagnostic_question: bool = False
    preamble: str | None = None
    diagnostic_question: str | None = None
    diagnostic_options: list[str] = Field(default_factory=list)


class ConfirmUnderstandingResponse(BaseModel):
    project_id: UUID
    understanding_id: UUID
    confirmed_by_user: bool
    status: str


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


class GenerateRevisionResponse(BaseModel):
    project_id: UUID
    revision_request_id: UUID
    from_version_id: UUID
    new_version_id: UUID
    output_id: UUID
    review_report_id: UUID
    status: str
    preview_data: dict[str, Any]
    message: str


class ExportRow(BaseModel):
    id: UUID
    project_id: UUID
    version_id: UUID
    export_type: str
    export_data: dict[str, Any]
    summary: str | None
    created_at: datetime


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
