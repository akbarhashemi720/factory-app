# Industry-to-Product Map — AI Factory v2 planning layer (data only).
#
# This package is intentionally ISOLATED: nothing in the current app
# imports from it yet. It exists only to hold the static
# Industry-to-Product Map — the data that will eventually help the
# future Solution Recommendation layer suggest the right digital tool
# based on a person's ordinary job/need, instead of asking
# "website, bot, or app?" up front.
#
#   User need -> Need Understanding -> Solution Recommendation
#   (uses this map) -> Product Blueprint -> Output Builder -> Launch
#   -> Managed Product Layer
#
# The current Website Preview Builder flow (pm_agent, builder,
# generate-preview, approve, export) and the ProductBlueprint model
# (app/blueprint/) are NOT touched by this package and continue to
# work exactly as before.
