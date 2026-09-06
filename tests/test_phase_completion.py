from copy import deepcopy
import json
from pathlib import Path

import pytest

from premium_model_budget_governor.workflow import plan_workflow
from premium_model_budget_governor.evidence_demand import evidence_packet


def packet():
    return json.loads((Path(__file__).parents[1] / "examples/astra_preferred.json").read_text())


def test_image_work_cannot_silently_lose_required_capability():
    p = packet()
    p["host_profiles"] = {"cli": {"capabilities": ["text"], "models": ["gpt-6-astra", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"]}}
    for c in p["candidates"]:
        for s in c["stages"]:
            s.update(host="cli", required_capabilities=["image"])
    assert plan_workflow(p)["decision"] == "needs_replan"
    p["host_profiles"]["cli"]["capabilities"].append("image")
    assert plan_workflow(p)["decision"] == "planned"


def test_upper_estimate_and_retry_budget_count_full_cost():
    p = packet()
    before = plan_workflow(p)
    for c in p["candidates"]:
        for s in c["stages"]:
            s["tokens_upper"] = {"input": 100000, "output": 10000}
            s["max_attempts"] = 2
    after = plan_workflow(p)
    assert before["decision"] == "planned"
    assert after["decision"] == "needs_replan"
    assert after["candidates"][0]["estimated_min_credits"] < after["candidates"][0]["estimated_total_credits"]


def test_project_model_restriction_does_not_force_sol():
    p = packet()
    p["project_profile"] = {"allowed_models": ["gpt-5.6-sol"]}
    assert plan_workflow(p)["decision"] == "needs_replan"


def test_evidence_snapshot_and_expiry_are_checked():
    from hashlib import sha256
    text = "current contract"
    row = {"id": "a", "source": "a.md", "text": text, "sha256": sha256(text.encode()).hexdigest(),
           "required": True, "snapshot": "old", "valid_until": "2020-01-01T00:00:00Z"}
    result = evidence_packet({"items": [row], "snapshot": "new"})
    assert result["decision"] == "blocked"
    assert "stale_evidence_snapshot" in result["blocks"]
    assert "expired_evidence" in result["blocks"]


def test_expired_reservation_is_not_freed_or_dispatched(tmp_path, monkeypatch):
    from premium_model_budget_governor.leases import budget_action
    from premium_model_budget_governor.host import _claim_dispatch
    import premium_model_budget_governor.leases as leases
    import premium_model_budget_governor.host as host
    monkeypatch.setattr(leases.time, "time", lambda: 100)
    db = tmp_path / "budget.sqlite3"
    budget_action({"action": "open", "task_id": "t", "budget_credits": 10}, db)
    budget_action({"action": "reserve", "task_id": "t", "lease_id": "l", "model": "gpt-6-astra", "estimated_credits": 5, "ttl_seconds": 1}, db)
    monkeypatch.setattr(leases.time, "time", lambda: 102)
    status = budget_action({"action": "status", "task_id": "t"}, db)
    assert status["reserved_credits"] == 5
    assert status["leases"][0]["expired"]
    with pytest.raises(ValueError, match="expired"):
        _claim_dispatch(db, "t", "l")
