import pytest

from taskapp.errors import ValidationError
from taskapp.services.validation import validate_priority, validate_status, validate_title


def test_validate_title_normalizes():
    assert validate_title("  write   docs ") == "write docs"


def test_validate_title_rejects_empty():
    with pytest.raises(ValidationError):
        validate_title("   ")


@pytest.mark.parametrize("value", [0, 6, True, "3"])
def test_validate_priority_rejects_out_of_range(value):
    with pytest.raises(ValidationError):
        validate_priority(value)


def test_validate_status():
    assert validate_status("done") == "done"
    with pytest.raises(ValidationError):
        validate_status("closed")
