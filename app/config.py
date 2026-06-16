from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Storage provider ──────────────────────────────────────────────────────
    # memory   = InMemoryStorage (no credentials needed — demo, dev, test)
    # supabase = SupabaseStorage (factory-owned Supabase — production)
    # Future: postgres, planetscale, ...
    storage_provider: str = "memory"

    # ── Supabase (only required when storage_provider=supabase) ───────────────
    supabase_url: str = ""
    supabase_service_key: str = ""

    # ── Deployment — CORS ─────────────────────────────────────────────────────
    # Set ALLOWED_ORIGINS to the deployed frontend URL before production deploy.
    # Multiple origins: comma-separated. Default "*" is for local/demo use only.
    # Example: https://ai-factory-xyz.vercel.app
    allowed_origins: str = "*"  # operator sets this via env var ALLOWED_ORIGINS
    app_env: str = "development"
    app_version: str = "sprint-storage-v1"

    # ── Provider selection ─────────────────────────────────────────────────────
    # Roles are stable. Providers are replaceable.
    pm_provider: str = "mock"              # mock | openai | anthropic
    builder_provider: str = "mock"         # mock | claude_code
    reviewer_provider: str = "rule_based"  # rule_based | ai

    # ai_provider kept for backward compatibility with Sprint 1/2 configs.
    # pm_provider is the preferred setting going forward.
    ai_provider: str = "mock"

    # ── AI API keys (required only when provider != mock) ──────────────────────
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
