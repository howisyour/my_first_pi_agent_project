from bench.runner.edits import replace_once


def apply(workdir):
    replace_once(
        workdir / "taskapp/services/pagination.py",
        "has_next=end <= len(items))",
        "has_next=end < len(items))",
    )
