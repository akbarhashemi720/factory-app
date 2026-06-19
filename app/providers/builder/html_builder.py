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
    domain = und.get("business_domain") or ""
    # Fallback: some keyword signal may live in bullets when business_domain is absent (mock path)
    signal_text = domain + " " + " ".join(und.get("bullets", []) or [])

    SPECS = {
        "restaurant": _restaurant_spec(),
        "general_class": _education_spec(signal_text),
        "booking": _booking_spec(),
        "telegram_bot": _booking_spec(bot=True),
        "store": _store_spec(),
    }
    spec = SPECS.get(scenario, _general_spec())

    if domain and len(domain) <= 24:
        spec["name"] = domain

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


def _education_spec(domain: str = ""):
    domain = domain or ""
    is_cooking = any(k in domain for k in ["آشپز", "غذا", "پخت", "کیک", "شیرینی"])
    is_music = any(k in domain for k in ["موسیقی", "ساز", "آواز", "گیتار", "پیانو"])
    is_art = any(k in domain for k in ["نقاشی", "هنر", "طراحی"])

    if is_cooking:
        return {
            "name": domain if domain else "آموزشگاه آشپزی ایرانی",
            "tagline": "طعم اصیل ایرانی، آموزش حرفه‌ای، در کلاس یا آنلاین",
            "type": "سایت آموزش آشپزی",
            "color": "#B45309",
            "color2": "#FBBF24",
            "hero_btn": "مشاهده دوره‌ها",
            "hero_btn2": "ثبت‌نام در کلاس",
            "nav_items": ["خانه", "دوره‌ها", "مدرس", "کلاس‌ها", "تماس"],
            "features": ["کلاس‌های آنلاین و حضوری", "دوره‌های غذاهای سنتی ایرانی", "ثبت‌نام آسان", "برنامه هفتگی کلاس‌ها"],
            "menu_items": [
                {"icon":"🍚","name":"دوره خوراک‌های سنتی","desc":"قورمه‌سبزی، فسنجان، آبگوشت","price":"حضوری/آنلاین"},
                {"icon":"🥘","name":"دوره خورشت‌های ایرانی","desc":"تکنیک‌های اصیل پخت","price":"حضوری/آنلاین"},
                {"icon":"🍞","name":"نان و خمیر سنتی","desc":"نان سنگک، بربری، لواش","price":"حضوری"},
                {"icon":"🍰","name":"شیرینی‌پزی ایرانی","desc":"باقلوا، نان نخودچی","price":"آنلاین"},
                {"icon":"🍢","name":"کباب و گریل","desc":"کباب کوبیده، جوجه، بختیاری","price":"حضوری"},
                {"icon":"🎓","name":"دوره جامع آشپزی","desc":"از مقدماتی تا حرفه‌ای","price":"ترمی"},
            ],
            "why_us": [
                {"icon":"👨‍🍳","title":"مدرس مجرب","desc":"سال‌ها تجربه آشپزی سنتی"},
                {"icon":"💻","title":"کلاس آنلاین و حضوری","desc":"یادگیری به سبک دلخواه شما"},
                {"icon":"📜","title":"مدرک پایان دوره","desc":"گواهی معتبر شرکت در دوره"},
            ],
            "about": "در این آموزشگاه، رازهای آشپزی ایرانی را قدم‌به‌قدم و با تمرین عملی یاد می‌گیرید — هم در کلاس حضوری، هم آنلاین.",
        }

    if is_music:
        return {
            "name": domain if domain else "آموزشگاه موسیقی",
            "tagline": "نواختن را از همین امروز شروع کن",
            "type": "سایت آموزش موسیقی",
            "color": "#5B21B6",
            "color2": "#A78BFA",
            "hero_btn": "مشاهده دوره‌ها",
            "hero_btn2": "ثبت‌نام در کلاس",
            "nav_items": ["خانه", "دوره‌ها", "مدرسین", "کلاس‌ها", "تماس"],
            "features": ["کلاس‌های آنلاین و حضوری", "آموزش انفرادی و گروهی", "ثبت‌نام آسان", "برنامه کلاس‌ها"],
            "menu_items": [
                {"icon":"🎸","name":"گیتار مقدماتی","desc":"برای تازه‌کارها","price":"ماهانه"},
                {"icon":"🎹","name":"پیانو پایه","desc":"تئوری و تکنیک","price":"ماهانه"},
                {"icon":"🎤","name":"آواز و صداسازی","desc":"تکنیک‌های صحیح خوانندگی","price":"جلسه‌ای"},
                {"icon":"🥁","name":"درام","desc":"ریتم و تمرین عملی","price":"ماهانه"},
                {"icon":"🎻","name":"ویولن","desc":"کلاسیک و محلی","price":"ماهانه"},
                {"icon":"🎓","name":"دوره تئوری موسیقی","desc":"برای همه سازها","price":"ترمی"},
            ],
            "why_us": [
                {"icon":"🎼","title":"مدرسین حرفه‌ای","desc":"تجربه آموزش چندساله"},
                {"icon":"💻","title":"کلاس آنلاین و حضوری","desc":"یادگیری به سبک دلخواه شما"},
                {"icon":"🎵","title":"تمرین عملی","desc":"یادگیری با تمرین واقعی"},
            ],
            "about": "در این آموزشگاه، نواختن ساز را با مدرسین حرفه‌ای و به‌صورت آنلاین یا حضوری یاد می‌گیرید.",
        }

    return {
        "name": domain if domain else "آموزشگاه زبان نوین",
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
          <div class="m-img">{m['icon']}</div>
          <div class="m-card-body">
            <div class="m-name">{m['name']}</div>
            <div class="m-desc">{m['desc']}</div>
            {price_html}
            <button class="m-btn" onclick="mockSelect('{m['name']}')">انتخاب</button>
          </div>
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

    gallery_icons = [m["icon"] for m in spec["menu_items"][:4]] or ["📷", "🏠", "✨", "👥"]
    while len(gallery_icons) < 4:
        gallery_icons.append("📷")
    gallery_html = "".join(f'<div class="gallery-item">{ic}</div>' for ic in gallery_icons[:4])

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html {{ scroll-behavior:smooth; }}
  body {{ font-family:Tahoma,Arial,sans-serif; background:#FBF7F0; color:#2D2424; direction:rtl; line-height:1.7; }}

  header {{ position:sticky; top:0; background:rgba(255,255,255,0.97); backdrop-filter:blur(8px); box-shadow:0 1px 12px rgba(0,0,0,0.07); z-index:10; padding:16px 32px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; }}
  .logo {{ font-weight:800; font-size:1.25rem; color:{color}; letter-spacing:.3px; }}
  .nav-link {{ color:#555; text-decoration:none; font-size:0.88rem; margin:0 10px; font-weight:500; transition:color .2s; }}

  .hero {{ position:relative; background:linear-gradient(160deg,{color} 0%,{color2} 55%,{color} 100%); color:#fff; padding:90px 24px 110px; text-align:center; overflow:hidden; }}
  .hero::before {{ content:""; position:absolute; inset:0; background:radial-gradient(circle at 20% 20%, rgba(255,255,255,0.15) 0%, transparent 45%), radial-gradient(circle at 85% 75%, rgba(255,255,255,0.12) 0%, transparent 40%); }}
  .hero-inner {{ position:relative; z-index:2; max-width:680px; margin:0 auto; }}
  .hero-badge {{ display:inline-block; background:rgba(255,255,255,0.22); border:1px solid rgba(255,255,255,0.35); padding:6px 18px; border-radius:20px; font-size:0.78rem; margin-bottom:22px; letter-spacing:.2px; }}
  .hero h1 {{ font-size:2.5rem; font-weight:800; margin-bottom:14px; text-shadow:0 2px 12px rgba(0,0,0,0.15); }}
  .hero p {{ font-size:1.15rem; opacity:0.96; margin-bottom:34px; }}
  .hero-btns {{ display:flex; gap:14px; justify-content:center; flex-wrap:wrap; }}
  .btn-primary {{ background:#fff; color:{color}; border:none; padding:15px 36px; border-radius:28px; font-size:0.98rem; font-weight:700; cursor:pointer; box-shadow:0 6px 18px rgba(0,0,0,0.18); transition:transform .15s; }}
  .btn-secondary {{ background:rgba(255,255,255,0.12); color:#fff; border:2px solid rgba(255,255,255,0.65); padding:13px 32px; border-radius:28px; font-size:0.98rem; font-weight:700; cursor:pointer; }}
  .hero-wave {{ position:absolute; bottom:-2px; left:0; right:0; height:50px; background:#FBF7F0; border-radius:50% 50% 0 0 / 100% 100% 0 0; }}

  .section {{ padding:64px 28px; max-width:1100px; margin:0 auto; }}
  .section-title {{ font-size:1.65rem; font-weight:800; text-align:center; margin-bottom:10px; color:#2D2424; }}
  .section-sub {{ text-align:center; color:#8a7a6e; font-size:0.92rem; margin-bottom:40px; }}

  .menu-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:22px; }}
  .m-card {{ background:#fff; border-radius:18px; padding:0; box-shadow:0 4px 20px rgba(45,36,36,0.08); text-align:center; overflow:hidden; transition:transform .2s,box-shadow .2s; }}
  .m-img {{ height:90px; background:linear-gradient(135deg,{color}1a,{color2}33); display:flex; align-items:center; justify-content:center; font-size:2.6rem; }}
  .m-card-body {{ padding:20px; }}
  .m-name {{ font-weight:700; font-size:1.02rem; margin-bottom:6px; color:#2D2424; }}
  .m-desc {{ color:#8a7a6e; font-size:0.82rem; margin-bottom:12px; min-height:32px; }}
  .m-price {{ color:{color}; font-weight:800; font-size:1rem; margin-bottom:14px; }}
  .m-btn {{ background:{color}; color:#fff; border:none; padding:9px 26px; border-radius:20px; font-size:0.83rem; cursor:pointer; font-weight:600; }}

  .about-wrap {{ background:#fff; border-radius:22px; padding:42px; box-shadow:0 4px 20px rgba(45,36,36,0.06); display:flex; gap:32px; align-items:center; flex-wrap:wrap; }}
  .about-icon {{ font-size:4rem; flex-shrink:0; width:90px; height:90px; background:linear-gradient(135deg,{color}1a,{color2}33); border-radius:50%; display:flex; align-items:center; justify-content:center; }}
  .about-text {{ flex:1; min-width:240px; color:#4a3f3a; font-size:0.94rem; }}
  .feature-list {{ list-style:none; margin-top:18px; }}
  .feature-list li {{ padding:7px 0; color:#4a3f3a; font-size:0.88rem; }}

  .why-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:24px; }}
  .why-card {{ text-align:center; padding:28px 20px; background:#fff; border-radius:18px; box-shadow:0 3px 16px rgba(45,36,36,0.05); }}
  .why-icon {{ font-size:2.6rem; margin-bottom:14px; }}
  .why-title {{ font-weight:700; margin-bottom:8px; font-size:1.02rem; color:#2D2424; }}
  .why-desc {{ color:#8a7a6e; font-size:0.86rem; }}

  .gallery-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:18px; }}
  .gallery-item {{ aspect-ratio:4/3; border-radius:18px; background:linear-gradient(135deg,{color}26,{color2}40); display:flex; align-items:center; justify-content:center; font-size:2.4rem; box-shadow:0 4px 16px rgba(45,36,36,0.08); position:relative; overflow:hidden; }}
  .gallery-item::after {{ content:""; position:absolute; inset:0; background:linear-gradient(180deg,transparent 60%,rgba(0,0,0,0.08) 100%); }}

  .form-wrap {{ background:#fff; border-radius:20px; padding:38px; box-shadow:0 4px 22px rgba(45,36,36,0.08); max-width:500px; margin:0 auto; }}
  .form-row {{ margin-bottom:16px; }}
  .form-row label {{ display:block; font-size:0.84rem; margin-bottom:6px; color:#4a3f3a; font-weight:600; }}
  .form-row input, .form-row select {{ width:100%; padding:11px 14px; border:1.5px solid #ECE2D6; border-radius:10px; font-size:0.87rem; font-family:inherit; background:#FBF7F0; }}
  .form-submit {{ width:100%; background:{color}; color:#fff; border:none; padding:14px; border-radius:12px; font-size:0.97rem; font-weight:700; cursor:pointer; margin-top:10px; box-shadow:0 4px 14px {color}40; }}
  .confirm-box {{ display:none; background:#ECFDF5; border:1.5px solid #10B981; color:#065F46; padding:16px; border-radius:12px; text-align:center; font-size:0.86rem; margin-top:16px; }}

  .cta {{ background:linear-gradient(160deg,{color},{color2}); color:#fff; padding:64px 24px; text-align:center; }}
  .cta h2 {{ font-size:1.6rem; font-weight:800; margin-bottom:12px; }}
  .cta p {{ opacity:0.94; margin-bottom:28px; font-size:0.95rem; }}

  footer {{ background:#241C1C; color:#a89b94; padding:32px 24px; text-align:center; font-size:0.82rem; }}
  footer .footer-logo {{ color:#fff; font-weight:700; margin-bottom:10px; font-size:1.05rem; }}
</style>
</head>
<body>

<header>
  <div class="logo">{name}</div>
  <nav>{nav_html}</nav>
</header>

<div class="hero" id="home">
  <div class="hero-inner">
    <div class="hero-badge">پیش‌نمایش اولیه • {ptype}</div>
    <h1>{name}</h1>
    <p>{tagline}</p>
    <div class="hero-btns">
      <button class="btn-primary" onclick="scrollToId('menu')">{spec['hero_btn']}</button>
      <button class="btn-secondary" onclick="scrollToId('reserve')">{spec['hero_btn2']}</button>
    </div>
  </div>
  <div class="hero-wave"></div>
</div>

<div class="section" id="menu">
  <div class="section-title">پیشنهادهای ویژه</div>
  <div class="section-sub">نمونه‌ای از آنچه مشتریان شما می‌بینند</div>
  <div class="menu-grid">{menu_html}</div>
</div>

<div class="section" id="gallery">
  <div class="section-title">گالری تصاویر</div>
  <div class="section-sub">نمونه‌ای از فضای کسب‌وکار شما</div>
  <div class="gallery-grid">{gallery_html}</div>
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
