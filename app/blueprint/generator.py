"""
Product Blueprint Generator — rule-based, isolated (Puzzle 3, AI Factory v2 planning).

This file takes a RAW user request (plain Persian text, exactly like
what the existing Website Preview Builder already collects) and turns
it into a ProductBlueprint by matching it against the static
Industry-to-Product Map (app/recommendation/industry_map.py).

This is intentionally a SAFE, LOCAL, RULE-BASED FIRST VERSION — no
Claude calls, no external APIs, no complex scoring. It exists only to
prove the shape of the future AI Factory v2 thinking step:

    Raw user request -> match likely industry/need -> ProductBlueprint

Nothing in the current app calls this function yet. The existing
Website Preview Builder flow (request -> understanding -> diagnostic
question -> confirm -> generate-preview -> revision/edit-direct ->
approve -> export), `website_intent`, app/blueprint/models.py, and
app/recommendation/industry_map.py are completely unaffected by this
file — it only READS from the other two, it does not modify them.
"""
from __future__ import annotations

from app.blueprint.models import ProductBlueprint
from app.recommendation.industry_map import get_industry_map


# Minimum number of matched signals (phrases/keywords/example-user words)
# before we trust a match enough to call it "high" confidence. Below this,
# a weak/partial match is still returned but marked "medium"; zero matches
# falls back to the "low confidence, ask questions" blueprint.
_STRONG_MATCH_THRESHOLD = 2


def generate_product_blueprint(raw_user_request: str) -> ProductBlueprint:
    """
    Detect the request's language, then:
      - "fa" -> match against the (Persian-first) Industry-to-Product Map
        using simple keyword/phrase overlap, same as before.
      - anything else ("en", "unknown") -> the Industry-to-Product Map is
        Persian-first and not safe to match against yet, so return a
        language-appropriate fallback blueprint instead of guessing.
    """
    text = (raw_user_request or "").strip()
    language = _detect_user_language(text)

    if language != "fa":
        return _fallback_blueprint(text, language)

    entry, match_count = _find_best_match(text)

    if entry is None:
        return _fallback_blueprint(text, language)

    confidence = "high" if match_count >= _STRONG_MATCH_THRESHOLD else "medium"
    return _blueprint_from_entry(text, entry, confidence, language)


# ── Language detection ───────────────────────────────────────────────────────
# Simple, rule-based, no external APIs — just enough to stop the architecture
# from being locked to Persian. Real multilingual matching (an English/other
# Industry-to-Product Map, real language models, etc.) is future work.

def _detect_user_language(text: str) -> str:
    """
    "fa"      -- text contains Persian/Arabic-script characters
    "en"      -- text contains mostly Latin letters (and no Persian script)
    "unknown" -- neither condition confidently matches (e.g. empty text,
                 numbers/symbols only, or a script we don't handle yet)
    """
    if not text:
        return "unknown"

    has_persian_script = any(
        "\u0600" <= ch <= "\u06FF" or "\u0750" <= ch <= "\u077F"
        for ch in text
    )
    if has_persian_script:
        return "fa"

    latin_letters = sum(1 for ch in text if ch.isalpha() and ch.isascii())
    total_letters = sum(1 for ch in text if ch.isalpha())
    if total_letters > 0 and latin_letters == total_letters:
        return "en"

    return "unknown"


# ── Matching ─────────────────────────────────────────────────────────────────

def _find_best_match(text: str) -> tuple[dict | None, int]:
    """
    Score every industry-map entry by how many of its
    common_user_phrases / example_users / industry_category words appear
    in the raw text, and return the best-scoring entry (and its score).
    Returns (None, 0) if nothing scores above zero.
    """
    if not text:
        return None, 0

    best_entry: dict | None = None
    best_score = 0

    for entry in get_industry_map():
        score = _score_entry(text, entry)
        if score > best_score:
            best_score = score
            best_entry = entry

    if best_score <= 0:
        return None, 0
    return best_entry, best_score


def _score_entry(text: str, entry: dict) -> int:
    """
    Simple overlap score: +1 for each common_user_phrase that appears
    (even partially) in the text, +1 for each example_user mentioned,
    +1 if any word from industry_category appears. No weighting beyond
    this — kept intentionally simple per the rule-based-only requirement.
    """
    score = 0

    for phrase in entry.get("common_user_phrases", []):
        if _phrase_overlaps(text, phrase):
            score += 1

    for user in entry.get("example_users", []):
        if _phrase_overlaps(text, user):
            score += 1

    category_words = entry.get("industry_category", "").replace("_", " ")
    if category_words and _phrase_overlaps(text, category_words):
        score += 1

    return score


# Generic Persian words that appear in almost every user request regardless
# of industry (e.g. "می‌خوام", "که", "را") — these must NOT count as a
# meaningful signal on their own, or every entry would score equally on
# them and the matcher would effectively become random/order-dependent.
# This was the actual bug found while testing: "می‌خوام" alone was
# matching unrelated industries just because most common_user_phrases
# happen to start with it.
_STOP_WORDS = {
    "می‌خوام", "میخوام", "می‌خواهم", "میخواهم",
    "که", "را", "و", "یا", "این", "آن", "از", "به", "در", "با",
    "برای", "هم", "هست", "است", "می", "خوام", "یک", "چی", "چیزی",
    "ولی", "نمی‌دونم", "نمیدونم", "دقیق",
    "آنلاین", "مشتری‌ها", "مشتری", "بفروشم", "دارم",
}


def _meaningful_words(phrase: str) -> list[str]:
    return [w for w in phrase.split() if len(w) >= 3 and w not in _STOP_WORDS]


def _phrase_overlaps(text: str, phrase: str) -> bool:
    """
    Treats overlap loosely: true if the phrase appears as a substring,
    OR if at least one meaningful word (3+ characters, not a generic
    filler word) from the phrase appears in the text. This keeps
    matching forgiving for everyday Persian phrasing without needing
    real NLP, while avoiding false matches caused by common words like
    "می‌خوام" that appear in almost every request regardless of industry.
    """
    if not phrase:
        return False
    if phrase in text:
        return True
    words = _meaningful_words(phrase)
    return any(w in text for w in words)


# ── Blueprint construction ──────────────────────────────────────────────────

def _blueprint_from_entry(text: str, entry: dict, confidence: str, language: str) -> ProductBlueprint:
    digital_needs = entry.get("digital_need_categories", [])
    tool_types = entry.get("recommended_tool_types", [])
    best_output = entry.get("best_first_output")
    example_users = entry.get("example_users", [])
    common_problems = entry.get("common_problems", [])

    user_type = example_users[0] if example_users else None
    problem_summary = "؛ ".join(common_problems) if common_problems else None
    digital_need_category = ", ".join(digital_needs) if digital_needs else None
    recommended_tool_type = ", ".join(tool_types) if tool_types else None

    user_need = (
        f"کمک به یک {user_type} برای حل مشکل اصلی‌اش: {common_problems[0]}"
        if user_type and common_problems
        else "نیاز کاربر بر اساس شغل/زمینه مشابه تشخیص داده شد"
    )

    reason_for_recommendation = (
        f"با توجه به اینکه کاربر شبیه «{user_type}» است و مشکل اصلی او "
        f"«{common_problems[0]}» می‌باشد، «{best_output}» ساده‌ترین و "
        f"مناسب‌ترین نقطه شروع است."
        if user_type and common_problems and best_output
        else f"«{best_output}» ساده‌ترین نقطه شروع متناسب با این نیاز است."
    )

    return ProductBlueprint(
        raw_user_request=text,
        user_language=language,
        user_need=user_need,
        user_type=user_type,
        business_or_personal_context=(
            f"این درخواست به‌نظر متعلق به یک «{entry.get('industry_category')}» "
            f"است — یک کسب‌وکار کوچک یا مستقل، نه یک شرکت بزرگ."
        ),
        industry_category=entry.get("industry_category"),
        problem_to_solve=problem_summary,
        digital_need_category=digital_need_category,
        recommended_tool_type=recommended_tool_type,
        reason_for_recommendation=reason_for_recommendation,
        recommended_starting_point=best_output,
        first_output_type=best_output,
        core_features=list(entry.get("core_features", [])),
        future_features=list(entry.get("future_features", [])),
        launch_requirements=[],
        managed_product_needs=[],
        possible_ai_agents=list(entry.get("possible_ai_agents", [])),
        confidence_level=confidence,
        assumptions=[
            f"فرض شده کاربر شبیه «{user_type}» است" if user_type else
            "فرض شده این درخواست به این صنعت نزدیک است",
        ],
        open_questions=[],
        not_recommended=list(entry.get("not_recommended", [])),
        reason_not_recommended=entry.get("reason_not_recommended"),
    )


_FA_OPEN_QUESTIONS = [
    "می‌خواهی چه کاری برایت راه بیفتد؟",
    "این ابزار برای فروش، مدیریت کارها، حساب‌وکتاب، رزرو، یا پاسخ‌گویی به مشتری است؟",
    "آیا مخاطب این ابزار مشتری است، کارمند است، یا خودت هستی؟",
]

_EN_OPEN_QUESTIONS = [
    "What do you want this tool to help you with?",
    "Is this for selling, booking, accounting, task management, or customer support?",
    "Who will use this tool: customers, employees, or you?",
]


def _fallback_blueprint(text: str, language: str) -> ProductBlueprint:
    """
    Used when no industry-map entry matches well enough, OR when the
    request isn't Persian (the Industry-to-Product Map is Persian-first
    and not safe to match against other languages yet). Honest,
    low-confidence, and asks simple clarifying questions in the
    detected language instead of guessing — never invents a tool
    recommendation it isn't sure about.
    """
    if language == "en":
        questions = _EN_OPEN_QUESTIONS
        user_need = "The user's need is not yet fully clear."
    else:
        # Persian fallback for "fa", and also the safe default for
        # "unknown" — Persian is this platform's first/primary language.
        questions = _FA_OPEN_QUESTIONS
        user_need = "نیاز کاربر هنوز به‌طور کامل مشخص نشده است"

    return ProductBlueprint(
        raw_user_request=text,
        user_language=language,
        user_need=user_need,
        recommended_tool_type=None,
        recommended_starting_point=None,
        first_output_type=None,
        confidence_level="low",
        assumptions=[],
        open_questions=questions,
    )
