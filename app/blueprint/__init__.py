# Product Blueprint — AI Factory v2 thinking layer (planning stage).
#
# This package is intentionally ISOLATED: nothing in the current app
# imports from it yet. It exists only to define the data shape of a
# future "Product Blueprint" — the layer that will eventually sit
# between Solution Recommendation and the Output Builder in the
# AI Factory v2 flow:
#
#   User need -> Need Understanding -> Solution Recommendation
#   -> Product Blueprint -> Output Builder -> Launch -> Managed Product Layer
#
# The current Website Preview Builder flow (pm_agent, builder,
# generate-preview, approve, export) is NOT touched by this package
# and continues to work exactly as before.
