"""
StorageProvider Interface — AI Factory

Defines the contract that all storage implementations must fulfill.
The API intentionally mirrors the Supabase client's fluent query interface
so existing routes (db.table(...).select(...).eq(...).execute()) work
without any changes.

Current implementations:
  InMemoryStorage  — no credentials needed (demo, test, MVP)
  SupabaseStorage  — factory-owned Supabase instance (production)

Future: PostgresStorage, PlanetScaleStorage, etc.
All are hot-swappable via STORAGE_PROVIDER env var.
"""
from __future__ import annotations

from abc import abstractmethod
from typing import Any

from app.providers.storage.base_provider import BaseProvider


class StorageProvider(BaseProvider):
    """
    Abstract storage provider.

    Routes always call:
        db = get_db()
        result = db.table("projects").select("*").eq("id", x).execute()
        result.data  # list[dict]

    Any StorageProvider implementation must return objects that support this pattern.
    """

    @abstractmethod
    def table(self, name: str) -> "TableQuery":
        """Return a query builder for the named table."""


class QueryResult:
    """Mimics Supabase APIResponse — result.data is always a list."""
    def __init__(self, data: list[dict[str, Any]]):
        self.data = data


class TableQuery:
    """
    Fluent query builder that routes call.
    Concrete implementations (InMemory, Supabase) override _execute().
    """

    def select(self, *columns: str) -> "TableQuery":
        return self

    def insert(self, data: dict | list) -> "TableQuery":
        return self

    def update(self, data: dict) -> "TableQuery":
        return self

    def delete(self) -> "TableQuery":
        return self

    def eq(self, column: str, value: Any) -> "TableQuery":
        return self

    def neq(self, column: str, value: Any) -> "TableQuery":
        return self

    def order(self, column: str, desc: bool = False) -> "TableQuery":
        return self

    def limit(self, n: int) -> "TableQuery":
        return self

    def execute(self) -> QueryResult:
        raise NotImplementedError
