from bench.runner.edits import replace_once


def apply(workdir):
    app = workdir / "taskapp"
    replace_once(app / "constants.py", "DEFAULT_PAGE_SIZE = 20\n", "LIST_PAGE_SIZE = 25\nSEARCH_PAGE_SIZE = 10\n")

    replace_once(
        app / "routes/tasks.py",
        "from taskapp.constants import DEFAULT_PAGE_SIZE, DEFAULT_PRIORITY, HTTP_CREATED, HTTP_OK",
        "from taskapp.constants import DEFAULT_PRIORITY, HTTP_CREATED, HTTP_OK, LIST_PAGE_SIZE, SEARCH_PAGE_SIZE",
    )
    replace_once(
        app / "routes/tasks.py",
        "def search_tasks(store, request):\n    page, size = parse_page_params(request.query, default_size=DEFAULT_PAGE_SIZE)",
        "def search_tasks(store, request):\n    page, size = parse_page_params(request.query, default_size=SEARCH_PAGE_SIZE)",
    )
    replace_once(
        app / "routes/tasks.py",
        "default_size=DEFAULT_PAGE_SIZE)",
        "default_size=LIST_PAGE_SIZE)",
    )

    replace_once(
        app / "services/tasks.py",
        "from taskapp.constants import DEFAULT_PAGE_SIZE, DEFAULT_PRIORITY",
        "from taskapp.constants import DEFAULT_PRIORITY, SEARCH_PAGE_SIZE",
    )
    replace_once(app / "services/tasks.py", "page_size: int = DEFAULT_PAGE_SIZE", "page_size: int = SEARCH_PAGE_SIZE")

    replace_once(
        app / "routes/projects.py",
        "from taskapp.constants import DEFAULT_PAGE_SIZE, HTTP_CREATED, HTTP_OK",
        "from taskapp.constants import HTTP_CREATED, HTTP_OK, LIST_PAGE_SIZE",
    )
    replace_once(app / "routes/projects.py", "default_size=DEFAULT_PAGE_SIZE", "default_size=LIST_PAGE_SIZE")

    replace_once(
        app / "routes/users.py",
        "from taskapp.constants import DEFAULT_PAGE_SIZE, HTTP_OK",
        "from taskapp.constants import HTTP_OK, LIST_PAGE_SIZE",
    )
    replace_once(app / "routes/users.py", "default_size=DEFAULT_PAGE_SIZE", "default_size=LIST_PAGE_SIZE")

    replace_once(
        app / "services/pagination.py",
        "from taskapp.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE",
        "from taskapp.constants import LIST_PAGE_SIZE, MAX_PAGE_SIZE",
    )
    replace_once(app / "services/pagination.py", "page_size: int = DEFAULT_PAGE_SIZE", "page_size: int = LIST_PAGE_SIZE")

    replace_once(
        app / "utils/querystring.py",
        "from taskapp.constants import DEFAULT_PAGE_SIZE",
        "from taskapp.constants import LIST_PAGE_SIZE",
    )
    replace_once(app / "utils/querystring.py", "default_size: int = DEFAULT_PAGE_SIZE", "default_size: int = LIST_PAGE_SIZE")
