"""
Section Renderer — Website Builder v3.

Renders the section-block model (section_model.py) into a single HTML
document. Every section wrapper carries:
  - data-section-id  → for click-to-select in the parent frame
  - data-section-type → for the editor panel to know which fields to show

The parent page (index.html) listens for clicks inside the iframe via
postMessage (injected script at the bottom of this document) and opens
the right-side editor panel accordingly.
"""
from __future__ import annotations
from typing import Any


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
        section_html = renderer(sec["content"], color, color2)
        body_html += (
            f'<div class="ed-section" data-section-id="{sec["id"]}" '
            f'data-section-type="{sec["type"]}" onclick="window.__selectSection(\'{sec["id"]}\', event)">'
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


# ── Per-section-type renderers ──────────────────────────────────────────────

def _render_navbar(c: dict, color: str, color2: str) -> str:
    nav_html = "".join(
        f'<a href="#sec-{i}" class="nav-link">{n}</a>'
        for i, n in enumerate(c.get("nav_items", []))
    )
    return f"""
    <header>
      <div class="logo">{c.get('logo_text','')}</div>
      <nav>{nav_html}</nav>
    </header>"""


def _render_hero(c: dict, color: str, color2: str) -> str:
    btn2 = f'<button class="btn-secondary">{c["secondary_button"]}</button>' if c.get("secondary_button") else ""
    return f"""
    <div class="hero">
      <div class="hero-inner">
        <div class="hero-badge">{c.get('badge','')}</div>
        <h1>{c.get('title','')}</h1>
        <p>{c.get('subtitle','')}</p>
        <div class="hero-btns">
          <button class="btn-primary">{c.get('primary_button','')}</button>
          {btn2}
        </div>
      </div>
      <div class="hero-wave"></div>
    </div>"""


def _render_menu_grid(c: dict, color: str, color2: str) -> str:
    cards = ""
    for item in c.get("items", []):
        price_html = f'<div class="m-price">{item.get("price","")}</div>' if item.get("price") else ""
        cards += f"""
        <div class="m-card">
          <div class="m-img">{item.get('icon','✨')}</div>
          <div class="m-card-body">
            <div class="m-name">{item.get('name','')}</div>
            <div class="m-desc">{item.get('desc','')}</div>
            {price_html}
            <button class="m-btn">انتخاب</button>
          </div>
        </div>"""
    return f"""
    <div class="section">
      <div class="section-title">{c.get('title','')}</div>
      <div class="section-sub">{c.get('subtitle','')}</div>
      <div class="menu-grid">{cards}</div>
    </div>"""


def _render_gallery(c: dict, color: str, color2: str) -> str:
    n = c.get("item_count", 4)
    items = "".join('<div class="gallery-item">📷</div>' for _ in range(n))
    return f"""
    <div class="section">
      <div class="section-title">{c.get('title','')}</div>
      <div class="section-sub">{c.get('subtitle','')}</div>
      <div class="gallery-grid">{items}</div>
    </div>"""


def _render_about(c: dict, color: str, color2: str) -> str:
    feats = "".join(f'<li>✓ {f}</li>' for f in c.get("features", []))
    return f"""
    <div class="section">
      <div class="about-wrap">
        <div class="about-icon">🏪</div>
        <div class="about-text">
          <div class="about-title">{c.get('title','')}</div>
          {c.get('body','')}
          <ul class="feature-list">{feats}</ul>
        </div>
      </div>
    </div>"""


def _render_benefits(c: dict, color: str, color2: str) -> str:
    cards = ""
    for item in c.get("items", []):
        cards += f"""
        <div class="why-card">
          <div class="why-icon">{item.get('icon','✅')}</div>
          <div class="why-title">{item.get('title','')}</div>
          <div class="why-desc">{item.get('desc','')}</div>
        </div>"""
    return f"""
    <div class="section">
      <div class="section-title">{c.get('title','')}</div>
      <div class="section-sub">{c.get('subtitle','')}</div>
      <div class="why-grid">{cards}</div>
    </div>"""


def _render_form(c: dict, color: str, color2: str) -> str:
    return f"""
    <div class="section">
      <div class="section-title">{c.get('title','')}</div>
      <div class="section-sub">{c.get('subtitle','')}</div>
      <div class="form-wrap">
        <div class="form-row"><label>نام</label><input type="text" placeholder="نام شما"></div>
        <div class="form-row"><label>شماره تماس</label><input type="text" placeholder="۰۹۱۲xxxxxxx"></div>
        <div class="form-row"><label>تاریخ و زمان</label><input type="text" placeholder="مثلاً امشب ساعت ۸"></div>
        <button class="form-submit" onclick="event.stopPropagation();window.__mockSubmit()">{c.get('submit_label','ثبت')}</button>
        <div class="confirm-box" id="confirmBox">✓ درخواست شما ثبت شد! به‌زودی با شما تماس می‌گیریم.</div>
      </div>
    </div>"""


def _render_cta(c: dict, color: str, color2: str) -> str:
    return f"""
    <div class="cta">
      <h2>{c.get('title','')}</h2>
      <p>{c.get('subtitle','')}</p>
      <button class="btn-primary">{c.get('button_label','')}</button>
    </div>"""


def _render_footer(c: dict, color: str, color2: str) -> str:
    return f"""
    <footer>
      <div class="footer-logo">{c.get('site_name','')}</div>
      <div>{c.get('tagline','')}</div>
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


# ── Shared CSS (parameterized by global style) ──────────────────────────────

_BASE_CSS = """
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html {{ scroll-behavior:smooth; }}
  body {{ font-family:{font}; background:#FBF7F0; color:#2D2424; direction:rtl; line-height:1.7; }}

  .ed-section {{ position:relative; cursor:pointer; transition:outline .15s; }}
  .ed-section:hover {{ outline:2px dashed {color}80; outline-offset:-2px; }}

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

  .ed-selected {{ outline:3px solid {color} !important; outline-offset:-3px; }}
"""

_INTERACTION_JS = """
window.__selectSection = function(id, ev) {
  if (ev) ev.stopPropagation();
  document.querySelectorAll('.ed-section').forEach(el => el.classList.remove('ed-selected'));
  const el = document.querySelector('[data-section-id="' + id + '"]');
  if (el) el.classList.add('ed-selected');
  if (window.parent) {
    window.parent.postMessage({ type: 'section-selected', sectionId: id }, '*');
  }
};
window.__mockSubmit = function() {
  const box = document.getElementById('confirmBox');
  if (box) box.style.display = 'block';
};
"""
