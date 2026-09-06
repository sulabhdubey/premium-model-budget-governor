from concurrent.futures import ThreadPoolExecutor

import pytest

from premium_model_budget_governor.leases import budget_action


def test_concurrent_calls_cannot_double_reserve(tmp_path):
    db = tmp_path / "budget.db"
    budget_action({"action": "open", "task_id": "t", "budget_credits": 3, "reserve_credits": 1}, db)

    def reserve(n):
        try:
            budget_action({"action": "reserve", "task_id": "t", "lease_id": str(n),
                           "model": "gpt-6-astra", "estimated_credits": 2}, db)
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sum(pool.map(reserve, range(4))) == 1


def test_receipts_count_actual_models_and_overruns(tmp_path):
    db = tmp_path / "budget.db"
    budget_action({"action": "open", "task_id": "t", "budget_credits": 2}, db)
    request = {"action": "reserve", "task_id": "t", "lease_id": "a", "model": "gpt-6-astra", "estimated_credits": 1}
    budget_action(request, db)
    assert budget_action(request, db)["reserved_credits"] == 1
    receipt = {"action": "settle", "task_id": "t", "lease_id": "a", "actual_model": "gpt-5.6-sol", "actual_credits": 3}
    result = budget_action(receipt, db)
    assert result["over_budget"] is True
    assert result["astra_receipts"] == 0
    assert budget_action(receipt, db)["spent_credits"] == 3
    with pytest.raises(ValueError):
        budget_action({**request, "lease_id": "b"}, db)
    with pytest.raises(ValueError):
        budget_action({**receipt, "actual_credits": 1}, db)


def test_unknown_usage_stays_reserved_until_confirmed(tmp_path):
    db = tmp_path / "budget.db"
    budget_action({"action": "open", "task_id": "t", "budget_credits": 2}, db)
    budget_action({"action": "reserve", "task_id": "t", "lease_id": "a", "model": "gpt-6-astra", "estimated_credits": 1}, db)
    cancel = {"action": "cancel", "task_id": "t", "lease_id": "a"}
    with pytest.raises(ValueError):
        budget_action(cancel, db)
    assert budget_action({**cancel, "confirmed_not_executed": True}, db)["available_credits"] == 2
def test_estimated_reconciliation_is_labeled_and_blocks_after_overrun(tmp_path):
    from premium_model_budget_governor.leases import budget_action
    import pytest
    ledger = tmp_path / "budget.sqlite3"
    base = {"task_id": "measured"}
    budget_action({**base, "action": "open", "budget_credits": 2}, ledger)
    budget_action({**base, "action": "reserve", "lease_id": "a", "model": "gpt-6-astra", "estimated_credits": 1}, ledger)
    status = budget_action({**base, "action": "settle", "lease_id": "a", "actual_model": "gpt-6-astra",
                           "actual_credits": 3, "cost_basis": "token_rate_estimate"}, ledger)
    assert status["over_budget"]
    assert status["leases"][0]["cost_basis"] == "token_rate_estimate"
    with pytest.raises(ValueError, match="exhausted"):
        budget_action({**base, "action": "reserve", "lease_id": "b", "model": "gpt-6-astra", "estimated_credits": .1}, ledger)
def test_new_budgets_serialize_calls_until_receipt(tmp_path):
    db = tmp_path / "serial.sqlite3"
    base = {"task_id": "serial"}
    budget_action({**base, "action": "open", "budget_credits": 100}, db)
    request = {**base, "action": "reserve", "lease_id": "first", "model": "gpt-6-astra", "estimated_credits": 1}
    budget_action(request, db)
    with pytest.raises(ValueError, match="pending"):
        budget_action({**request, "lease_id": "second"}, db)
    budget_action({**base, "action": "settle", "lease_id": "first", "actual_model": "gpt-6-astra", "actual_credits": 10}, db)
    assert budget_action({**request, "lease_id": "second"}, db)["reserved_credits"] == 1
