"""In-memory storage backend."""

from __future__ import annotations

from itertools import count


class InMemoryStore:
    def __init__(self) -> None:
        self.tables: dict[str, dict[int, object]] = {}
        self._counters: dict[str, count] = {}

    def table(self, name: str) -> dict[int, object]:
        return self.tables.setdefault(name, {})

    def next_id(self, name: str) -> int:
        counter = self._counters.setdefault(name, count(start=1))
        return next(counter)
