"""Query-string parsing."""

from taskapp.constants import DEFAULT_PAGE_SIZE
from taskapp.utils.ids import parse_positive_int


def parse_page_params(query: dict[str, str], default_size: int = DEFAULT_PAGE_SIZE) -> tuple[int, int]:
    page = parse_positive_int(query.get("page", "1"), field="page")
    size = parse_positive_int(query.get("page_size", str(default_size)), field="page_size")
    return page, size
