import pytest

from taskapp.errors import ValidationError
from taskapp.utils.ids import parse_id


def test_parse_id():
    assert parse_id("42") == 42


@pytest.mark.parametrize("raw", ["", "abc", "0", "-3"])
def test_parse_id_rejects_bad_input(raw):
    with pytest.raises(ValidationError):
        parse_id(raw)
