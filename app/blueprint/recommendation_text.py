"""
Recommendation wording — Puzzle 6.6 (AI Factory v2 user-facing step).

Converts a ProductBlueprint (from app.blueprint.generator) into the
simple, human-readable Persian fields needed for the "پیشنهاد کارخانه"
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
    "product catalog + order page": "کاتالوگ محصول و صفحه سفارش ساده",
    "portfolio page + customer request form": "صفحه نمونه‌کار و فرم درخواست سفارش",
    "service listing + simple booking form": "لیست خدمات و فرم ساده رزرو نوبت",
    "simple financial dashboard": "داشبورد مالی ساده",
    "simple task dashboard": "داشبورد ساده وظایف",
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

    # 1. What we understood — built from problem_to_solve/user_type when
    #    available, with an honest, low-confidence-friendly fallback otherwise.
    if bp.user_type and bp.problem_to_solve and bp.confidence_level != "low":
        first_problem = bp.problem_to_solve.split("؛")[0]
        understood_summary = (
            f"فهمیدم می‌خواهی به‌عنوان یک «{bp.user_type}» فعالیت کنی و مشکل اصلی‌ات این است که: {first_problem}."
        )
    elif bp.confidence_level != "low":
        understood_summary = "فهمیدم چه نیازی داری."
    else:
        understood_summary = "هنوز کاملاً مشخص نیست دقیقاً چه نیازی داری — برایت چند سؤال ساده می‌پرسیم تا بهتر بفهمیم."

    # 2/3. What we recommend, and why — built fresh in Persian rather than
    # reusing reason_for_recommendation directly, since that field embeds
    # the raw English first_output_type phrase (e.g. "product catalog +
    # order page") which must never reach the user-facing recommendation.
    if bp.user_type and bp.problem_to_solve:
        first_problem = bp.problem_to_solve.split("؛")[0]
        reason = (
            f"با توجه به اینکه مشکل اصلی‌ات «{first_problem}» است، "
            f"«{output_label}» ساده‌ترین و مناسب‌ترین نقطه شروع است."
        )
    else:
        reason = f"«{output_label}» ساده‌ترین و سریع‌ترین نقطه شروع متناسب با نیازت است."

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

    # 5. What's NOT recommended for the first version, if available.
    not_recommended_note = None
    if bp.not_recommended:
        items_fa = "، ".join(bp.not_recommended)
        if bp.reason_not_recommended:
            not_recommended_note = f"{bp.reason_not_recommended}"
        else:
            not_recommended_note = f"برای نسخه اول، {items_fa} پیشنهاد نمی‌شود."

    return {
        "understood_summary": understood_summary,
        "recommended_output_label": output_label,
        "reason": reason,
        "first_output_note": first_output_note,
        "not_recommended_note": not_recommended_note,
    }
