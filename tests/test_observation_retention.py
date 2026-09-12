import pytest

from premium_model_budget_governor.work_journal import save_observation, read_observation
from premium_model_budget_governor.observation_retention import preview_retention, apply_retention


def seed(tmp_path):
    path = tmp_path / "observations.sqlite3"
    saved = save_observation(path, "o1", {"work_units": ["w1"], "receipts": []})
    return path, saved


def test_preview_does_not_delete(tmp_path):
    path, saved = seed(tmp_path)
    before = path.read_bytes()
    plan = preview_retention(path, "2099-01-01T00:00:00+00:00")
    assert plan["observation_ids"] == ["o1"]
    assert path.read_bytes() == before
    assert read_observation(path, "o1") == saved


@pytest.mark.parametrize("approved", [False, None, 1, "yes"])
def test_requires_explicit_boolean_approval(tmp_path, approved):
    path, _ = seed(tmp_path)
    plan = preview_retention(path, "2099-01-01T00:00:00+00:00")
    with pytest.raises(ValueError, match="approval"):
        apply_retention(path, plan, approved=approved)
    assert len(list(tmp_path.iterdir())) == 1


def test_applied_retention_has_restorable_backup(tmp_path):
    from pathlib import Path
    path, saved = seed(tmp_path)
    plan = preview_retention(path, "2099-01-01T00:00:00+00:00")
    result = apply_retention(path, plan, approved=True)
    assert result["removed"] == 1
    assert read_observation(Path(result["backup_path"]), "o1") == saved
    with pytest.raises(ValueError, match="missing"):
        read_observation(path, "o1")


def test_stale_preview_never_deletes_new_data(tmp_path):
    path, saved = seed(tmp_path)
    plan = preview_retention(path, "2099-01-01T00:00:00+00:00")
    save_observation(path, "o2", {"receipts": []})
    with pytest.raises(ValueError, match="stale"):
        apply_retention(path, plan, approved=True)
    assert read_observation(path, "o1") == saved
    assert read_observation(path, "o2")


def test_naive_cutoff_and_forged_plan_rejected(tmp_path):
    path, _ = seed(tmp_path)
    with pytest.raises(ValueError, match="timezone"):
        preview_retention(path, "2099-01-01")
    plan = preview_retention(path, "2099-01-01T00:00:00+00:00")
    plan["observation_ids"] = []
    with pytest.raises(ValueError, match="stale"):
        apply_retention(path, plan, approved=True)


def test_empty_plan_makes_no_backup(tmp_path):
    path, saved = seed(tmp_path)
    plan = preview_retention(path, "2000-01-01T00:00:00+00:00")
    result = apply_retention(path, plan, approved=True)
    assert result["removed"] == 0 and result["backup_path"] is None
    assert read_observation(path, "o1") == saved


def test_writer_between_backup_and_delete_forces_new_preview(tmp_path, monkeypatch):
    import premium_model_budget_governor.observation_retention as retention
    path, saved = seed(tmp_path)
    plan = preview_retention(path, "2099-01-01T00:00:00+00:00")
    original = retention._rows
    calls = 0
    def racing_rows(db):
        nonlocal calls
        rows = original(db)
        calls += 1
        if calls == 2:
            save_observation(path, "concurrent", {"receipts": []})
        return rows
    monkeypatch.setattr(retention, "_rows", racing_rows)
    with pytest.raises(ValueError, match="stale"):
        apply_retention(path, plan, approved=True)
    assert read_observation(path, "o1") == saved
    assert read_observation(path, "concurrent")
