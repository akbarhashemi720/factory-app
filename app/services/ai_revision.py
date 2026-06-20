"""
AI Revision Engine — Website Builder v5 (contextual editing).

Replaces the old keyword-matching revision.py, which operated on stale
mock-only fields (title, primary_button) that the real html_preview
no longer uses. This module operates directly on the live
section_blocks + global_style model and RE-RENDERS html_preview, so
every applied change is immediately visible.

v5 adds CONTEXTUAL editing: when the user has clicked a specific element
or section in the full-site preview before describing the change (e.g.
clicked the menu card "کیک شکلاتی" then wrote "اسمش بشه کیک روز"), that
selection is passed in as `selected_context` and used directly — the
model is told exactly which section/element/item the user means, so it
should almost never need to ask "کدام بخش؟" when context is present.

Uses Claude with forced tool-use to interpret free-form Persian change
requests into concrete, structured edits:
  - field-level edits on a section (title, button text, ...)
  - field-level edits on ONE ITEM inside a section's item list
    (a single menu card's name/desc/price, a single benefit card, ...)
  - section reordering (move a section up/down)
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
    apply_item_field_edit,
    reorder_section,
)
from app.providers.builder.render_sections import render_website


_SYSTEM_PROMPT = """تو دستیار فنی یک کارخانه ساخت وب‌سایت هستی. کاربر غیرفنی یک درخواست تغییر به زبان فارسی روزمره می‌نویسد.
وظیفه‌ات: این درخواست را به یک یا چند تغییر دقیق و قابل‌اجرا روی ساختار سایت تبدیل کنی.

ساختار سایت یک آرایه از بخش‌ها (sections) است. هر بخش یک «نوع» (type)، یک «شناسه» (id) و یک شیء «محتوا» (content) دارد.
بعضی بخش‌ها (مثل menu_grid یا benefits) یک لیست «items» دارند — هرکدام از این آیتم‌ها هم اندیس (index) خودش را دارد.
انواع بخش‌ها: navbar, hero, menu_grid, gallery, about, benefits, form, cta, footer.

⭐ قانون مهم‌ترین: اگر کاربر قبلاً روی یک عنصر یا بخش مشخص در سایت کلیک کرده (که در پیام به‌صورت «کاربر روی ... کلیک کرده» مشخص می‌شود)، حتماً تغییر را روی همان عنصر/بخش انتخاب‌شده اعمال کن — هرگز دوباره نپرس «کدام بخش؟» وقتی این اطلاعات از قبل داده شده.
مثال: اگر کاربر روی آیتم منو «کیک شکلاتی» کلیک کرده و نوشته «اسمش بشه کیک روز»، باید دقیقاً همان آیتم (با همان section_id و item_index) را به فیلد name تغییر بدهی — نه آیتم دیگری، نه کل بخش.
مثال: اگر کاربر روی دکمه «مشاهده منو» کلیک کرده و نوشته «متنش بشه فروش محصولات»، باید همان دکمه (همان section_id و همان field_key که در context آمده) را تغییر بدهی.
مثال: اگر کاربر روی بخش اصلی/هرو سایت کلیک کرده و نوشته «رنگش قرمز بشه»، باید رنگ کلی سایت (change_global_color) را تغییر بدهی، چون هرو از رنگ اصلی سایت استفاده می‌کند.
مثال: اگر کاربر روی بخش تماس/فرم کلیک کرده و نوشته «این بخش را ببر پایین»، باید همان بخش (با section_id از context) را با move_section به پایین منتقل کنی.

اگر هیچ context ای داده نشده (کاربر فقط از دکمه عمومی «تغییر می‌خواهم» استفاده کرده، بدون کلیک روی چیزی)، آن‌وقت باید از روی فهرست کامل بخش‌های سایت که در پیام آمده، حدس بزنی منظور کدام بخش است.

برای انواع درخواست:
- «رنگ ... قرمز/آبی/سبز/زرد/کرم/قهوه‌ای ... کن» → change_global_color با رنگ مناسب (hex) برای primary_color
  رنگ‌های پیشنهادی: قرمز=#DC2626, آبی=#2563EB, سبز=#16A34A, زرد=#F59E0B, نارنجی=#EA580C, کرم=#D4A574, قهوه‌ای=#92400E, بنفش=#7C3AED, مشکی=#1F2937
- تغییر نام/متن/توضیح/قیمت یک آیتم خاص (کارت منو، کارت ویژگی) → update_item_field با section_id و item_index درست
- تغییر متن دکمه، عنوان، زیرعنوان یک بخش (نه یک آیتم خاص) → update_field
- «بخش X را پایین/بالا ببر» → move_section با جهت down یا up، تکرار چندباره اگر لازم باشد
- اگر واقعاً نمی‌فهمی منظور کاربر چیست (حتی با وجود context) و نوع تغییر برای آن عنصر امکان‌پذیر نیست، needs_clarification را true بگذار و یک سؤال ساده فارسی بنویس. هرگز حدس کور نزن، اما اگر context کافی است هرگز سؤال تکراری نپرس."""


_TOOL = {
    "name": "apply_website_changes",
    "description": "Apply one or more structured changes to the website based on the user's natural language request and (optionally) the element/section they had already selected.",
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
                            "enum": ["update_field", "update_item_field", "move_section", "change_global_color"],
                        },
                        "section_id": {"type": "string", "description": "Required for update_field, update_item_field, and move_section"},
                        "field_key": {"type": "string", "description": "Required for update_field/update_item_field, e.g. title, primary_button, name, desc, price"},
                        "item_index": {"type": "integer", "description": "Required for update_item_field — index of the item within the section's items list"},
                        "new_value": {"type": "string", "description": "Required for update_field and update_item_field"},
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
        lines.append(f"- section_id={sec['id']} | type={sec['type']} | content={content_preview}")
        items = sec["content"].get("items")
        if isinstance(items, list):
            for idx, item in enumerate(items):
                item_preview = {k: v for k, v in item.items() if isinstance(v, (str, int, float))}
                lines.append(f"    item_index={idx} (in section_id={sec['id']}): {item_preview}")
    return "\n".join(lines)


def _describe_selected_context(selected_context: dict[str, Any] | None) -> str:
    """
    Turn the frontend's click-selection payload into a clear Persian
    sentence Claude can use directly, so it never needs to ask "کدام بخش؟"
    when the user already clicked something.
    """
    if not selected_context:
        return "کاربر هیچ عنصر یا بخش خاصی را از قبل انتخاب نکرده — از روی متن درخواست و فهرست بخش‌ها حدس بزن."

    el_text = selected_context.get("selected_element_text")
    el_type = selected_context.get("selected_element_type")
    sec_id = selected_context.get("selected_section_id")
    sec_type = selected_context.get("selected_section_type")
    el_id = selected_context.get("selected_element_id")

    parts = [f"کاربر روی یک عنصر در سایت کلیک کرده و سپس درخواست تغییر نوشته. این اطلاعات دقیق انتخاب اوست:"]
    if sec_id:
        parts.append(f"- section_id انتخاب‌شده: {sec_id} (نوع بخش: {sec_type or 'نامشخص'})")
    if el_id:
        parts.append(f"- element_id دقیق انتخاب‌شده: {el_id} (نوع عنصر: {el_type or 'نامشخص'})")
    if el_text:
        parts.append(f"- متن فعلی همان عنصر: «{el_text}»")
    parts.append(
        "تغییر را حتماً روی همین section_id/element_id اعمال کن — اگر عنصر داخل یک آیتم لیست "
        "(مثل یک کارت منو) است، element_id معمولاً به شکل «{section_id}-item-{index}-...» است؛ "
        "از همان index برای item_index استفاده کن. هرگز دوباره نپرس کدام بخش، چون مشخص شده."
    )
    return "\n".join(parts)


def interpret_and_apply(
    raw_text: str,
    sections: list[dict[str, Any]],
    global_style: dict[str, Any],
    api_key: str | None = None,
    selected_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Interpret the user's natural-language request and apply it directly
    to a working copy of sections + global_style, then re-render HTML.

    selected_context (optional): payload from the frontend describing an
    element/section the user clicked in the full-site preview before
    opening the change panel. When present, this is given directly to
    Claude so it applies the change to that exact target instead of
    asking "کدام بخش؟".

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
        result = _call_claude(raw_text, working_sections, api_key, selected_context)
    except Exception:
        result = _fallback_interpret(raw_text, selected_context)

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
        elif action == "update_item_field":
            sid, fkey, val = change.get("section_id"), change.get("field_key"), change.get("new_value")
            idx = change.get("item_index")
            if sid and fkey and val is not None and idx is not None and any(s["id"] == sid for s in working_sections):
                working_sections = apply_item_field_edit(working_sections, sid, int(idx), fkey, val)
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


def _call_claude(raw_text: str, sections: list[dict[str, Any]], api_key: str | None,
                  selected_context: dict[str, Any] | None = None) -> dict[str, Any]:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    sections_desc = _describe_sections_for_prompt(sections)
    context_desc = _describe_selected_context(selected_context)
    user_msg = (
        f"بخش‌ها و آیتم‌های موجود در سایت:\n{sections_desc}\n\n"
        f"{context_desc}\n\n"
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


def _fallback_interpret(raw_text: str, selected_context: dict[str, Any] | None = None) -> dict[str, Any]:
    t = raw_text.strip()
    sec_type = (selected_context or {}).get("selected_section_type")
    for word, hex_value in _COLOR_WORDS.items():
        # Normal case: user explicitly mentions "رنگ" in the text.
        # Contextual case: user clicked the hero/header and just named a
        # color ("قرمز بشه") without saying "رنگ" — the context makes it clear.
        if word in t and ("رنگ" in t or sec_type in ("hero", "navbar")):
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
