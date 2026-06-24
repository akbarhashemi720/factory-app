"""
Industry-to-Product Map — static data (Puzzle 2, AI Factory v2 planning).

This file holds a small, hand-written map from ordinary jobs/industries
to the digital tools that usually fit their real needs. It exists so a
future Solution Recommendation layer can start from "what does this
person actually do, and what do they keep struggling with?" instead of
asking the user to pick "website, bot, or app" up front.

This is intentionally DATA ONLY — a plain list of dictionaries, no
matching logic, no scoring, no AI calls. Nothing in the current app
imports or uses this file yet. The existing Website Preview Builder
flow (request -> understanding -> diagnostic question -> confirm ->
generate-preview -> revision/edit-direct -> approve -> export), the
`website_intent` field, and the ProductBlueprint model (app/blueprint/)
are completely unaffected by this file.

Each entry follows the same shape so a future recommender can simply
iterate the list. Field meanings:

  industry_category        -- the broad job/industry group
  example_users             -- ordinary people/businesses in that group
  common_user_phrases       -- simple things a non-technical user might say
  common_problems           -- the real pain points behind those phrases
  digital_need_categories   -- the need family (selling, booking, ...)
  recommended_tool_types    -- candidate tools that may fit this need
  best_first_output         -- the simplest recommended starting point
  core_features             -- features needed in the first version
  future_features           -- features that can be added later
  not_recommended           -- tools likely too heavy for a first version
  reason_not_recommended    -- why those tools are not recommended yet
  possible_ai_agents        -- future management agent NAMES only (no
                                real or fake agent behavior implied)
"""
from __future__ import annotations

from typing import Any


INDUSTRY_TO_PRODUCT_MAP: list[dict[str, Any]] = [
    {
        "industry_category": "homemade_food_products",
        "example_users": [
            "فروشنده ترشی خانگی",
            "فروشنده شیرینی و کیک خانگی",
            "فروشنده غذای آماده خانگی",
        ],
        "common_user_phrases": [
            "می‌خوام ترشی خانگی بفروشم",
            "می‌خوام شیرینی‌هایی که می‌پزم را آنلاین بفروشم",
            "مشتری‌ها نمی‌دونن چی دارم می‌فروشم",
        ],
        "common_problems": [
            "مشتریان نمی‌دانند چه محصولاتی و با چه قیمتی موجود است",
            "سفارش‌گیری فقط از طریق پیام شخصی و نامنظم است",
            "پیگیری سفارش‌های جدید و قبلی سخت است",
        ],
        "digital_need_categories": ["selling", "customer_management"],
        "recommended_tool_types": [
            "order page", "product catalog", "order form",
        ],
        "best_first_output": "product catalog + order page",
        "core_features": [
            "نمایش محصولات با عکس و قیمت",
            "فرم سفارش ساده",
            "اطلاعات تماس فروشنده",
        ],
        "future_features": [
            "پرداخت آنلاین",
            "پیگیری وضعیت سفارش برای مشتری",
            "اعلان سفارش جدید به فروشنده",
        ],
        "not_recommended": ["mobile app", "full e-commerce platform"],
        "reason_not_recommended": (
            "برای یک فروشنده خانگی در شروع کار، اپلیکیشن موبایل یا یک "
            "پلتفرم فروشگاهی کامل بیش از حد سنگین و غیرضروری است؛ یک "
            "صفحه ساده سفارش همان نیاز را با هزینه و پیچیدگی بسیار کمتر "
            "برطرف می‌کند."
        ),
        "possible_ai_agents": ["Sales Agent", "Support Agent"],
    },
    {
        "industry_category": "tailoring_fashion",
        "example_users": [
            "خیاط سفارشی‌دوز",
            "طراح لباس مستقل",
            "اتو و ترمیم لباس",
        ],
        "common_user_phrases": [
            "می‌خوام مشتری‌های بیشتری برای خیاطیم جذب کنم",
            "می‌خوام نمونه کارهامو نشون بدم",
            "مشتری‌ها سفارش می‌دن ولی پیگیریش سخته",
        ],
        "common_problems": [
            "نمونه کارهای قبلی جایی برای نمایش ندارند",
            "درخواست سفارش جدید فقط از طریق تماس تلفنی است",
            "پیگیری وضعیت سفارش‌های در حال انجام سخت است",
        ],
        "digital_need_categories": ["showcase", "selling", "task_tracking"],
        "recommended_tool_types": [
            "portfolio page", "customer request form", "order tracking",
        ],
        "best_first_output": "portfolio page + customer request form",
        "core_features": [
            "نمایش نمونه کارها با عکس",
            "فرم درخواست سفارش جدید",
            "اطلاعات تماس و آدرس",
        ],
        "future_features": [
            "پیگیری آنلاین وضعیت سفارش برای مشتری",
            "نوبت‌دهی برای اندازه‌گیری",
            "گالری دسته‌بندی‌شده بر اساس نوع لباس",
        ],
        "not_recommended": ["mobile app", "full booking system with payments"],
        "reason_not_recommended": (
            "در شروع کار، یک خیاط مستقل به یک اپ کامل یا سیستم رزرو با "
            "پرداخت آنلاین نیاز ندارد؛ آنچه واقعاً کمک می‌کند نمایش نمونه "
            "کارها و یک راه ساده برای ثبت درخواست مشتری است."
        ),
        "possible_ai_agents": ["Sales Agent", "Task Agent"],
    },
    {
        "industry_category": "beauty_appointments",
        "example_users": [
            "آرایشگر زنانه/مردانه",
            "متخصص ناخن",
            "سالن زیبایی کوچک",
        ],
        "common_user_phrases": [
            "می‌خوام مشتری‌ها بتونن آنلاین نوبت بگیرن",
            "می‌خوام خدمات و قیمت‌هامو نشون بدم",
            "تلفن مدام زنگ می‌زنه برای رزرو نوبت",
        ],
        "common_problems": [
            "رزرو نوبت فقط از طریق تلفن انجام می‌شود و وقت‌گیر است",
            "مشتریان جدید لیست خدمات و قیمت‌ها را نمی‌دانند",
            "نمایش فضای سالن و نمونه کارها وجود ندارد",
        ],
        "digital_need_categories": ["booking", "showcase"],
        "recommended_tool_types": [
            "service listing", "gallery", "appointment booking",
        ],
        "best_first_output": "service listing + simple booking form",
        "core_features": [
            "لیست خدمات با قیمت",
            "فرم ساده رزرو نوبت",
            "گالری نمونه کارها/فضای سالن",
        ],
        "future_features": [
            "تأیید خودکار نوبت",
            "یادآور نوبت برای مشتری",
            "مدیریت تقویم نوبت‌های پر/خالی",
        ],
        "not_recommended": ["full booking platform with online payments"],
        "reason_not_recommended": (
            "یک سیستم رزرو کامل با پرداخت آنلاین و مدیریت چندشعبه‌ای برای "
            "یک سالن کوچک در شروع کار بیش از نیاز است؛ یک فرم رزرو ساده "
            "همان مشکل اصلی (کاهش تماس تلفنی) را حل می‌کند."
        ),
        "possible_ai_agents": ["Support Agent", "Marketing Agent"],
    },
    {
        "industry_category": "small_finance_accounting",
        "example_users": [
            "حسابدار مستقل",
            "صاحب کسب‌وکار کوچک بدون حسابدار",
            "فریلنسر که خودش حساب‌هایش را نگه می‌دارد",
        ],
        "common_user_phrases": [
            "می‌خوام حساب‌های شرکتمو در یک صفحه ساده ببینم",
            "نمی‌دونم این ماه چقدر سود کردم",
            "هزینه و درآمدمو جایی منظم ثبت نکردم",
        ],
        "common_problems": [
            "درآمد و هزینه در جاهای پراکنده (دفترچه، پیام، حافظه) ثبت می‌شود",
            "نمای کلی واضحی از وضعیت مالی فعلی وجود ندارد",
            "گزارش‌گیری برای ماه/فصل قبلی سخت و وقت‌گیر است",
        ],
        "digital_need_categories": ["accounting", "reporting"],
        "recommended_tool_types": [
            "simple financial dashboard", "income/expense tracker",
        ],
        "best_first_output": "simple financial dashboard",
        "core_features": [
            "ثبت درآمد و هزینه",
            "مشاهده مانده فعلی",
            "جمع‌بندی ساده ماهانه",
        ],
        "future_features": [
            "گزارش‌های مقایسه‌ای بین ماه‌ها",
            "دسته‌بندی هزینه‌ها",
            "اتصال به حساب بانکی",
        ],
        "not_recommended": ["full accounting/ERP software"],
        "reason_not_recommended": (
            "نرم‌افزار کامل حسابداری یا ERP برای یک کسب‌وکار کوچک یا "
            "فریلنسر در شروع کار بسیار پیچیده و پرهزینه است؛ یک داشبورد "
            "مالی ساده همان نیاز اصلی (دیدن وضعیت مالی) را برطرف می‌کند."
        ),
        "possible_ai_agents": ["Finance Agent", "Analytics Agent"],
    },
    {
        "industry_category": "office_task_management",
        "example_users": [
            "کارمند اداری",
            "مدیر یک تیم کوچک",
            "صاحب کسب‌وکاری با چند نفر کارمند",
        ],
        "common_user_phrases": [
            "می‌خوام کارهای روزانه تیممو مدیریت کنم",
            "فراموش می‌کنم کارها به کجا رسیده",
            "نمی‌دونم هرکدوم از بچه‌های تیم چیکار دارن می‌کنن",
        ],
        "common_problems": [
            "وظایف روی کاغذ، پیام، یا حافظه پراکنده‌اند",
            "مشخص نیست مسئول هر کار کیست و وضعیتش چیست",
            "پیگیری کارهای معوق وقت‌گیر و فراموش‌شدنی است",
        ],
        "digital_need_categories": ["task_management", "team_coordination"],
        "recommended_tool_types": [
            "task dashboard", "task agent",
        ],
        "best_first_output": "simple task dashboard",
        "core_features": [
            "تعریف وظیفه جدید",
            "تعیین مسئول هر وظیفه",
            "وضعیت انجام/در حال انجام",
        ],
        "future_features": [
            "اعلان خودکار به اعضای تیم",
            "گزارش هفتگی پیشرفت",
            "اولویت‌بندی خودکار وظایف",
        ],
        "not_recommended": ["full enterprise project-management suite"],
        "reason_not_recommended": (
            "یک ابزار کامل و پیچیده مدیریت پروژه سازمانی برای یک تیم کوچک "
            "در شروع کار بیش از حد سنگین است؛ یک داشبورد ساده وظایف همان "
            "نیاز اصلی (نظم و شفافیت کارها) را برطرف می‌کند."
        ),
        "possible_ai_agents": ["Task Agent", "Analytics Agent"],
    },
]


def get_industry_map() -> list[dict[str, Any]]:
    """Return the full static Industry-to-Product Map (read-only use)."""
    return INDUSTRY_TO_PRODUCT_MAP
