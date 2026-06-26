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
    # theme switches between the default warm-cafe visual system and a
    # dark/editorial luxury system — a REAL visual transformation (dark
    # palette, large whitespace, refined typography, cinematic hero),
    # not just a color swap on the same generic layout.
    theme = global_style.get("theme", "default")

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

    css = _BASE_CSS.format(color=color, color2=color2, radius=radius, font=font)
    if theme == "luxury":
        css += _LUXURY_CSS_OVERRIDE.format(color=color, color2=color2, radius=radius)

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
{css}
</style>
</head>
<body class="{'theme-luxury' if theme == 'luxury' else ''}">
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


def _card_bg_style_attr(overrides: dict[str, Any], item_id: str) -> str:
    """
    "رنگ زمینه" chosen while editing a card's title/desc/price must color
    the whole VISIBLE card (.m-card / .why-card), not a thin strip behind
    one text element. The frontend stores this under the item's own key
    (item_id, e.g. "{section_id}-item-2") — distinct from the per-element
    text-color overrides stored under the sub-element ids.
    """
    ov = overrides.get(item_id)
    if not ov:
        return ""
    bg = ov.get("background_color")
    if bg:
        return f' style="background:{_esc(bg)} !important"'
    return ""


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
    # For card sub-elements (title/desc/price), background is applied at
    # the card container level (.m-card) via _card_bg_style_attr instead —
    # putting it here would only color a thin strip behind the text.
    if bg_color and element_type not in ("card_title", "card_desc", "card_price"):
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
        extra_class: str = "", overrides: dict[str, Any] | None = None, item_id: str | None = None) -> str:
    """
    Wrap a piece of inner HTML as a clickable, selectable element.

    item_id (optional): if this element lives inside a card/item (e.g. a
    menu card, a benefit card), this is the card's own override key —
    exposed as data-card-id so the frontend can offer a layer choice
    ("خود آیکون" / "باکس تصویر" / "کارت") instead of only ever selecting
    the exact clicked element.
    """
    style_attr = _element_style_attr(overrides or {}, element_id, element_type)
    card_attr = f' data-card-id="{item_id}"' if item_id else ""
    return (
        f'<span class="ed-el {extra_class}" '
        f'data-section-id="{section_id}" '
        f'data-element-id="{element_id}" '
        f'data-element-type="{element_type}" '
        f'data-element-text="{_esc(text)}"{card_attr}{style_attr}>{inner_html}</span>'
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

        name_html = _el(sid, f"{item_id}-name", "card_title", name, f'<div class="m-name">{name}</div>', "ed-el-block", overrides, item_id)
        desc_html = _el(sid, f"{item_id}-desc", "card_desc", desc, f'<div class="m-desc">{desc}</div>', "ed-el-block", overrides, item_id)
        price_html = ""
        if price:
            price_html = _el(sid, f"{item_id}-price", "card_price", price, f'<div class="m-price">{price}</div>', "ed-el-block", overrides, item_id)
        # The image/icon has its own layer hierarchy: the icon itself
        # (element_id), the box behind it ("{item_id}-imgbox"), and the
        # whole card (item_id). data-card-id + data-box-id expose this
        # so the frontend can offer "آیکون / باکس تصویر / کارت" choices.
        img_box_id = f"{item_id}-imgbox"
        img_box_style = _element_style_attr(overrides, img_box_id, "image_box")
        img_html = _el(sid, f"{item_id}-img", "image", item.get('icon', '✨'),
                        f'<div class="m-img"{img_box_style} data-box-id="{img_box_id}">{item.get("icon","✨")}</div>',
                        "ed-el-block", overrides, item_id)
        # card_button_label is set per-spec-type in section_model.py
        # (e.g. "افزودن به سفارش" for homemade-food/order stores). Falls
        # back to the original generic label for every template that
        # doesn't set it, so nothing else changes.
        btn_label = c.get("card_button_label", "انتخاب")
        btn_html = _el(sid, f"{item_id}-btn", "button", btn_label,
                        f'<button class="m-btn">{btn_label}</button>', "ed-el-inline", overrides, item_id)

        # "رنگ زمینه" on a card title/desc must color the whole VISIBLE
        # card container (.m-card), not just a thin strip behind the text
        # span — look up the card-level background override by item_id
        # (set when either the title or desc element's bg color is chosen).
        card_bg = _card_bg_style_attr(overrides, item_id)

        cards += f"""
        <div class="m-card" data-section-id="{sid}" data-card-id="{item_id}"{card_bg}>
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


def _render_task_dashboard(sid: str, c: dict, color: str, color2: str, overrides: dict, section_bg: str | None = None) -> str:
    """
    Task Dashboard Mockup (Puzzle: preview product-type awareness).

    A genuinely different visual archetype from the marketing-website
    sections above: status columns of task cards + an upcoming-meetings
    list + two simple action buttons. No gallery/offers/services/about —
    this section IS the main content for dashboard-style recommendations
    (e.g. "داشبورد ساده وظایف + جلسات").

    Still uses _el() for the title/subtitle/buttons so basic click-to-edit
    keeps working, matching the existing editing model — task card text
    itself is treated as static mockup content for this first version
    (no per-card editing yet), consistent with "smallest safe change".
    """
    title = c.get("title", "")
    subtitle = c.get("subtitle", "")
    title_html = _el(sid, f"{sid}-title", "section_title", title, f'<div class="section-title">{title}</div>', "ed-el-block", overrides)
    subtitle_html = _el(sid, f"{sid}-subtitle", "subtitle", subtitle, f'<div class="section-sub">{subtitle}</div>', "ed-el-block", overrides)

    status_cols_html = ""
    for col in c.get("status_columns", []):
        cards_html = "".join(
            f'<div class="dash-task-card"><div class="dash-task-name">{task}</div></div>'
            for task in col.get("tasks", [])
        )
        status_cols_html += f"""
        <div class="dash-col">
          <div class="dash-col-title">{col.get("label", "")}</div>
          {cards_html}
        </div>"""

    meetings_html = "".join(
        f"""<div class="dash-meeting-row">
              <div class="dash-meeting-time">{m.get("time", "")}</div>
              <div class="dash-meeting-title">{m.get("title", "")}</div>
            </div>"""
        for m in c.get("upcoming_meetings", [])
    )

    add_task_btn = c.get("add_task_button", "افزودن کار")
    add_meeting_btn = c.get("add_meeting_button", "افزودن جلسه")
    add_task_html = _el(sid, f"{sid}-add-task", "button", add_task_btn,
                         f'<button class="m-btn">{add_task_btn}</button>', "ed-el-inline", overrides)
    add_meeting_html = _el(sid, f"{sid}-add-meeting", "button", add_meeting_btn,
                            f'<button class="m-btn dash-btn-secondary">{add_meeting_btn}</button>', "ed-el-inline", overrides)

    return f"""
    <div class="section dash-section"{_bg_style_attr(section_bg)}>
      {title_html}
      {subtitle_html}
      <div class="dash-toolbar">{add_task_html}{add_meeting_html}</div>
      <div class="dash-board">{status_cols_html}</div>
      <div class="dash-meetings-wrap">
        <div class="dash-meetings-title">جلسات پیش رو</div>
        {meetings_html if meetings_html else '<div class="dash-empty">جلسه‌ای ثبت نشده</div>'}
      </div>
    </div>"""


def _render_crm_followup(sid: str, c: dict, color: str, color2: str, overrides: dict, section_bg: str | None = None) -> str:
    """
    Customer Follow-up List Mockup (Puzzle: "Fix selected option
    propagation"). A simple table-like list of customers with status/
    last-contact/next-step — genuinely different visual structure from
    _render_task_dashboard (no status columns, no meetings list).
    """
    title = c.get("title", "")
    subtitle = c.get("subtitle", "")
    title_html = _el(sid, f"{sid}-title", "section_title", title, f'<div class="section-title">{title}</div>', "ed-el-block", overrides)
    subtitle_html = _el(sid, f"{sid}-subtitle", "subtitle", subtitle, f'<div class="section-sub">{subtitle}</div>', "ed-el-block", overrides)

    rows_html = ""
    for cust in c.get("customers", []):
        rows_html += f"""
        <div class="crm-row">
          <div class="crm-name">{cust.get("name", "")}</div>
          <div class="crm-status">{cust.get("status", "")}</div>
          <div class="crm-last-contact">{cust.get("last_contact", "")}</div>
          <div class="crm-next-step">{cust.get("next_step", "")}</div>
        </div>"""

    return f"""
    <div class="section crm-section"{_bg_style_attr(section_bg)}>
      {title_html}
      {subtitle_html}
      <div class="crm-table">
        <div class="crm-row crm-header">
          <div class="crm-name">مشتری</div>
          <div class="crm-status">وضعیت پیگیری</div>
          <div class="crm-last-contact">آخرین تماس/پیام</div>
          <div class="crm-next-step">مرحله بعدی</div>
        </div>
        {rows_html if rows_html else '<div class="dash-empty">مشتری‌ای ثبت نشده</div>'}
      </div>
    </div>"""


def _render_team_task_board(sid: str, c: dict, color: str, color2: str, overrides: dict, section_bg: str | None = None) -> str:
    """
    Team Task Board Mockup (Legacy Replacement Sprint, Phase 4) — per-
    person columns, each showing that person's tasks with a deadline
    and status badge. Genuinely different from _render_task_dashboard
    (status-only columns shared across everyone) and from
    _render_crm_followup (customer rows) — this is "who owns what",
    not "what stage is each task in" or "who are our customers".
    """
    title = c.get("title", "")
    subtitle = c.get("subtitle", "")
    title_html = _el(sid, f"{sid}-title", "section_title", title, f'<div class="section-title">{title}</div>', "ed-el-block", overrides)
    subtitle_html = _el(sid, f"{sid}-subtitle", "subtitle", subtitle, f'<div class="section-sub">{subtitle}</div>', "ed-el-block", overrides)

    members_html = ""
    for member in c.get("team_members", []):
        tasks_html = "".join(
            f'''<div class="team-task-row">
                  <div class="team-task-title">{t.get("title", "")}</div>
                  <div class="team-task-deadline">{t.get("deadline", "")}</div>
                  <div class="team-task-status">{t.get("status", "")}</div>
                </div>'''
            for t in member.get("tasks", [])
        )
        members_html += f"""
        <div class="team-col">
          <div class="team-col-name">{member.get("name", "")}</div>
          {tasks_html}
        </div>"""

    meetings_html = "".join(
        f'''<div class="dash-meeting-row">
              <div class="dash-meeting-time">{m.get("time", "")}</div>
              <div class="dash-meeting-title">{m.get("title", "")}</div>
            </div>'''
        for m in c.get("team_meetings", [])
    )

    return f"""
    <div class="section team-section"{_bg_style_attr(section_bg)}>
      {title_html}
      {subtitle_html}
      <div class="team-board">{members_html}</div>
      {f'<div class="dash-meetings-wrap"><div class="dash-meetings-title">جلسات تیم</div>{meetings_html}</div>' if meetings_html else ''}
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
        title_html = _el(sid, f"{item_id}-title", "card_title", title, f'<div class="why-title">{title}</div>', "ed-el-block", overrides, item_id)
        desc_html = _el(sid, f"{item_id}-desc", "card_desc", desc, f'<div class="why-desc">{desc}</div>', "ed-el-block", overrides, item_id)
        icon_box_id = f"{item_id}-iconbox"
        icon_box_style = _element_style_attr(overrides, icon_box_id, "image_box")
        icon_html = _el(sid, f"{item_id}-icon", "image", item.get('icon', '✅'),
                         f'<div class="why-icon"{icon_box_style} data-box-id="{icon_box_id}">{item.get("icon","✅")}</div>',
                         "ed-el-block", overrides, item_id)
        card_bg = _card_bg_style_attr(overrides, item_id)
        cards += f"""
        <div class="why-card" data-section-id="{sid}" data-card-id="{item_id}"{card_bg}>
          {icon_html}
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


def _render_signature_experience(sid: str, c: dict, color: str, color2: str, overrides: dict, section_bg: str | None = None) -> str:
    """
    Luxury-only section: an editorial "signature experience" block — a
    large visual on one side, an eyebrow label + title + description on
    the other. Used by cafe_luxury_premium right after the hero, in place
    of jumping straight into a generic menu grid.
    Still exposes the full icon/box/card editable hierarchy: the visual
    box is its own card (item_id), with the icon/image inside it.
    """
    item_id = f"{sid}-signature"
    eyebrow = c.get('eyebrow', '')
    title = c.get('title', '')
    desc = c.get('desc', '')
    icon = c.get('icon', '☕')

    eyebrow_html = _el(sid, f"{item_id}-eyebrow", "subtitle", eyebrow, f'<span class="signature-eyebrow">{eyebrow}</span>', "ed-el-block", overrides, item_id)
    title_html = _el(sid, f"{item_id}-title", "card_title", title, f'<div class="signature-title">{title}</div>', "ed-el-block", overrides, item_id)
    desc_html = _el(sid, f"{item_id}-desc", "card_desc", desc, f'<div class="signature-desc">{desc}</div>', "ed-el-block", overrides, item_id)

    box_id = f"{item_id}-imgbox"
    box_style = _element_style_attr(overrides, box_id, "image_box")
    visual_html = _el(sid, f"{item_id}-img", "image", icon,
                       f'<div class="signature-visual"{box_style} data-box-id="{box_id}">{icon}</div>',
                       "ed-el-block", overrides, item_id)

    card_bg = _card_bg_style_attr(overrides, item_id)
    return f"""
    <div class="section"{_bg_style_attr(section_bg)}>
      <div class="signature-wrap" data-card-id="{item_id}"{card_bg}>
        {visual_html}
        <div class="signature-text">
          {eyebrow_html}
          {title_html}
          {desc_html}
        </div>
      </div>
    </div>"""


def _render_ambience(sid: str, c: dict, color: str, color2: str, overrides: dict, section_bg: str | None = None) -> str:
    """
    Luxury-only section: an asymmetric photo-mosaic "ambience" gallery —
    visually distinct from the plain even-grid .gallery-grid used by the
    default theme. Each tile is independently selectable/editable.
    """
    title = c.get('title', '')
    subtitle = c.get('subtitle', '')
    n = c.get("item_count", 4)
    items = ""
    for i in range(n):
        box_id = f"{sid}-amb-{i}"
        box_style = _element_style_attr(overrides, box_id, "image_box")
        items += _el(sid, box_id, "image", "تصویر فضا",
                      f'<div class="ambience-item"{box_style} data-box-id="{box_id}">📷</div>',
                      "ed-el-block", overrides)
    title_html = _el(sid, f"{sid}-title", "section_title", title, f'<div class="section-title">{title}</div>', "ed-el-block", overrides)
    subtitle_html = _el(sid, f"{sid}-subtitle", "subtitle", subtitle, f'<div class="section-sub">{subtitle}</div>', "ed-el-block", overrides)
    return f"""
    <div class="section"{_bg_style_attr(section_bg)}>
      {title_html}
      {subtitle_html}
      <div class="ambience-grid">{items}</div>
    </div>"""


_RENDERERS = {
    "navbar": _render_navbar,
    "hero": _render_hero,
    "menu_grid": _render_menu_grid,
    "task_dashboard": _render_task_dashboard,
    "team_task_board": _render_team_task_board,
    "crm_followup": _render_crm_followup,
    "gallery": _render_gallery,
    "about": _render_about,
    "benefits": _render_benefits,
    "form": _render_form,
    "cta": _render_cta,
    "footer": _render_footer,
    "signature_experience": _render_signature_experience,
    "ambience": _render_ambience,
}


# ── Section-level human-readable labels (for the change panel title when
#    the user clicks a whole section rather than one specific element) ──────

SECTION_TYPE_LABEL_FA = {
    "navbar": "هدر و منو",
    "hero": "بخش اصلی سایت",
    "menu_grid": "بخش منو",
    "task_dashboard": "بخش داشبورد وظایف",
    "team_task_board": "بخش تقسیم وظایف تیم",
    "crm_followup": "بخش پیگیری مشتری‌ها",
    "gallery": "گالری تصاویر",
    "about": "بخش درباره ما",
    "benefits": "بخش چرا ما را انتخاب کنید",
    "form": "بخش تماس / رزرو",
    "cta": "بخش دعوت به اقدام",
    "footer": "فوتر",
    "signature_experience": "بخش تجربه ویژه",
    "ambience": "بخش فضای کافه",
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

  /* ── Task Dashboard Mockup (Puzzle: preview product-type awareness) ──
     Deliberately NOT marketing-website styling — flat panels, status
     columns, a simple meetings list. */
  .dash-section {{ background:#F4F6F8; }}
  .dash-toolbar {{ display:flex; gap:12px; justify-content:center; margin-bottom:30px; flex-wrap:wrap; }}
  .dash-btn-secondary {{ background:#fff !important; color:{color} !important; border:1.5px solid {color}55 !important; }}
  .dash-board {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:18px; margin-bottom:32px; }}
  .dash-col {{ background:#fff; border-radius:{radius}; padding:16px; box-shadow:0 2px 10px rgba(45,36,36,0.06); }}
  .dash-col-title {{ font-weight:700; font-size:0.88rem; color:#4a3f3a; margin-bottom:12px; padding-bottom:8px; border-bottom:2px solid {color}33; }}
  .dash-task-card {{ background:#FAFAFA; border-radius:8px; padding:10px 12px; margin-bottom:8px; font-size:0.84rem; color:#2D2424; box-shadow:0 1px 4px rgba(0,0,0,0.05); }}
  .dash-meetings-wrap {{ background:#fff; border-radius:{radius}; padding:22px; box-shadow:0 2px 10px rgba(45,36,36,0.06); max-width:640px; margin:0 auto; }}
  .dash-meetings-title {{ font-weight:700; font-size:0.92rem; margin-bottom:14px; color:#2D2424; }}
  .dash-meeting-row {{ display:flex; gap:14px; padding:9px 0; border-bottom:1px solid #ECE2D6; font-size:0.85rem; }}
  .dash-meeting-row:last-child {{ border-bottom:none; }}
  .dash-meeting-time {{ color:{color}; font-weight:700; min-width:56px; }}
  .dash-meeting-title {{ color:#4a3f3a; }}
  .dash-empty {{ color:#8a7a6e; font-size:0.84rem; text-align:center; padding:8px 0; }}

  /* ── Customer Follow-up List Mockup (Puzzle: option propagation fix) ─ */
  .crm-section {{ background:#FAF5FF; }}
  .crm-table {{ background:#fff; border-radius:{radius}; box-shadow:0 2px 10px rgba(45,36,36,0.06); overflow:hidden; max-width:780px; margin:0 auto; }}
  .crm-row {{ display:grid; grid-template-columns:1.3fr 1.3fr 1fr 1.4fr; gap:10px; padding:13px 18px; font-size:0.84rem; border-bottom:1px solid #F1E9FB; align-items:center; }}
  .crm-row:last-child {{ border-bottom:none; }}
  .crm-header {{ background:{color}10; font-weight:700; color:#4a3f3a; font-size:0.78rem; }}
  .crm-name {{ font-weight:600; color:#2D2424; }}
  .crm-status {{ color:{color}; font-weight:600; }}
  .crm-last-contact {{ color:#8a7a6e; }}
  .crm-next-step {{ color:#4a3f3a; }}

  /* ── Team Task Board Mockup (Legacy Replacement Sprint, Phase 4) ───── */
  .team-section {{ background:#F4F6F8; }}
  .team-board {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:18px; margin-bottom:32px; }}
  .team-col {{ background:#fff; border-radius:{radius}; padding:16px; box-shadow:0 2px 10px rgba(45,36,36,0.06); }}
  .team-col-name {{ font-weight:700; font-size:0.92rem; color:#2D2424; margin-bottom:12px; padding-bottom:8px; border-bottom:2px solid {color}33; }}
  .team-task-row {{ background:#FAFAFA; border-radius:8px; padding:10px 12px; margin-bottom:8px; box-shadow:0 1px 4px rgba(0,0,0,0.05); }}
  .team-task-title {{ font-size:0.84rem; color:#2D2424; margin-bottom:4px; }}
  .team-task-deadline {{ font-size:0.74rem; color:#8a7a6e; display:inline-block; margin-left:8px; }}
  .team-task-status {{ font-size:0.74rem; color:{color}; font-weight:600; display:inline-block; }}
"""

# ── Luxury theme override (cafe_luxury_premium) ─────────────────────────────
# A REAL visual transformation on top of _BASE_CSS — dark espresso/black
# background, warm gold accents, large whitespace, editorial serif-leaning
# typography, refined/fewer cards, cinematic full-bleed hero. Appended
# after _BASE_CSS so unstyled new section types (ambience,
# signature_experience) still inherit sane defaults, while everything
# listed here visibly overrides the warm-cafe defaults.
_LUXURY_CSS_OVERRIDE = """
  body.theme-luxury {{ background:#0F0D0C; color:#EDE6DD; font-family:'Georgia','Tahoma',serif; letter-spacing:.2px; }}

  body.theme-luxury header {{ background:rgba(15,13,12,0.92); backdrop-filter:blur(10px); box-shadow:none; border-bottom:1px solid rgba(212,175,116,0.18); padding:22px 40px; }}
  body.theme-luxury .logo {{ color:{color2}; font-family:'Georgia',serif; font-size:1.4rem; letter-spacing:1px; }}
  body.theme-luxury .nav-link {{ color:#C9BCA8; font-size:.82rem; letter-spacing:.5px; }}

  body.theme-luxury .hero {{
    background:linear-gradient(180deg, rgba(15,13,12,.55) 0%, rgba(15,13,12,.85) 65%, #0F0D0C 100%), radial-gradient(circle at 50% 20%, {color}33 0%, transparent 60%);
    padding:160px 24px 150px; color:#F4EDE3;
  }}
  body.theme-luxury .hero-badge {{ background:transparent; border:1px solid {color2}; color:{color2}; letter-spacing:2px; font-size:.7rem; text-transform:uppercase; padding:7px 22px; }}
  body.theme-luxury .hero h1 {{ font-family:'Georgia',serif; font-size:3.4rem; font-weight:400; letter-spacing:1px; text-shadow:none; line-height:1.3; }}
  body.theme-luxury .hero p {{ font-size:1.05rem; color:#C9BCA8; max-width:480px; margin:0 auto 40px; opacity:1; }}
  body.theme-luxury .btn-primary {{ background:{color2}; color:#0F0D0C; border-radius:2px; padding:16px 42px; font-weight:600; letter-spacing:1px; box-shadow:none; }}
  body.theme-luxury .btn-secondary {{ background:transparent; border:1px solid #C9BCA8; color:#F4EDE3; border-radius:2px; padding:14px 38px; letter-spacing:1px; }}
  body.theme-luxury .hero-wave {{ display:none; }}

  body.theme-luxury .section {{ padding:110px 28px; max-width:1180px; }}
  body.theme-luxury .section-title {{ font-family:'Georgia',serif; font-weight:400; font-size:2.1rem; letter-spacing:.5px; color:#F4EDE3; margin-bottom:18px; }}
  body.theme-luxury .section-sub {{ color:#8C7F6E; font-size:.88rem; margin-bottom:64px; }}

  body.theme-luxury .menu-grid {{ gap:36px; grid-template-columns:repeat(auto-fit,minmax(270px,1fr)); }}
  body.theme-luxury .m-card {{ background:#1A1614; border:1px solid rgba(212,175,116,0.15); border-radius:2px; box-shadow:none; transition:border-color .2s; }}
  body.theme-luxury .m-img {{ height:140px; background:linear-gradient(135deg,{color}22,{color2}22); font-size:3rem; }}
  body.theme-luxury .m-card-body {{ padding:32px 26px; }}
  body.theme-luxury .m-name {{ font-family:'Georgia',serif; font-weight:400; font-size:1.15rem; color:#F4EDE3; }}
  body.theme-luxury .m-desc {{ color:#8C7F6E; font-size:.84rem; }}
  body.theme-luxury .m-price {{ color:{color2}; font-weight:400; font-family:'Georgia',serif; font-size:1.05rem; }}
  body.theme-luxury .m-btn {{ background:transparent; border:1px solid {color2}; color:{color2}; border-radius:2px; letter-spacing:.5px; }}

  body.theme-luxury .about-wrap {{ background:#1A1614; border:1px solid rgba(212,175,116,0.15); border-radius:2px; padding:56px; }}
  body.theme-luxury .about-icon {{ background:transparent; border:1px solid {color2}55; }}
  body.theme-luxury .about-title {{ font-family:'Georgia',serif; color:#F4EDE3; font-size:1.3rem; }}
  body.theme-luxury .about-text {{ color:#B8AB98; }}
  body.theme-luxury .feature-list li {{ color:#B8AB98; }}

  body.theme-luxury .why-grid {{ gap:48px; }}
  body.theme-luxury .why-card {{ background:transparent; box-shadow:none; border-top:1px solid rgba(212,175,116,0.25); padding-top:32px; }}
  body.theme-luxury .why-title {{ font-family:'Georgia',serif; color:#F4EDE3; }}
  body.theme-luxury .why-desc {{ color:#8C7F6E; }}

  body.theme-luxury .gallery-grid {{ gap:8px; }}
  body.theme-luxury .gallery-item {{ border-radius:2px; background:linear-gradient(135deg,{color}2a,{color2}2a); box-shadow:none; aspect-ratio:3/4; }}

  body.theme-luxury .form-wrap {{ background:#1A1614; border:1px solid rgba(212,175,116,0.2); border-radius:2px; box-shadow:none; }}
  body.theme-luxury .form-row input {{ background:#0F0D0C; border:1px solid rgba(212,175,116,0.25); color:#F4EDE3; border-radius:2px; }}
  body.theme-luxury .form-submit {{ background:{color2}; color:#0F0D0C; border-radius:2px; letter-spacing:1px; }}

  body.theme-luxury .cta {{ background:#1A1614; border-top:1px solid rgba(212,175,116,0.2); border-bottom:1px solid rgba(212,175,116,0.2); padding:96px 24px; }}
  body.theme-luxury .cta h2 {{ font-family:'Georgia',serif; font-weight:400; font-size:1.9rem; }}
  body.theme-luxury .cta p {{ color:#8C7F6E; }}

  body.theme-luxury footer {{ background:#0F0D0C; color:#6B6259; border-top:1px solid rgba(212,175,116,0.15); padding:48px 24px; }}
  body.theme-luxury footer .footer-logo {{ color:{color2}; font-family:'Georgia',serif; }}

  /* New luxury-only sections */
  body.theme-luxury .signature-wrap {{ display:grid; grid-template-columns:1fr 1fr; gap:56px; align-items:center; }}
  body.theme-luxury .signature-visual {{ aspect-ratio:4/5; background:linear-gradient(135deg,{color}2a,{color2}2a); border-radius:2px; display:flex; align-items:center; justify-content:center; font-size:3.5rem; }}
  body.theme-luxury .signature-text {{ }}
  body.theme-luxury .signature-eyebrow {{ color:{color2}; font-size:.75rem; letter-spacing:2px; text-transform:uppercase; margin-bottom:16px; display:block; }}
  body.theme-luxury .signature-title {{ font-family:'Georgia',serif; font-size:2rem; font-weight:400; color:#F4EDE3; margin-bottom:18px; }}
  body.theme-luxury .signature-desc {{ color:#B8AB98; line-height:1.9; font-size:.95rem; }}
  @media (max-width:760px) {{ body.theme-luxury .signature-wrap {{ grid-template-columns:1fr; }} }}

  body.theme-luxury .ambience-grid {{ display:grid; grid-template-columns:1.3fr 1fr 1fr; gap:10px; grid-auto-rows:160px; }}
  body.theme-luxury .ambience-item {{ background:linear-gradient(135deg,{color}26,{color2}26); border-radius:2px; display:flex; align-items:center; justify-content:center; font-size:2.2rem; }}
  body.theme-luxury .ambience-item:first-child {{ grid-row:span 2; }}
"""

_INTERACTION_JS = """
window.__selectElement = function(el, ev) {
  if (ev) ev.stopPropagation();
  document.querySelectorAll('.ed-selected').forEach(e => e.classList.remove('ed-selected'));
  el.classList.add('ed-selected');
  const sectionEl = el.closest('.ed-section');
  const sectionId = sectionEl ? sectionEl.getAttribute('data-section-id') : null;
  const sectionType = sectionEl ? sectionEl.getAttribute('data-section-type') : null;
  // Layer hierarchy: the exact clicked element may sit inside a "box"
  // (e.g. the colored square behind an icon) which itself sits inside a
  // card. Both ids are exposed so the user can choose which layer they
  // actually meant — "خود آیکون" / "باکس تصویر" / "کارت" — instead of
  // only ever editing the exact element under the cursor.
  const boxEl = ev && ev.target ? ev.target.closest('[data-box-id]') : null;
  const boxId = boxEl ? boxEl.getAttribute('data-box-id') : null;
  const cardId = el.getAttribute('data-card-id');
  if (window.parent) {
    window.parent.postMessage({
      type: 'element-selected',
      elementId: el.getAttribute('data-element-id'),
      elementType: el.getAttribute('data-element-type'),
      elementText: el.getAttribute('data-element-text'),
      boxId: boxId,
      cardId: cardId,
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
      boxId: null,
      cardId: null,
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

