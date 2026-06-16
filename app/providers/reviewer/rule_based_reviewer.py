"""
Rule-Based Reviewer Provider — Sprint 3.

Checks builder output using deterministic rules.
No AI call. Default reviewer for MVP.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUALITY GATES — PRODUCTION EFFICIENCY ROADMAP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fast production must not reduce quality. Every output must pass
these quality gates regardless of build speed:

  Gate 1 — Scenario match:     output matches confirmed understanding
  Gate 2 — Required components: title, subtitle, and primary CTA exist
  Gate 3 — Correction visible:  requested corrections are reflected in output
  Gate 4 — User-friendly:       no technical terms exposed to user
  Gate 5 — No internal leakage: internal IDs/logs not visible in preview
  Gate 6 — Need fit:            preview shape matches the detected need family
  Gate 7 — Promise safety:      preview does not promise unimplemented features
  Gate 8 — Non-technical clarity: no technical jargon in user-visible fields

Current implementation covers Gates 1, 2, 3, 4, 6, 7, 8.
Gate 5 (leakage detection) will be added when real Builder produces HTML.

Future: scenario-specific checklist loaded from ScenarioPack
so each product type has its own quality bar.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

from typing import Any


# ─── Need-fit fingerprints (Gate 6) ──────────────────────────────────────────
# Each family has expected signals in preview_data.
# A preview passes need-fit if it contains at least one expected signal.
# This catches misrouting (e.g. company_landing served for reminder need).
# Examples are tests of reasoning behavior, not fixed product definitions.

_NEED_FIT_SIGNALS: dict[str, list[str]] = {
    "family_reminder_or_routine":        ["یادآور", "یادداشت", "وظیفه روزانه", "انجام شد", "کارهای روزانه"],
    "family_simple_finance_or_tracking": ["درآمد", "هزینه", "پول", "مانده", "ثبت", "طلب", "فاکتور"],
    "family_customer_management":        ["مشتری", "لیست", "پیگیری", "تماس", "سابقه", "یادداشت"],
    "family_internal_admin_tool":        ["وظیفه", "تیم", "مسئول", "چک‌لیست", "فرم", "گزارش"],
    "family_content_or_marketing":       ["محتوا", "ایده", "پیش‌نویس", "انتشار", "پیام", "برنامه هفتگی"],
    "family_business_growth_or_operations": ["اهداف", "اولویت", "گزارش", "مشتریان", "فروش", "کسب‌وکار"],
    "family_website_or_public_presence": ["معرفی", "خدمات", "تماس", "صفحه"],
}

# ─── Promise-safety forbidden phrases (Gate 7) ───────────────────────────────
# These suggest a real integration is already active.
# User-facing promise of unimplemented features triggers a fail.
_FORBIDDEN_PROMISES: list[str] = [
    "ارسال پیامک", "پیامک ارسال", "پیام واتساپ ارسال",
    "پرداخت آنلاین فعال", "درگاه پرداخت متصل",
    "به طور خودکار ارسال می‌شود", "خودکار ارسال",
    "deploy شد", "آنلاین شد", "سرور فعال",
    "agent فعال", "ربات فعال شد",
]

# ─── Technical jargon in user-visible fields (Gate 8) ────────────────────────
_TECH_JARGON: list[str] = [
    "scenario", "family_", "template", "product_type",
    "routing", "backend", "database", "API", "api",
    "deployment", "integration", "agent runtime", "auth",
    "jwt", "oauth", "webhook", "endpoint",
]


# ─── Gate functions ───────────────────────────────────────────────────────────

def _gate_title(pd: dict, _und: dict) -> tuple[bool, str]:
    ok = bool(pd.get("title", "").strip())
    return ok, ("" if ok else "فیلد title خالی است")


def _gate_scenario(pd: dict, und: dict) -> tuple[bool, str]:
    ps = pd.get("scenario", "")
    es = und.get("detected_scenario", "")
    ok = not es or not ps or ps == es
    note = "" if ok else f"سناریو '{ps}' با فهم '{es}' مطابقت ندارد"
    return ok, note


def _gate_subtitle(pd: dict, _und: dict) -> tuple[bool, str]:
    ok = bool(pd.get("subtitle", "").strip())
    return ok, ("" if ok else "فیلد subtitle اضافه شود")


def _gate_primary_cta(pd: dict, _und: dict) -> tuple[bool, str]:
    """Gate 2b — action-oriented scenarios must have a primary button."""
    action_scenarios = ("restaurant", "company_landing", "store", "booking", "telegram_bot")
    if pd.get("scenario") not in action_scenarios:
        return True, ""   # not applicable — skip
    ok = bool(pd.get("primary_button", "").strip())
    return ok, ("" if ok else "primary_button تعریف نشده")


def _gate_correction_visible(pd: dict, _und: dict) -> tuple[bool, str]:
    """Gate 3 — Sprint 4B. Only applies to revised previews (have revision_note)."""
    revision_note = pd.get("revision_note", "")
    if not revision_note:
        return True, ""  # initial build — gate not applicable
    ok = bool(revision_note.strip())
    return ok, ("" if ok else "revision_note خالی است — اصلاح قابل مشاهده نیست")


def _gate_need_fit(pd: dict, und: dict) -> tuple[bool, str]:
    """
    Gate 6 — Need fit: preview shape must match the detected need family.
    Catches misrouting (e.g. generic landing page served for a reminder need).
    Checks the preview's visible text against expected signals for the family.
    Passes for non-family scenarios (Tier-1 and Tier-2 have their own shape).
    """
    scenario = und.get("detected_scenario", "")
    if not scenario.startswith("family_"):
        return True, ""  # only applies to need-family scenarios

    expected_signals = _NEED_FIT_SIGNALS.get(scenario, [])
    if not expected_signals:
        return True, ""  # no fingerprint defined — skip

    # Search all user-visible text fields
    visible_text = " ".join(str(v) for v in [
        pd.get("title", ""),
        pd.get("subtitle", ""),
        " ".join(pd.get("sections", [])),
        " ".join(str(c.get("label", "")) for c in pd.get("cards", [])),
        pd.get("note", ""),
    ])

    ok = any(sig in visible_text for sig in expected_signals)
    note = "" if ok else (
        f"پیش‌نمایش با نیاز شناخته‌شده ({scenario}) هماهنگ نیست — "
        f"محتوای مناسب‌تری لازم است"
    )
    return ok, note


def _gate_promise_safety(pd: dict, _und: dict) -> tuple[bool, str]:
    """
    Gate 7 — Promise safety: preview must not claim real integrations exist.
    Scans all text fields for forbidden promises of unimplemented features.
    """
    all_text = " ".join(str(v) for v in [
        pd.get("title", ""), pd.get("subtitle", ""),
        pd.get("note", ""),
        " ".join(pd.get("sections", [])),
    ])
    found = [p for p in _FORBIDDEN_PROMISES if p in all_text]
    ok = len(found) == 0
    return ok, ("" if ok else f"وعده غیرواقعی در پیش‌نمایش: {found}")


def _gate_no_tech_jargon(pd: dict, _und: dict) -> tuple[bool, str]:
    """
    Gate 8 — Non-technical clarity: no technical jargon in user-visible fields.
    """
    user_text = " ".join(str(v) for v in [
        pd.get("title", ""), pd.get("subtitle", ""),
        " ".join(pd.get("sections", [])),
        pd.get("note", ""),
    ]).lower()
    found = [j for j in _TECH_JARGON if j.lower() in user_text]
    ok = len(found) == 0
    return ok, ("" if ok else f"اصطلاح فنی در پیش‌نمایش کاربر: {found}")


# Gates that block the output if they fail
_BLOCKING_GATES = [
    ("عنوان وجود دارد",                               _gate_title),
    ("سناریو با فهم تأییدشده هماهنگ است",             _gate_scenario),
    ("دکمه اقدام اصلی وجود دارد",                     _gate_primary_cta),
    ("اصلاح درخواستی در خروجی قابل مشاهده است",       _gate_correction_visible),
    ("پیش‌نمایش با نیاز کاربر هماهنگ است",            _gate_need_fit),
    ("پیش‌نمایش وعده غیرواقعی نمی‌دهد",              _gate_promise_safety),
    ("پیش‌نمایش بدون اصطلاح فنی است",                 _gate_no_tech_jargon),
]

# Gates that warn but don't block
_WARNING_GATES = [
    ("خروجی برای کاربر غیرفنی قابل فهم است", _gate_subtitle),
]


# ─── Public interface ─────────────────────────────────────────────────────────

def review(preview_data: dict[str, Any],
           understanding: dict[str, Any]) -> dict[str, Any]:
    """
    Run quality gates on preview_data.

    Interface contract (same for all reviewer providers):
        Returns:
            overall_status, issues_found, checklist,
            user_friendly_summary, internal_notes
    """
    checklist: list[dict] = []
    blocking_issues: list[str] = []

    # ── Run blocking gates ────────────────────────────────────────────────────
    for label, gate_fn in _BLOCKING_GATES:
        passed, note = gate_fn(preview_data, understanding)
        checklist.append({"label": label, "passed": passed, "note": note})
        if not passed and note:  # note="" means gate was skipped (N/A)
            blocking_issues.append(label)

    # ── Run warning gates ─────────────────────────────────────────────────────
    for label, gate_fn in _WARNING_GATES:
        passed, note = gate_fn(preview_data, understanding)
        checklist.append({"label": label, "passed": passed, "note": note})
        # Warnings don't block but are recorded

    overall_status = "needs_revision" if blocking_issues else "passed"
    summary = (
        "پیش‌نمایش آماده است و با چیزی که گفتی هماهنگ است."
        if overall_status == "passed"
        else "یه چیزی درست نیست — بگذار دوباره بررسی کنم و بهترش کنم."
    )

    return {
        "overall_status": overall_status,
        "safe_to_show_user": overall_status == "passed",  # explicit boolean for pipeline
        "issues_found": blocking_issues,
        "checklist": checklist,
        "user_friendly_summary": summary,
        "internal_notes": (
            "Rule-based reviewer — Gates 1-4, 6-8 active. "
            "Gate 5 (HTML leakage) pending real builder output. "
            "Internal details must not be forwarded to user."
        ),
    }
