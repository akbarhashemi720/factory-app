# Product Contract — central validation for the need-first flow.
#
# Core rule (Legacy Replacement Sprint): NO Product Contract, NO preview.
#
# This package is the single source of truth for which preview
# archetypes exist and what counts as a valid, complete contract before
# any preview is generated. Both app/advisor (which CREATES candidate
# contracts from user choices) and app/providers/builder (which
# CONSUMES a validated contract to render a preview) import from here —
# neither defines its own separate archetype list.
