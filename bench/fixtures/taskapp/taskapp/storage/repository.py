"""Typed access to store tables."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class Repository(Generic[T]):
    def __init__(self, store, name: str) -> None:
        self._store = store
        self._name = name

    def add(self, factory: Callable[[int], T]) -> T:
        new_id = self._store.next_id(self._name)
        obj = factory(new_id)
        self._store.table(self._name)[new_id] = obj
        return obj

    def get(self, obj_id: int) -> T | None:
        return self._store.table(self._name).get(obj_id)

    def all(self) -> list[T]:
        return sorted(self._store.table(self._name).values(), key=lambda obj: obj.id)

    def save(self, obj: T) -> T:
        self._store.table(self._name)[obj.id] = obj
        return obj


def get_repo(store, name: str) -> Repository:
    return Repository(store, name)
