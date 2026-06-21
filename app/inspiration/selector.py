"""
Inspiration Bank — selector logic (Part 3 + Part 5).

Maps user intent (free Persian text) to a small set of suitable design
families from the bank, ranked by inspiration_value_score within the
matched group. Surfaces exactly 3 options to the customer in simple
Persian — never the underlying reference_id, scores, or any technical
field.

Important: popularity alone never picks a family — selection is driven
by intent-keyword matches against `best_for`, with inspiration_value_score
used only to rank/break ties among already-relevant candidates.
"""
from __future__ import annotations

import random
from typing import Any

from app.inspiration.models import InspirationReference
from app.inspiration.cafe_seed import get_cafe_bank


# Intent keyword → preferred visual_style/layout family mapping.
# Order matters only for readability; matching is independent per group.
_CAFE_INTENT_KEYWORDS: dict[str, list[str]] = {
    "luxury_premium": ["لوکس", "خاص", "گرانقیمت", "شیک", "حرفه‌ای", "premium", "luxury"],
    "minimal_clean": ["ساده", "مینیمال", "مدرن", "تمیز", "minimal", "simple"],
    "product_commerce": ["سفارش", "خرید", "فروش", "محصول", "آنلاین", "order", "shop"],
    "bakery_warm": ["نان", "شیرینی", "کیک", "صبحانه", "نانوایی", "bakery"],
    "local_practical": ["محلی", "آدرس", "شعبه", "نزدیک", "سریع", "local"],
    "visual_storytelling": ["عکس", "گالری", "فضا", "محیط", "دکوراسیون", "اتمسفر", "gallery"],
    "service_focused": ["رزرو", "میز", "نشستن", "مهمانی", "رویداد", "reservation", "booking"],
    "warm_handmade": ["گرم", "صمیمی", "دست‌ساز", "خانگی", "طبیعی", "ارگانیک", "روستیک"],
}


def _get_bank(business_type: str) -> list[InspirationReference]:
    if business_type == "cafe":
        return get_cafe_bank()
    return []


def match_families_by_intent(business_type: str, raw_text: str) -> list[InspirationReference]:
    """
    Scan raw_text for intent keywords and return matching records,
    ranked by inspiration_value_score. Falls back to a curated rotation
    of generally-strong defaults when no keyword matches.
    """
    bank = _get_bank(business_type)
    if not bank:
        return []

    text = raw_text or ""
    matched_styles: set[str] = set()
    for style, keywords in _CAFE_INTENT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            matched_styles.add(style)

    if matched_styles:
        candidates = [r for r in bank if r.visual_style in matched_styles]
    else:
        candidates = []

    if not candidates:
        # No clear style signal — rotate among generally strong defaults
        # rather than always returning the same family for every vague request.
        candidates = list(bank)
        random.shuffle(candidates)

    candidates.sort(key=lambda r: r.inspiration_value_score, reverse=True)
    return candidates


def get_customer_options(business_type: str, raw_text: str, n: int = 3) -> list[dict[str, Any]]:
    """
    Returns up to n customer-facing option dicts: {"reference_id", "name",
    "description"}. reference_id is included so the caller can later
    resolve the customer's pick back to a full InspirationReference, but
    it is never rendered to the customer directly — only "name" and
    "description" should ever reach UI copy.
    """
    candidates = match_families_by_intent(business_type, raw_text)
    # Deduplicate by visual_style family so the 3 options feel meaningfully
    # different to the customer, not 3 near-identical luxury variants.
    seen_styles: set[str] = set()
    options: list[dict[str, Any]] = []
    for ref in candidates:
        if ref.visual_style in seen_styles:
            continue
        seen_styles.add(ref.visual_style)
        options.append({
            "reference_id": ref.reference_id,
            "name": ref.reference_name,
            "description": ref.inspiration_notes,
        })
        if len(options) >= n:
            break
    return options


def resolve_reference(business_type: str, reference_id: str) -> InspirationReference | None:
    """Look up a specific reference by id — used once the customer picks one."""
    bank = _get_bank(business_type)
    return next((r for r in bank if r.reference_id == reference_id), None)


def pick_default_reference(business_type: str, raw_text: str) -> InspirationReference | None:
    """
    Non-interactive path: when the builder needs to just pick a family
    immediately (e.g. mock/test flows, or after the customer skips the
    style choice), use the top-ranked match for the given intent text.
    """
    candidates = match_families_by_intent(business_type, raw_text)
    return candidates[0] if candidates else None
