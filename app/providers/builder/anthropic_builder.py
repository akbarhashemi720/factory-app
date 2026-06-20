"""
Anthropic Builder — Builder v2.

Converts the rich structured understanding (from anthropic_pm) into a
polished, real-feeling HTML/CSS website preview — reusing the same
visual rendering engine as html_builder, but driven by Claude's actual
content instead of static scenario templates.

Falls back to html_builder (scenario templates) if rich fields are missing.
"""
from __future__ import annotations
from typing import Any
from app.providers.builder.html_builder import _render_html as _render_rich_html


def generate(
    project: dict,
    understanding: dict,
    scenario_pattern: dict | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Build a rich preview from Claude's structured understanding."""

    # If understanding has rich fields (menu_items, benefits, etc.) from Claude,
    # use them directly. Otherwise fall back to scenario template.
    has_rich_data = bool(understanding.get("menu_items")) or bool(understanding.get("benefits"))

    if has_rich_data:
        spec = _spec_from_understanding(understanding)
    else:
        # No rich Claude data available — use website_intent-aware scenario fallback
        from app.providers.builder.html_builder import _build_spec
        scenario = understanding.get("detected_scenario") or project.get("scenario") or "general"
        website_intent = understanding.get("website_intent")
        spec = _build_spec(scenario, understanding, website_intent)

    html = _render_rich_html(spec)

    return {
        "preview_data": {
            "scenario":     understanding.get("detected_scenario", "general"),
            "title":        spec["name"],
            "subtitle":     spec["tagline"],
            "product_type": spec["type"],
            "sections":     spec["nav_items"],
            "features":     spec.get("features", []),
            "html_preview": html,
            "_is_html_preview": True,
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
