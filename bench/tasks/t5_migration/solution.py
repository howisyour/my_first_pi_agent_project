import os
import subprocess

from bench.runner.config import PYTHON_EXE
from bench.runner.edits import append_text, replace_once

MIGRATION = '''"""Add Task.due_date (schema version 3)."""

VERSION = 3
TABLE = "tasks"
FIELD = "due_date"


def up(store) -> None:
    for record in store.table(TABLE).values():
        if FIELD not in vars(record):
            setattr(record, FIELD, None)


def down(store) -> None:
    for record in store.table(TABLE).values():
        if FIELD in vars(record):
            delattr(record, FIELD)
'''


def apply(workdir):
    replace_once(workdir / "schema/models.json", '"version": 2', '"version": 3')
    replace_once(
        workdir / "schema/models.json",
        '{"name": "assignee_id", "type": "int | None", "default": "None"}',
        '{"name": "assignee_id", "type": "int | None", "default": "None"},\n'
        '        {"name": "due_date", "type": "str | None", "default": "None"}',
    )
    subprocess.run(
        [PYTHON_EXE, "scripts/gen_models.py"], cwd=workdir, check=True, capture_output=True,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    (workdir / "migrations/0003_add_task_due_date.py").write_text(MIGRATION, encoding="utf-8", newline="\n")
    append_text(workdir / "migrations/INDEX", "0003_add_task_due_date\n")
    replace_once(workdir / "taskapp/schemas/task.py", '"assignee_id")', '"assignee_id", "due_date")')
