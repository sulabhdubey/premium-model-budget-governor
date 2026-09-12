import importlib.util
import json
from pathlib import Path

from premium_model_budget_governor.accounting import estimate_observed


def module():
    spec = importlib.util.spec_from_file_location("accounted_trial", Path(__file__).parents[1] / "scripts/run_accounted_trial.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_dry_run_admits_only_declared_bootstrap_without_execution(tmp_path):
    result = module().run(tmp_path / "trial")
    assert result["model_calls"] == 0
    assert result["gate"]["selected"]["estimated_total_credits"] == 60
    assert not (tmp_path / "trial").exists()


def test_external_fixture_accounts_every_phase(tmp_path, monkeypatch):
    trial = module()
    seen = []
    def execute(packet, ledger):
        seen.append(packet["call_id"])
        answer = ({"uncached_input": 20, "total_input_output": 110} if packet["call_id"].startswith("cal-")
                  else {"total_candidate_credits": 12, "baseline_credits": 10, "savings_credits": -2, "claim_supported": False})
        usage = {"input_tokens": 100, "cached_tokens": 0, "output_tokens": 10}
        rates = estimate_observed("gpt-6-astra", usage)
        return {"status": "completed", "requested_model": "gpt-6-astra", "host_configured_model": "gpt-6-astra",
                "context_profile": packet["context_profile"], "call_id": packet["call_id"], "usage": usage,
                "estimated_credits": rates["estimated_credits"], "rate_snapshot": rates["rate_snapshot"],
                "answer": json.dumps(answer), "host_identity": {"config_stable": True,
                    "scope": "one_turn_in_new_ephemeral_thread", "source_id": packet["call_id"],
                    "config_fingerprint": "same-config", "reasoning_requested": "low",
                    "context_requested": packet["context_profile"]}}
    monkeypatch.setattr(trial, "execute_app_server", execute)
    result = trial.run(tmp_path / "trial", execute=True)
    assert len(seen) == 4
    assert result["status"] == "complete_for_declared_phases"
    assert result["task"]["totals"]["input_tokens"] == 400
    assert result["reporting"] is None
