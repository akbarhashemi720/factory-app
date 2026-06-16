"""
InMemoryStorage — AI Factory

A fully functional StorageProvider that requires no external credentials.

Purpose:
  - Removes the Supabase credential requirement for demo and development
  - Enables the full user journey (request → diagnostic → build → revise →
    approve → export) without any infrastructure setup
  - First step toward factory-managed infrastructure where customers never
    need to provide credentials

Part of the Build → Connect → Operate → Manage vision:
  Every future capability (agents, bots, automation) needs reliable state.
  This is the foundation. The customer never sees it.

Trade-offs:
  - Data does not persist across server restarts (acceptable for demo)
  - Not suitable for production multi-user scale (SupabaseStorage for that)
  - No concurrent write guarantees (single-instance only)

Hot-swap: set STORAGE_PROVIDER=memory in .env (or no .env at all)
"""
from __future__ import annotations

import copy
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from app.providers.storage.storage_provider import (
    QueryResult,
    StorageProvider,
    TableQuery,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class InMemoryTableQuery(TableQuery):
    """
    Fluent query builder backed by an in-memory dict-of-lists store.
    Supports the full subset of Supabase API that routes currently use.
    """

    def __init__(self, store: dict[str, list[dict]], table: str) -> None:
        self._store  = store
        self._table  = table
        self._lock   = threading.Lock()
        # Operation state
        self._op          : str | None  = None
        self._insert_data : dict | None = None
        self._update_data : dict | None = None
        self._filters     : list[tuple] = []
        self._order_col   : str | None  = None
        self._order_desc  : bool        = False
        self._limit_n     : int | None  = None
        self._select_cols : list[str]   = ["*"]

    # ── Builder methods ───────────────────────────────────────────────────────

    def select(self, *columns: str) -> "InMemoryTableQuery":
        self._op = "select"
        self._select_cols = list(columns) if columns else ["*"]
        return self

    def insert(self, data: dict | list) -> "InMemoryTableQuery":
        self._op = "insert"
        self._insert_data = data
        return self

    def update(self, data: dict) -> "InMemoryTableQuery":
        self._op = "update"
        self._update_data = data
        return self

    def delete(self) -> "InMemoryTableQuery":
        self._op = "delete"
        return self

    def eq(self, column: str, value: Any) -> "InMemoryTableQuery":
        self._filters.append(("eq", column, value))
        return self

    def neq(self, column: str, value: Any) -> "InMemoryTableQuery":
        self._filters.append(("neq", column, value))
        return self

    def order(self, column: str, desc: bool = False) -> "InMemoryTableQuery":
        self._order_col  = column
        self._order_desc = desc
        return self

    def limit(self, n: int) -> "InMemoryTableQuery":
        self._limit_n = n
        return self

    # ── Execute ───────────────────────────────────────────────────────────────

    def execute(self) -> QueryResult:
        with self._lock:
            if self._table not in self._store:
                self._store[self._table] = []

            rows = self._store[self._table]

            if self._op == "insert":
                return self._do_insert(rows)
            if self._op == "update":
                return self._do_update(rows)
            if self._op == "delete":
                return self._do_delete(rows)
            # default: select
            return self._do_select(rows)

    # ── Internal operations ───────────────────────────────────────────────────

    def _do_insert(self, rows: list) -> QueryResult:
        data = self._insert_data
        if isinstance(data, dict):
            data = [data]
        inserted = []
        for item in data:
            row = copy.deepcopy(item)
            # Auto-generate id and timestamps if not present
            if "id" not in row:
                row["id"] = str(uuid.uuid4())
            now = _now()
            row.setdefault("created_at", now)
            row.setdefault("updated_at", now)
            rows.append(row)
            inserted.append(copy.deepcopy(row))
        return QueryResult(inserted)

    def _do_update(self, rows: list) -> QueryResult:
        matched = self._apply_filters(rows)
        now = _now()
        updated = []
        for row in matched:
            row.update(self._update_data or {})
            row["updated_at"] = now
            updated.append(copy.deepcopy(row))
        return QueryResult(updated)

    def _do_delete(self, rows: list) -> QueryResult:
        to_remove = set(id(r) for r in self._apply_filters(rows))
        self._store[self._table] = [r for r in rows if id(r) not in to_remove]
        return QueryResult([])

    def _do_select(self, rows: list) -> QueryResult:
        result = self._apply_filters(rows)
        if self._order_col:
            result = sorted(
                result,
                key=lambda r: r.get(self._order_col, ""),
                reverse=self._order_desc,
            )
        if self._limit_n is not None:
            result = result[: self._limit_n]
        return QueryResult([copy.deepcopy(r) for r in result])

    def _apply_filters(self, rows: list) -> list:
        result = rows
        for f in self._filters:
            op, col, val = f
            if op == "eq":
                result = [r for r in result if str(r.get(col, "")) == str(val)]
            elif op == "neq":
                result = [r for r in result if str(r.get(col, "")) != str(val)]
        return result


class InMemoryStorage(StorageProvider):
    """
    Factory-internal storage with no external dependencies.

    The shared `_store` dict is the entire "database".
    Tables are created on demand.
    """

    # Class-level store — shared across all requests in the same process
    _store: dict[str, list[dict]] = {}

    @property
    def name(self) -> str:
        return "InMemoryStorage"

    def table(self, name: str) -> InMemoryTableQuery:
        return InMemoryTableQuery(self._store, name)

    def health_check(self) -> dict:
        return {
            "provider": self.name,
            "status":   "ok",
            "tables":   list(self._store.keys()),
            "rows":     {t: len(r) for t, r in self._store.items()},
        }

    @classmethod
    def reset(cls) -> None:
        """Clear all data. Useful for testing."""
        cls._store.clear()
