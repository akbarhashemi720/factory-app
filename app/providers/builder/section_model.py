"""
Section Block Model — Website Builder v3.

Separates GENERATED WEBSITE CONTENT (data) from the VISUAL BUILDER UI
that renders, selects, and edits it.

A website is now an ordered list of section blocks. Each block has:
  - id:        stable identifier (for selection/reorder/delete)
  - type:      section type (drives which editor fields + renderer apply)
  - visible:   show/hide toggle
  - content:   the actual editable data (title, items, etc.)
  - style:     section-level style overrides (bg, alignment, spacing)

This is the single source of truth. The HTML preview is rendered FROM
this model (see render_sections.py), and edits update this model, then
re-render — never the other way around.
"""
from __future__ import annotations
from typing import Any
from uuid import uuid4


# ── Section type registry ───────────────────────────────────────────────────
# Each type declares which content fields its editor panel should show.

SECTION_FIELD_SCHEMA: dict[str, list[dict[str, str]]] = {
    "navbar": [
        {"key": "logo_text", "label": "نام در هدر", "type": "text"},
        {"key": "nav_items", "label": "آیتم‌های منو", "type": "list"},
    ],
    "hero": [
        {"key": "badge", "label": "برچسب کوچک بالای عنوان", "type": "text"},
        {"key": "title", "label": "عنوان اصلی", "type": "text"},
        {"key": "subtitle", "label": "زیرعنوان", "type": "textarea"},
        {"key": "primary_button", "label": "متن دکمه اصلی", "type": "text"},
        {"key": "secondary_button", "label": "متن دکمه دوم", "type": "text"},
    ],
    "menu_grid": [
        {"key": "title", "label": "عنوان بخش", "type": "text"},
        {"key": "subtitle", "label": "توضیح کوتاه", "type": "text"},
        {"key": "items", "label": "آیتم‌ها (منو/دوره/خدمات)", "type": "item_list"},
    ],
    "gallery": [
        {"key": "title", "label": "عنوان بخش", "type": "text"},
        {"key": "subtitle", "label": "توضیح کوتاه", "type": "text"},
        {"key": "item_count", "label": "تعداد تصویر", "type": "number"},
    ],
    "about": [
        {"key": "title", "label": "عنوان بخش", "type": "text"},
        {"key": "body", "label": "متن درباره ما", "type": "textarea"},
        {"key": "features", "label": "ویژگی‌ها", "type": "list"},
    ],
    "benefits": [
        {"key": "title", "label": "عنوان بخش", "type": "text"},
        {"key": "subtitle", "label": "توضیح کوتاه", "type": "text"},
        {"key": "items", "label": "موارد", "type": "benefit_list"},
    ],
    "form": [
        {"key": "title", "label": "عنوان بخش", "type": "text"},
        {"key": "subtitle", "label": "توضیح کوتاه", "type": "text"},
        {"key": "submit_label", "label": "متن دکمه ثبت", "type": "text"},
    ],
    "cta": [
        {"key": "title", "label": "عنوان", "type": "text"},
        {"key": "subtitle", "label": "توضیح", "type": "text"},
        {"key": "button_label", "label": "متن دکمه", "type": "text"},
    ],
    "footer": [
        {"key": "site_name", "label": "نام سایت", "type": "text"},
        {"key": "tagline", "label": "متن کوتاه پایین", "type": "text"},
    ],
}

DEFAULT_SECTION_ORDER = [
    "navbar", "hero", "menu_grid", "gallery", "about", "benefits", "form", "cta", "footer",
]


def new_block(section_type: str, content: dict[str, Any],
              visible: bool = True, style: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create one section block with a stable id."""
    return {
        "id": f"sec_{uuid4().hex[:8]}",
        "type": section_type,
        "visible": visible,
        "content": content,
        "style": style or {},
    }


def build_sections_from_spec(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Convert the existing flat `spec` dict (from html_builder._build_spec /
    anthropic_builder._spec_from_understanding) into an ordered list of
    editable section blocks. This is the bridge from the old spec shape
    to the new section-block model, without touching spec generation logic.
    """
    sections: list[dict[str, Any]] = []

    sections.append(new_block("navbar", {
        "logo_text": spec.get("name", "محصول شما"),
        "nav_items": spec.get("nav_items", []),
    }))

    sections.append(new_block("hero", {
        "badge": f"پیش‌نمایش اولیه • {spec.get('type', '')}",
        "title": spec.get("name", "محصول شما"),
        "subtitle": spec.get("tagline", ""),
        "primary_button": spec.get("hero_btn", "شروع کنید"),
        "secondary_button": spec.get("hero_btn2", ""),
    }))

    if spec.get("menu_items"):
        sections.append(new_block("menu_grid", {
            "title": "پیشنهادهای ویژه",
            "subtitle": "نمونه‌ای از آنچه مشتریان شما می‌بینند",
            "items": spec.get("menu_items", []),
        }))

    sections.append(new_block("gallery", {
        "title": "گالری تصاویر",
        "subtitle": "نمونه‌ای از فضای کسب‌وکار شما",
        "item_count": 4,
    }))

    sections.append(new_block("about", {
        "title": "درباره ما",
        "body": spec.get("about", ""),
        "features": spec.get("features", []),
    }))

    if spec.get("why_us"):
        sections.append(new_block("benefits", {
            "title": "چرا ما را انتخاب کنید",
            "subtitle": "دلایلی که مشتریان به ما اعتماد می‌کنند",
            "items": spec.get("why_us", []),
        }))

    sections.append(new_block("form", {
        "title": "رزرو یا سفارش",
        "subtitle": "فرم زیر را پر کنید تا با شما تماس بگیریم",
        "submit_label": "ثبت درخواست",
    }))

    sections.append(new_block("cta", {
        "title": "همین حالا شروع کنید",
        "subtitle": "برای رزرو، سفارش یا اطلاعات بیشتر با ما در ارتباط باشید",
        "button_label": "تماس با ما",
    }))

    sections.append(new_block("footer", {
        "site_name": spec.get("name", "محصول شما"),
        "tagline": "این یک پیش‌نمایش اولیه است",
    }))

    return sections


def apply_section_edit(sections: list[dict[str, Any]], section_id: str,
                        field_key: str, new_value: Any) -> list[dict[str, Any]]:
    """Update one content field on one section, return the new sections list."""
    for sec in sections:
        if sec["id"] == section_id:
            sec["content"][field_key] = new_value
            break
    return sections


def apply_item_field_edit(sections: list[dict[str, Any]], section_id: str,
                           item_index: int, field_key: str, new_value: Any) -> list[dict[str, Any]]:
    """
    Update one field on one item WITHIN a section's items list — e.g. a single
    menu card's name/desc/price, or a single benefit card's title/desc.
    Used for contextual edits like "این کارت رو ... کن" where the user
    clicked one specific card, not the whole section.
    """
    for sec in sections:
        if sec["id"] == section_id:
            items = sec["content"].get("items")
            if isinstance(items, list) and 0 <= item_index < len(items):
                items[item_index][field_key] = new_value
            break
    return sections


def reorder_section(sections: list[dict[str, Any]], section_id: str,
                     direction: str) -> list[dict[str, Any]]:
    """direction: 'up' or 'down'. Swap with neighbor."""
    idx = next((i for i, s in enumerate(sections) if s["id"] == section_id), None)
    if idx is None:
        return sections
    if direction == "up" and idx > 0:
        sections[idx - 1], sections[idx] = sections[idx], sections[idx - 1]
    elif direction == "down" and idx < len(sections) - 1:
        sections[idx + 1], sections[idx] = sections[idx], sections[idx + 1]
    return sections


def duplicate_section(sections: list[dict[str, Any]], section_id: str) -> list[dict[str, Any]]:
    idx = next((i for i, s in enumerate(sections) if s["id"] == section_id), None)
    if idx is None:
        return sections
    import copy
    clone = copy.deepcopy(sections[idx])
    clone["id"] = f"sec_{uuid4().hex[:8]}"
    sections.insert(idx + 1, clone)
    return sections


def delete_section(sections: list[dict[str, Any]], section_id: str) -> list[dict[str, Any]]:
    return [s for s in sections if s["id"] != section_id]


def toggle_visibility(sections: list[dict[str, Any]], section_id: str) -> list[dict[str, Any]]:
    for sec in sections:
        if sec["id"] == section_id:
            sec["visible"] = not sec["visible"]
            break
    return sections
