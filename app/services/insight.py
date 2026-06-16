"""
User Testing Insight Center — AI Factory MVP v2

Lightweight internal event tracking for private user testing only.

Privacy rules:
  - No passwords, secrets, or credentials recorded
  - No payment data recorded
  - No screen recording
  - No third-party analytics providers (Hotjar, Mixpanel, GA, etc.)
  - No telemetry sent outside the factory system
  - Data stored in the same storage backend (memory or Supabase)
  - Technical terms (event, tracking, session_id) never shown to users

User-facing text is a simple feedback form — not surveillance language.

Dependency: Demo Access Gate must reach classification A before 5-person testing.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Tracked event types ───────────────────────────────────────────────────────
# These are operator-internal. Never shown to the user.

TRACKED_EVENTS = [
    "app_opened",
    "new_project_clicked",
    "request_submitted",
    "diagnostic_question_shown",
    "diagnostic_answered",
    "understanding_shown",
    "understanding_confirmed",
    "preview_generated",
    "revision_requested",
    "revision_succeeded",
    "revision_failed",
    "final_approval_clicked",
    "delivery_requested",
    "delivery_education_shown",
    "project_opened_from_my_projects",
    "error_shown",
    "final_feedback_submitted",
]


# ── Session management ────────────────────────────────────────────────────────

def create_session(db, tester_label: str = "") -> dict:
    """
    Open a new test session for one private tester.
    session_id is internal — never shown to the tester.
    """
    row = {
        "session_id":   str(uuid.uuid4()),
        "tester_label": tester_label or "anonymous",
        "project_id":   None,
        "started_at":   _now(),
        "last_event_at":_now(),
        "status":       "active",
        "final_feedback": None,
    }
    result = db.table("test_sessions").insert(row).execute()
    return result.data[0] if result.data else row


def update_session(db, session_id: str, updates: dict) -> None:
    updates["last_event_at"] = _now()
    db.table("test_sessions").update(updates).eq("session_id", session_id).execute()


# ── Event logging ─────────────────────────────────────────────────────────────

def log_event(
    db,
    session_id: str,
    event_type: str,
    project_id: str | None = None,
    meta: dict | None = None,
) -> None:
    """
    Log a single test event.
    - event_type must be from TRACKED_EVENTS
    - meta is optional operator context (never shown to user)
    - Never log passwords, credentials, or payment data
    """
    if event_type not in TRACKED_EVENTS:
        return  # silently ignore unknown events

    row = {
        "session_id":  session_id,
        "event_type":  event_type,
        "project_id":  project_id,
        "occurred_at": _now(),
        "meta":        meta or {},
    }
    db.table("test_events").insert(row).execute()
    update_session(db, session_id, {"last_event_at": _now()})


# ── Final feedback ────────────────────────────────────────────────────────────

def save_feedback(
    db,
    session_id: str,
    understood: str,      # «بله / تقریباً / نه»
    output_matched: str,  # «بله / تقریباً / نه»
    confusion_note: str,
    improvement: str,
) -> None:
    """
    Save tester's final feedback and mark session complete.
    Called after delivery education is shown.
    """
    feedback = {
        "understood":      understood,
        "output_matched":  output_matched,
        "confusion_note":  confusion_note,
        "improvement":     improvement,
        "submitted_at":    _now(),
    }
    update_session(db, session_id, {
        "final_feedback": feedback,
        "status": "completed",
    })
    log_event(db, session_id, "final_feedback_submitted", meta={"has_feedback": True})


# ── Operator summary report ───────────────────────────────────────────────────

def session_summary(db, session_id: str) -> dict:
    """
    Return a simple operator-facing summary for one test session.
    Operator-only — never shown to the non-technical tester.
    """
    sessions = db.table("test_sessions").select("*").eq("session_id", session_id).execute().data
    if not sessions:
        return {"error": "session not found"}
    session = sessions[0]

    events = (
        db.table("test_events")
        .select("*")
        .eq("session_id", session_id)
        .order("occurred_at")
        .execute()
        .data
    )

    event_types = [e["event_type"] for e in events]

    # Determine last step reached
    STEP_ORDER = [
        "app_opened", "new_project_clicked", "request_submitted",
        "diagnostic_question_shown", "diagnostic_answered",
        "understanding_shown", "understanding_confirmed",
        "preview_generated", "revision_requested",
        "revision_succeeded", "final_approval_clicked",
        "delivery_requested", "delivery_education_shown",
        "final_feedback_submitted",
    ]
    last_step = "none"
    for step in STEP_ORDER:
        if step in event_types:
            last_step = step

    # Drop-off: first expected step not reached
    drop_off = None
    for step in STEP_ORDER:
        if step not in event_types:
            drop_off = step
            break

    return {
        "session_id":       session_id,
        "tester":           session.get("tester_label", "anonymous"),
        "status":           session.get("status"),
        "started_at":       session.get("started_at"),
        "last_event_at":    session.get("last_event_at"),
        "last_step_reached":last_step,
        "drop_off_at":      drop_off,
        "events_logged":    len(events),
        "had_revision":     "revision_requested" in event_types,
        "revision_succeeded":"revision_succeeded" in event_types,
        "revision_failed":  "revision_failed" in event_types,
        "approved":         "final_approval_clicked" in event_types,
        "delivered":        "delivery_education_shown" in event_types,
        "errors_shown":     event_types.count("error_shown"),
        "final_feedback":   session.get("final_feedback"),
    }


def all_sessions_report(db) -> list[dict]:
    """
    Return operator summary for all test sessions.
    Operator-only — never shown to non-technical tester.
    """
    sessions = db.table("test_sessions").select("*").execute().data
    return [session_summary(db, s["session_id"]) for s in sessions]
