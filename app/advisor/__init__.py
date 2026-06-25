# Need-First Advisor — AI Factory v2 product-advisor layer.
#
# This package is gated behind ENABLE_NEED_FIRST_RECOMMENDATION. When the
# flag is off (default), nothing in this package is reached and the
# existing website-first diagnostic flow (app/providers/pm/mock_pm.py,
# anthropic_pm.py) runs completely unchanged.
#
# When the flag is on, this advisor runs BEFORE the website-section
# diagnostic question, so the factory explains what it understood and
# recommends a practical product/tool — instead of jumping straight to
# "سایت کافه چه بخش‌هایی داشته باشد؟" before the user has even confirmed
# they want a website at all.
