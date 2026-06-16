"""
Memory / Learning Layer — Sprint 5.

Records what the factory learned after a user gives final approval.
Sprint 5 adds reusable_patterns for scenario-based future acceleration.
"""
from __future__ import annotations

from typing import Any


# ─── Learning Note ────────────────────────────────────────────────────────────

def create_learning_note(
    project: dict,
    version: dict,
    builder_output: dict | None,
    user_feedback: str | None,
    had_revisions: bool = False,
) -> dict[str, Any]:
    """
    Derive a structured learning note from a completed, approved project.

    Args:
        project:        projects row (final_approval_status=True by caller)
        version:        the approved versions row
        builder_output: optional builder_outputs row for this version
        user_feedback:  free-text feedback the user gave at approval time
        had_revisions:  True if the project had at least one revision_request
    """
    scenario = project.get("scenario") or "general"

    what_worked: list[str] = [
        "کاربر نسخه فعلی را تأیید نهایی کرد",
        "پیش‌نمایش با سناریوی تأییدشده هماهنگ بود",
    ]
    if had_revisions:
        what_worked.append("کاربر بعد از اصلاح، نسخه نهایی را تأیید کرد")
    if user_feedback:
        what_worked.append(f"بازخورد کاربر: «{user_feedback}»")

    user_preferences: dict[str, Any] = {
        "approved_without_revision": not had_revisions,
        "scenario": scenario,
    }
    if user_feedback:
        user_preferences["user_feedback"] = user_feedback

    reusable_patterns_notes: list[str] = [
        "سناریوی فعلی می‌تواند به عنوان الگوی اولیه برای پروژه‌های مشابه استفاده شود",
    ]
    if builder_output and builder_output.get("preview_data"):
        title = builder_output["preview_data"].get("title", "")
        if title:
            reusable_patterns_notes.append(
                f"عنوان «{title}» با سناریوی {scenario} تأیید شد"
            )

    return {
        "project_id": project["id"],
        "version_id": version["id"],
        "scenario": scenario,
        "product_type": "preview",
        "what_worked": what_worked,
        "user_preferences_detected": user_preferences,
        "reusable_patterns": reusable_patterns_notes,
    }


# ─── Reusable Pattern ─────────────────────────────────────────────────────────

def create_reusable_pattern(
    project: dict,
    version: dict,
    builder_output: dict | None,
) -> dict[str, Any]:
    """
    Build a reusable pattern record from an approved project.

    This is stored in the reusable_patterns table so future Builder
    providers can start from proven structures instead of starting from zero.
    """
    scenario = project.get("scenario") or "general"
    preview: dict[str, Any] = {}
    title = None

    if builder_output and builder_output.get("preview_data"):
        preview = builder_output["preview_data"]
        title = preview.get("title")

    pattern_data: dict[str, Any] = {
        "scenario":           scenario,
        "title_style":        "short" if title and len(title) <= 15 else "medium",
        "has_subtitle":       bool(preview.get("subtitle")),
        "has_primary_button": bool(preview.get("primary_button")),
        "has_contact":        bool(preview.get("show_contact")),
        "tone":               preview.get("tone", "neutral"),
    }

    # Carry through any extra keys that future builders may find useful
    for key in ("show_menu", "menu_items", "sections", "cards"):
        if key in preview:
            pattern_data[key] = preview[key]

    return {
        "scenario":          scenario,
        "pattern_type":      "approved_preview_pattern",
        "source_project_id": project["id"],
        "source_version_id": version["id"],
        "title":             title,
        "pattern_data":      pattern_data,
        "usage_count":       0,
        "approval_count":    1,
    }


def find_latest_pattern_for_scenario(scenario: str, db: Any) -> dict | None:
    """
    Return the most recently created reusable_pattern for this scenario,
    or None if none exists yet.

    Future Builder providers can call this at build time to get a
    proven starting point instead of generating from scratch.
    """
    result = (
        db.table("reusable_patterns")
        .select("*")
        .eq("scenario", scenario)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]
    return None
