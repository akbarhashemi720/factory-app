"""
AI Revision Engine — Website Builder v4.

Replaces the old keyword-matching revision.py, which operated on stale
mock-only fields (title, primary_button) that the real html_preview
no longer uses. This module is the actual fix for the "click اعمال
تغییر and nothing happens" bug: it operates directly on the live
section_blocks + global_style model and RE-RENDERS html_preview, so
every applied change is immediately visible.

Uses Claude with forced tool-use to interpret free-form Persian change
requests (e.g. "رنگ هدر بالا قرمز بشه") into concrete, structured edits:
  - field-level content edits on a specific section (title, button text, ...)
  - section reordering (move a section up/down/to a position)
  - global style changes (primary/secondary color)

Falls back to a small honest set of deterministic keyword rules only if
the Claude call itself fails (network/auth error) — never silently does
nothing, and never claims success without changing anything.
"""
from __future__ import annotations

import re
from typing import Any

from app.providers.builder.section_model import (
    apply_section_edit,
    reorder_section,
)
from app.providers.builder.render_sections import render_website


_SYSTEM_PROMPT = """تو دستیار فنی یک کارخانه ساخت وب‌سایت هستی. کاربر غیرفنی یک درخواست تغییر به زبان فارسی روزمره می‌نویسد (مثلاً «رنگ هدر را قرمز کن» یا «دکمه منو بشه فروش محصولات»).
وظیفه‌ات: این درخواست را به یک یا چند تغییر دقیق و قابل‌اجرا روی ساختار سایت تبدیل کنی.

ساختار سایت یک آرایه از بخش‌ها (sections) است. هر بخش یک «نوع» (type) و یک «شناسه» (id) و یک شیء «محتوا» (content) دارد.
انواع بخش‌ها: navbar, hero, menu_grid, gallery, about, benefits, form, cta, footer.

برای هرکدام از این درخواست‌ها دقیقاً این کار را بکن:
- «رنگ ... قرمز/آبی/سبز/زرد/کرم/قهوه‌ای ... کن» → یک تغییر از نوع change_global_color با رنگ مناسب (hex) برای primary_color
  رنگ‌های پیشنهادی: قرمز=#DC2626, آبی=#2563EB, سبز=#16A34A, زرد=#F59E0B, نارنجی=#EA580C, کرم=#D4A574, قهوه‌ای=#92400E, بنفش=#7C3AED, مشکی=#1F2937
- «دکمه ... بشه/شود ...» یا «متن دکمه ... عوض کن» → یک تغییر از نوع update_field روی بخش hero یا navbar، روی فیلد primary_button یا secondary_button یا nav_items
- «عنوان سایت را بکن/عوض کن ...» → یک تغییر از نوع update_field روی بخش hero، فیلد title
- «بخش X را پایین/بالا ببر» → یک تغییر از نوع move_section با جهت down یا up، تکرار چندباره اگر لازم باشد تا به انتها/ابتدا برسد
- اگر واقعاً نمی‌فهمی منظور کاربر چیست، در پاسخ needs_clarification را true بگذار و یک سؤال ساده فارسی در clarification_question بنویس. هرگز حدس کور نزن.

همیشه changes را نسبت به بخش‌های واقعی موجود در ورودی (که در پیام کاربر فهرست می‌شود) تنظیم کن — section_id ها را دقیقاً از آن فهرست استفاده کن."""


_TOOL = {
    "name": "apply_website_changes",
    "description": "Apply one or more structured changes to the website based on the user's natural language request.",
    "input_schema": {
        "type": "object",
        "properties": {
            "needs_clarification": {"type": "boolean"},
            "clarification_question": {
                "type": "string",
                "description": "Simple Persian question to ask the user if the request was not clear enough to apply safely.",
            },
            "summary": {
                "type": "string",
                "description": "One short Persian sentence describing what was changed, for the success message.",
            },
            "changes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["update_field", "move_section", "change_global_color"],
                        },
                        "section_id": {"type": "string", "description": "Required for update_field and move_section"},
                        "field_key": {"type": "string", "description": "Required for update_field, e.g. title, primary_button, logo_text"},
                        "new_value": {"type": "string", "description": "Required for update_field"},
                        "direction": {"type": "string", "enum": ["up", "down"], "description": "Required for move_section"},
                        "repeat": {"type": "integer", "description": "How many times to repeat the move (default 1)"},
                        "color_target": {"type": "string", "enum": ["primary_color", "secondary_color"]},
                        "color_value": {"type": "string", "description": "Hex color code, e.g. #DC2626"},
                    },
                    "required": ["action"],
                },
            },
        },
        "required": ["needs_clarification", "changes"],
    },
}


def _describe_sections_for_prompt(sections: list[dict[str, Any]]) -> str:
    lines = []
    for sec in sections:
        content_preview = {k: v for k, v in sec["content"].items() if isinstance(v, (str, int, float))}
        lines.append(f"- id={sec['id']} | type={sec['type']} | content={content_preview}")
    return "\n".join(lines)


def interpret_and_apply(
    raw_text: str,
    sections: list[dict[str, Any]],
    global_style: dict[str, Any],
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    Interpret the user's natural-language request and apply it directly
    to a working copy of sections + global_style, then re-render HTML.

    Returns:
        {
          "success": bool,
          "needs_clarification": bool,
          "clarification_question": str | None,
          "summary": str,
          "sections": [...],       # updated, only meaningful if success
          "global_style": {...},   # updated, only meaningful if success
          "html_preview": str,     # re-rendered, only meaningful if success
        }
    """
    import copy as _copy
    working_sections = _copy.deepcopy(sections)
    working_style = _copy.deepcopy(global_style)

    try:
        result = _call_claude(raw_text, working_sections, api_key)
    except Exception:
        result = _fallback_interpret(raw_text)

    if result.get("needs_clarification"):
        return {
            "success": False,
            "needs_clarification": True,
            "clarification_question": result.get("clarification_question")
                or "متوجه نشدم. لطفاً ساده‌تر بگو چه چیزی را تغییر بدهیم.",
            "summary": "",
            "sections": sections,
            "global_style": global_style,
            "html_preview": None,
        }

    changes = result.get("changes") or []
    if not changes:
        return {
            "success": False,
            "needs_clarification": True,
            "clarification_question": "متوجه نشدم. لطفاً ساده‌تر بگو چه چیزی را تغییر بدهیم.",
            "summary": "",
            "sections": sections,
            "global_style": global_style,
            "html_preview": None,
        }

    any_applied = False
    for change in changes:
        action = change.get("action")
        if action == "update_field":
            sid, fkey, val = change.get("section_id"), change.get("field_key"), change.get("new_value")
            if sid and fkey and val is not None and any(s["id"] == sid for s in working_sections):
                working_sections = apply_section_edit(working_sections, sid, fkey, val)
                any_applied = True
        elif action == "move_section":
            sid, direction = change.get("section_id"), change.get("direction")
            repeat = max(1, int(change.get("repeat", 1) or 1))
            if sid and direction and any(s["id"] == sid for s in working_sections):
                for _ in range(repeat):
                    working_sections = reorder_section(working_sections, sid, direction)
                any_applied = True
        elif action == "change_global_color":
            target = change.get("color_target") or "primary_color"
            value = change.get("color_value")
            if value and re.match(r"^#[0-9A-Fa-f]{6}$", value):
                working_style[target] = value
                any_applied = True

    if not any_applied:
        return {
            "success": False,
            "needs_clarification": True,
            "clarification_question": "متوجه نشدم. لطفاً ساده‌تر بگو چه چیزی را تغییر بدهیم.",
            "summary": "",
            "sections": sections,
            "global_style": global_style,
            "html_preview": None,
        }

    new_html = render_website(working_sections, working_style)

    return {
        "success": True,
        "needs_clarification": False,
        "clarification_question": None,
        "summary": result.get("summary") or "تغییر انجام شد.",
        "sections": working_sections,
        "global_style": working_style,
        "html_preview": new_html,
    }


def _call_claude(raw_text: str, sections: list[dict[str, Any]], api_key: str | None) -> dict[str, Any]:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    sections_desc = _describe_sections_for_prompt(sections)
    user_msg = (
        f"بخش‌های موجود در سایت:\n{sections_desc}\n\n"
        f"درخواست تغییر کاربر: {raw_text}"
    )

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "apply_website_changes"},
        messages=[{"role": "user", "content": user_msg}],
    )
    tool_block = next((b for b in message.content if b.type == "tool_use"), None)
    if tool_block is None:
        raise ValueError("No tool_use block in Claude response")
    return dict(tool_block.input)


# ─── Fallback — only used if the Claude call itself fails (network/auth) ────
# Deterministic, honest, narrow: handles the clearest cases so a transient
# API failure doesn't fully break the experience, but never pretends to
# understand something it doesn't.

_COLOR_WORDS = {
    "قرمز": "#DC2626", "آبی": "#2563EB", "سبز": "#16A34A", "زرد": "#F59E0B",
    "نارنجی": "#EA580C", "کرم": "#D4A574", "قهوه‌ای": "#92400E",
    "بنفش": "#7C3AED", "مشکی": "#1F2937", "سفید": "#F3F4F6",
}


def _fallback_interpret(raw_text: str) -> dict[str, Any]:
    t = raw_text.strip()
    for word, hex_value in _COLOR_WORDS.items():
        if word in t and ("رنگ" in t):
            return {
                "needs_clarification": False,
                "summary": "رنگ سایت تغییر کرد.",
                "changes": [{"action": "change_global_color", "color_target": "primary_color", "color_value": hex_value}],
            }
    return {
        "needs_clarification": True,
        "clarification_question": "متوجه نشدم. لطفاً ساده‌تر بگو چه چیزی را تغییر بدهیم.",
        "changes": [],
    }
