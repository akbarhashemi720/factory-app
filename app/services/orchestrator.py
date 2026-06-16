"""
Factory Orchestrator.

Watches project status and returns the recommended next action.
Does NOT talk to the user, generate content, or make product decisions.
Only recommends; it never auto-triggers Builder or Reviewer.
"""
from __future__ import annotations

from uuid import UUID

from app.database import get_db


def orchestrate(project_id: UUID) -> dict:
    """Inspect project status and return the next recommended action."""
    db = get_db()

    proj_result = (
        db.table("projects").select("id, status").eq("id", str(project_id)).execute()
    )
    if not proj_result.data:
        return _action(project_id, "error", "Project not found")

    status = proj_result.data[0]["status"]

    if status == "draft":
        return _action(project_id, "wait_for_user_request",
                       "Project created. Waiting for user request.")

    if status == "waiting_for_user_confirmation":
        # Check for unconfirmed understanding
        und = (
            db.table("understandings")
            .select("id, confirmed_by_user")
            .eq("project_id", str(project_id))
            .eq("confirmed_by_user", False)
            .execute()
        )
        if und.data:
            return _action(project_id, "wait_for_user_confirmation",
                           "Understanding generated. Waiting for user to confirm.")
        return _action(project_id, "generate_understanding",
                       "User request received. PM Agent should generate understanding.")

    if status == "ready_for_builder":
        return _action(project_id, "generate_preview",
                       "Understanding confirmed. Call POST /generate-preview.")

    if status == "building":
        return _action(project_id, "wait_for_builder",
                       "Builder is running. Wait for output.")

    if status == "reviewing":
        return _action(project_id, "wait_for_reviewer",
                       "Reviewer is running. Wait for report.")

    if status == "ready_for_user_review":
        return _action(project_id, "wait_for_user_review",
                       "Output ready. Waiting for user to approve or request revision.")

    if status == "revision_requested":
        return _action(project_id, "confirm_revision",
                       "User requested revision. PM Agent should confirm correction.")

    if status == "approved":
        return _action(project_id, "project_completed",
                       "Project approved and learning note created. No further action needed.")

    return _action(project_id, "unknown_status", f"Unrecognised status: {status}")


def _action(project_id: UUID, next_action: str, message: str) -> dict:
    return {
        "project_id": str(project_id),
        "next_action": next_action,
        "message": message,
    }
