"""
Need-First Advisor — response wording (presentation layer).

Converts get_need_first_recommendation()'s internal dict into the plain
Persian sentences needed for NeedFirstResponse. Kept separate from
need_first_advisor.py itself, mirroring the existing separation between
app/blueprint/generator.py and app/blueprint/recommendation_text.py in
this project.
"""
from __future__ import annotations

from typing import Any


def build_need_first_text(advice: dict[str, Any]) -> dict[str, Any]:
    if advice.get("needs_clarification"):
        return {
            "understood_summary": "هنوز کاملاً مشخص نیست دقیقاً چه نیازی داری.",
            "framing_note": "",
            "options": [],
            "factory_recommendation_key": None,
            "factory_recommendation_label": None,
            "reason": None,
            "needs_clarification": True,
            "clarification_question": advice.get("clarification_question") or "",
            "clarification_options": list(advice.get("clarification_options") or []),
            "preview_archetype": None,
        }

    pain = advice.get("detected_pain_or_goal") or "نیاز کسب‌وکارت"
    understood_summary = f"فهمیدم مشکل اصلی تو {pain} است."

    named_tool = advice.get("user_named_tool_if_any")
    if named_tool:
        framing_note = (
            f"{named_tool} فقط یک راه‌حل ممکن است؛ اول باید ببینیم کدام مسیر برای هدفت بهتر است."
        )
    else:
        framing_note = (
            "سایت، بات، صفحه سفارش یا ابزارهای دیگر فقط راه‌حل هستند؛ "
            "اول باید ببینیم کدام مسیر برای هدفت بهتر است."
        )

    explanations = advice.get("recommended_options_explanations") or {}
    options = []
    for o in (advice.get("recommended_options") or []):
        label = o["label"]
        explanation = explanations.get(o["tool_key"])
        if explanation:
            label = f"{label} — {explanation}"
        options.append({"option_key": o["tool_key"], "label": label})

    rec_key = advice.get("factory_recommendation")
    # Prefer an explicit combo label (e.g. "جذب مشتری جدید + منوی دیجیتال")
    # over the single matched option's label, since the factory's actual
    # recommendation can legitimately combine two of the listed paths.
    rec_label = advice.get("factory_recommendation_combo_label") or next(
        (o["label"] for o in (advice.get("recommended_options") or []) if o["tool_key"] == rec_key),
        None,
    )

    return {
        "understood_summary": understood_summary,
        "framing_note": framing_note,
        "options": options,
        "factory_recommendation_key": rec_key,
        "factory_recommendation_label": rec_label,
        "reason": advice.get("reason_for_recommendation"),
        "needs_clarification": False,
        "clarification_question": None,
        "clarification_options": [],
        "preview_archetype": advice.get("preview_archetype"),
    }
