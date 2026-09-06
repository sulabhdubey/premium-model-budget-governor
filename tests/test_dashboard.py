from pathlib import Path
import pytest

from premium_model_budget_governor.dashboard import export_dashboard
from premium_model_budget_governor.leases import budget_action


def test_export_is_read_only_private_and_escaped(tmp_path):
    ledger = tmp_path / "budget.sqlite3"
    budget_action({"action": "open", "task_id": "private-project-secret", "budget_credits": 10}, ledger)
    budget_action({"action": "reserve", "task_id": "private-project-secret", "lease_id": "private-call", "model": '<script>alert(1)</script>', "estimated_credits": 2}, ledger)
    before = ledger.read_bytes()
    output = tmp_path / "dashboard.html"
    result = export_dashboard(ledger, output)
    content = output.read_text()
    assert ledger.read_bytes() == before
    assert "private-project-secret" not in content and "private-call" not in content
    assert "<script>" not in content and "&lt;script&gt;" in content
    assert result["read_only"] and result["tasks"] == 1
    assert "Weekly capacity and saved credits are unknown" in content
    with pytest.raises(ValueError, match="overwrite"):
        export_dashboard(ledger, ledger)


def test_missing_ledger_is_not_created(tmp_path):
    with pytest.raises(FileNotFoundError):
        export_dashboard(tmp_path / "absent.db", tmp_path / "out.html")
    assert not (tmp_path / "absent.db").exists()
