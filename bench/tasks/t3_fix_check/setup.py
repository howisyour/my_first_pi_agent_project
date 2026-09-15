from bench.runner.edits import replace_once

CHANGES = [
    (
        "taskapp/services/validation.py",
        "from taskapp.constants import MAX_COMMENT_LENGTH, MAX_TITLE_LENGTH,",
        "from taskapp.constants import MAX_TITLE_LENGTH,",
    ),
    (
        "taskapp/services/validation.py",
        "len(raw) > MAX_COMMENT_LENGTH:",
        "len(raw) > 2000:",
    ),
    (
        "taskapp/services/users.py",
        'raise NotFoundError(f"user {user_id} not found", code="USER_NOT_FOUND")',
        'raise ValueError(f"user {user_id} not found")',
    ),
    (
        "taskapp/utils/timeutil.py",
        '"""Time helpers."""\n\n',
        '"""Time helpers."""\n\nimport os\n',
    ),
]


def apply(workdir):
    for rel, old, new in CHANGES:
        replace_once(workdir / rel, old, new)
