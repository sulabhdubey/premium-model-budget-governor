import json
import sqlite3

import pytest

from premium_model_budget_governor.leases import budget_action
from premium_model_budget_governor.host import _claim_dispatch


def setup_ledger(tmp_path):
    path = tmp_path / "budget.sqlite3"
    budget_action({"action": "open", "task_id": "task", "budget_credits": 20}, path)
    budget_action({"action": "reserve", "task_id": "task", "lease_id": "call",
                   "model": "gpt-6-astra", "estimated_credits": 10}, path)
    _claim_dispatch(path, "task", "call")
    return path


def receipt():
    return {"task_id": "task", "call_id": "call", "model": "gpt-6-astra",
            "thread_id": "host-thread", "turn_id": "host-turn",
            "usage": {"input_tokens": 5000, "cached_tokens": 0, "output_tokens": 0}}


def test_terminal_receipt_recovery_is_idempotent(tmp_path):
    from premium_model_budget_governor.receipt_journal import record_terminal, recover_terminal
    path = setup_ledger(tmp_path)
    record_terminal(path, **receipt())
    first = recover_terminal(path, "task", "call")
    second = recover_terminal(path, "task", "call")
    assert first == second
    assert first["budget"]["spent_credits"] == 1.25
    assert first["budget"]["reserved_credits"] == 0
    assert first["cost_basis"] == "token_rate_estimate"


def test_missing_terminal_receipt_does_not_release_reservation(tmp_path):
    from premium_model_budget_governor.receipt_journal import recover_terminal
    path = setup_ledger(tmp_path)
    assert recover_terminal(path, "task", "call") is None
    assert budget_action({"action": "status", "task_id": "task"}, path)["reserved_credits"] == 10


def test_journal_requires_dispatch_and_rejects_conflicts(tmp_path):
    from premium_model_budget_governor.receipt_journal import record_terminal
    path = setup_ledger(tmp_path)
    with pytest.raises(ValueError):
        record_terminal(path, **{**receipt(), "call_id": "other"})
    record_terminal(path, **receipt())
    with pytest.raises(ValueError):
        record_terminal(path, **{**receipt(), "turn_id": "different"})


def test_corrupt_journal_never_settles(tmp_path):
    from premium_model_budget_governor.receipt_journal import record_terminal, recover_terminal
    path = setup_ledger(tmp_path)
    record_terminal(path, **receipt())
    with sqlite3.connect(path) as db:
        db.execute("UPDATE terminal_receipts SET payload=?", (json.dumps({"usage": {}}),))
    with pytest.raises(ValueError):
        recover_terminal(path, "task", "call")
    assert budget_action({"action": "status", "task_id": "task"}, path)["reserved_credits"] == 10
