import importlib.util
import sqlite3

import pytest

from premium_model_budget_governor.workflow import plan_workflow


SCOPE = {"project": "fixture-project", "family": "review", "host_profile": "fixture-host-v1", "mode": "astra_preferred"}


def store(tmp_path):
    assert importlib.util.find_spec("premium_model_budget_governor.reviewed_policy"), "reviewed policy store missing"
    from premium_model_budget_governor.reviewed_policy import PolicyStore
    return PolicyStore(tmp_path / "policies.sqlite3")


def evidence(n=20, **changes):
    return [{"task_id": f"{split}-{i}", "family":"review", "snapshot":f"snap-{i}", "rubric":"v1",
             "candidate":"astra-direct", "baseline":"astra-review", "split":split,
             "cost_basis":"token_rate_estimate", "matched":True,"complete":True,
             "candidate_pass":True,"baseline_pass":True,"candidate_credits":2,"baseline_credits":3, **changes}
            for split in ["calibration","holdout"] for i in range(n)]


def propose(db, pairs=None):
    return db.propose(SCOPE, evidence() if pairs is None else pairs)


def test_proposal_never_activates_itself(tmp_path):
    db=store(tmp_path)
    row=propose(db)
    assert row["eligible_for_review"] is True
    assert db.status(SCOPE)["active_id"] is None
    assert row["automatic_promotion"] is False


def test_schema_failure_closes_policy_connection(tmp_path, monkeypatch):
    from premium_model_budget_governor.reviewed_policy import PolicyStore
    original = sqlite3.connect
    handles = []
    class BrokenSchema(sqlite3.Connection):
        def executescript(self, script):
            raise sqlite3.OperationalError("schema failure fixture")
    def connect(*args, **kwargs):
        db = original(*args, **kwargs, factory=BrokenSchema)
        handles.append(db)
        return db
    monkeypatch.setattr(sqlite3, "connect", connect)
    with pytest.raises(sqlite3.OperationalError):
        PolicyStore(tmp_path / "failed.sqlite3")._write()
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        handles[0].execute("SELECT 1")


@pytest.mark.parametrize("rows", [evidence(1), evidence(candidate_pass=False), evidence(candidate_credits=4), evidence(0)])
def test_weak_or_regressing_evidence_cannot_activate(tmp_path, rows):
    db=store(tmp_path)
    row=propose(db,rows)
    assert row["eligible_for_review"] is False
    with pytest.raises(ValueError):
        db.activate(row["id"], approved=True, expected_active=None)


def test_holdout_required_and_labels_must_match_scope(tmp_path):
    db=store(tmp_path)
    row=propose(db,[v for v in evidence() if v["split"]=="calibration"])
    assert not row["eligible_for_review"]
    with pytest.raises(ValueError, match="family"):
        db.propose({**SCOPE,"family":"writing"},evidence())


def test_approval_compare_and_swap_and_rollback(tmp_path):
    db=store(tmp_path)
    row=propose(db)
    with pytest.raises(ValueError, match="approval"):
        db.activate(row["id"], approved=False, expected_active=None)
    db.activate(row["id"], approved=True, expected_active=None)
    assert db.status(SCOPE)["active_id"]==row["id"]
    with pytest.raises(ValueError, match="changed"):
        db.rollback(SCOPE, target_id=None, approved=True, expected_active=None)
    db.rollback(SCOPE, target_id=None, approved=True, expected_active=row["id"])
    assert db.status(SCOPE)["active_id"] is None
    assert len(db.status(SCOPE)["events"])==2


def test_tampered_proposal_cannot_activate(tmp_path):
    db=store(tmp_path)
    row=propose(db)
    with sqlite3.connect(db.path) as conn:
        conn.execute("UPDATE proposals SET payload='{}' WHERE id=?",(row["id"],))
    with pytest.raises(ValueError, match="integrity"):
        db.activate(row["id"], approved=True, expected_active=None)


def test_expired_policy_is_not_applied(tmp_path, monkeypatch):
    db=store(tmp_path)
    row=propose(db)
    db.activate(row["id"],approved=True,expected_active=None)
    monkeypatch.setattr("premium_model_budget_governor.reviewed_policy.time.time",lambda:row["expires_at"]+1)
    assert db.status(SCOPE)["usable"] is False


def plan():
    return plan_workflow({"mode":"astra_preferred","budget_credits":20,"explicit_approval":True,"candidates":[
        {"id":"astra-direct","complete_workflow":True,"quality_score":0,"stages":[{"model":"gpt-6-astra","role":"investigate","evidence_ready":True,"tokens":{"input":10000}}]},
        {"id":"astra-review","complete_workflow":True,"quality_score":0,"stages":[{"model":"gpt-6-astra","role":"review","evidence_ready":True,"tokens":{"input":9000}}]}]})


def test_policy_selects_only_feasible_requested_participation(tmp_path):
    db=store(tmp_path); row=propose(db)
    db.activate(row["id"],approved=True,expected_active=None)
    original=plan()
    assert original["selected"]["id"]=="astra-review"
    routed=db.apply(original,SCOPE)
    assert routed["selected"]["id"]=="astra-direct"
    assert original["selected"]["id"]=="astra-review"
    original["candidates"][0]["blocks"]=["whole_workflow_over_budget"]
    assert db.apply(original,SCOPE)["selected"]["id"]=="astra-review"


def test_scope_mismatch_never_applies_policy(tmp_path):
    db=store(tmp_path);row=propose(db)
    db.activate(row["id"],approved=True,expected_active=None)
    assert db.apply(plan(),{**SCOPE,"project":"different"})["selected"]["id"]=="astra-review"


def test_rollback_cannot_introduce_unreviewed_target(tmp_path):
    db=store(tmp_path); row=propose(db)
    with pytest.raises(ValueError,match="never active"):
        db.rollback(SCOPE,target_id=row["id"],approved=True,expected_active=None)


def test_astra_preference_survives_misleading_candidate_label(tmp_path):
    db=store(tmp_path); row=propose(db)
    db.activate(row["id"],approved=True,expected_active=None)
    current=plan()
    current["candidates"][0]["astra_roles"]=[]
    assert db.apply(current,SCOPE)["selected"]["id"]=="astra-review"


def test_cli_requires_explicit_current_version(tmp_path,capsys):
    from premium_model_budget_governor.cli import main
    import json
    path=tmp_path/"input.json"
    path.write_text(json.dumps({"action":"activate","id":"unknown","approved":True}))
    assert main(["policy","--input",str(path),"--store",str(tmp_path/"store.sqlite3")])==2
    assert "expected_active" in capsys.readouterr().out


@pytest.mark.parametrize("block", [
    "whole_workflow_over_budget", "emergency_requires_approval",
    "unknown_capacity_requires_approval", "required_capability_unavailable",
    "project_model_restriction", "measure_host_context_before_execution",
])
def test_reviewed_policy_never_clears_current_execution_blocks(tmp_path, block):
    db = store(tmp_path)
    row = propose(db)
    db.activate(row["id"], approved=True, expected_active=None)
    current = plan()
    current["candidates"][0]["blocks"] = [block]
    result = db.apply(current, SCOPE)
    assert result["selected"] == current["selected"]
    assert result["candidates"][0]["blocks"] == [block]
    assert result["policy_application"]["status"] == "candidate_not_feasible"
