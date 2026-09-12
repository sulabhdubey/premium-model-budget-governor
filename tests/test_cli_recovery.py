import json

from premium_model_budget_governor.cli import main
from premium_model_budget_governor.host import _claim_dispatch
from premium_model_budget_governor.leases import budget_action
from premium_model_budget_governor.receipt_journal import record_terminal


def test_recovery_preview_apply_and_repeat(tmp_path, capsys):
    ledger = tmp_path / "budget.sqlite3"
    budget_action({"action": "open", "task_id": "task", "budget_credits": 10}, ledger)
    budget_action({"action": "reserve", "task_id": "task", "lease_id": "call",
                   "model": "gpt-6-astra", "estimated_credits": 5}, ledger)
    _claim_dispatch(ledger, "task", "call")
    record_terminal(ledger, task_id="task", call_id="call", model="gpt-6-astra",
                    thread_id=None, turn_id=None, host_source="codex_cli",
                    usage={"input_tokens": 100, "cached_tokens": 0, "output_tokens": 0})
    args = ["recover", "--ledger", str(ledger), "--task-id", "task", "--call-id", "call"]
    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)["result"]
    assert result["status"] == "preview"
    assert budget_action({"action": "status", "task_id": "task"}, ledger)["reserved_credits"] == 5
    for _ in range(2):
        assert main([*args, "--apply"]) == 0
        result = json.loads(capsys.readouterr().out)["result"]
        assert result["status"] == "reconciled"
        assert result["receipt"]["budget"]["spent_credits"] == .025
        assert result["receipt"]["budget"]["reserved_credits"] == 0


def test_missing_recovery_does_not_create_database(tmp_path, capsys):
    ledger = tmp_path / "missing.sqlite3"
    assert main(["recover", "--ledger", str(ledger), "--task-id", "task", "--call-id", "call"]) == 0
    assert json.loads(capsys.readouterr().out)["result"]["status"] == "no_terminal_evidence"
    assert not ledger.exists()


def test_corrupt_evidence_cannot_apply(tmp_path, capsys):
    import sqlite3
    ledger = tmp_path / "corrupt.sqlite3"
    budget_action({"action": "open", "task_id": "task", "budget_credits": 10}, ledger)
    budget_action({"action": "reserve", "task_id": "task", "lease_id": "call",
                   "model": "gpt-6-astra", "estimated_credits": 5}, ledger)
    _claim_dispatch(ledger, "task", "call")
    record_terminal(ledger, task_id="task", call_id="call", model="gpt-6-astra",
                    thread_id="th", turn_id="tu", usage={"input_tokens": 100, "output_tokens": 0})
    with sqlite3.connect(ledger) as db:
        db.execute("UPDATE terminal_receipts SET checksum='invalid'")
    assert main(["recover", "--ledger", str(ledger), "--task-id", "task", "--call-id", "call", "--apply"]) != 0
    capsys.readouterr()
    assert budget_action({"action": "status", "task_id": "task"}, ledger)["reserved_credits"] == 5
