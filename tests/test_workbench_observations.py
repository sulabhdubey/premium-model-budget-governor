import pytest
from premium_model_budget_governor.workbench import Workbench


def test_preview_import_and_list_require_matching_approval(tmp_path):
    app = Workbench({"p": tmp_path}, tmp_path / "data")
    packet = {"work_units": ["missing"], "receipts": []}
    assert app.observation_history()["observations"] == []
    preview = app.preview_observation(packet)
    assert app.observation_history()["observations"] == []
    request = {"id": preview["id"], "fingerprint": preview["fingerprint"], "packet": packet}
    with pytest.raises(ValueError, match="approval"):
        app.import_observation(request)
    with pytest.raises(ValueError, match="differs"):
        app.import_observation({**request, "approved": True, "packet": {"receipts": []}})
    result = app.import_observation({**request, "approved": True})
    assert result["report"]["totals"] is None
    assert len(app.observation_history()["observations"]) == 1
    assert app.import_observation({**request, "approved": True}) == result


def test_retention_only_affects_observation_database(tmp_path):
    app = Workbench({"p": tmp_path}, tmp_path / "data")
    packet = {"receipts": []}
    preview = app.preview_observation(packet)
    app.import_observation({**preview, "packet": packet, "approved": True})
    original = app.database.read_bytes()
    plan = app.observation_retention({"action": "preview", "before": "2099-01-01T00:00:00+00:00"})
    with pytest.raises(ValueError, match="approval"):
        app.observation_retention({"action": "apply", "plan": plan})
    result = app.observation_retention({"action": "apply", "plan": plan, "approved": True})
    assert result["removed"] == 1 and result["backup_verified"]
    assert app.database.read_bytes() == original
