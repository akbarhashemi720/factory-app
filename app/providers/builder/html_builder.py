"""
HTML Builder — Builder v1.

Generates a real HTML/CSS preview for each product type.
Scenario-aware: different HTML for education, restaurant, booking, etc.
Safe to render inside iframe (srcdoc) — no external dependencies.

When Anthropic API is active, this module can receive structured Claude output
instead of mock data and generate richer previews.
"""
from __future__ import annotations
from typing import Any


# ── Public interface ──────────────────────────────────────────────────────────

def generate(
    project: dict,
    understanding: dict,
    scenario_pattern: dict | None = None,
) -> dict[str, Any]:
    """Generate a real HTML/CSS preview based on understanding."""

    scenario = (
        understanding.get("detected_scenario")
        or project.get("scenario")
        or "general"
    )

    bullets   = understanding.get("bullets", [])
    business  = understanding.get("business_domain", "")
    goal      = understanding.get("primary_goal", "")

    # Build structured spec from understanding
    spec = _build_spec(scenario, bullets, business, goal, understanding)

    # Generate HTML preview from spec
    html = _render_html(spec)

    return {
        "preview_data": {
            "scenario":      scenario,
            "title":         spec["name"],
            "subtitle":      spec["tagline"],
            "product_type":  spec["type"],
            "sections":      spec["sections"],
            "features":      spec.get("features", []),
            "html_preview":  html,
            "_is_html_preview": True,
        },
        "change_summary": [
            f"پیش‌نمایش اولیه «{spec['name']}» آماده شد",
            f"نوع محصول: {spec['type']}",
            "این پیش‌نمایش اولیه است — در مراحل بعد می‌توانی تغییر دهی",
        ],
        "known_limitations": [
            "این پیش‌نمایش اولیه است، نه محصول نهایی آماده",
            "محتوای واقعی و تصاویر در مراحل بعد اضافه می‌شود",
        ],
    }


# ── Spec builder — maps scenario to product spec ──────────────────────────────

def _build_spec(scenario: str, bullets: list, business: str, goal: str, und: dict) -> dict:
    """Build a structured product spec based on scenario."""

    SPECS = {
        "general_class": {
            "name":     "آموزشگاه آنلاین",
            "tagline":  "یادگیری ساده‌تر، دسترسی آسان‌تر",
            "type":     "سایت آموزشی",
            "color":    "#4F46E5",
            "hero_btn": "مشاهده دوره‌ها",
            "sections": ["دوره‌های ما", "مزایا", "ثبت‌نام", "تماس"],
            "features": ["لیست دوره‌ها", "ثبت‌نام آنلاین", "جدول زمانی", "اطلاعات مدرس"],
            "cards": [
                {"icon": "📚", "title": "دوره مقدماتی", "desc": "برای تازه‌کارها"},
                {"icon": "🎯", "title": "دوره پیشرفته", "desc": "برای علاقه‌مندان"},
                {"icon": "🏆", "title": "دوره ویژه", "desc": "با مدرک معتبر"},
            ],
        },
        "restaurant": {
            "name":     "رستوران آنلاین",
            "tagline":  "سفارش آسان، طعم عالی",
            "type":     "سایت سفارش غذا",
            "color":    "#E85D04",
            "hero_btn": "مشاهده منو",
            "sections": ["منو", "پیشنهاد ویژه", "ثبت سفارش", "تماس"],
            "features": ["منو آنلاین", "ثبت سفارش", "پیگیری سفارش", "پنل مدیریت"],
            "cards": [
                {"icon": "🍕", "title": "پیتزا ویژه", "desc": "۸۵,۰۰۰ تومان"},
                {"icon": "🍔", "title": "برگر خاص", "desc": "۶۵,۰۰۰ تومان"},
                {"icon": "🥗", "title": "سالاد تازه", "desc": "۴۵,۰۰۰ تومان"},
            ],
        },
        "booking": {
            "name":     "رزرو آنلاین",
            "tagline":  "نوبت بگیر، بدون معطلی",
            "type":     "سیستم رزرو نوبت",
            "color":    "#0EA5E9",
            "hero_btn": "رزرو نوبت",
            "sections": ["خدمات", "نحوه رزرو", "ساعات کاری", "تماس"],
            "features": ["رزرو آنلاین", "یادآور خودکار", "مدیریت نوبت‌ها", "پروفایل مشتری"],
            "cards": [
                {"icon": "✂️", "title": "کوتاهی مو", "desc": "۴۵ دقیقه"},
                {"icon": "🧔", "title": "اصلاح ریش", "desc": "۳۰ دقیقه"},
                {"icon": "💆", "title": "ماساژ سر", "desc": "۲۰ دقیقه"},
            ],
        },
        "telegram_bot": {
            "name":     "ربات هوشمند",
            "tagline":  "خدمات شما، همیشه در دسترس",
            "type":     "ربات پیام‌رسان",
            "color":    "#0088CC",
            "hero_btn": "شروع استفاده",
            "sections": ["چه کاری می‌کند", "خدمات", "مراحل استفاده", "تماس"],
            "features": ["پاسخ خودکار", "رزرو نوبت", "ارسال اطلاعات", "پشتیبانی ۲۴ ساعته"],
            "cards": [
                {"icon": "🤖", "title": "پاسخ سریع", "desc": "بدون معطلی"},
                {"icon": "📅", "title": "رزرو آسان", "desc": "در چند ثانیه"},
                {"icon": "💬", "title": "پشتیبانی", "desc": "همیشه آماده"},
            ],
        },
        "store": {
            "name":     "فروشگاه آنلاین",
            "tagline":  "خرید آسان، تحویل سریع",
            "type":     "فروشگاه اینترنتی",
            "color":    "#10B981",
            "hero_btn": "مشاهده محصولات",
            "sections": ["محصولات", "پیشنهاد ویژه", "سبد خرید", "تماس"],
            "features": ["نمایش محصولات", "سبد خرید", "پرداخت آنلاین", "پیگیری سفارش"],
            "cards": [
                {"icon": "🛍️", "title": "محصول ۱", "desc": "۱۲۰,۰۰۰ تومان"},
                {"icon": "🎁", "title": "محصول ۲", "desc": "۸۵,۰۰۰ تومان"},
                {"icon": "⭐", "title": "محصول ۳", "desc": "۶۵,۰۰۰ تومان"},
            ],
        },
    }

    spec = SPECS.get(scenario, {
        "name":     "محصول شما",
        "tagline":  "آماده برای کاربران شما",
        "type":     "وب‌سایت",
        "color":    "#6366F1",
        "hero_btn": "شروع کنید",
        "sections": ["معرفی", "خدمات", "تماس"],
        "features": ["صفحه اصلی", "معرفی خدمات", "فرم تماس"],
        "cards": [
            {"icon": "✨", "title": "ویژگی ۱", "desc": "توضیح کوتاه"},
            {"icon": "🚀", "title": "ویژگی ۲", "desc": "توضیح کوتاه"},
            {"icon": "💡", "title": "ویژگی ۳", "desc": "توضیح کوتاه"},
        ],
    })

    # Override with real data if available from Anthropic
    if und.get("business_domain"):
        spec["name"] = _extract_name(und["business_domain"], spec["name"])
    if bullets:
        spec["bullets"] = bullets

    return spec


def _extract_name(domain: str, fallback: str) -> str:
    """Extract a good product name from business domain."""
    if not domain or len(domain) < 3:
        return fallback
    # Use domain as name if short enough
    if len(domain) <= 20:
        return domain
    return fallback


# ── HTML renderer ─────────────────────────────────────────────────────────────

def _render_html(spec: dict) -> str:
    """Render a complete HTML/CSS page from product spec."""

    color   = spec.get("color", "#6366F1")
    name    = spec.get("name", "محصول شما")
    tagline = spec.get("tagline", "")
    hero_btn= spec.get("hero_btn", "شروع")
    cards   = spec.get("cards", [])
    sections= spec.get("sections", [])
    features= spec.get("features", [])
    ptype   = spec.get("type", "")

    # Build cards HTML
    cards_html = ""
    for c in cards:
        cards_html += f"""
        <div style="background:#fff;border-radius:12px;padding:24px;box-shadow:0 2px 12px rgba(0,0,0,0.08);text-align:center">
          <div style="font-size:2rem;margin-bottom:12px">{c['icon']}</div>
          <div style="font-weight:700;font-size:1rem;margin-bottom:8px;color:#1a1a2e">{c['title']}</div>
          <div style="color:#666;font-size:0.875rem">{c['desc']}</div>
        </div>"""

    # Build features HTML
    features_html = ""
    for f in features:
        features_html += f"""
        <div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #f0f0f0">
          <span style="color:{color};font-size:1.1rem">✓</span>
          <span style="color:#333;font-size:0.9rem">{f}</span>
        </div>"""

    # Build sections pills
    sections_html = ""
    for s in sections:
        sections_html += f'<span style="background:rgba(255,255,255,0.2);padding:6px 16px;border-radius:20px;font-size:0.85rem">{s}</span>'

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:Tahoma,Arial,sans-serif; background:#f8f9fa; color:#333; direction:rtl; }}
  .hero {{ background:linear-gradient(135deg, {color}, {color}dd); color:#fff; padding:48px 24px; text-align:center; }}
  .hero h1 {{ font-size:1.8rem; font-weight:800; margin-bottom:12px; }}
  .hero p {{ font-size:1rem; opacity:0.9; margin-bottom:24px; }}
  .hero-btn {{ background:#fff; color:{color}; border:none; padding:12px 32px; border-radius:25px; font-size:1rem; font-weight:700; cursor:pointer; }}
  .nav {{ display:flex; gap:12px; justify-content:center; flex-wrap:wrap; margin-top:20px; }}
  .section {{ padding:40px 24px; max-width:900px; margin:0 auto; }}
  .section-title {{ font-size:1.3rem; font-weight:700; color:#1a1a2e; margin-bottom:24px; text-align:center; }}
  .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:16px; }}
  .cta {{ background:{color}; color:#fff; padding:40px 24px; text-align:center; }}
  .cta-btn {{ background:#fff; color:{color}; border:none; padding:14px 40px; border-radius:25px; font-size:1rem; font-weight:700; cursor:pointer; }}
  .badge {{ display:inline-block; background:{color}22; color:{color}; padding:4px 12px; border-radius:12px; font-size:0.8rem; margin-bottom:12px; }}
</style>
</head>
<body>

<div class="hero">
  <div class="badge">پیش‌نمایش اولیه • {ptype}</div>
  <h1>{name}</h1>
  <p>{tagline}</p>
  <button class="hero-btn">{hero_btn}</button>
  <div class="nav">{sections_html}</div>
</div>

<div class="section">
  <div class="section-title">امکانات اصلی</div>
  <div class="cards">{cards_html}</div>
</div>

<div class="section">
  <div class="section-title">آنچه این نسخه شامل می‌شود</div>
  <div style="background:#fff;border-radius:12px;padding:24px;box-shadow:0 2px 12px rgba(0,0,0,0.05)">
    {features_html}
  </div>
</div>

<div class="cta">
  <div style="font-size:1.2rem;font-weight:700;margin-bottom:8px">آماده ادامه هستید؟</div>
  <div style="opacity:0.9;margin-bottom:20px;font-size:0.9rem">این پیش‌نمایش اولیه است — می‌توانید تغییر دهید یا تأیید کنید</div>
  <button class="cta-btn">تأیید و ادامه</button>
</div>

</body>
</html>"""
