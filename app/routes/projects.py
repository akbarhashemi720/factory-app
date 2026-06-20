from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException

from app.database import get_db
from app.models import (
    AnswerDiagnosticRequest,
    ApproveVersionRequest,
    ApproveVersionResponse,
    ConfirmUnderstandingRequest,
    ConfirmUnderstandingResponse,
    CreateProjectRequest,
    CreateProjectResponse,
    CustomerProjectsResponse,
    ExportResponse,
    GeneratePreviewResponse,
    GenerateRevisionResponse,
    GenerateUnderstandingResponse,
    ProjectStateResponse,
    ProjectSummary,
    RevisionRequestBody,
    DirectEditRequest,
    DirectEditResponse,
    SaveHtmlRequest,
    SaveHtmlResponse,
    SubmitRequestBody,
    SubmitRequestResponse,
)
from app.services.builder import generate_preview
from app.services.exporter import create_export_package
from app.services.memory import (create_learning_note, create_reusable_pattern,
                                  find_latest_pattern_for_scenario)
from app.services.pm_agent import generate_understanding, refine_understanding
from app.services.ai_revision import interpret_and_apply
from app.services.reviewer import review_preview

router = APIRouter(prefix="/projects", tags=["projects"])


# ─── helpers ─────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_project_or_404(db, project_id: UUID) -> dict:
    result = db.table("projects").select("*").eq("id", str(project_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Project not found")
    return result.data[0]


def _get_project_for_customer_or_404(
    db, project_id: UUID, customer_id: str | None
) -> dict:
    """
    Fetch project and optionally verify customer ownership.

    MVP SCOPING NOTE:
    This is MVP ownership scoping, not authentication.
    Unscoped fallback exists only for backward compatibility and must be
    removed once real auth is added.

    If customer_id is provided and the project has one, they must match.
    If either is absent, falls back to unscoped access (backward compat).
    """
    project = _get_project_or_404(db, project_id)
    project_cid = project.get("customer_id")
    if customer_id and project_cid and customer_id != project_cid:
        raise HTTPException(status_code=403, detail="Project not found")
    return project


def _update_project(db, project_id: UUID, payload: dict) -> None:
    """Update project fields; always refreshes updated_at."""
    payload["updated_at"] = _now_iso()
    db.table("projects").update(payload).eq("id", str(project_id)).execute()


# ─── POST /insight/session — Create a test session (operator-internal) ─────────

@router.post("/insight/session", status_code=201)
def create_insight_session(body: dict = None):
    """
    Create a private test session. Operator-internal only.
    No auth required for MVP private testing.
    session_id is never shown to the non-technical tester.
    """
    from app.services.insight import create_session
    db = get_db()
    session = create_session(db, (body or {}).get("tester_label", ""))
    return {"session_id": session["session_id"], "status": "created"}


# ─── POST /insight/event — Log a test event (operator-internal) ──────────────

@router.post("/insight/event", status_code=201)
def log_insight_event(body: dict):
    """
    Log a user testing event. Operator-internal only.
    Never shown to non-technical tester. No external analytics.
    """
    from app.services.insight import log_event
    db = get_db()
    log_event(
        db,
        session_id=body.get("session_id", ""),
        event_type=body.get("event_type", ""),
        project_id=body.get("project_id"),
        meta=body.get("meta", {}),
    )
    return {"status": "recorded"}


# ─── GET /insight/report — Operator summary (operator-internal) ──────────────

@router.get("/insight/report")
def get_insight_report():
    """
    Operator-only summary of all test sessions.
    Never shown to non-technical tester.
    """
    from app.services.insight import all_sessions_report
    db = get_db()
    return {"sessions": all_sessions_report(db)}


# ─── POST /insight/feedback — Private testing feedback (operator-internal) ────

@router.post("/insight/feedback", status_code=201)
def submit_insight_feedback(
    body: dict,
    x_customer_id: Optional[str] = Header(default=None),
):
    """
    Store private tester feedback internally.
    Operator-only insight — never exposed in the user-facing UI.
    No external analytics services. No passwords or secrets recorded.
    """
    db = get_db()
    db.table("test_events").insert({
        "session_id":    x_customer_id or "anonymous",
        "event_type":    "final_feedback_submitted",
        "project_id":    body.get("project_id"),
        "occurred_at":   body.get("submitted_at", ""),
        "meta": {
            "understood":     body.get("understood", ""),
            "output_matched": body.get("output_matched", ""),
            "confusion_note": body.get("confusion_note", ""),
            "improvement":    body.get("improvement", ""),
        },
    }).execute()
    return {"status": "recorded"}


# ─── GET /projects ── Customer Workspace List ─────────────────────────────────

@router.get("", response_model=CustomerProjectsResponse)
def list_customer_projects(
    x_customer_id: Optional[str] = Header(default=None),
):
    """
    Return projects owned by the requesting customer.

    Requires X-Customer-Id header.
    If missing → returns empty list (do not leak other customers' projects).
    Projects are sorted by updated_at descending (most recent first).
    """
    if not x_customer_id:
        return CustomerProjectsResponse(customer_id="", projects=[])

    db = get_db()
    result = (
        db.table("projects")
        .select("*")
        .eq("customer_id", x_customer_id)
        .order("updated_at", desc=True)
        .execute()
    )

    summaries: list[ProjectSummary] = []
    for row in result.data:
        # Try to find a human title from the latest understanding
        title = None
        try:
            und_result = (
                db.table("understandings")
                .select("bullets")
                .eq("project_id", str(row["id"]))
                .eq("confirmed_by_user", True)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if und_result.data:
                bullets = und_result.data[0].get("bullets", [])
                if bullets:
                    # Use first bullet as a short title hint
                    title = bullets[0][:60] if isinstance(bullets[0], str) else None
        except Exception:
            pass  # title stays None — not critical

        summaries.append(
            ProjectSummary(
                project_id=row["id"],
                title=title,
                scenario=row.get("scenario"),
                status=row.get("status", "draft"),
                updated_at=str(row.get("updated_at", "")),
                current_version_id=row.get("current_version_id"),
            )
        )

    return CustomerProjectsResponse(
        customer_id=x_customer_id,
        projects=summaries,
    )


# ─── POST /projects ───────────────────────────────────────────────────────────

@router.post("", response_model=CreateProjectResponse, status_code=201)
def create_project(body: CreateProjectRequest):
    """
    Create a new factory project.

    customer_id is an MVP ownership identifier — not real auth.
    If the caller provides one (e.g. from browser localStorage), it is stored.
    If not, the backend generates one. Either way it is always present.
    The customer_id is never shown to the user.
    """
    import uuid as _uuid
    db = get_db()

    # Resolve customer_id: use provided or generate a new one
    customer_id = body.customer_id or str(_uuid.uuid4())

    data: dict = {
        "language":    body.language,
        "status":      "draft",
        "customer_id": customer_id,
    }
    if body.user_id:
        data["user_id"] = body.user_id

    result = db.table("projects").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create project")
    row = result.data[0]
    return CreateProjectResponse(
        project_id=row["id"],
        status=row["status"],
        language=row["language"],
        customer_id=row["customer_id"],
    )


# ─── POST /projects/{project_id}/request ─────────────────────────────────────

@router.post("/{project_id}/request", response_model=SubmitRequestResponse)
def submit_request(project_id: UUID, body: SubmitRequestBody, x_customer_id: Optional[str] = Header(default=None)):
    """Save user request and advance to waiting_for_user_confirmation."""
    db = get_db()
    _get_project_for_customer_or_404(db, project_id, x_customer_id)

    req_data = {
        "project_id": str(project_id),
        "raw_text": body.raw_text,
        "input_type": body.input_type,
        "detected_language": body.detected_language,
        "attachments": body.attachments,
    }
    req_result = db.table("user_requests").insert(req_data).execute()
    if not req_result.data:
        raise HTTPException(status_code=500, detail="Failed to save user request")

    _update_project(db, project_id, {"status": "waiting_for_user_confirmation"})

    row = req_result.data[0]
    return SubmitRequestResponse(
        project_id=project_id,
        request_id=row["id"],
        status="waiting_for_user_confirmation",
        raw_text=row["raw_text"],
    )


# ─── POST /projects/{project_id}/understanding ───────────────────────────────

@router.post("/{project_id}/understanding",
             response_model=GenerateUnderstandingResponse)
def create_understanding(project_id: UUID, x_customer_id: Optional[str] = Header(default=None)):
    """Run PM Agent on the latest user request and save understanding."""
    db = get_db()
    project = _get_project_for_customer_or_404(db, project_id, x_customer_id)

    req_result = (
        db.table("user_requests")
        .select("raw_text, detected_language")
        .eq("project_id", str(project_id))
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not req_result.data:
        raise HTTPException(
            status_code=400,
            detail="No user request found. Submit a request before generating understanding.",
        )

    latest = req_result.data[0]
    language = latest.get("detected_language") or project.get("language", "fa")

    try:
        ai = generate_understanding(latest["raw_text"], language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PM Agent failed: {e}") from e

    und_data = {
        "project_id": str(project_id),
        "bullets": ai.get("bullets", []),
        "assumptions": ai.get("assumptions", []),
        "clarification_questions": ai.get("clarification_questions", []),
        "detected_scenario": ai.get("detected_scenario"),
        "confidence": ai.get("confidence"),
        "confirmed_by_user": False,
        # Rich structured fields — persisted so they survive into generate-preview
        "product_type": ai.get("product_type"),
        "business_domain": ai.get("business_domain"),
        "website_intent": ai.get("website_intent"),
        "primary_goal": ai.get("primary_goal"),
        "target_users": ai.get("target_users"),
        "product_name": ai.get("product_name"),
        "visual_style": ai.get("visual_style"),
        "color_palette": ai.get("color_palette") or {},
        "hero_title": ai.get("hero_title"),
        "hero_subtitle": ai.get("hero_subtitle"),
        "primary_cta": ai.get("primary_cta"),
        "secondary_cta": ai.get("secondary_cta"),
        "navigation_items": ai.get("navigation_items") or [],
        "required_sections": ai.get("required_sections") or ai.get("sections") or [],
        "user_actions": ai.get("user_actions") or [],
        "owner_actions": ai.get("owner_actions") or [],
        "suggested_features": ai.get("suggested_features") or [],
        "menu_items": ai.get("menu_items") or [],
        "benefits": ai.get("benefits") or [],
        "about_text": ai.get("about_text"),
        "first_version_scope": ai.get("first_version_scope"),
    }
    und_result = db.table("understandings").insert(und_data).execute()
    if not und_result.data:
        raise HTTPException(status_code=500, detail="Failed to save understanding")

    _update_project(db, project_id, {
        "status": project["status"],
        "scenario": ai.get("detected_scenario"),
    })

    und_row = und_result.data[0]
    return GenerateUnderstandingResponse(
        project_id=project_id,
        understanding_id=und_row["id"],
        bullets=und_row["bullets"],
        assumptions=und_row["assumptions"],
        clarification_questions=und_row["clarification_questions"],
        detected_scenario=und_row["detected_scenario"],
        confidence=und_row["confidence"],
        confirmed_by_user=False,
        status=project["status"],
        has_diagnostic_question=ai.get("has_diagnostic_question", False),
        preamble=ai.get("preamble"),
        diagnostic_question=ai.get("diagnostic_question"),
        diagnostic_options=ai.get("diagnostic_options", []),
    )


# ─── POST /projects/{project_id}/answer-diagnostic ───────────────────────────

@router.post("/{project_id}/answer-diagnostic",
             response_model=GenerateUnderstandingResponse)
def answer_diagnostic(project_id: UUID, body: AnswerDiagnosticRequest, x_customer_id: Optional[str] = Header(default=None)):
    """
    Phase 2: user answers the diagnostic question.
    PM Agent refines the understanding with tighter bullets.
    Updates the understanding row in-place with refined bullets.
    """
    db = get_db()
    project = _get_project_for_customer_or_404(db, project_id, x_customer_id)

    # Fetch the understanding being refined
    und_result = (
        db.table("understandings")
        .select("*")
        .eq("id", str(body.understanding_id))
        .execute()
    )
    if not und_result.data:
        raise HTTPException(status_code=404, detail="Understanding not found")
    und_row = und_result.data[0]
    if und_row["project_id"] != str(project_id):
        raise HTTPException(status_code=400,
                            detail="Understanding does not belong to this project")

    # Fetch the original request text for context
    req_result = (
        db.table("user_requests")
        .select("raw_text, detected_language")
        .eq("project_id", str(project_id))
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    raw_text = req_result.data[0]["raw_text"] if req_result.data else ""
    language = (req_result.data[0].get("detected_language") if req_result.data
                else project.get("language", "fa"))

    # Phase 2: refine understanding with diagnostic answer
    try:
        refined = refine_understanding(
            raw_text=raw_text,
            diagnostic_answer=body.diagnostic_answer,
            detected_scenario=und_row.get("detected_scenario") or "",
            language=language,
        )
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"PM Agent refine failed: {e}") from e

    # Update understanding row with refined bullets + rich fields
    # Rich fields fall back to the existing Phase-1 value if refine() doesn't override them,
    # so structured data from Claude's first pass is never silently dropped.
    now = _now_iso()
    db.table("understandings").update({
        "bullets":           refined.get("bullets", []),
        "assumptions":       refined.get("assumptions", []),
        "clarification_questions": [],
        "detected_scenario": refined.get("detected_scenario") or und_row.get("detected_scenario"),
        "updated_at":        now,
        # Rich structured fields
        "product_type":        refined.get("product_type") or und_row.get("product_type"),
        "business_domain":     refined.get("business_domain") or und_row.get("business_domain"),
        "website_intent":      refined.get("website_intent") or und_row.get("website_intent"),
        "primary_goal":        refined.get("primary_goal") or und_row.get("primary_goal"),
        "target_users":        refined.get("target_users") or und_row.get("target_users"),
        "product_name":        refined.get("product_name") or und_row.get("product_name"),
        "visual_style":        refined.get("visual_style") or und_row.get("visual_style"),
        "color_palette":       refined.get("color_palette") or und_row.get("color_palette") or {},
        "hero_title":          refined.get("hero_title") or und_row.get("hero_title"),
        "hero_subtitle":       refined.get("hero_subtitle") or und_row.get("hero_subtitle"),
        "primary_cta":         refined.get("primary_cta") or und_row.get("primary_cta"),
        "secondary_cta":       refined.get("secondary_cta") or und_row.get("secondary_cta"),
        "navigation_items":    refined.get("navigation_items") or und_row.get("navigation_items") or [],
        "required_sections":   refined.get("required_sections") or und_row.get("required_sections") or [],
        "user_actions":        refined.get("user_actions") or und_row.get("user_actions") or [],
        "owner_actions":       refined.get("owner_actions") or und_row.get("owner_actions") or [],
        "suggested_features":  refined.get("suggested_features") or und_row.get("suggested_features") or [],
        "menu_items":          refined.get("menu_items") or und_row.get("menu_items") or [],
        "benefits":            refined.get("benefits") or und_row.get("benefits") or [],
        "about_text":          refined.get("about_text") or und_row.get("about_text"),
        "first_version_scope": refined.get("first_version_scope") or und_row.get("first_version_scope"),
    }).eq("id", str(body.understanding_id)).execute()

    # Update project scenario if refined
    refined_scenario = refined.get("detected_scenario") or und_row.get("detected_scenario")
    _update_project(db, project_id, {
        "status": project["status"],
        "scenario": refined_scenario,
    })

    return GenerateUnderstandingResponse(
        project_id=project_id,
        understanding_id=body.understanding_id,
        bullets=refined.get("bullets", []),
        assumptions=refined.get("assumptions", []),
        clarification_questions=[],
        detected_scenario=refined_scenario,
        confidence=refined.get("confidence"),
        confirmed_by_user=False,
        status=project["status"],
        has_diagnostic_question=False,
    )


# ─── POST /projects/{project_id}/confirm-understanding ───────────────────────

@router.post("/{project_id}/confirm-understanding",
             response_model=ConfirmUnderstandingResponse)
def confirm_understanding(project_id: UUID, body: ConfirmUnderstandingRequest, x_customer_id: Optional[str] = Header(default=None)):
    """Confirm (or decline) PM understanding. On confirm → ready_for_builder."""
    db = get_db()
    _get_project_for_customer_or_404(db, project_id, x_customer_id)

    und_result = (
        db.table("understandings")
        .select("*")
        .eq("id", str(body.understanding_id))
        .execute()
    )
    if not und_result.data:
        raise HTTPException(status_code=404, detail="Understanding not found")

    und_row = und_result.data[0]
    if und_row["project_id"] != str(project_id):
        raise HTTPException(
            status_code=400,
            detail="Understanding does not belong to this project",
        )

    if not body.confirmed:
        return ConfirmUnderstandingResponse(
            project_id=project_id,
            understanding_id=body.understanding_id,
            confirmed_by_user=False,
            status="waiting_for_user_confirmation",
        )

    now = _now_iso()
    db.table("understandings").update(
        {"confirmed_by_user": True, "confirmed_at": now, "updated_at": now}
    ).eq("id", str(body.understanding_id)).execute()

    _update_project(db, project_id, {"status": "ready_for_builder"})

    return ConfirmUnderstandingResponse(
        project_id=project_id,
        understanding_id=body.understanding_id,
        confirmed_by_user=True,
        status="ready_for_builder",
    )


# ─── POST /projects/{project_id}/generate-preview ────────────────────────────

@router.post("/{project_id}/generate-preview",
             response_model=GeneratePreviewResponse)
def generate_preview_endpoint(project_id: UUID, x_customer_id: Optional[str] = Header(default=None)):
    """
    Build simulated preview + run reviewer + create version.
    Project must be in ready_for_builder with a confirmed understanding.
    """
    db = get_db()
    project = _get_project_for_customer_or_404(db, project_id, x_customer_id)

    # Guard: must be ready_for_builder
    if project["status"] != "ready_for_builder":
        raise HTTPException(
            status_code=400,
            detail=f"Project status is '{project['status']}'. Must be 'ready_for_builder'.",
        )

    # Need a confirmed understanding
    und_result = (
        db.table("understandings")
        .select("*")
        .eq("project_id", str(project_id))
        .eq("confirmed_by_user", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not und_result.data:
        raise HTTPException(
            status_code=400,
            detail="No confirmed understanding found. User must confirm understanding first.",
        )
    understanding = und_result.data[0]

    # ── Builder ───────────────────────────────────────────────────────────────
    _update_project(db, project_id, {"status": "building"})

    # Look for a reusable pattern from previous approved projects in this scenario.
    # If found, pass it as a soft starting hint — Builder never blindly copies it.
    # If not found, Builder works as before (no change in behaviour).
    scenario = understanding.get("detected_scenario") or project.get("scenario") or ""
    scenario_pattern: dict | None = None
    if scenario:
        try:
            scenario_pattern = find_latest_pattern_for_scenario(scenario, db)
        except Exception:
            pass  # pattern lookup is best-effort; never blocks build

    builder_result = generate_preview(project, understanding, scenario_pattern)
    # If html builder is configured but not available, fall back to inline html builder
    preview_data = builder_result["preview_data"]
    if not preview_data.get("_is_html_preview"):
        try:
            from app.providers.builder.html_builder import generate as html_build
            builder_result = html_build(project, understanding, scenario_pattern)
            preview_data = builder_result["preview_data"]
        except Exception:
            pass  # keep mock preview if html builder unavailable

    # Determine next version number
    versions_result = (
        db.table("versions")
        .select("version_number")
        .eq("project_id", str(project_id))
        .order("version_number", desc=True)
        .limit(1)
        .execute()
    )
    next_version_number = 1
    if versions_result.data:
        next_version_number = versions_result.data[0]["version_number"] + 1

    version_label = "نسخه اول" if next_version_number == 1 else f"نسخه {next_version_number}"

    # Create a preliminary version row (output_id linked after output insert)
    version_data = {
        "project_id": str(project_id),
        "version_number": next_version_number,
        "version_label": version_label,
        "user_visible_preview": preview_data,
        "approved_by_user": False,
    }
    version_result = db.table("versions").insert(version_data).execute()
    if not version_result.data:
        raise HTTPException(status_code=500, detail="Failed to create version")
    version_row = version_result.data[0]
    version_id = version_row["id"]

    # Save builder output
    output_data = {
        "project_id": str(project_id),
        "version_id": version_id,
        "output_type": "preview_json",
        "preview_data": preview_data,
        "change_summary": builder_result["change_summary"],
        "known_limitations": builder_result["known_limitations"],
    }
    output_result = db.table("builder_outputs").insert(output_data).execute()
    if not output_result.data:
        raise HTTPException(status_code=500, detail="Failed to save builder output")
    output_id = output_result.data[0]["id"]

    # Link output_id back to version
    db.table("versions").update({"output_id": output_id}).eq("id", version_id).execute()

    # ── Reviewer ──────────────────────────────────────────────────────────────
    _update_project(db, project_id, {"status": "reviewing"})

    review_result = review_preview(preview_data, understanding)

    report_data = {
        "project_id": str(project_id),
        "version_id": version_id,
        "overall_status": review_result["overall_status"],
        "issues_found": review_result["issues_found"],
        "checklist": review_result["checklist"],
        "user_friendly_summary": review_result["user_friendly_summary"],
        "internal_notes": review_result["internal_notes"],
    }
    report_result = db.table("review_reports").insert(report_data).execute()
    if not report_result.data:
        raise HTTPException(status_code=500, detail="Failed to save review report")
    review_report_id = report_result.data[0]["id"]

    # Link review_report_id to version
    db.table("versions").update(
        {"review_report_id": review_report_id}
    ).eq("id", version_id).execute()

    # ── safe_to_show_user: if review failed, return clear, confidence-building, non-technical, and anxiety-free message only ──────────
    # Internal checklist and gate details are never forwarded to the user.
    # The user sees only user_friendly_summary — never issue labels or gate names.
    if not review_result.get("safe_to_show_user", True):
        _update_project(db, project_id, {"status": "building"})  # revert to allow retry
        return GeneratePreviewResponse(
            project_id=project_id,
            status="building",
            version_id=version_id,
            output_id=output_id,
            review_report_id=review_report_id,
            preview_data=preview_data,
            review_summary=(
                "یه بررسی پشت صحنه لازم شد تا مطمئن بشیم پیش‌نمایش دقیق‌تره. "
                "چند لحظه دیگه دوباره امتحان کن."
            ),
        )

    # ── Finalize ──────────────────────────────────────────────────────────────
    _update_project(db, project_id, {
        "status": "ready_for_user_review",
        "current_version_id": version_id,
    })

    return GeneratePreviewResponse(
        project_id=project_id,
        status="ready_for_user_review",
        version_id=version_id,
        output_id=output_id,
        review_report_id=review_report_id,
        preview_data=preview_data,
        review_summary=review_result["user_friendly_summary"],
    )


# ─── POST /projects/{project_id}/revision ────────────────────────────────────

@router.post("/{project_id}/revision", response_model=GenerateRevisionResponse)
def request_revision(project_id: UUID, body: RevisionRequestBody, x_customer_id: Optional[str] = Header(default=None)):
    """
    User requests changes to the current visible version.

    The factory automatically:
      1. Saves the revision request
      2. Interprets the correction into actions
      3. Applies actions to the current preview
      4. Creates a new version
      5. Runs the reviewer
      6. Makes the new version the current one

    The user never needs to manage files or pick version numbers.
    """
    db = get_db()
    project = _get_project_for_customer_or_404(db, project_id, x_customer_id)

    # Guard: must be ready for user review
    if project["status"] != "ready_for_user_review":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Project status is '{project['status']}'. "
                "Must be 'ready_for_user_review' to request a revision."
            ),
        )

    # Determine which version to revise — always use current_version_id
    # from_version_id in the body is optional; the factory chooses for the user
    from_version_id = (
        body.from_version_id
        if body.from_version_id
        else project.get("current_version_id")
    )
    if not from_version_id:
        raise HTTPException(
            status_code=400,
            detail="No current version found. Generate a preview first.",
        )

    # Fetch the base version
    ver_result = (
        db.table("versions").select("*").eq("id", str(from_version_id)).execute()
    )
    if not ver_result.data:
        raise HTTPException(status_code=404, detail="Version not found")
    base_version = ver_result.data[0]

    if base_version["project_id"] != str(project_id):
        raise HTTPException(
            status_code=400, detail="Version does not belong to this project"
        )

    # The revision must target the current version — safety check
    if str(project.get("current_version_id", "")) != str(from_version_id):
        raise HTTPException(
            status_code=400,
            detail="Only the current version can be revised.",
        )

    # ── Interpret & apply revision directly on section_blocks ─────────────────
    # This is the actual fix for "click اعمال تغییر and nothing happens":
    # the old engine edited stale mock-only fields (title, primary_button)
    # that the real html_preview never read. The new engine edits the live
    # section_blocks + global_style and RE-RENDERS html_preview, so every
    # applied change is immediately visible in the output.
    base_preview = base_version.get("user_visible_preview") or {}
    base_sections = base_preview.get("section_blocks")
    base_style = base_preview.get("global_style") or {
        "primary_color": "#4F46E5", "secondary_color": "#818CF8",
        "border_radius": "14px", "font_family": "Tahoma,Arial,sans-serif",
    }

    if not base_sections:
        # Older version without a section model — cannot apply a structured
        # edit. Be honest rather than silently doing nothing.
        raise HTTPException(
            status_code=400,
            detail="این نسخه قابلیت ویرایش با توضیح متنی را ندارد. لطفاً دوباره پیش‌نمایش بساز.",
        )

    from app.config import settings as _settings
    selected_context = None
    if body.selected_element_id or body.selected_section_id:
        selected_context = {
            "selected_element_id": body.selected_element_id,
            "selected_element_type": body.selected_element_type,
            "selected_element_text": body.selected_element_text,
            "selected_section_id": body.selected_section_id,
            "selected_section_type": body.selected_section_type,
        }
    revision_result = interpret_and_apply(
        body.raw_revision_text, base_sections, base_style,
        api_key=_settings.anthropic_api_key,
        selected_context=selected_context,
    )

    # ── Save revision request ──────────────────────────────────────────────────
    revision_data = {
        "project_id": str(project_id),
        "from_version_id": str(from_version_id),
        "raw_revision_text": body.raw_revision_text,
        "interpreted_actions": [{"type": "ai_revision", "value": body.raw_revision_text}],
        "status": "pending" if revision_result["success"] else "needs_clarification",
    }
    rev_result = db.table("revision_requests").insert(revision_data).execute()
    if not rev_result.data:
        raise HTTPException(status_code=500, detail="Failed to save revision request")
    revision_request_id = rev_result.data[0]["id"]

    # ── If the request wasn't clear enough, ask — never fail silently ─────────
    if not revision_result["success"]:
        db.table("revision_requests").update({
            "status": "needs_clarification", "updated_at": _now_iso(),
        }).eq("id", revision_request_id).execute()
        return GenerateRevisionResponse(
            project_id=project_id,
            revision_request_id=revision_request_id,
            from_version_id=from_version_id,
            new_version_id=from_version_id,   # nothing new was created
            output_id=base_version.get("output_id") or revision_request_id,
            review_report_id=base_version.get("review_report_id") or revision_request_id,
            status="ready_for_user_review",
            preview_data=None,
            message=revision_result["clarification_question"],
        )

    new_preview_data = dict(base_preview)
    new_preview_data["section_blocks"] = revision_result["sections"]
    new_preview_data["global_style"] = revision_result["global_style"]
    new_preview_data["html_preview"] = revision_result["html_preview"]
    new_preview_data["_is_html_preview"] = True
    change_summary_text = revision_result["summary"]

    # ── Determine new version number ──────────────────────────────────────────
    versions_result = (
        db.table("versions")
        .select("version_number")
        .eq("project_id", str(project_id))
        .order("version_number", desc=True)
        .limit(1)
        .execute()
    )
    next_number = 1
    if versions_result.data:
        next_number = versions_result.data[0]["version_number"] + 1
    version_label = f"نسخه اصلاح‌شده {next_number - 1}" if next_number > 2 else "نسخه اصلاح‌شده"

    # ── Create new version ────────────────────────────────────────────────────
    new_version_data = {
        "project_id": str(project_id),
        "version_number": next_number,
        "version_label": version_label,
        "user_visible_preview": new_preview_data,
        "approved_by_user": False,
    }
    new_ver_result = db.table("versions").insert(new_version_data).execute()
    if not new_ver_result.data:
        raise HTTPException(status_code=500, detail="Failed to create new version")
    new_version = new_ver_result.data[0]
    new_version_id = new_version["id"]

    # ── Save builder output ───────────────────────────────────────────────────
    output_data = {
        "project_id": str(project_id),
        "version_id": new_version_id,
        "output_type": "preview_json",
        "preview_data": new_preview_data,
        "change_summary": [change_summary_text],
        "known_limitations": ["این نسخه اصلاح‌شده همچنان یک پیش‌نمایش است"],
    }
    output_result = db.table("builder_outputs").insert(output_data).execute()
    if not output_result.data:
        raise HTTPException(status_code=500, detail="Failed to save builder output")
    output_id = output_result.data[0]["id"]

    # Link output_id to new version
    db.table("versions").update({"output_id": output_id}).eq("id", new_version_id).execute()

    # ── Run reviewer (with Gate 3: correction_is_visible) ─────────────────────
    # Fetch confirmed understanding for reviewer context
    und_result = (
        db.table("understandings")
        .select("*")
        .eq("project_id", str(project_id))
        .eq("confirmed_by_user", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    understanding = und_result.data[0] if und_result.data else {}
    review_result = review_preview(new_preview_data, understanding)

    report_data = {
        "project_id": str(project_id),
        "version_id": new_version_id,
        "overall_status": review_result["overall_status"],
        "issues_found": review_result["issues_found"],
        "checklist": review_result["checklist"],
        "user_friendly_summary": review_result["user_friendly_summary"],
        "internal_notes": review_result["internal_notes"],
    }
    report_result = db.table("review_reports").insert(report_data).execute()
    if not report_result.data:
        raise HTTPException(status_code=500, detail="Failed to save review report")
    review_report_id = report_result.data[0]["id"]

    # Link review_report_id to new version
    db.table("versions").update(
        {"review_report_id": review_report_id}
    ).eq("id", new_version_id).execute()

    # ── Revision review protection ────────────────────────────────────────────
    # If the revised preview does not pass the quality review:
    #   • do NOT make the failed version current
    #   • preserve the previous current_version_id
    #   • store the failed review report internally (already done above)
    #   • return a clear, confidence-building, non-technical, and anxiety-free message
    #   • never expose checklist, gate names, family_, scenario, or internal notes
    if not review_result.get("safe_to_show_user", True):
        # Mark revision as review_failed — not "pending" (which implies still waiting)
        # Internal status only — never shown to user
        db.table("revision_requests").update({
            "status":     "review_failed",
            "updated_at": _now_iso(),
        }).eq("id", revision_request_id).execute()

        # Project status stays 'ready_for_user_review' with previous version unchanged
        _update_project(db, project_id, {"status": "ready_for_user_review"})
        return GenerateRevisionResponse(
            project_id=project_id,
            revision_request_id=revision_request_id,
            from_version_id=from_version_id,
            new_version_id=new_version_id,
            output_id=output_id,
            review_report_id=review_report_id,
            status="ready_for_user_review",   # previous version still current
            preview_data=None,                 # failed preview not shown to user
            message=(
                "این ویرایش نیاز به یک بررسی بیشتر داشت، برای همین نسخه قبلی را نگه داشتیم. "
                "می‌تونی دوباره ساده‌تر بگی چه چیزی را تغییر بدهیم."
            ),
        )

    # ── Revision passed review — mark as applied and make current ─────────────
    db.table("revision_requests").update(
        {"status": "applied", "updated_at": _now_iso()}
    ).eq("id", revision_request_id).execute()

    _update_project(db, project_id, {
        "status": "ready_for_user_review",
        "current_version_id": new_version_id,
        "final_approval_status": False,     # must re-approve new version
    })

    return GenerateRevisionResponse(
        project_id=project_id,
        revision_request_id=revision_request_id,
        from_version_id=from_version_id,
        new_version_id=new_version_id,
        output_id=output_id,
        review_report_id=review_report_id,
        status="ready_for_user_review",
        preview_data=new_preview_data,
        message="تغییر انجام شد.",
    )


# ─── POST /projects/{project_id}/save-html ───────────────────────────────────

@router.post("/{project_id}/save-html", response_model=SaveHtmlResponse)
def save_html(project_id: UUID, body: SaveHtmlRequest,
              x_customer_id: Optional[str] = Header(default=None)):
    """
    Save HTML exported from the GrapesJS website editor back onto the
    current version, in place — no new version number, no AI re-generation.

    The user has already made their visual edits in the editor; this just
    persists the result so it survives a refresh and is shown next time
    the preview or editor opens.
    """
    db = get_db()
    project = _get_project_for_customer_or_404(db, project_id, x_customer_id)

    ver_result = db.table("versions").select("*").eq("id", str(body.version_id)).execute()
    if not ver_result.data:
        raise HTTPException(status_code=404, detail="Version not found")
    version = ver_result.data[0]
    if version["project_id"] != str(project_id):
        raise HTTPException(status_code=400, detail="Version does not belong to this project")

    preview = version.get("user_visible_preview") or {}
    preview["html_preview"] = body.html_preview
    preview["_is_html_preview"] = True

    db.table("versions").update(
        {"user_visible_preview": preview}
    ).eq("id", str(body.version_id)).execute()

    return SaveHtmlResponse(
        project_id=project_id,
        version_id=body.version_id,
        preview_data=preview,
        message="تغییرات ذخیره شد.",
    )


# ─── POST /projects/{project_id}/edit-direct ─────────────────────────────────

@router.post("/{project_id}/edit-direct", response_model=DirectEditResponse)
def edit_direct(project_id: UUID, body: DirectEditRequest,
                 x_customer_id: Optional[str] = Header(default=None)):
    """
    Apply a DIRECT, deterministic edit from the Contextual Edit Panel's
    mini-dashboard — text, color, size, icon, price, or section move.

    This is the fix for "direct fields don't apply unless the user also
    writes a natural-language instruction": the panel calls this endpoint
    immediately when the user clicks "اعمال این تغییر", with no AI
    interpretation step and no dependency on the lower text box. The free
    text box remains a separate, optional fallback (still going through
    /revision) for anything the mini-dashboard doesn't cover.
    """
    db = get_db()
    project = _get_project_for_customer_or_404(db, project_id, x_customer_id)

    ver_result = db.table("versions").select("*").eq("id", str(body.version_id)).execute()
    if not ver_result.data:
        raise HTTPException(status_code=404, detail="Version not found")
    version = ver_result.data[0]
    if version["project_id"] != str(project_id):
        raise HTTPException(status_code=400, detail="Version does not belong to this project")

    preview = version.get("user_visible_preview") or {}
    sections = preview.get("section_blocks")
    global_style = preview.get("global_style") or {
        "primary_color": "#4F46E5", "secondary_color": "#818CF8",
        "border_radius": "14px", "font_family": "Tahoma,Arial,sans-serif",
    }
    if not sections:
        raise HTTPException(
            status_code=400,
            detail="این نسخه قابلیت ویرایش مستقیم را ندارد. لطفاً دوباره پیش‌نمایش بساز.",
        )

    from app.providers.builder.section_model import (
        apply_section_edit, apply_item_field_edit, apply_element_style_edit,
        reorder_section,
    )
    from app.providers.builder.render_sections import render_website

    sid = body.selected_section_id
    section_exists = any(s["id"] == sid for s in sections)
    if not section_exists:
        raise HTTPException(status_code=400, detail="بخش انتخاب‌شده پیدا نشد.")

    applied_anything = False

    # 1. Text content change — either on a list item (card title/desc/price)
    #    or directly on the section's own content field.
    if body.new_text is not None and body.field_key:
        if body.item_index is not None:
            sections = apply_item_field_edit(sections, sid, body.item_index, body.field_key, body.new_text)
        else:
            sections = apply_section_edit(sections, sid, body.field_key, body.new_text)
        applied_anything = True

    # 2. Per-element style overrides (color / size / icon) — deterministic,
    #    rendered directly by render_sections.py without any AI step.
    if body.selected_element_id and (body.color or body.size or body.icon or body.background_color):
        if body.color:
            sections = apply_element_style_edit(sections, sid, body.selected_element_id, "color", body.color)
            applied_anything = True
        if body.background_color:
            sections = apply_element_style_edit(sections, sid, body.selected_element_id, "background_color", body.background_color)
            applied_anything = True
        if body.size:
            sections = apply_element_style_edit(sections, sid, body.selected_element_id, "size", body.size)
            applied_anything = True
        if body.icon and body.item_index is not None:
            sections = apply_item_field_edit(sections, sid, body.item_index, "icon", body.icon)
            applied_anything = True

    # 3. Whole-section background color (clicked the section itself, no
    #    specific element — e.g. the hero gradient background).
    if body.background_color and not body.selected_element_id:
        for sec in sections:
            if sec["id"] == sid:
                sec.setdefault("style", {})
                sec["style"]["background_color"] = body.background_color
                break
        applied_anything = True

    # 4. Move the whole selected section up/down.
    if body.move_section in ("up", "down"):
        sections = reorder_section(sections, sid, body.move_section)
        applied_anything = True

    if not applied_anything:
        raise HTTPException(status_code=400, detail="چیزی برای اعمال مشخص نشده است.")

    new_html = render_website(sections, global_style)
    preview["section_blocks"] = sections
    preview["global_style"] = global_style
    preview["html_preview"] = new_html
    preview["_is_html_preview"] = True

    db.table("versions").update(
        {"user_visible_preview": preview}
    ).eq("id", str(body.version_id)).execute()

    return DirectEditResponse(
        project_id=project_id,
        version_id=body.version_id,
        preview_data=preview,
        message="تغییر انجام شد.",
    )


# ─── POST /projects/{project_id}/approve ─────────────────────────────────────

@router.post("/{project_id}/approve", response_model=ApproveVersionResponse)
def approve_version(project_id: UUID, body: ApproveVersionRequest, x_customer_id: Optional[str] = Header(default=None)):
    """
    User gives final approval for the current version.
    Creates approved_version and learning_note rows.
    Project status becomes 'approved'.
    """
    db = get_db()
    project = _get_project_for_customer_or_404(db, project_id, x_customer_id)

    # Guard: project must be ready for user review
    if project["status"] != "ready_for_user_review":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Project status is '{project['status']}'. "
                "Must be 'ready_for_user_review' to approve."
            ),
        )

    # Find version
    ver_result = (
        db.table("versions").select("*").eq("id", str(body.version_id)).execute()
    )
    if not ver_result.data:
        raise HTTPException(status_code=404, detail="Version not found")
    version = ver_result.data[0]

    # Ownership check
    if version["project_id"] != str(project_id):
        raise HTTPException(
            status_code=400, detail="Version does not belong to this project"
        )

    # Current-version guard — only the currently visible version can be approved
    if project.get("current_version_id") and \
            str(project["current_version_id"]) != str(body.version_id):
        raise HTTPException(
            status_code=400,
            detail="Only the current version can be approved.",
        )

    # ── Mark version as approved ──────────────────────────────────────────────
    db.table("versions").update(
        {"approved_by_user": True}
    ).eq("id", str(body.version_id)).execute()

    # ── Create approved_version row ───────────────────────────────────────────
    approved_data = {
        "project_id": str(project_id),
        "version_id": str(body.version_id),
        "user_feedback": body.user_feedback,
        "final_summary": (
            f"نسخه {version.get('version_label', 'اول')} توسط کاربر تأیید شد."
        ),
    }
    approved_result = db.table("approved_versions").insert(approved_data).execute()
    if not approved_result.data:
        raise HTTPException(status_code=500, detail="Failed to create approved_version")

    # ── Fetch builder output for learning note context ─────────────────────────
    output_row: dict | None = None
    if version.get("output_id"):
        out_res = (
            db.table("builder_outputs")
            .select("*")
            .eq("id", str(version["output_id"]))
            .execute()
        )
        if out_res.data:
            output_row = out_res.data[0]

    # ── Check whether this project had any revisions ──────────────────────────
    rev_check = (
        db.table("revision_requests")
        .select("id")
        .eq("project_id", str(project_id))
        .limit(1)
        .execute()
    )
    had_revisions = bool(rev_check.data)

    # ── Create learning note ──────────────────────────────────────────────────
    # Pass the already-approved project dict with updated status for context
    project_ctx = {**project, "final_approval_status": True}
    note_data = create_learning_note(
        project=project_ctx,
        version=version,
        builder_output=output_row,
        user_feedback=body.user_feedback,
        had_revisions=had_revisions,
    )
    note_result = db.table("learning_notes").insert(note_data).execute()
    if not note_result.data:
        raise HTTPException(status_code=500, detail="Failed to create learning_note")
    learning_note_id = note_result.data[0]["id"]

    # ── Create reusable pattern (best-effort — must not block approval) ──────────
    # Reusable pattern creation is helpful for future acceleration but non-blocking.
    # Final approval must succeed even if this step fails.
    try:
        pattern_data = create_reusable_pattern(
            project=project_ctx,
            version=version,
            builder_output=output_row,
        )
        db.table("reusable_patterns").insert(pattern_data).execute()
    except Exception:
        pass  # pattern creation is best-effort in MVP

    # ── Update project status ─────────────────────────────────────────────────
    _update_project(db, project_id, {
        "status": "approved",
        "final_approval_status": True,
        "current_version_id": str(body.version_id),
    })

    return ApproveVersionResponse(
        project_id=project_id,
        version_id=body.version_id,
        status="approved",
        approved_by_user=True,
        learning_note_id=learning_note_id,
        message="خروجی تأیید شد و یادگیری پروژه ثبت شد.",
    )


# ─── POST /projects/{project_id}/export ──────────────────────────────────────

@router.post("/{project_id}/export", response_model=ExportResponse)
def export_project(project_id: UUID, x_customer_id: Optional[str] = Header(default=None)):
    """
    Create an export package for the currently approved version.
    Project must be approved and current version must be approved by user.
    """
    db = get_db()
    project = _get_project_for_customer_or_404(db, project_id, x_customer_id)

    # Guard: project must be approved
    if project["status"] != "approved":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Project status is '{project['status']}'. "
                "Must be 'approved' to export."
            ),
        )

    # Must have a current version
    if not project.get("current_version_id"):
        raise HTTPException(
            status_code=400,
            detail="No current version found. Approve a version first.",
        )

    # Fetch the approved version
    ver_result = (
        db.table("versions")
        .select("*")
        .eq("id", str(project["current_version_id"]))
        .execute()
    )
    if not ver_result.data:
        raise HTTPException(status_code=404, detail="Current version not found")
    version = ver_result.data[0]

    # Guard: version must be approved by user
    if not version.get("approved_by_user"):
        raise HTTPException(
            status_code=400,
            detail="Current version has not been approved by user yet.",
        )

    # Guard: latest review report for this version must have passed quality check
    # (No False Success — export blocked if reviewer marked needs_revision)
    review_result = (
        db.table("review_reports")
        .select("overall_status")
        .eq("version_id", str(project["current_version_id"]))
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not review_result.data:
        raise HTTPException(
            status_code=400,
            detail="Quality review has not passed",
        )
    if review_result.data[0]["overall_status"] != "passed":
        raise HTTPException(
            status_code=400,
            detail="Quality review has not passed",
        )

    # Fetch builder output for richest preview data
    output_row: dict | None = None
    if version.get("output_id"):
        out_res = (
            db.table("builder_outputs")
            .select("*")
            .eq("id", str(version["output_id"]))
            .execute()
        )
        if out_res.data:
            output_row = out_res.data[0]

    # Create export package
    pkg = create_export_package(project, version, output_row)

    # Save to exports table
    export_insert = {
        "project_id":  str(project_id),
        "version_id":  str(version["id"]),
        "export_type": pkg["export_type"],
        "export_data": pkg["export_data"],
        "summary":     pkg["summary"],
    }
    export_result = db.table("exports").insert(export_insert).execute()
    if not export_result.data:
        raise HTTPException(status_code=500, detail="Failed to save export")
    export_id = export_result.data[0]["id"]

    return ExportResponse(
        project_id=project_id,
        version_id=version["id"],
        export_id=export_id,
        export_type=pkg["export_type"],
        summary=pkg["summary"],
        export_data=pkg["export_data"],
        delivery_education=pkg["delivery_education"],
        message="خروجی برای ارائه و تحویل آماده شد.",
    )


# ─── GET /projects/{project_id} ──────────────────────────────────────────────

@router.get("/{project_id}", response_model=ProjectStateResponse)
def get_project(
    project_id: UUID,
    x_customer_id: Optional[str] = Header(default=None),
):
    """Return full project state for the UI."""
    db = get_db()
    # MVP ownership scoping — not production auth
    project_result = (
        db.table("projects").select("*").eq("id", str(project_id)).execute()
    )
    if not project_result.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = project_result.data[0]
    # Scope check: if both are present, they must match
    project_cid = project.get("customer_id")
    if x_customer_id and project_cid and x_customer_id != project_cid:
        raise HTTPException(status_code=404, detail="Project not found")
    def fetch(table: str, order: str = "created_at") -> list:
        return (
            db.table(table)
            .select("*")
            .eq("project_id", str(project_id))
            .order(order)
            .execute()
            .data or []
        )

    # Reusable patterns are indexed by scenario, not project_id
    scenario = project_result.data[0].get("scenario") or ""
    patterns: list = []
    if scenario:
        patterns = (
            db.table("reusable_patterns")
            .select("*")
            .eq("scenario", scenario)
            .order("created_at", desc=True)
            .execute()
            .data or []
        )

    # Add default values for fields that may be missing in memory mode
    project_data = project_result.data[0]
    project_data.setdefault("user_id", None)
    project_data.setdefault("final_approval_status", False)
    project_data.setdefault("customer_id", None)

    # Add default values to understandings
    understandings = fetch("understandings")
    for u in understandings:
        u.setdefault("user_answers", [])
        u.setdefault("assumptions", [])
        u.setdefault("clarification_questions", [])
        u.setdefault("bullets", [])
        u.setdefault("detected_scenario", None)
        u.setdefault("confidence", None)
        u.setdefault("confirmed_by_user", False)
        u.setdefault("confirmed_at", None)
        u.setdefault("created_at", None)
        u.setdefault("updated_at", None)
        u.setdefault("diagnostic_question", None)
        u.setdefault("diagnostic_options", [])
        u.setdefault("primary_goal", None)
        u.setdefault("business_domain", None)

    return ProjectStateResponse(
        project=project_data,
        user_requests=fetch("user_requests"),
        understandings=understandings,
        builder_outputs=fetch("builder_outputs"),
        versions=fetch("versions"),
        review_reports=fetch("review_reports"),
        approved_versions=fetch("approved_versions"),
        learning_notes=fetch("learning_notes"),
        revision_requests=fetch("revision_requests"),
        reusable_patterns=patterns,
        exports=fetch("exports"),
    )
