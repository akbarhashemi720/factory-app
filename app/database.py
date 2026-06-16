"""
Factory Storage Gateway

Routes always call get_db() — they never import a provider directly.
The factory decides which storage provider to use based on STORAGE_PROVIDER.

STORAGE_PROVIDER=memory   → InMemoryStorage (no credentials, demo/dev/test)
STORAGE_PROVIDER=supabase → SupabaseStorage (factory-owned credentials)

The customer never sees credentials. The customer never configures storage.
This is part of the Build → Connect → Operate → Manage foundation:
every future capability needs reliable state — this is that foundation.
"""
from __future__ import annotations

from app.config import settings
from app.providers.storage.storage_provider import StorageProvider

_provider: StorageProvider | None = None


def get_db() -> StorageProvider:
    """Return the configured storage provider. Initialised once on first call."""
    global _provider
    if _provider is None:
        _provider = _build_provider()
    return _provider


def _build_provider() -> StorageProvider:
    p = settings.storage_provider.lower().strip()

    if p == "supabase":
        if not settings.supabase_url or not settings.supabase_service_key:
            raise RuntimeError(
                "STORAGE_PROVIDER=supabase requires SUPABASE_URL and "
                "SUPABASE_SERVICE_KEY to be set. "
                "Set STORAGE_PROVIDER=memory for credential-free operation."
            )
        from app.providers.storage.supabase_storage import SupabaseStorage
        return SupabaseStorage()

    # Default: memory — no credentials needed
    from app.providers.storage.in_memory import InMemoryStorage
    return InMemoryStorage()


def reset_db() -> None:
    """Reset provider — useful for testing."""
    global _provider
    _provider = None
