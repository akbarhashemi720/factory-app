"""
Anthropic Builder — Builder v2/v3/v7.

Converts the rich structured understanding (from anthropic_pm) into a
polished, real-feeling, EDITABLE website preview — using the same
section-block model and renderer as html_builder (v3), so the click-to-edit
full-page editor works identically regardless of which provider built
the spec.

Falls back to html_builder (scenario templates) if rich fields are missing.

v7 fix: this provider previously never connected to the Inspiration Bank
luxury routing that html_builder.py has — BUILDER_PROVIDER=anthropic is
the active provider in production, so all of html_builder.py's luxury
work was invisible in the real output. This file now applies the exact
same routing: when the chosen cafe inspiration family's visual_style is
"luxury_premium", use build_luxury_cafe_sections() + theme="luxury"
instead of the generic section order/CSS, for BOTH the rich-Claude-data
path and the scenario-template fallback path.
"""
from __future__ import annotations
from typing import Any
from app.providers.builder.section_model import build_sections_from_spec, build_luxury_cafe_sections
from app.providers.builder.render_sections import render_website


def generate(
    project: dict,
    understanding: dict,
    scenario_pattern: dict | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Build a rich, editable preview from Claude's structured understanding."""

    raw_text = understanding.get("raw_text") or " ".join(understanding.get("bullets", []) or [])

    # If understanding has rich fields (menu_items, benefits, etc.) from Claude,
    # use them directly. Otherwise fall back to scenario template.
    has_rich_data = bool(understanding.get("menu_items")) or bool(understanding.get("benefits"))

    if has_rich_data:
        spec = _spec_from_understanding(understanding)
        # Rich-Claude-data path still needs the Inspiration Bank applied —
        # otherwise a cafe request that already has Claude-generated menu
        # items would never get routed to the luxury layout either.
        scenario = understanding.get("detected_scenario") or project.get("scenario") or "general"
        website_intent = understanding.get("website_intent")
        from app.providers.builder.html_builder import _CAFE_INTENTS, _apply_cafe_inspiration
        intent = website_intent or scenario
        if intent in _CAFE_INTENTS or scenario == "restaurant":
            spec = _apply_cafe_inspiration(spec, raw_text)
    else:
        # No rich Claude data available — use website_intent-aware scenario
        # fallback, WITH raw_text so the Inspiration Bank can match real
        # intent keywords ("لوکس", "رزرو میز", ...) — this was the missing
        # argument that silently broke luxury routing in this file.
        from app.providers.builder.html_builder import _build_spec
        scenario = understanding.get("detected_scenario") or project.get("scenario") or "general"
        website_intent = understanding.get("website_intent")
        spec = _build_spec(scenario, understanding, website_intent, raw_text)

    if spec.get("_inspiration_visual_style") == "luxury_premium":
        sections = build_luxury_cafe_sections(spec)
    else:
        sections = build_sections_from_spec(spec)

    global_style = {
        "primary_color": spec.get("color", "#4F46E5"),
        "secondary_color": spec.get("color2", "#818CF8"),
        "border_radius": "14px",
        "font_family": "Tahoma,Arial,sans-serif",
        "theme": "luxury" if spec.get("_inspiration_visual_style") == "luxury_premium" else "default",
    }
    html = render_website(sections, global_style)

    return {
        "preview_data": {
            "scenario":     understanding.get("detected_scenario", "general"),
            "website_intent": understanding.get("website_intent"),
            "title":        spec["name"],
            "subtitle":     spec["tagline"],
            "product_type": spec["type"],
            "sections":     spec["nav_items"],
            "features":     spec.get("features", []),
            "html_preview": html,
            "_is_html_preview": True,
            "section_blocks": sections,
            "global_style": global_style,
            "inspiration_style_name": spec.get("_inspiration_style_name"),
        },
        "change_summary": [
            f"پیش‌نمایش اولیه «{spec['name']}» ساخته شد",
            f"نوع محصول: {spec['type']}",
            "محتوا بر اساس نیاز واقعی شما طراحی شده",
        ],
        "known_limitations": [
            "این پیش‌نمایش اولیه است — جزئیات قابل تغییر است",
            "تصاویر واقعی در مراحل بعد اضافه می‌شود",
        ],
    }


def _spec_from_understanding(und: dict) -> dict:
    """Map Claude's rich structured fields onto the spec shape html_builder expects."""

    palette = und.get("color_palette") or {}
    color = palette.get("primary") or "#4F46E5"
    color2 = palette.get("secondary") or "#818CF8"

    menu_items = und.get("menu_items") or []
    # Normalize menu items to expected shape
    norm_menu = []
    for m in menu_items[:6]:
        norm_menu.append({
            "icon": m.get("icon", "✨"),
            "name": m.get("name", ""),
            "desc": m.get("desc", ""),
            "price": m.get("price", ""),
        })
    while len(norm_menu) < 3:
        norm_menu.append({"icon": "✨", "name": "ویژگی", "desc": "در حال تکمیل", "price": ""})

    benefits = und.get("benefits") or []
    norm_benefits = []
    for b in benefits[:3]:
        norm_benefits.append({
            "icon": b.get("icon", "✅"),
            "title": b.get("title", ""),
            "desc": b.get("desc", ""),
        })
    while len(norm_benefits) < 3:
        norm_benefits.append({"icon": "✅", "title": "کیفیت", "desc": "تجربه‌ای متفاوت"})

    nav_items = und.get("navigation_items") or und.get("sections") or ["خانه", "خدمات", "تماس"]

    return {
        "name": und.get("product_name") or und.get("business_domain") or "محصول شما",
        "tagline": und.get("hero_subtitle") or und.get("primary_goal") or "",
        "type": und.get("product_type", "وب‌سایت"),
        "color": color,
        "color2": color2,
        "hero_btn": und.get("primary_cta") or "شروع کنید",
        "hero_btn2": und.get("secondary_cta") or "اطلاعات بیشتر",
        "nav_items": nav_items,
        "features": und.get("suggested_features") or [],
        "menu_items": norm_menu,
        "why_us": norm_benefits,
        "about": und.get("about_text") or und.get("primary_goal") or "",
    }
