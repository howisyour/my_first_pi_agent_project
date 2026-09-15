"""Identifier parsing."""

from taskapp.errors import ValidationError


def parse_positive_int(raw: str, *, field: str) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be an integer", code="INVALID_ID") from exc
    if value < 1:
        raise ValidationError(f"{field} must be positive", code="INVALID_ID")
    return value


def parse_id(raw: str, *, field: str = "id") -> int:
    return parse_positive_int(raw, field=field)
