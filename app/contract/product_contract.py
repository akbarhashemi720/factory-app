"""
Product Contract — central validation module (Legacy Replacement Sprint).

Core rule: NO Product Contract, NO preview.

This module is the ONLY place that defines:
  1. the list of valid preview archetypes (Phase 4 — central archetype list)
  2. what counts as a complete, valid Product Contract (Phase 3)

Both app/advisor/need_first_advisor.py (which builds candidate contracts
from the user's request/option choice) and
app/providers/builder/html_builder.py (which consumes a validated
contract to render a preview) import VALID_ARCHETYPES from here. Neither
file defines its own separate archetype list — this is what Phase 4
explicitly requires ("remove separate inconsistent archetype lists").
"""
from __future__ import annotations

from dataclasses import dataclass


# ── Central archetype list (Phase 4) ─────────────────────────────────────────
# Exactly the 8 archetypes named in the sprint brief. booking_page_mockup is
# included but is only ever assigned by the advisor when the user's own
# request/option explicitly supports booking (e.g. "رزرو وقت اندازه‌گیری")
# — never as a silent fallback for unrelated requests.
VALID_ARCHETYPES: frozenset[str] = frozenset({
    "task_dashboard_mockup",
    "team_task_board_mockup",
    "simple_crm_followup_mockup",
    "product_catalog_order_page",
    "digital_menu_order_page",
    "service_portfolio_request_page",
    "lead_landing_page",
    "booking_page_mockup",
})


@dataclass(frozen=True)
class ProductContract:
    """
    A validated, immutable record of exactly what the user asked for and
    confirmed. Builder functions receive THIS, not raw `understanding`
    dict fields like scenario/website_intent — those legacy fields
    cannot override or influence a confirmed contract.
    """
    raw_request: str
    selected_option_id: str
    selected_label: str
    preview_archetype: str
    proposed_sections: tuple[str, ...]
    confirmed_scope_text: str


class ContractValidationError(ValueError):
    """Raised when a candidate contract fails validation. Carries a safe,
    user-facing Persian message — never a stack trace or technical detail."""
    def __init__(self, user_message_fa: str, reason_code: str):
        super().__init__(reason_code)
        self.user_message_fa = user_message_fa
        self.reason_code = reason_code


_BLOCKED_MESSAGE_FA = (
    "برای ساخت پیش‌نمایش، اول باید یکی از گزینه‌های پیشنهادی را انتخاب کنی. "
    "یک گزینه را انتخاب کن یا دوباره توضیح بده."
)


def validate_contract(
    raw_request: str | None,
    selected_option_id: str | None,
    selected_label: str | None,
    preview_archetype: str | None,
    proposed_sections: list[str] | None,
    confirmed_scope_text: str | None = None,
) -> ProductContract:
    """
    Validates a candidate Product Contract per Phase 3's exact rules:
      - selected_option_id must be present
      - selected_label must be present
      - preview_archetype must be present
      - preview_archetype must be one of VALID_ARCHETYPES
      - proposed_sections must be non-empty
      - proposed_sections must have at least 3 items (matches the
        empty-screen-prevention rule from the previous sprint)

    Raises ContractValidationError (with a safe Persian message, never a
    technical detail) if any rule fails. Never returns a partial/invalid
    contract — callers must NOT proceed to preview generation if this
    raises.
    """
    if not selected_option_id:
        raise ContractValidationError(_BLOCKED_MESSAGE_FA, "missing_option_id")

    if not selected_label:
        raise ContractValidationError(_BLOCKED_MESSAGE_FA, "missing_label")

    if not preview_archetype:
        raise ContractValidationError(_BLOCKED_MESSAGE_FA, "missing_archetype")

    if preview_archetype not in VALID_ARCHETYPES:
        raise ContractValidationError(_BLOCKED_MESSAGE_FA, "unknown_archetype")

    sections = proposed_sections or []
    if len(sections) < 3:
        raise ContractValidationError(_BLOCKED_MESSAGE_FA, "insufficient_sections")

    return ProductContract(
        raw_request=raw_request or "",
        selected_option_id=selected_option_id,
        selected_label=selected_label,
        preview_archetype=preview_archetype,
        proposed_sections=tuple(sections),
        confirmed_scope_text=confirmed_scope_text or selected_label,
    )
