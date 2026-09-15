"""Schema base class: turns models, lists and pages into plain dicts."""

from __future__ import annotations

from typing import Any

from taskapp.services.pagination import Page


class Schema:
    fields: tuple[str, ...] = ()

    @classmethod
    def dump(cls, obj: Any) -> dict[str, Any]:
        if isinstance(obj, dict):
            return {name: obj[name] for name in cls.fields}
        return {name: getattr(obj, name) for name in cls.fields}

    @classmethod
    def render(cls, payload: Any) -> Any:
        if payload is None:
            return None
        if isinstance(payload, Page):
            return {
                "items": [cls.dump(item) for item in payload.items],
                "page": payload.page,
                "page_size": payload.page_size,
                "has_next": payload.has_next,
            }
        if isinstance(payload, list):
            return [cls.dump(item) for item in payload]
        return cls.dump(payload)
