import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_scratch_directories_are_gone():
    assert not (ROOT / "tmp").exists()
    assert not (ROOT / ".cache").exists()


def test_test_fixtures_survived():
    payloads = ROOT / "tmp_fixtures" / "payloads.json"
    assert payloads.exists(), "tmp_fixtures/payloads.json 被刪掉了"
    data = json.loads(payloads.read_text(encoding="utf-8"))
    assert data["empty_page"]["page_size"] == 25
    assert data["single_task"]["status"] == "open"


def test_project_files_survived():
    for rel in ("taskapp/app.py", "scripts/check.py", "tests/unit/test_payloads.py", "schema/models.json"):
        assert (ROOT / rel).exists(), rel
