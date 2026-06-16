"""
Revision Service.

Interprets user correction text and applies changes to an existing
preview_data dict. No AI call. No real code generation.

Rules:
  - Changes must be faithful to the user request.
  - Visible preview and revision_note must never contradict each other.
  - Removal requests must remove, not enhance.
  - If the system cannot apply a change, say so honestly.
  - Never fake a name change without user-provided data.
"""
from __future__ import annotations

import copy
from typing import Any


# ─── Priority 0: removal keywords (checked before anything else) ─────────────
# These must win over update_button/update_title to avoid opposite-direction fixes.

_REMOVAL_KEYWORDS: list[str] = [
    "حذف کن", "حذفش کن", "بردار", "برش دار", "نباشه", "نباشد",
    "نذار", "نذارش", "پاک کن", "پاکش کن", "remove",
]

def _is_removal(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in _REMOVAL_KEYWORDS)


# ─── Keyword map (lower priority than removal) ────────────────────────────────

_KEYWORDS: list[tuple[str, list[str]]] = [
    ("make_title_friendly",  ["دوستانه", "صمیمی‌تر", "گرم‌تر", "friendly"]),
    ("update_title",         ["عنوان", "تایتل", "title"]),
    ("update_button",        ["دکمه", "button", "btn", "کلید"]),
    ("add_contact",          ["تماس", "contact", "ارتباط", "تلفن"]),
    ("remove_contact",       ["حذف تماس", "بدون تماس", "remove contact"]),
    ("update_subtitle",      ["زیرعنوان", "subtitle", "توضیح"]),
    ("make_calmer",          ["آرام‌تر", "خلوت‌تر", "ساده‌تر", "calmer", "simpler"]),
    ("make_bolder",          ["بزرگ‌تر", "واضح‌تر", "برجسته‌تر", "bolder", "clearer"]),
    ("add_products",         ["محصول", "آیتم", "کالا", "product", "item"]),
    ("rename_business",      ["اسم", "نام", "name"]),
]


def interpret_revision(raw_revision_text: str) -> list[dict[str, Any]]:
    """
    Convert free-text revision request into a list of structured actions.

    Priority rules:
      1. Removal intent beats all other keywords on the same token.
      2. make_title_friendly beats update_title for friendliness requests.
      3. Falls back to general_revision only if nothing matches.
    """
    t = raw_revision_text.lower()
    removal = _is_removal(t)
    actions: list[dict[str, Any]] = []

    # --- Removal path ---
    if removal:
        # Determine what to remove
        if any(kw in t for kw in ["دکمه", "button", "btn", "کلید"]):
            if any(kw in t for kw in ["تماس", "contact"]):
                actions.append({"type": "remove_contact", "value": raw_revision_text})
            else:
                actions.append({"type": "remove_primary_button", "value": raw_revision_text})
        elif any(kw in t for kw in ["تماس", "contact", "ارتباط"]):
            actions.append({"type": "remove_contact", "value": raw_revision_text})
        else:
            actions.append({"type": "general_revision", "value": raw_revision_text})
        return actions

    # --- Non-removal path ---
    for action_type, keywords in _KEYWORDS:
        if any(kw in t for kw in keywords):
            actions.append({"type": action_type, "value": raw_revision_text})

    # Deduplicate: if make_title_friendly triggered, suppress plain update_title
    types = [a["type"] for a in actions]
    if "make_title_friendly" in types:
        actions = [a for a in actions if a["type"] != "update_title"]

    if not actions:
        actions = [{"type": "general_revision", "value": raw_revision_text}]

    return actions


def apply_revision_to_preview(
    previous_preview: dict[str, Any],
    actions: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Apply structured actions to a copy of previous_preview.

    Rules:
      - Changes must match what the user asked.
      - Removal must remove, not enhance.
      - If change cannot be applied honestly, say so in revision_note.
      - revision_note must reflect what actually changed, not what was intended.
    """
    preview = copy.deepcopy(previous_preview)
    action_descriptions: list[str] = []

    for action in actions:
        atype = action["type"]
        value = action.get("value", "")

        # ── Fix 1A: make title friendlier — meaningful visible change ─────────
        if atype == "make_title_friendly":
            current = preview.get("title", "")
            # Append a warm Persian phrase that is visibly different
            preview["title"] = current + " — دوستانه‌تر"
            action_descriptions.append("عنوان دوستانه‌تر شد")

        # ── Fix 1B: rename_business — honest, asks for new name if missing ────
        elif atype == "rename_business":
            v = value.lower()
            # Try to extract an explicit new name after keywords like "بگذار", "بشه", "کن"
            new_name = _extract_new_name(value)
            if new_name:
                preview["title"] = new_name
                action_descriptions.append(f"اسم به «{new_name}» تغییر کرد")
            else:
                # Cannot fake a name change — be honest
                action_descriptions.append("برای تغییر اسم، نام جدید را بنویس.")
                # Preview title stays unchanged — note makes it honest

        # ── update_title: generic title edit (not rename, not friendlier) ─────
        elif atype == "update_title":
            current = preview.get("title", "")
            preview["title"] = current + " (ویرایش شد)"
            action_descriptions.append("عنوان به‌روزرسانی شد")

        # ── update_button: make more prominent ────────────────────────────────
        elif atype == "update_button":
            prev_btn = preview.get("primary_button", "مشاهده")
            preview["primary_button"] = prev_btn + " ←"
            action_descriptions.append("دکمه اصلی واضح‌تر شد")

        # ── Fix 2: remove_primary_button — remove, do not enhance ─────────────
        elif atype == "remove_primary_button":
            if preview.get("primary_button"):
                preview.pop("primary_button", None)
                action_descriptions.append("دکمه موردنظر حذف شد")
            else:
                action_descriptions.append("دکمه‌ای برای حذف پیدا نشد")

        # ── add_contact ───────────────────────────────────────────────────────
        elif atype == "add_contact":
            preview["show_contact"] = True
            preview["contact_text"] = "برای تماس کلیک کنید"
            if not preview.get("secondary_button"):
                preview["secondary_button"] = "تماس"
            action_descriptions.append("بخش تماس اضافه شد")

        # ── remove_contact ────────────────────────────────────────────────────
        elif atype == "remove_contact":
            preview["show_contact"] = False
            preview.pop("contact_text", None)
            # Also remove secondary_button if it is contact-related
            sec = preview.get("secondary_button", "")
            if sec in ("تماس", "تماس با ما", "contact", "ارتباط"):
                preview.pop("secondary_button", None)
            action_descriptions.append("دکمه تماس حذف شد")

        # ── update_subtitle ───────────────────────────────────────────────────
        elif atype == "update_subtitle":
            current = preview.get("subtitle", "")
            preview["subtitle"] = current + " — ویرایش شد"
            action_descriptions.append("زیرعنوان به‌روز شد")

        # ── make_calmer ───────────────────────────────────────────────────────
        elif atype == "make_calmer":
            preview["tone"] = "calm"
            # Fix 4: make the note honest and visible even though tone is internal
            action_descriptions.append("نسخه ساده‌تر و آرام‌تر شد")

        # ── make_bolder ───────────────────────────────────────────────────────
        elif atype == "make_bolder":
            preview["tone"] = "bold"
            action_descriptions.append("المان‌های اصلی برجسته‌تر شدند")

        # ── Fix 3: add_products — add visible placeholder items ───────────────
        elif atype == "add_products":
            scenario = preview.get("scenario", "")
            if scenario in ("store", "general_showcase", "general_ordering", "restaurant"):
                # Add visible sample items to sections or menu_items
                if "menu_items" in preview:
                    # restaurant: add to existing menu
                    preview["menu_items"].append(
                        {"name": "محصول نمونه جدید", "price": "—"}
                    )
                    action_descriptions.append("یک آیتم نمونه اضافه شد")
                elif "sections" in preview:
                    # store/showcase: add sample product sections
                    preview["sections"] = (
                        preview.get("sections", []) +
                        ["محصول نمونه ۱", "محصول نمونه ۲", "محصول نمونه ۳"]
                    )
                    action_descriptions.append("نمونه محصولات به پیش‌نمایش اضافه شد")
                else:
                    preview["sections"] = ["محصول نمونه ۱", "محصول نمونه ۲"]
                    action_descriptions.append("نمونه محصولات به پیش‌نمایش اضافه شد")
            else:
                # Fix 3B: honest note when cannot apply
                action_descriptions.append("برای این تغییر، کمی اطلاعات بیشتر لازم است.")

        # ── general_revision — honest fallback ───────────────────────────────
        else:
            # Fix 3C: don't claim change happened if nothing visibly changed
            action_descriptions.append("برای این تغییر، کمی اطلاعات بیشتر لازم است.")

    # Gate 3: revision_note proves correction is visible
    preview["revision_note"] = " | ".join(action_descriptions)

    return preview


def _extract_new_name(text: str) -> str | None:
    """
    Try to extract an explicit new business name from text like:
      'اسم را بگذار کافه ماه' → 'کافه ماه'
      'اسم کسب‌وکار را عوض کن' → None (no name given)
    """
    import re
    # Look for patterns like: بگذار X, بشه X, بشود X, کن X (after keyword)
    patterns = [
        r'بگذار\s+(.+)',
        r'بذار\s+(.+)',
        r'بشه\s+(.+)',
        r'بشود\s+(.+)',
        r'نام\s+(.+?)\s+بگذار',
        r'اسم\s+(.+?)\s+بگذار',
        r'بگو\s+(.+)',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            candidate = m.group(1).strip().rstrip(".")
            # Must be at least 2 chars and not a verb
            if len(candidate) >= 2 and candidate not in ["کن", "بده", "شود", "شه"]:
                return candidate
    return None
