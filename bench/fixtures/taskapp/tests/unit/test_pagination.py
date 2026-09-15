import pytest

from taskapp.errors import ValidationError
from taskapp.services.pagination import paginate


def test_first_page_has_next_when_more_items():
    page = paginate(list(range(45)), page=1, page_size=20)
    assert len(page.items) == 20
    assert page.has_next is True


def test_exact_last_page_has_no_next():
    page = paginate(list(range(40)), page=2, page_size=20)
    assert page.items == list(range(20, 40))
    assert page.has_next is False


def test_page_must_be_positive():
    with pytest.raises(ValidationError):
        paginate([], page=0)


def test_page_size_is_capped():
    with pytest.raises(ValidationError):
        paginate([], page=1, page_size=1000)
