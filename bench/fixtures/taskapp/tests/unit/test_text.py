from taskapp.utils.text import normalize_title, slugify


def test_normalize_title_collapses_whitespace():
    assert normalize_title("  fix   the\tbug ") == "fix the bug"


def test_slugify():
    assert slugify("Hello, World  2026!") == "hello-world-2026"
