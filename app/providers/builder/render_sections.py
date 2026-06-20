"""
Section Renderer — Website Builder v4 (contextual element selection).

Renders the section-block model (section_model.py) into a single HTML
document. Every section wrapper carries:
  - data-section-id   → which section this belongs to
  - data-section-type → section type (hero, menu_grid, navbar, ...)

In addition, individual EDITABLE ELEMENTS inside each section (the hero
title, a button, a single menu card's name/desc/price, a nav link, ...)
carry their own:
  - data-element-id    → stable id for this specific element
  - data-element-type  → "title" | "subtitle" | "button" | "card_title" |
                          "card_desc" | "card_price" | "nav_item" | "text" | ...
  - data-element-text  → the current visible text, used for chat context

The parent page (index.html) listens for clicks inside the iframe via
postMessage (injected script at the bottom of this document) and opens
the change panel pre-filled with this context — "چه چیزی را درباره
«X» تغییر بدهیم؟" — instead of asking the user to explain which section
they mean.
"""
from __future__ import annotations
from typing import Any
import html as _html


def _esc(text: Any) -> str:
    return _html.escape(str(text), quote=True)


def render_website(sections: list[dict[str, Any]], global_style: dict[str, Any]) -> str:
    """Render the full HTML document from section blocks."""
    color = global_style.get("primary_color", "#4F46E5")
    color2 = global_style.get("secondary_color", "#818CF8")
    radius = global_style.get("border_radius", "14px")
    font = global_style.get("font_family", "Tahoma,Arial,sans-serif")

    body_html = ""
    for sec in sections:
        if not sec.get("visible", True):
            continue
        renderer = _RENDERERS.get(sec["type"])
        if renderer is None:
            continue
        sec_style = sec.get("style") or {}
        overrides = sec_style.get("element_overrides") or {}
        section_bg = sec_style.get("background_color")
        section_html = renderer(sec["id"], sec["content"], color, color2, overrides, section_bg)
        body_html += (
            f'<div class="ed-section" data-section-id="{sec["id"]}" '
            f'data-section-type="{sec["type"]}">'
            f'{section_html}</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
{_BASE_CSS.format(color=color, color2=color2, radius=radius, font=font)}
</style>
</head>
<body>
{body_html}
<script>
{_INTERACTION_JS}
</script>
</body>
</html>"""


def _bg_style_attr(section_bg: str | None) -> str:
    """Inline style override for a section's own root visual element
    (e.g. .hero, .section, .cta, header) — not the invisible click-wrapper."""
    if section_bg:
        return f' style="background:{_esc(section_bg)} !important"'
    return ""


_SIZE_PRESETS = {
    "small": {"title": "1.8rem", "subtitle": "0.95rem", "button": "0.85rem", "text": "0.85rem"},
    "medium": {"title": "2.5rem", "subtitle": "1.15rem", "button": "0.98rem", "text": "1rem"},
    "large": {"title": "3.2rem", "subtitle": "1.4rem", "button": "1.1rem", "text": "1.2rem"},
}


def _element_style_attr(overrides: dict[str, Any], element_id: str, element_type: str) -> str:
    """
    Build an inline style="" attribute from this element's direct overrides
    (color, size) — deterministic, no AI involved. Used by the Contextual
    Edit Panel's direct color/size controls.
    """
    ov = overrides.get(element_id)
    if not ov:
        return ""
    styles = []
    color = ov.get("color")
    if color:
        styles.append(f"color:{_esc(color)} !important")
    bg_color = ov.get("background_color")
    if bg_color:
        styles.append(f"background:{_esc(bg_color)} !important")
    size_key = ov.get("size")
    if size_key and size_key in _SIZE_PRESETS:
        size_category = "button" if element_type == "button" else (
            "title" if element_type in ("title", "card_title", "section_title") else
            "subtitle" if element_type in ("subtitle", "card_desc") else "text"
        )
        font_size = _SIZE_PRESETS[size_key].get(size_category)
        if font_size:
            styles.append(f"font-size:{font_size} !important")
    if not styles:
        return ""
    return f' style="{";".join(styles)}"'


# ── Per-section-type renderers ──────────────────────────────────────────────
# Every renderer now takes section_id as its first argument so each
# individual editable element can be tagged with data-section-id +
# data-element-id + data-element-type + data-element-text. They also
# receive `overrides` (this section's element_overrides dict) so direct
# color/size edits from the Contextual Edit Panel are applied on render.

def _el(section_id: str, element_id: str, element_type: str, text: Any, inner_html: str,
        extra_class: str = "", overrides: dict[str, Any] | None = None) -> str:
    """Wrap a piece of inner HTML as a clickable, selectable element."""
    style_attr = _element_style_attr(overrides or {}, element_id, element_type)
    return (
        f'<span class="ed-el {extra_class}" '
        f'data-section-id="{section_id}" '
        f'data-element-id="{element_id}" '
        f'data-element-type="{element_type}" '
        f'data-element-text="{_esc(text)}"{style_attr}>{inner_html}</span>'
    )


def _render_navbar(sid: str, c: dict, color: str, color2: str, overrides: dict[str, Any], section_bg: str | None = None) -> str:
    nav_html = "".join(
        _el(sid, f"{sid}-nav-{i}", "nav_item", n,
            f'<a href="#sec-{i}" class="nav-link">{n}</a>', "ed-el-inline", overrides)
        for i, n in enumerate(c.get("nav_items", []))
    )
    logo_text = c.get('logo_text', '')
    logo_html = _el(sid, f"{sid}-logo", "title", logo_text, f'<div class="logo">{logo_text}</div>', "ed-el-inline", overrides)
    return f"""
    <header{_bg_style_attr(section_bg)}>
      {logo_html}
      <nav>{nav_html}</nav>
    </header>"""


def _render_hero(sid: str, c: dict, color: str, color2: str, overrides: dict, section_bg: str | None = None) -> str:
    title = c.get('title', '')
    subtitle = c.get('subtitle', '')
    pbtn = c.get('primary_button', '')
    sbtn = c.get('secondary_button', '')

    title_html = _el(sid, f"{sid}-title", "title", title, f'<h1>{title}</h1>', "ed-el-block", overrides)
    subtitle_html = _el(sid, f"{sid}-subtitle", "subtitle", subtitle, f'<p>{subtitle}</p>', "ed-el-block", overrides)
    pbtn_html = _el(sid, f"{sid}-pbtn", "button", pbtn,
                     f'<button class="btn-primary">{pbtn}</button>', "ed-el-inline", overrides)
    sbtn_html = ""
    if sbtn:
        sbtn_html = _el(sid, f"{sid}-sbtn", "button", sbtn,
                         f'<button class="btn-secondary">{sbtn}</button>', "ed-el-inline", overrides)

    return f"""
    <div class="hero"{_bg_style_attr(section_bg)}>
      <div class="hero-inner">
        <div class="hero-badge">{c.get('badge','')}</div>
        {title_html}
        {subtitle_html}
        <div class="hero-btns">
          {pbtn_html}
          {sbtn_html}
        </div>
      </div>
      <div class="hero-wave"></div>
    </div>"""


def _render_menu_grid(sid: str, c: dict, color: str, color2: str, overrides: dict, section_bg: str | None = None) -> str:
    cards = ""
    for idx, item in enumerate(c.get("items", [])):
        item_id = f"{sid}-item-{idx}"
        name = item.get('name', '')
        desc = item.get('desc', '')
        price = item.get('price', '')

        name_html = _el(sid, f"{item_id}-name", "card_title", name, f'<div class="m-name">{name}</div>', "ed-el-block", overrides)
        desc_html = _el(sid, f"{item_id}-desc", "card_desc", desc, f'<div class="m-desc">{desc}</div>', "ed-el-block", overrides)
        price_html = ""
        if price:
            price_html = _el(sid, f"{item_id}-price", "card_price", price, f'<div class="m-price">{price}</div>', "ed-el-block", overrides)
        img_html = _el(sid, f"{item_id}-img", "image", item.get('icon', '✨'),
                        f'<div class="m-img">{item.get("icon","✨")}</div>', "ed-el-block", overrides)
        btn_html = _el(sid, f"{item_id}-btn", "button", "انتخاب",
                        '<button class="m-btn">انتخاب</button>', "ed-el-inline", overrides)

        cards += f"""
        <div class="m-card" data-section-id="{sid}" data-card-id="{item_id}">
          {img_html}
          <div class="m-card-body">
            {name_html}
            {desc_html}
            {price_html}
            {btn_html}
          </div>
        </div>"""

    title = c.get('title', '')
    subtitle = c.get('subtitle', '')
    title_html = _el(sid, f"{sid}-title", "section_title", title, f'<div class="section-title">{title}</div>', "ed-el-block", overrides)
    subtitle_html = _el(sid, f"{sid}-subtitle", "subtitle", subtitle, f'<div class="section-sub">{subtitle}</div>', "ed-el-block", overrides)

    return f"""
    <div class="section"{_bg_style_attr(section_bg)}>
      {title_html}
      {subtitle_html}
      <div class="menu-grid">{cards}</div>
    </div>"""


def _render_gallery(sid: str, c: dict, color: str, color2: str, overrides: dict, section_bg: str | None = None) -> str:
    n = c.get("item_count", 4)
    items = "".join(
        _el(sid, f"{sid}-img-{i}", "image", "تصویر گالری",
            '<div class="gallery-item">📷</div>', "ed-el-block", overrides)
        for i in range(n)
    )
    title = c.get('title', '')
    subtitle = c.get('subtitle', '')
    title_html = _el(sid, f"{sid}-title", "section_title", title, f'<div class="section-title">{title}</div>', "ed-el-block", overrides)
    subtitle_html = _el(sid, f"{sid}-subtitle", "subtitle", subtitle, f'<div class="section-sub">{subtitle}</div>', "ed-el-block", overrides)
    return f"""
    <div class="section"{_bg_style_attr(section_bg)}>
      {title_html}
      {subtitle_html}
      <div class="gallery-grid">{items}</div>
    </div>"""


def _render_about(sid: str, c: dict, color: str, color2: str, overrides: dict, section_bg: str | None = None) -> str:
    feats = "".join(f'<li>✓ {f}</li>' for f in c.get("features", []))
    title = c.get('title', '')
    body = c.get('body', '')
    title_html = _el(sid, f"{sid}-title", "section_title", title, f'<div class="about-title">{title}</div>', "ed-el-block", overrides)
    body_html = _el(sid, f"{sid}-body", "text", body, f'<div class="about-body">{body}</div>', "ed-el-block", overrides)
    return f"""
    <div class="section"{_bg_style_attr(section_bg)}>
      <div class="about-wrap">
        <div class="about-icon">🏪</div>
        <div class="about-text">
          {title_html}
          {body_html}
          <ul class="feature-list">{feats}</ul>
        </div>
      </div>
    </div>"""


def _render_benefits(sid: str, c: dict, color: str, color2: str, overrides: dict, section_bg: str | None = None) -> str:
    cards = ""
    for idx, item in enumerate(c.get("items", [])):
        item_id = f"{sid}-item-{idx}"
        title = item.get('title', '')
        desc = item.get('desc', '')
        title_html = _el(sid, f"{item_id}-title", "card_title", title, f'<div class="why-title">{title}</div>', "ed-el-block", overrides)
        desc_html = _el(sid, f"{item_id}-desc", "card_desc", desc, f'<div class="why-desc">{desc}</div>', "ed-el-block", overrides)
        cards += f"""
        <div class="why-card" data-section-id="{sid}" data-card-id="{item_id}">
          <div class="why-icon">{item.get('icon','✅')}</div>
          {title_html}
          {desc_html}
        </div>"""
    title = c.get('title', '')
    subtitle = c.get('subtitle', '')
    title_html = _el(sid, f"{sid}-title", "section_title", title, f'<div class="section-title">{title}</div>', "ed-el-block", overrides)
    subtitle_html = _el(sid, f"{sid}-subtitle", "subtitle", subtitle, f'<div class="section-sub">{subtitle}</div>', "ed-el-block", overrides)
    return f"""
    <div class="section"{_bg_style_attr(section_bg)}>
      {title_html}
      {subtitle_html}
      <div class="why-grid">{cards}</div>
    </div>"""


def _render_form(sid: str, c: dict, color: str, color2: str, overrides: dict, section_bg: str | None = None) -> str:
    title = c.get('title', '')
    subtitle = c.get('subtitle', '')
    submit_label = c.get('submit_label', 'ثبت')
    title_html = _el(sid, f"{sid}-title", "section_title", title, f'<div class="section-title">{title}</div>', "ed-el-block", overrides)
    subtitle_html = _el(sid, f"{sid}-subtitle", "subtitle", subtitle, f'<div class="section-sub">{subtitle}</div>', "ed-el-block", overrides)
    submit_html = _el(sid, f"{sid}-submit", "button", submit_label,
                       f'<button class="form-submit" onclick="event.stopPropagation();window.__mockSubmit()">{submit_label}</button>', "ed-el-inline")
    return f"""
    <div class="section"{_bg_style_attr(section_bg)}>
      {title_html}
      {subtitle_html}
      <div class="form-wrap">
        <div class="form-row"><label>نام</label><input type="text" placeholder="نام شما"></div>
        <div class="form-row"><label>شماره تماس</label><input type="text" placeholder="۰۹۱۲xxxxxxx"></div>
        <div class="form-row"><label>تاریخ و زمان</label><input type="text" placeholder="مثلاً امشب ساعت ۸"></div>
        {submit_html}
        <div class="confirm-box" id="confirmBox">✓ درخواست شما ثبت شد! به‌زودی با شما تماس می‌گیریم.</div>
      </div>
    </div>"""


def _render_cta(sid: str, c: dict, color: str, color2: str, overrides: dict, section_bg: str | None = None) -> str:
    title = c.get('title', '')
    subtitle = c.get('subtitle', '')
    btn_label = c.get('button_label', '')
    title_html = _el(sid, f"{sid}-title", "title", title, f'<h2>{title}</h2>', "ed-el-block", overrides)
    subtitle_html = _el(sid, f"{sid}-subtitle", "subtitle", subtitle, f'<p>{subtitle}</p>', "ed-el-block", overrides)
    btn_html = _el(sid, f"{sid}-btn", "button", btn_label, f'<button class="btn-primary">{btn_label}</button>', "ed-el-inline", overrides)
    return f"""
    <div class="cta"{_bg_style_attr(section_bg)}>
      {title_html}
      {subtitle_html}
      {btn_html}
    </div>"""


def _render_footer(sid: str, c: dict, color: str, color2: str, overrides: dict, section_bg: str | None = None) -> str:
    site_name = c.get('site_name', '')
    tagline = c.get('tagline', '')
    name_html = _el(sid, f"{sid}-name", "title", site_name, f'<div class="footer-logo">{site_name}</div>', "ed-el-inline", overrides)
    tagline_html = _el(sid, f"{sid}-tagline", "text", tagline, f'<div>{tagline}</div>', "ed-el-inline", overrides)
    return f"""
    <footer{_bg_style_attr(section_bg)}>
      {name_html}
      {tagline_html}
    </footer>"""


_RENDERERS = {
    "navbar": _render_navbar,
    "hero": _render_hero,
    "menu_grid": _render_menu_grid,
    "gallery": _render_gallery,
    "about": _render_about,
    "benefits": _render_benefits,
    "form": _render_form,
    "cta": _render_cta,
    "footer": _render_footer,
}


# ── Section-level human-readable labels (for the change panel title when
#    the user clicks a whole section rather than one specific element) ──────

SECTION_TYPE_LABEL_FA = {
    "navbar": "هدر و منو",
    "hero": "بخش اصلی سایت",
    "menu_grid": "بخش منو",
    "gallery": "گالری تصاویر",
    "about": "بخش درباره ما",
    "benefits": "بخش چرا ما را انتخاب کنید",
    "form": "بخش تماس / رزرو",
    "cta": "بخش دعوت به اقدام",
    "footer": "فوتر",
}


# ── Shared CSS (parameterized by global style) ──────────────────────────────

_BASE_CSS = """
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html {{ scroll-behavior:smooth; }}
  body {{ font-family:{font}; background:#FBF7F0; color:#2D2424; direction:rtl; line-height:1.7; }}

  .ed-section {{ position:relative; cursor:pointer; }}
  .ed-el {{ cursor:pointer; transition:outline .12s, background-color .12s; border-radius:4px; }}
  .ed-el-block {{ display:block; }}
  .ed-el-inline {{ display:inline-block; }}
  .ed-el:hover {{ outline:2px dashed {color}90; outline-offset:2px; background-color:{color}0d; }}
  .ed-el.ed-selected {{ outline:3px solid {color} !important; outline-offset:2px; background-color:{color}1a; }}

  header {{ position:sticky; top:0; background:rgba(255,255,255,0.97); backdrop-filter:blur(8px); box-shadow:0 1px 12px rgba(0,0,0,0.07); z-index:10; padding:16px 32px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; }}
  .logo {{ font-weight:800; font-size:1.25rem; color:{color}; letter-spacing:.3px; }}
  .nav-link {{ color:#555; text-decoration:none; font-size:0.88rem; margin:0 10px; font-weight:500; }}

  .hero {{ position:relative; background:linear-gradient(160deg,{color} 0%,{color2} 55%,{color} 100%); color:#fff; padding:90px 24px 110px; text-align:center; overflow:hidden; }}
  .hero-inner {{ position:relative; z-index:2; max-width:680px; margin:0 auto; }}
  .hero-badge {{ display:inline-block; background:rgba(255,255,255,0.22); border:1px solid rgba(255,255,255,0.35); padding:6px 18px; border-radius:20px; font-size:0.78rem; margin-bottom:22px; }}
  .hero h1 {{ font-size:2.5rem; font-weight:800; margin-bottom:14px; text-shadow:0 2px 12px rgba(0,0,0,0.15); }}
  .hero p {{ font-size:1.15rem; opacity:0.96; margin-bottom:34px; }}
  .hero-btns {{ display:flex; gap:14px; justify-content:center; flex-wrap:wrap; }}
  .btn-primary {{ background:#fff; color:{color}; border:none; padding:15px 36px; border-radius:{radius}; font-size:0.98rem; font-weight:700; cursor:pointer; box-shadow:0 6px 18px rgba(0,0,0,0.18); }}
  .btn-secondary {{ background:rgba(255,255,255,0.12); color:#fff; border:2px solid rgba(255,255,255,0.65); padding:13px 32px; border-radius:{radius}; font-size:0.98rem; font-weight:700; cursor:pointer; }}
  .hero-wave {{ position:absolute; bottom:-2px; left:0; right:0; height:50px; background:#FBF7F0; border-radius:50% 50% 0 0 / 100% 100% 0 0; }}

  .section {{ padding:64px 28px; max-width:1100px; margin:0 auto; }}
  .section-title {{ font-size:1.65rem; font-weight:800; text-align:center; margin-bottom:10px; color:#2D2424; }}
  .section-sub {{ text-align:center; color:#8a7a6e; font-size:0.92rem; margin-bottom:40px; }}

  .menu-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:22px; }}
  .m-card {{ background:#fff; border-radius:{radius}; box-shadow:0 4px 20px rgba(45,36,36,0.08); text-align:center; overflow:hidden; }}
  .m-img {{ height:90px; background:linear-gradient(135deg,{color}1a,{color2}33); display:flex; align-items:center; justify-content:center; font-size:2.6rem; }}
  .m-card-body {{ padding:20px; }}
  .m-name {{ font-weight:700; font-size:1.02rem; margin-bottom:6px; }}
  .m-desc {{ color:#8a7a6e; font-size:0.82rem; margin-bottom:12px; min-height:32px; }}
  .m-price {{ color:{color}; font-weight:800; font-size:1rem; margin-bottom:14px; }}
  .m-btn {{ background:{color}; color:#fff; border:none; padding:9px 26px; border-radius:{radius}; font-size:0.83rem; cursor:pointer; font-weight:600; }}

  .about-wrap {{ background:#fff; border-radius:{radius}; padding:42px; box-shadow:0 4px 20px rgba(45,36,36,0.06); display:flex; gap:32px; align-items:center; flex-wrap:wrap; }}
  .about-icon {{ font-size:4rem; flex-shrink:0; width:90px; height:90px; background:linear-gradient(135deg,{color}1a,{color2}33); border-radius:50%; display:flex; align-items:center; justify-content:center; }}
  .about-title {{ font-weight:700; font-size:1.1rem; margin-bottom:8px; color:#2D2424; }}
  .about-text {{ flex:1; min-width:240px; color:#4a3f3a; font-size:0.94rem; }}
  .about-body {{ display:block; }}
  .feature-list {{ list-style:none; margin-top:18px; }}
  .feature-list li {{ padding:7px 0; color:#4a3f3a; font-size:0.88rem; }}

  .why-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:24px; }}
  .why-card {{ text-align:center; padding:28px 20px; background:#fff; border-radius:{radius}; box-shadow:0 3px 16px rgba(45,36,36,0.05); }}
  .why-icon {{ font-size:2.6rem; margin-bottom:14px; }}
  .why-title {{ font-weight:700; margin-bottom:8px; font-size:1.02rem; color:#2D2424; }}
  .why-desc {{ color:#8a7a6e; font-size:0.86rem; }}

  .gallery-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:18px; }}
  .gallery-item {{ aspect-ratio:4/3; border-radius:{radius}; background:linear-gradient(135deg,{color}26,{color2}40); display:flex; align-items:center; justify-content:center; font-size:2.4rem; box-shadow:0 4px 16px rgba(45,36,36,0.08); }}

  .form-wrap {{ background:#fff; border-radius:{radius}; padding:38px; box-shadow:0 4px 22px rgba(45,36,36,0.08); max-width:500px; margin:0 auto; }}
  .form-row {{ margin-bottom:16px; }}
  .form-row label {{ display:block; font-size:0.84rem; margin-bottom:6px; color:#4a3f3a; font-weight:600; }}
  .form-row input {{ width:100%; padding:11px 14px; border:1.5px solid #ECE2D6; border-radius:10px; font-size:0.87rem; font-family:inherit; background:#FBF7F0; }}
  .form-submit {{ width:100%; background:{color}; color:#fff; border:none; padding:14px; border-radius:{radius}; font-size:0.97rem; font-weight:700; cursor:pointer; margin-top:10px; }}
  .confirm-box {{ display:none; background:#ECFDF5; border:1.5px solid #10B981; color:#065F46; padding:16px; border-radius:12px; text-align:center; font-size:0.86rem; margin-top:16px; }}

  .cta {{ background:linear-gradient(160deg,{color},{color2}); color:#fff; padding:64px 24px; text-align:center; }}
  .cta h2 {{ font-size:1.6rem; font-weight:800; margin-bottom:12px; }}
  .cta p {{ opacity:0.94; margin-bottom:28px; font-size:0.95rem; }}

  footer {{ background:#241C1C; color:#a89b94; padding:32px 24px; text-align:center; font-size:0.82rem; }}
  footer .footer-logo {{ color:#fff; font-weight:700; margin-bottom:10px; font-size:1.05rem; }}
"""

_INTERACTION_JS = """
window.__selectElement = function(el, ev) {
  if (ev) ev.stopPropagation();
  document.querySelectorAll('.ed-selected').forEach(e => e.classList.remove('ed-selected'));
  el.classList.add('ed-selected');
  const sectionEl = el.closest('.ed-section');
  const sectionId = sectionEl ? sectionEl.getAttribute('data-section-id') : null;
  const sectionType = sectionEl ? sectionEl.getAttribute('data-section-type') : null;
  if (window.parent) {
    window.parent.postMessage({
      type: 'element-selected',
      elementId: el.getAttribute('data-element-id'),
      elementType: el.getAttribute('data-element-type'),
      elementText: el.getAttribute('data-element-text'),
      sectionId: sectionId,
      sectionType: sectionType,
    }, '*');
  }
};
window.__selectSectionBackground = function(sectionEl) {
  document.querySelectorAll('.ed-selected').forEach(e => e.classList.remove('ed-selected'));
  if (window.parent) {
    window.parent.postMessage({
      type: 'element-selected',
      elementId: null,
      elementType: null,
      elementText: null,
      sectionId: sectionEl.getAttribute('data-section-id'),
      sectionType: sectionEl.getAttribute('data-section-type'),
    }, '*');
  }
};
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.ed-el').forEach(function(el) {
    el.addEventListener('click', function(ev) { window.__selectElement(el, ev); });
  });
  // Clicking the empty background of a section (not a specific element)
  // selects the whole section — e.g. clicking the hero's gradient area.
  document.querySelectorAll('.ed-section').forEach(function(sec) {
    sec.addEventListener('click', function(ev) {
      if (ev.target.closest('.ed-el')) return; // a more specific element already handled it
      window.__selectSectionBackground(sec);
    });
  });
});
window.__mockSubmit = function() {
  const box = document.getElementById('confirmBox');
  if (box) box.style.display = 'block';
};
"""

