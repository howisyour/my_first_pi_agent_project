"""Text helpers."""

import re

_WHITESPACE = re.compile(r"\s+")
_NON_SLUG = re.compile(r"[^a-z0-9]+")


def normalize_title(raw: str) -> str:
    return _WHITESPACE.sub(" ", raw).strip()


def slugify(raw: str) -> str:
    return _NON_SLUG.sub("-", normalize_title(raw).lower()).strip("-")
