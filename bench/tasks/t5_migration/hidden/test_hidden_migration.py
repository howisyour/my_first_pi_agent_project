import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from taskapp.models_generated import Task
from taskapp.schemas import TaskOut
from taskapp.storage.memory import InMemoryStore

ROOT = Path(__file__).resolve().parents[1]


def _load_migration():
    names = (ROOT / "migrations" / "INDEX").read_text(encoding="utf-8").split()
    assert names[:2] == ["0001_initial", "0002_add_task_priority"]
    assert len(names) == 3 and names[2].startswith("0003_"), names
    path = ROOT / "migrations" / f"{names[2]}.py"
    spec = importlib.util.spec_from_file_location(names[2], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_schema_version_and_field():
    schema = json.loads((ROOT / "schema" / "models.json").read_text(encoding="utf-8"))
    assert schema["version"] == 3
    task = next(model for model in schema["models"] if model["name"] == "Task")
    field = next(field for field in task["fields"] if field["name"] == "due_date")
    assert field.get("default") == "None"


def test_generated_model_has_field():
    assert Task(id=1, project_id=1, title="t").due_date is None


def test_migration_is_registered_with_version():
    assert _load_migration().VERSION == 3


def test_migration_backfills_and_reverts():
    module = _load_migration()
    store = InMemoryStore()
    store.table("tasks")[1] = SimpleNamespace(id=1, title="legacy")
    store.table("tasks")[2] = SimpleNamespace(id=2, title="dated", due_date="2026-10-01")
    module.up(store)
    assert store.table("tasks")[1].due_date is None
    assert store.table("tasks")[2].due_date == "2026-10-01"
    module.down(store)
    assert not hasattr(store.table("tasks")[1], "due_date")


def test_api_exposes_due_date(app_client):
    assert "due_date" in TaskOut.fields
    assert app_client.get("/projects/1/tasks").body["items"][0]["due_date"] is None
