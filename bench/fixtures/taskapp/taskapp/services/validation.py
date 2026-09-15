"""Input validation."""

from taskapp.constants import MAX_COMMENT_LENGTH, MAX_TITLE_LENGTH, PRIORITY_MAX, PRIORITY_MIN, TASK_STATUSES
from taskapp.errors import ValidationError
from taskapp.utils.text import normalize_title


def validate_title(raw) -> str:
    if not isinstance(raw, str):
        raise ValidationError("title must be a string", code="INVALID_TITLE")
    title = normalize_title(raw)
    if not title or len(title) > MAX_TITLE_LENGTH:
        raise ValidationError("title length out of range", code="INVALID_TITLE")
    return title


def validate_priority(raw) -> int:
    if not isinstance(raw, int) or isinstance(raw, bool) or not PRIORITY_MIN <= raw <= PRIORITY_MAX:
        raise ValidationError("priority out of range", code="INVALID_PRIORITY")
    return raw


def validate_status(raw) -> str:
    if raw not in TASK_STATUSES:
        raise ValidationError("unknown status", code="INVALID_STATUS")
    return raw


def validate_comment_body(raw) -> str:
    if not isinstance(raw, str) or not raw.strip() or len(raw) > MAX_COMMENT_LENGTH:
        raise ValidationError("comment body length out of range", code="INVALID_COMMENT")
    return raw.strip()
