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
        # "type" carries enough signal to tell a homemade-food/order store
        # apart from everything else (cafe, education, generic store, ...).
        # Only that specific case gets food/order wording — every other
        # template keeps the existing generic title/button untouched.
        is_homemade_food_store = spec.get("type") == "کاتالوگ محصول و سفارش ساده"
        menu_title = "محصولات قابل سفارش" if is_homemade_food_store else "پیشنهادهای ویژه"
        menu_subtitle = (
            "محصولات خانگی ما را ببین و سفارش بده"
            if is_homemade_food_store
            else "نمونه‌ای از آنچه مشتریان شما می‌بینند"
        )
        card_button_label = "افزودن به سفارش" if is_homemade_food_store else "انتخاب"
        sections.append(new_block("menu_grid", {
            "title": menu_title,
            "subtitle": menu_subtitle,
            "items": spec.get("menu_items", []),
            "card_button_label": card_button_label,
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


def build_luxury_cafe_sections(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Dedicated section order for cafe_luxury_premium — STRUCTURALLY
    different from build_sections_from_spec, not just a recolor:

      1. Premium navbar
      2. Dark editorial hero
      3. Signature experience / tasting section   (new section type)
      4. Elegant menu preview (fewer, richer cards)
      5. Ambience/gallery section                  (new section type)
      6. Reservation CTA
      7. Location/contact footer

    Still produces the same editable section-block model — every block
    still has id/type/visible/content/style — so the contextual editor
    (icon/box/card/section layers, separate text vs background color)
    keeps working exactly as it does for the default theme.
    """
    sections: list[dict[str, Any]] = []

    sections.append(new_block("navbar", {
        "logo_text": spec.get("name", "کافه"),
        "nav_items": spec.get("nav_items", []),
    }))

    sections.append(new_block("hero", {
        "badge": "تجربه‌ای متفاوت از قهوه",
        "title": spec.get("name", "کافه"),
        "subtitle": spec.get("tagline", ""),
        "primary_button": spec.get("hero_btn", "رزرو میز"),
        "secondary_button": spec.get("hero_btn2", "مشاهده منو"),
    }))

    sections.append(new_block("signature_experience", {
        "eyebrow": "تجربه ویژه",
        "title": "هنر قهوه، با تمام جزئیات",
        "desc": spec.get("about") or "هر فنجان با دقت، با دانه‌های منتخب و دستان مجرب باریستاهای ما آماده می‌شود — تجربه‌ای آرام و خاص که فقط در یک بازدید قابل درک است.",
        "icon": "☕",
    }))

    if spec.get("menu_items"):
        # Fewer, more elegant cards — luxury feels curated, not exhaustive.
        sections.append(new_block("menu_grid", {
            "title": "منتخب منو",
            "subtitle": "نمونه‌ای از پیشنهادهای ویژه ما",
            "items": (spec.get("menu_items") or [])[:4],
        }))

    sections.append(new_block("ambience", {
        "title": "فضای کافه",
        "subtitle": "اتمسفری که برایش طراحی شده",
        "item_count": 4,
    }))

    sections.append(new_block("cta", {
        "title": "میزی برای شما رزرو شده است",
        "subtitle": "برای رزرو میز یا اطلاعات بیشتر درباره تجربه ما، با ما در ارتباط باشید",
        "button_label": "رزرو میز",
    }))

    sections.append(new_block("footer", {
        "site_name": spec.get("name", "کافه"),
        "tagline": "یک تجربه قهوه برتر",
    }))

    return sections


def build_task_dashboard_sections(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Dedicated section order for the task_dashboard_mockup preview
    archetype (Puzzle: "Make preview product-type aware and stop
    generic website fallback"). STRUCTURALLY different from
    build_sections_from_spec — the main content is a single
    `task_dashboard` section, never the marketing sections (menu_grid /
    gallery / benefits / about / form) those use:

      1. Simple navbar
      2. Small hero (just a title/subtitle, no marketing CTAs)
      3. Task dashboard (status columns + upcoming meetings) — the
         actual main content
      4. Minimal footer

    spec is expected to carry dashboard_columns / dashboard_meetings —
    see _task_dashboard_spec() in html_builder.py.
    """
    sections: list[dict[str, Any]] = []

    sections.append(new_block("navbar", {
        "logo_text": spec.get("name", "داشبورد کارها"),
        "nav_items": spec.get("nav_items", ["خانه"]),
    }))

    sections.append(new_block("hero", {
        "badge": f"پیش‌نمایش اولیه • {spec.get('type', 'داشبورد ساده وظایف')}",
        "title": spec.get("name", "داشبورد کارها"),
        "subtitle": spec.get("tagline", ""),
        "primary_button": "",
        "secondary_button": "",
    }))

    sections.append(new_block("task_dashboard", {
        "title": "کارهای امروز",
        "subtitle": "نمای ساده از کارها و جلسات — این فقط یک پیش‌نمایش اولیه است",
        "status_columns": spec.get("dashboard_columns", []),
        "upcoming_meetings": spec.get("dashboard_meetings", []),
        "add_task_button": "افزودن کار",
        "add_meeting_button": "افزودن جلسه",
    }))

    sections.append(new_block("footer", {
        "site_name": spec.get("name", "داشبورد کارها"),
        "tagline": "این یک پیش‌نمایش اولیه است، نه یک سیستم مدیریت پروژه کامل",
    }))

    return sections


def build_crm_followup_sections(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Dedicated section order for the simple_crm_followup_mockup preview
    archetype (Puzzle: "Fix selected option propagation"). Deliberately
    different from BOTH the marketing-website sections (menu_grid/
    gallery/benefits/about/form) AND build_task_dashboard_sections — the
    main content is a single `crm_followup` section (customer list with
    status/last-contact/next-step), not task columns and not a booking
    form.

      1. Simple navbar
      2. Small hero (title/subtitle only)
      3. Customer follow-up list — the actual main content
      4. Minimal footer
    """
    sections: list[dict[str, Any]] = []

    sections.append(new_block("navbar", {
        "logo_text": spec.get("name", "لیست پیگیری مشتری‌ها"),
        "nav_items": spec.get("nav_items", ["خانه"]),
    }))

    sections.append(new_block("hero", {
        "badge": f"پیش‌نمایش اولیه • {spec.get('type', 'لیست پیگیری مشتری‌ها')}",
        "title": spec.get("name", "لیست پیگیری مشتری‌ها"),
        "subtitle": spec.get("tagline", ""),
        "primary_button": "",
        "secondary_button": "",
    }))

    sections.append(new_block("crm_followup", {
        "title": "مشتری‌ها و وضعیت پیگیری",
        "subtitle": "نمای ساده از مرحله پیگیری هرکدام — این فقط یک پیش‌نمایش اولیه است",
        "customers": spec.get("crm_customers", []),
    }))

    sections.append(new_block("footer", {
        "site_name": spec.get("name", "لیست پیگیری مشتری‌ها"),
        "tagline": "این یک پیش‌نمایش اولیه است، نه یک سیستم CRM واقعی",
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


def apply_element_style_edit(sections: list[dict[str, Any]], section_id: str,
                              element_id: str, style_key: str, style_value: Any) -> list[dict[str, Any]]:
    """
    Set a direct, per-ELEMENT style override (color, font-size, ...) —
    deterministic, no AI involved. Used by the Contextual Edit Panel's
    direct color/size buttons, which must work instantly without going
    through natural-language interpretation.

    Stored at sec["style"]["element_overrides"][element_id][style_key],
    and applied by render_sections.py when rendering that element.
    """
    for sec in sections:
        if sec["id"] == section_id:
            sec.setdefault("style", {})
            sec["style"].setdefault("element_overrides", {})
            sec["style"]["element_overrides"].setdefault(element_id, {})
            sec["style"]["element_overrides"][element_id][style_key] = style_value
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
