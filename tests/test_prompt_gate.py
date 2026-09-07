from hashlib import sha256
import json
import subprocess
import sys

import pytest

from premium_model_budget_governor.leases import budget_action
from premium_model_budget_governor.prompt_gate import check_prompt


def setup(tmp_path):
    ledger = tmp_path / "budget.sqlite3"
    budget_action({"action":"open", "task_id":"t", "budget_credits":10}, ledger)
    budget_action({"action":"reserve", "task_id":"t", "lease_id":"l", "model":"gpt-6-astra", "estimated_credits":5}, ledger)
    event = {"hook_event_name":"UserPromptSubmit", "session_id":"session", "turn_id":"turn", "cwd":str(tmp_path), "prompt":"private prompt"}
    grant = {"session_id":"session", "cwd":str(tmp_path), "prompt_sha256":sha256(event["prompt"].encode()).hexdigest(), "ledger":str(ledger), "task_id":"t", "lease_id":"l"}
    return event, grant


def test_grant_is_bound_and_replay_is_idempotent(tmp_path):
    event, grant = setup(tmp_path)
    assert check_prompt(event, grant) == {"continue":True}
    assert check_prompt(event, grant) == {"continue":True}
    with pytest.raises(ValueError, match="consumed"):
        check_prompt({**event, "turn_id":"other"}, grant)


@pytest.mark.parametrize("change", [{"session_id":"other"}, {"prompt":"altered"}, {"hook_event_name":"Stop"}])
def test_mismatch_blocks(tmp_path, change):
    event, grant = setup(tmp_path)
    with pytest.raises(ValueError):
        check_prompt({**event, **change}, grant)


def test_lease_cannot_be_shared_with_cli_dispatch(tmp_path):
    from pathlib import Path
    from premium_model_budget_governor.host import _claim_dispatch
    event, grant = setup(tmp_path)
    _claim_dispatch(Path(grant["ledger"]), "t", "l")
    with pytest.raises(ValueError, match="another path"):
        check_prompt(event, grant)


def test_expired_grant_blocks_without_refund(tmp_path, monkeypatch):
    import premium_model_budget_governor.prompt_gate as gate
    event, grant = setup(tmp_path)
    monkeypatch.setattr(gate.time, "time", lambda: 10**12)
    with pytest.raises(ValueError, match="expired"):
        check_prompt(event, grant)
    assert budget_action({"action":"status", "task_id":"t"}, __import__('pathlib').Path(grant["ledger"]))["reserved_credits"] == 5


def test_hook_protocol_blocks_missing_grant_without_echoing_prompt(tmp_path):
    result = subprocess.run([sys.executable, "-m", "premium_model_budget_governor.prompt_gate", "--grant", str(tmp_path/"absent.json")], input='{"prompt":"private secret"}', text=True, capture_output=True, timeout=10)
    assert result.returncode == 0
    assert json.loads(result.stdout)["decision"] == "block"
    assert "private secret" not in result.stdout + result.stderr
