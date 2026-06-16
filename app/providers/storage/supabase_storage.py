"""
SupabaseStorage — AI Factory

Wraps the Supabase client behind the StorageProvider interface.
Used when STORAGE_PROVIDER=supabase (factory-owned credentials).

The customer never provides or sees these credentials.
They are owned and managed by the factory.
"""
from __future__ import annotations

from typing import Any

from app.providers.storage.storage_provider import QueryResult, StorageProvider, TableQuery


class SupabaseTableQuery(TableQuery):
    """Delegates to the real Supabase query builder."""

    def __init__(self, real_query: Any) -> None:
        self._q = real_query

    def select(self, *columns: str) -> "SupabaseTableQuery":
        cols = ", ".join(columns) if columns else "*"
        return SupabaseTableQuery(self._q.select(cols))

    def insert(self, data: dict | list) -> "SupabaseTableQuery":
        return SupabaseTableQuery(self._q.insert(data))

    def update(self, data: dict) -> "SupabaseTableQuery":
        return SupabaseTableQuery(self._q.update(data))

    def delete(self) -> "SupabaseTableQuery":
        return SupabaseTableQuery(self._q.delete())

    def eq(self, column: str, value: Any) -> "SupabaseTableQuery":
        return SupabaseTableQuery(self._q.eq(column, value))

    def neq(self, column: str, value: Any) -> "SupabaseTableQuery":
        return SupabaseTableQuery(self._q.neq(column, value))

    def order(self, column: str, desc: bool = False) -> "SupabaseTableQuery":
        return SupabaseTableQuery(self._q.order(column, desc=desc))

    def limit(self, n: int) -> "SupabaseTableQuery":
        return SupabaseTableQuery(self._q.limit(n))

    def execute(self) -> QueryResult:
        resp = self._q.execute()
        return QueryResult(resp.data if resp.data is not None else [])


class SupabaseStorage(StorageProvider):
    """Factory-owned Supabase instance. Credentials are never customer-provided."""

    def __init__(self) -> None:
        from supabase import create_client
        from app.config import settings
        self._client = create_client(settings.supabase_url, settings.supabase_service_key)

    @property
    def name(self) -> str:
        return "SupabaseStorage"

    def table(self, name: str) -> SupabaseTableQuery:
        return SupabaseTableQuery(self._client.table(name))
