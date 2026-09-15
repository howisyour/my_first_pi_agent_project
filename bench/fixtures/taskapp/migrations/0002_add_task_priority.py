"""Add Task.priority (schema version 2)."""

from taskapp.constants import DEFAULT_PRIORITY

VERSION = 2
TABLE = "tasks"
FIELD = "priority"


def up(store) -> None:
    for record in store.table(TABLE).values():
        if FIELD not in vars(record):
            setattr(record, FIELD, DEFAULT_PRIORITY)


def down(store) -> None:
    for record in store.table(TABLE).values():
        if FIELD in vars(record):
            delattr(record, FIELD)
