"""
HTML Builder — Builder v1 (Rich Edition).

Generates a real, visually rich HTML/CSS preview for each product type.
Scenario-aware: full landing pages with hero, menu/courses, gallery, contact, footer.
Safe to render inside iframe (srcdoc) — no external dependencies.
"""
from __future__ import annotations
from typing import Any


def generate(
    project: dict,
    understanding: dict,
    scenario_pattern: dict | None = None,
) -> dict[str, Any]:
    """Generate a rich HTML/CSS preview based on understanding."""

    scenario = (
        understanding.get("detected_scenario")
        or project.get("scenario")
        or "general"
    )

    spec = _build_spec(scenario, understanding)
    html = _render_html(spec)

    return {
        "preview_data": {
            "scenario":      scenario,
            "title":         spec["name"],
            "subtitle":      spec["tagline"],
            "product_type":  spec["type"],
            "sections":      spec["nav_items"],
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


# ── Spec builder ───────────────────────────────────────────────────────────────

def _build_spec(scenario: str, und: dict) -> dict:
    SPECS = {
        "restaurant": _restaurant_spec(),
        "general_class": _education_spec(),
        "booking": _booking_spec(),
        "telegram_bot": _booking_spec(bot=True),
        "store": _store_spec(),
    }
    spec = SPECS.get(scenario, _general_spec())

    if und.get("business_domain") and len(und["business_domain"]) <= 24:
        spec["name"] = und["business_domain"]

    return spec


def _restaurant_spec():
    return {
        "name": "کافه و رستوران آرام",
        "tagline": "قهوه تازه، طعم اصیل، فضای دلنشین",
        "type": "سایت معرفی و سفارش غذا",
        "color": "#C2410C",
        "color2": "#FB923C",
        "hero_btn": "مشاهده منو",
        "hero_btn2": "رزرو میز",
        "nav_items": ["خانه", "منو", "درباره ما", "رزرو", "تماس"],
        "features": ["منو آنلاین کامل", "ثبت سفارش از سایت", "رزرو میز آنلاین", "پنل مدیریت سفارش‌ها"],
        "menu_items": [
            {"icon":"🍕","name":"پیتزا مخصوص","desc":"پنیر، قارچ، فلفل دلمه‌ای","price":"۸۵,۰۰۰"},
            {"icon":"🍔","name":"برگر ویژه","desc":"گوشت گریل، سس مخصوص","price":"۶۵,۰۰۰"},
            {"icon":"☕","name":"قهوه تخصصی","desc":"دانه برزیلی تازه آسیاب","price":"۳۵,۰۰۰"},
            {"icon":"🥗","name":"سالاد سزار","desc":"مرغ گریل، سس سزار خانگی","price":"۴۵,۰۰۰"},
            {"icon":"🍰","name":"کیک شکلاتی","desc":"دستپخت روزانه","price":"۴۰,۰۰۰"},
            {"icon":"🍝","name":"پاستا آلفردو","desc":"کرم چیز، قارچ، مرغ","price":"۷۵,۰۰۰"},
        ],
        "why_us": [
            {"icon":"⭐","title":"کیفیت بالا","desc":"مواد اولیه تازه و باکیفیت"},
            {"icon":"⚡","title":"سفارش سریع","desc":"تحویل در کمترین زمان"},
            {"icon":"❤️","title":"طعم اصیل","desc":"دستور پخت اختصاصی"},
        ],
        "about": "ما با عشق و دقت، هر روز بهترین مواد اولیه را برای شما آماده می‌کنیم تا تجربه‌ای خاص از غذا خوردن داشته باشید.",
    }


def _education_spec():
    return {
        "name": "آموزشگاه زبان نوین",
        "tagline": "یادگیری شیرین‌تر، آینده روشن‌تر",
        "type": "سایت آموزشی",
        "color": "#4338CA",
        "color2": "#818CF8",
        "hero_btn": "مشاهده دوره‌ها",
        "hero_btn2": "ثبت‌نام رایگان",
        "nav_items": ["خانه", "دوره‌ها", "روش تدریس", "ثبت‌نام", "تماس"],
        "features": ["لیست کامل دوره‌ها", "ثبت‌نام آنلاین", "جدول زمانی کلاس‌ها", "پیگیری پیشرفت دانش‌آموز"],
        "menu_items": [
            {"icon":"🐣","name":"دوره مقدماتی کودکان","desc":"۴ تا ۷ سال، آموزش بازی‌محور","price":"ماهانه"},
            {"icon":"📘","name":"دوره پایه","desc":"۸ تا ۱۲ سال، تقویت مکالمه","price":"ماهانه"},
            {"icon":"🎯","name":"دوره پیشرفته","desc":"نوجوانان، آمادگی آزمون","price":"ماهانه"},
            {"icon":"🗣️","name":"کلاس مکالمه","desc":"تمرین با مدرس بومی","price":"جلسه‌ای"},
            {"icon":"📝","name":"آماده‌سازی آیلتس","desc":"بزرگسالان، نمره‌محور","price":"ماهانه"},
            {"icon":"🏆","name":"دوره ویژه VIP","desc":"خصوصی، برنامه اختصاصی","price":"توافقی"},
        ],
        "why_us": [
            {"icon":"👩‍🏫","title":"مدرسین مجرب","desc":"سال‌ها تجربه آموزش کودکان"},
            {"icon":"🎮","title":"یادگیری بازی‌محور","desc":"آموزش از طریق بازی و سرگرمی"},
            {"icon":"📊","title":"پیگیری پیشرفت","desc":"گزارش منظم به والدین"},
        ],
        "about": "هدف ما ساختن پایه‌ای قوی برای یادگیری زبان انگلیسی در محیطی شاد و امن برای کودکان است.",
    }


def _booking_spec(bot=False):
    return {
        "name": "آرایشگاه سلطانی" if not bot else "ربات رزرو هوشمند",
        "tagline": "نوبت بگیر، بدون معطلی، بدون تماس",
        "type": "سیستم رزرو نوبت" if not bot else "ربات رزرو نوبت",
        "color": "#0E7490",
        "color2": "#22D3EE",
        "hero_btn": "رزرو نوبت",
        "hero_btn2": "مشاهده خدمات",
        "nav_items": ["خانه", "خدمات", "نحوه رزرو", "ساعات کاری", "تماس"],
        "features": ["رزرو آنلاین ۲۴ ساعته", "یادآور خودکار نوبت", "مدیریت نوبت‌های روزانه", "تاریخچه مشتری"],
        "menu_items": [
            {"icon":"✂️","name":"کوتاهی مو","desc":"مدل‌های روز، مشاوره رایگان","price":"۴۵ دقیقه"},
            {"icon":"🧔","name":"اصلاح و فرم ریش","desc":"اصلاح دقیق با تیغ گرم","price":"۳۰ دقیقه"},
            {"icon":"💆","name":"ماساژ سر و صورت","desc":"آرامش‌بخش، رفع خستگی","price":"۲۰ دقیقه"},
            {"icon":"💇","name":"رنگ مو","desc":"محصولات بدون آمونیاک","price":"۹۰ دقیقه"},
            {"icon":"🪒","name":"اصلاح صورت","desc":"پاکسازی و اصلاح کامل","price":"۲۵ دقیقه"},
            {"icon":"👔","name":"پکیج داماد","desc":"کامل: مو، ریش، پاکسازی","price":"۱۲۰ دقیقه"},
        ],
        "why_us": [
            {"icon":"⏱️","title":"بدون معطلی","desc":"رزرو دقیق، بدون انتظار"},
            {"icon":"📱","title":"یادآور خودکار","desc":"پیام یادآوری قبل از نوبت"},
            {"icon":"⭐","title":"کیفیت تضمینی","desc":"آرایشگران حرفه‌ای و مجرب"},
        ],
        "about": "با بیش از ده سال تجربه، بهترین خدمات آرایشی مردانه را با کیفیت بالا و قیمت مناسب ارائه می‌دهیم.",
    }


def _store_spec():
    return {
        "name": "فروشگاه آنلاین برتر",
        "tagline": "خرید آسان، تحویل سریع، کیفیت تضمینی",
        "type": "فروشگاه اینترنتی",
        "color": "#15803D",
        "color2": "#4ADE80",
        "hero_btn": "مشاهده محصولات",
        "hero_btn2": "پیشنهادهای ویژه",
        "nav_items": ["خانه", "محصولات", "تخفیف‌ها", "سبد خرید", "تماس"],
        "features": ["نمایش محصولات با تصویر", "سبد خرید آنلاین", "پرداخت امن", "پیگیری سفارش"],
        "menu_items": [
            {"icon":"👕","name":"تیشرت کلاسیک","desc":"نخ پنبه، رنگ‌بندی متنوع","price":"۱۲۰,۰۰۰"},
            {"icon":"👜","name":"کیف چرم","desc":"چرم طبیعی، دست‌دوز","price":"۸۵۰,۰۰۰"},
            {"icon":"⌚","name":"ساعت مردانه","desc":"ضدآب، گارانتی یک‌ساله","price":"۴۵۰,۰۰۰"},
            {"icon":"👟","name":"کفش اسپرت","desc":"سایزبندی کامل","price":"۶۵۰,۰۰۰"},
            {"icon":"🎒","name":"کوله پشتی","desc":"ضدآب، جادار","price":"۲۸۰,۰۰۰"},
            {"icon":"🕶️","name":"عینک آفتابی","desc":"محافظ UV، طراحی مدرن","price":"۱۹۰,۰۰۰"},
        ],
        "why_us": [
            {"icon":"🚚","title":"ارسال سریع","desc":"تحویل ۱ تا ۲ روز کاری"},
            {"icon":"🔒","title":"خرید امن","desc":"پرداخت با درگاه معتبر"},
            {"icon":"↩️","title":"ضمانت بازگشت","desc":"۷ روز ضمانت بازگشت کالا"},
        ],
        "about": "ما محصولات با کیفیت را با بهترین قیمت و سریع‌ترین زمان ارسال، مستقیم به دست شما می‌رسانیم.",
    }


def _general_spec():
    return {
        "name": "محصول شما",
        "tagline": "ساده، سریع، حرفه‌ای",
        "type": "وب‌سایت",
        "color": "#4F46E5",
        "color2": "#818CF8",
        "hero_btn": "شروع کنید",
        "hero_btn2": "اطلاعات بیشتر",
        "nav_items": ["خانه", "خدمات", "درباره ما", "تماس"],
        "features": ["صفحه اصلی حرفه‌ای", "معرفی کامل خدمات", "فرم تماس آسان"],
        "menu_items": [
            {"icon":"✨","name":"ویژگی یک","desc":"توضیح کوتاه ویژگی","price":""},
            {"icon":"🚀","name":"ویژگی دو","desc":"توضیح کوتاه ویژگی","price":""},
            {"icon":"💡","name":"ویژگی سه","desc":"توضیح کوتاه ویژگی","price":""},
        ],
        "why_us": [
            {"icon":"✅","title":"ساده و سریع","desc":"تجربه کاربری روان"},
            {"icon":"🔒","title":"امن و مطمئن","desc":"حفظ اطلاعات کاربران"},
            {"icon":"📞","title":"پشتیبانی","desc":"همیشه در دسترس"},
        ],
        "about": "ما محصولی ساده و کاربردی می‌سازیم که دقیقاً نیاز شما را برطرف می‌کند.",
    }


# ── HTML renderer ────────────────────────────────────────────────────────────

def _render_html(spec: dict) -> str:
    color, color2 = spec["color"], spec["color2"]
    name, tagline = spec["name"], spec["tagline"]
    ptype = spec["type"]

    section_ids = ["home", "menu", "gallery", "about", "reserve", "contact"]
    nav_html = ""
    for i, n in enumerate(spec["nav_items"]):
        target = section_ids[i] if i < len(section_ids) else "home"
        nav_html += f'<a href="#{target}" class="nav-link">{n}</a>'

    menu_html = ""
    for m in spec["menu_items"]:
        price_html = f'<div class="m-price">{m["price"]}</div>' if m["price"] else ""
        menu_html += f"""
        <div class="m-card">
          <div class="m-icon">{m['icon']}</div>
          <div class="m-name">{m['name']}</div>
          <div class="m-desc">{m['desc']}</div>
          {price_html}
          <button class="m-btn" onclick="mockSelect('{m['name']}')">انتخاب</button>
        </div>"""

    why_html = ""
    for w in spec["why_us"]:
        why_html += f"""
        <div class="why-card">
          <div class="why-icon">{w['icon']}</div>
          <div class="why-title">{w['title']}</div>
          <div class="why-desc">{w['desc']}</div>
        </div>"""

    features_html = "".join(f'<li>✓ {f}</li>' for f in spec.get("features", []))

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html {{ scroll-behavior:smooth; }}
  body {{ font-family:Tahoma,Arial,sans-serif; background:#fafafa; color:#1f2937; direction:rtl; line-height:1.6; }}

  header {{ position:sticky; top:0; background:#fff; box-shadow:0 1px 8px rgba(0,0,0,0.06); z-index:10; padding:14px 24px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; }}
  .logo {{ font-weight:800; font-size:1.1rem; color:{color}; }}
  .nav-link {{ color:#444; text-decoration:none; font-size:0.85rem; margin:0 8px; }}

  .hero {{ background:linear-gradient(135deg,{color},{color2}); color:#fff; padding:64px 24px; text-align:center; }}
  .hero-badge {{ display:inline-block; background:rgba(255,255,255,0.25); padding:5px 14px; border-radius:14px; font-size:0.75rem; margin-bottom:16px; }}
  .hero h1 {{ font-size:2rem; font-weight:800; margin-bottom:10px; }}
  .hero p {{ font-size:1.05rem; opacity:0.95; margin-bottom:26px; }}
  .hero-btns {{ display:flex; gap:12px; justify-content:center; flex-wrap:wrap; }}
  .btn-primary {{ background:#fff; color:{color}; border:none; padding:13px 30px; border-radius:25px; font-size:0.95rem; font-weight:700; cursor:pointer; }}
  .btn-secondary {{ background:transparent; color:#fff; border:2px solid rgba(255,255,255,0.7); padding:11px 28px; border-radius:25px; font-size:0.95rem; font-weight:700; cursor:pointer; }}

  .section {{ padding:56px 24px; max-width:1080px; margin:0 auto; }}
  .section-title {{ font-size:1.5rem; font-weight:800; text-align:center; margin-bottom:8px; color:#111827; }}
  .section-sub {{ text-align:center; color:#6b7280; font-size:0.9rem; margin-bottom:36px; }}

  .menu-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:20px; }}
  .m-card {{ background:#fff; border-radius:14px; padding:22px; box-shadow:0 2px 14px rgba(0,0,0,0.06); text-align:center; transition:transform .2s; }}
  .m-icon {{ font-size:2.2rem; margin-bottom:10px; }}
  .m-name {{ font-weight:700; font-size:1rem; margin-bottom:6px; }}
  .m-desc {{ color:#6b7280; font-size:0.82rem; margin-bottom:10px; min-height:32px; }}
  .m-price {{ color:{color}; font-weight:700; font-size:0.95rem; margin-bottom:12px; }}
  .m-btn {{ background:{color}; color:#fff; border:none; padding:8px 22px; border-radius:18px; font-size:0.82rem; cursor:pointer; }}

  .about-wrap {{ background:#fff; border-radius:18px; padding:36px; box-shadow:0 2px 14px rgba(0,0,0,0.05); display:flex; gap:28px; align-items:center; flex-wrap:wrap; }}
  .about-icon {{ font-size:3.5rem; flex-shrink:0; }}
  .about-text {{ flex:1; min-width:240px; color:#374151; font-size:0.92rem; }}
  .feature-list {{ list-style:none; margin-top:16px; }}
  .feature-list li {{ padding:6px 0; color:#374151; font-size:0.88rem; }}

  .why-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:20px; }}
  .why-card {{ text-align:center; padding:20px; }}
  .why-icon {{ font-size:2.4rem; margin-bottom:10px; }}
  .why-title {{ font-weight:700; margin-bottom:6px; }}
  .why-desc {{ color:#6b7280; font-size:0.85rem; }}

  .gallery-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:14px; }}
  .gallery-item {{ aspect-ratio:1; border-radius:14px; background:linear-gradient(135deg,{color}22,{color2}22); display:flex; align-items:center; justify-content:center; font-size:2rem; color:{color}; }}

  .form-wrap {{ background:#fff; border-radius:16px; padding:32px; box-shadow:0 2px 14px rgba(0,0,0,0.06); max-width:480px; margin:0 auto; }}
  .form-row {{ margin-bottom:14px; }}
  .form-row label {{ display:block; font-size:0.82rem; margin-bottom:5px; color:#374151; font-weight:600; }}
  .form-row input, .form-row select {{ width:100%; padding:10px 12px; border:1px solid #e5e7eb; border-radius:8px; font-size:0.85rem; font-family:inherit; }}
  .form-submit {{ width:100%; background:{color}; color:#fff; border:none; padding:13px; border-radius:10px; font-size:0.95rem; font-weight:700; cursor:pointer; margin-top:8px; }}
  .confirm-box {{ display:none; background:#ECFDF5; border:1px solid #10B981; color:#065F46; padding:14px; border-radius:10px; text-align:center; font-size:0.85rem; margin-top:14px; }}

  .cta {{ background:linear-gradient(135deg,{color},{color2}); color:#fff; padding:54px 24px; text-align:center; }}
  .cta h2 {{ font-size:1.4rem; font-weight:800; margin-bottom:10px; }}
  .cta p {{ opacity:0.92; margin-bottom:24px; font-size:0.92rem; }}

  footer {{ background:#111827; color:#9ca3af; padding:28px 24px; text-align:center; font-size:0.8rem; }}
  footer .footer-logo {{ color:#fff; font-weight:700; margin-bottom:8px; font-size:1rem; }}
</style>
</head>
<body>

<header>
  <div class="logo">{name}</div>
  <nav>{nav_html}</nav>
</header>

<div class="hero" id="home">
  <div class="hero-badge">پیش‌نمایش اولیه • {ptype}</div>
  <h1>{name}</h1>
  <p>{tagline}</p>
  <div class="hero-btns">
    <button class="btn-primary" onclick="scrollToId('menu')">{spec['hero_btn']}</button>
    <button class="btn-secondary" onclick="scrollToId('reserve')">{spec['hero_btn2']}</button>
  </div>
</div>

<div class="section" id="menu">
  <div class="section-title">پیشنهادهای ویژه</div>
  <div class="section-sub">نمونه‌ای از آنچه مشتریان شما می‌بینند</div>
  <div class="menu-grid">{menu_html}</div>
</div>

<div class="section" id="gallery">
  <div class="section-title">گالری تصاویر</div>
  <div class="section-sub">نمونه‌ای از فضای کسب‌وکار شما</div>
  <div class="gallery-grid">
    <div class="gallery-item">📷</div>
    <div class="gallery-item">📷</div>
    <div class="gallery-item">📷</div>
    <div class="gallery-item">📷</div>
  </div>
</div>

<div class="section" id="about">
  <div class="about-wrap">
    <div class="about-icon">🏪</div>
    <div class="about-text">
      <div style="font-weight:700;font-size:1.1rem;margin-bottom:8px;color:#111827">درباره ما</div>
      {spec['about']}
      <ul class="feature-list">{features_html}</ul>
    </div>
  </div>
</div>

<div class="section">
  <div class="section-title">چرا ما را انتخاب کنید</div>
  <div class="section-sub">دلایلی که مشتریان به ما اعتماد می‌کنند</div>
  <div class="why-grid">{why_html}</div>
</div>

<div class="section" id="reserve">
  <div class="section-title">رزرو یا سفارش</div>
  <div class="section-sub">فرم زیر را پر کنید تا با شما تماس بگیریم</div>
  <div class="form-wrap">
    <div class="form-row">
      <label>نام</label>
      <input type="text" placeholder="نام شما">
    </div>
    <div class="form-row">
      <label>شماره تماس</label>
      <input type="text" placeholder="۰۹۱۲xxxxxxx">
    </div>
    <div class="form-row">
      <label>تاریخ و زمان</label>
      <input type="text" placeholder="مثلاً امشب ساعت ۸">
    </div>
    <button class="form-submit" onclick="mockSubmit()">ثبت درخواست</button>
    <div class="confirm-box" id="confirmBox">✓ درخواست شما ثبت شد! به‌زودی با شما تماس می‌گیریم.</div>
  </div>
</div>

<div class="cta" id="contact">
  <h2>همین حالا شروع کنید</h2>
  <p>برای رزرو، سفارش یا اطلاعات بیشتر با ما در ارتباط باشید</p>
  <button class="btn-primary" onclick="scrollToId('reserve')">تماس با ما</button>
</div>

<footer>
  <div class="footer-logo">{name}</div>
  <div>این یک پیش‌نمایش اولیه است</div>
</footer>

<script>
function scrollToId(id) {{
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({{behavior:'smooth'}});
}}
function mockSelect(itemName) {{
  scrollToId('reserve');
}}
function mockSubmit() {{
  const box = document.getElementById('confirmBox');
  if (box) box.style.display = 'block';
}}
</script>

</body>
</html>"""
