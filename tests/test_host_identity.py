import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("host_test_support", Path(__file__).with_name("test_app_server.py"))
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)
FakeClient, packet = support.FakeClient, support.packet
import premium_model_budget_governor.app_server as app
from premium_model_budget_governor.leases import budget_action


def test_identity_is_bounded_and_does_not_export_configuration(tmp_path, monkeypatch):
    class Client(FakeClient):
        def request(self, method, params):
            if method == "config/read":
                return {"config": {"private": "do-not-export"}}
            return super().request(method, params)
    monkeypatch.setattr(app, "AppServer", Client)
    ledger = tmp_path / "budget.sqlite3"
    budget_action({"action": "open", "task_id": "t", "budget_credits": 10}, ledger)
    result = app.execute_app_server({**packet(tmp_path), "capture_identity": True}, ledger)
    identity = result["host_identity"]
    assert identity["config_stable"] is True
    assert len(identity["config_fingerprint"]) == 64
    assert "do-not-export" not in str(result)
    assert identity["effective_context_attested"] is False
