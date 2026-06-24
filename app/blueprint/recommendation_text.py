"""
Recommendation wording — Puzzle 6.6 (AI Factory v2 user-facing step),
polished in Puzzle 6.7 to feel more human and less mechanical.

Converts a ProductBlueprint (from app.blueprint.generator) into the
simple, human-readable Persian fields needed for the "پیشنهاد راه‌حل"
confirmation step shown to normal users.

This module is deliberately separate from app/blueprint/generator.py —
the generator itself is unchanged. This file only adds a presentation
layer on top: it reads a ProductBlueprint and produces plain Persian
sentences, never exposing internal/debug fields (industry_category,
confidence_level, recommended_tool_type, raw English first_output_type)
directly to the user.

Honesty rule: when the recommended first output is NOT a website
(e.g. "simple financial dashboard" for an accounting need), the wording
must clearly say that dashboard/bot/app outputs are not fully supported
yet, and that what gets built right now is still a website-preview-based
first look — never claim an unsupported output is fully buildable.
"""
from __future__ import annotations

from app.blueprint.models import ProductBlueprint


# English first_output_type values (from the Industry-to-Product Map) that
# describe an output OTHER than a website/page — these are the cases where
# we must add the honest "not fully supported yet" caveat.
_NON_WEBSITE_OUTPUT_MARKERS = (
    "dashboard", "bot", "task agent", "tracker",
)

# Maps the generator's English first_output_type phrases to a short,
# human Persian label for the recommendation panel. Falls back to a
# generic translation attempt (just showing the Persian "خروجی پیشنهادی"
# wrapper) when a phrase isn't in this table yet — never raw English.
_OUTPUT_LABELS_FA: dict[str, str] = {
    "product catalog + order page": "یک کاتالوگ محصول همراه با صفحه سفارش ساده",
    "portfolio page + customer request form": "صفحه نمونه‌کار و فرم درخواست سفارش",
    "service listing + simple booking form": "لیست خدمات و فرم ساده رزرو نوبت",
    "simple financial dashboard": "داشبورد مالی ساده",
    "simple task dashboard": "داشبورد ساده وظایف",
}

# Per-industry human, conversational templates — written the way a person
# would actually talk, not a mechanical "با توجه به اینکه..." sentence.
# Only covers industries with a clear, natural phrasing the puzzle asked
# for; anything else falls back to the generic (but still human) template
# in build_recommendation_text below.
_HUMAN_UNDERSTOOD_FA: dict[str, str] = {
    "homemade_food_products": "فهمیدم می‌خواهی ترشی‌های خانگی‌ات را بفروشی.",
    "tailoring_fashion": "فهمیدم می‌خواهی برای خیاطی‌ات مشتری بیشتری جذب کنی.",
    "beauty_appointments": "فهمیدم می‌خواهی مشتری‌ها راحت‌تر نوبت بگیرند.",
    "small_finance_accounting": "فهمیدم می‌خواهی حساب‌های مالی‌ات را در یک صفحه ساده ببینی.",
    "office_task_management": "فهمیدم می‌خواهی کارهای روزانه تیمت را بهتر مدیریت کنی.",
}

_HUMAN_REASON_FA: dict[str, str] = {
    "homemade_food_products": "برای شروع، بهتر است مشتری‌ها بتوانند محصولات، قیمت‌ها و راه سفارش را سریع ببینند.",
    "tailoring_fashion": "برای شروع، بهتر است مشتری‌ها اول نمونه‌کارهایت را ببینند و بعد بتوانند راحت سفارش بدهند.",
    "beauty_appointments": "برای شروع، بهتر است مشتری‌ها خدمات و قیمت‌ها را ببینند و بدون تماس تلفنی نوبت بگیرند.",
    "small_finance_accounting": "برای شروع، یک نمای ساده از درآمد و هزینه کافی است — نه یک نرم‌افزار کامل حسابداری.",
    "office_task_management": "برای شروع، یک نمای ساده از وظایف و مسئول هرکدام کافی است.",
}


def _output_label_fa(first_output_type: str | None) -> str:
    if not first_output_type:
        return "یک پیش‌نمایش اولیه ساده"
    return _OUTPUT_LABELS_FA.get(first_output_type, "یک پیش‌نمایش اولیه متناسب با نیازت")


def _is_non_website_output(first_output_type: str | None) -> bool:
    if not first_output_type:
        return False
    text = first_output_type.lower()
    return any(marker in text for marker in _NON_WEBSITE_OUTPUT_MARKERS)


def build_recommendation_text(bp: ProductBlueprint) -> dict[str, str]:
    """
    Returns the 4-5 plain Persian fields needed for the RecommendationResponse:
    understood_summary, recommended_output_label, reason, first_output_note,
    not_recommended_note (or None).
    """
    output_label = _output_label_fa(bp.first_output_type)
    industry = bp.industry_category or ""

    # 1. What we understood — a short, human sentence. Prefers the
    #    hand-written conversational template for the industries the
    #    puzzle specifically asked to sound natural; otherwise falls back
    #    to a simple, still-human sentence built from user_type/problem.
    if bp.confidence_level == "low":
        understood_summary = "هنوز کاملاً مشخص نیست دقیقاً چه نیازی داری — برایت چند سؤال ساده می‌پرسیم تا بهتر بفهمیم."
    elif industry in _HUMAN_UNDERSTOOD_FA:
        understood_summary = _HUMAN_UNDERSTOOD_FA[industry]
    elif bp.user_type:
        understood_summary = f"فهمیدم می‌خواهی به‌عنوان یک «{bp.user_type}» کارت را جلو ببری."
    else:
        understood_summary = "فهمیدم چه نیازی داری."

    # 2/3. Why this output fits — a short human sentence (the "بهتر است..."
    # style), followed by a clear, simple recommendation line. Built fresh
    # in Persian rather than reusing reason_for_recommendation directly,
    # since that field embeds the raw English first_output_type phrase.
    if industry in _HUMAN_REASON_FA:
        why_sentence = _HUMAN_REASON_FA[industry]
    elif bp.problem_to_solve:
        first_problem = bp.problem_to_solve.split("؛")[0]
        why_sentence = f"برای شروع، بهتر است اول مشکل اصلی حل شود: {first_problem}."
    else:
        why_sentence = "برای شروع، بهتر است ساده و سریع جلو برویم."

    reason = f"{why_sentence} پیشنهاد من: {output_label}."

    # 4. Honest note about what's actually being built right now.
    if _is_non_website_output(bp.first_output_type):
        first_output_note = (
            f"این خروجی («{output_label}») هنوز در نسخه فعلی کارخانه به‌طور کامل پشتیبانی نمی‌شود. "
            "برای الان، یک پیش‌نمایش اولیه از همین صفحه/داشبورد ساخته می‌شود — نه یک سایت تبلیغاتی معمولی — "
            "تا بتوانی شکل اولیه آن را ببینی."
        )
    else:
        first_output_note = (
            f"اولین چیزی که برایت می‌سازیم یک پیش‌نمایش اولیه از «{output_label}» است. "
            "این فقط نخستین خروجی کارخانه است، نه همه قابلیت‌های آن."
        )

    # 5. What's NOT recommended for the first version — kept short and
    #    plain rather than the longer, more formal generator wording.
    not_recommended_note = None
    if bp.not_recommended:
        if industry == "homemade_food_products":
            not_recommended_note = "فعلاً اپلیکیشن یا فروشگاه کامل پیشنهاد نمی‌شود، چون برای شروع سنگین و پرهزینه است."
        else:
            items_fa = "، ".join(bp.not_recommended)
            not_recommended_note = f"فعلاً {items_fa} پیشنهاد نمی‌شود، چون برای شروع سنگین و پرهزینه است."

    return {
        "understood_summary": understood_summary,
        "recommended_output_label": output_label,
        "reason": reason,
        "first_output_note": first_output_note,
        "not_recommended_note": not_recommended_note,
    }
