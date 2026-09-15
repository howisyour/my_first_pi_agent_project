"""Pagination helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from taskapp.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from taskapp.errors import ValidationError


@dataclass
class Page:
    items: list[Any]
    page: int
    page_size: int
    has_next: bool


def paginate(items: list[Any], page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Page:
    if page < 1:
        raise ValidationError("page must be >= 1", code="INVALID_PAGE")
    if page_size < 1 or page_size > MAX_PAGE_SIZE:
        raise ValidationError("page_size out of range", code="INVALID_PAGE_SIZE")
    start = (page - 1) * page_size
    end = start + page_size
    return Page(items=items[start:end], page=page, page_size=page_size, has_next=end < len(items))
