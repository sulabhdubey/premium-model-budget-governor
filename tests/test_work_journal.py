import json
import sqlite3

import pytest

from premium_model_budget_governor.work_journal import save_observation, read_observation
from premium_model_budget_governor.cli import main


def packet():
    return {"work_units": ["unit-1"], "receipts": []}


def test_roundtrip_and_idempotent_replay(tmp_path):
    path = tmp_path / "work.sqlite3"
    first = save_observation(path, "obs-1", packet())
    assert save_observation(path, "obs-1", packet()) == first
    assert read_observation(path, "obs-1") == first
    assert first["report"]["totals"] is None


def test_conflict_does_not_replace_history(tmp_path):
    path = tmp_path / "work.sqlite3"
    first = save_observation(path, "obs-1", packet())
    with pytest.raises(ValueError, match="conflicting"):
        save_observation(path, "obs-1", {"work_units": ["unit-2"], "receipts": []})
    assert read_observation(path, "obs-1") == first


def test_foreign_database_is_not_modified(tmp_path):
    path = tmp_path / "foreign.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE private_data (value TEXT)")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="unrecognized"):
        save_observation(path, "obs-1", packet())
    assert path.read_bytes() == before


def test_missing_read_does_not_create_database(tmp_path):
    path = tmp_path / "absent.sqlite3"
    with pytest.raises(ValueError, match="missing"):
        read_observation(path, "obs-1")
    assert not path.exists()


def test_corruption_rejected(tmp_path):
    path = tmp_path / "work.sqlite3"
    save_observation(path, "obs-1", packet())
    with sqlite3.connect(path) as db:
        db.execute("UPDATE observations SET payload='{}'")
    with pytest.raises(ValueError, match="integrity"):
        read_observation(path, "obs-1")


def test_unknown_schema_is_not_migrated(tmp_path):
    path = tmp_path / "work.sqlite3"
    save_observation(path, "obs-1", packet())
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA user_version=999")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="schema"):
        save_observation(path, "obs-2", packet())
    assert path.read_bytes() == before


def test_cli_save_read_and_conflict(tmp_path, capsys):
    source = tmp_path / "input.json"
    source.write_text(json.dumps(packet()), encoding="utf-8")
    journal = tmp_path / "work.sqlite3"
    args = ["long-work", "--journal", str(journal), "--observation-id", "obs-1"]
    assert main([*args, "--input", str(source)]) == 0
    saved = json.loads(capsys.readouterr().out)["result"]
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out)["result"] == saved
    source.write_text('{"receipts": []}', encoding="utf-8")
    assert main([*args, "--input", str(source)]) == 2
    assert "conflicting" in capsys.readouterr().out


def test_extra_fields_not_persisted(tmp_path):
    path = tmp_path / "work.sqlite3"
    save_observation(path, "obs-1", {**packet(), "prompt": "private-marker"})
    assert b"private-marker" not in path.read_bytes()


def test_backup_restores_the_same_observation(tmp_path):
    path = tmp_path / "work.sqlite3"
    backup = tmp_path / "restored.sqlite3"
    saved = save_observation(path, "obs-1", packet())
    with sqlite3.connect(path) as source, sqlite3.connect(backup) as destination:
        source.backup(destination)
    assert read_observation(backup, "obs-1") == saved
    assert read_observation(path, "obs-1") == saved


def test_concurrent_replay_keeps_one_snapshot(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    path = tmp_path / "work.sqlite3"
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: save_observation(path, "obs-1", packet()), range(8)))
    assert all(result == results[0] for result in results)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM observations").fetchone()[0] == 1
