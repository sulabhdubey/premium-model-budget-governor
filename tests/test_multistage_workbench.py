from threading import Event
import os
from pathlib import Path
import subprocess
import sys

import pytest

from premium_model_budget_governor.workbench import Workbench
from premium_model_budget_governor.leases import budget_action
from premium_model_budget_governor.host import _claim_dispatch
from premium_model_budget_governor.receipt_journal import record_terminal


def service(tmp_path, executor):
    root = tmp_path / "project"
    root.mkdir()
    probe = lambda root: {"models":[{"model":model,"reasoning_efforts":["low"],"input_modalities":["text","image"]}
                                    for model in ["gpt-5.6-sol","gpt-6-astra"]]}
    return Workbench({"p":root},tmp_path / "data",probe=probe,executor=executor)


def packet(strategy="prepared"):
    return {"project":"p","task":"Assess the evidence.","strategy":strategy,"budget_credits":40}


def completed(packet, ledger, crash=False):
    base = {"task_id":packet["task_id"],"lease_id":packet["call_id"]}
    model = packet["model"]
    cost = .1 if model == "gpt-5.6-sol" else .25
    usage = {"input_tokens":1000,"output_tokens":0}
    budget_action({**base,"action":"reserve","model":model,"estimated_credits":packet["estimated_credits"]},ledger)
    _claim_dispatch(ledger,packet["task_id"],packet["call_id"])
    record_terminal(ledger,task_id=packet["task_id"],call_id=packet["call_id"],model=model,thread_id="host",turn_id=packet["call_id"],usage=usage)
    if crash:
        raise OSError("interrupted after terminal receipt")
    budget_action({**base,"action":"settle","actual_model":model,"actual_credits":cost,"cost_basis":"token_rate_estimate"},ledger)
    return {"status":"completed","host_configured_model":model,"usage":usage,"answer":"PRIVATE RESULT"}


@pytest.mark.parametrize("strategy",["prepared","review"])
def test_whole_workflow_approval_and_prompt_free_stage_receipts(tmp_path,strategy):
    calls = []
    def execute(stage,ledger):
        calls.append(stage)
        return completed(stage,ledger)
    app = service(tmp_path,execute)
    preview = app.preview(packet(strategy))
    assert len(preview["plan"]["selected"]["stages"]) == 2
    with pytest.raises(ValueError,match="approval"):
        app.execute(preview["id"])
    result = app.execute(preview["id"],approved=True)
    assert result["status"] == "completed" and result["estimated_credits"] == pytest.approx(.35)
    assert len(result["stages"]) == 2 and result["usage"] is None
    assert "Assess the evidence" in calls[0]["prompt"] and "Assess the evidence" in calls[1]["prompt"]
    assert "PRIVATE RESULT" in calls[1]["prompt"] and "PRIVATE RESULT" not in str(app.history())
    with pytest.raises(ValueError,match="replay"):
        app.execute(preview["id"],approved=True)


def test_multistage_crash_recovers_all_started_receipts_without_replay(tmp_path):
    calls = []
    def execute(stage,ledger):
        calls.append(stage["call_id"])
        return completed(stage,ledger,crash=len(calls)==2)
    app = service(tmp_path,execute)
    identifier = app.preview(packet())["id"]
    result = app.execute(identifier,approved=True)
    assert result["status"] == "unknown_usage"
    recovered = app.reconcile(identifier,approved=True)
    assert recovered["status"] == "usage_recovered" and recovered["estimated_credits"] == pytest.approx(.35)
    assert len(recovered["stages"]) == 2 and len(calls) == 2


def test_multistage_cancel_does_not_launch_final_model(tmp_path):
    stop = Event()
    def execute(stage,ledger,**kwargs):
        result = completed(stage,ledger)
        stop.set()
        return result
    app = service(tmp_path,execute)
    result = app.execute(app.preview(packet())["id"],approved=True,cancel_event=stop)
    assert result["status"] == "stopped_between_stages" and result["estimated_credits"] == .1
    assert len(result["stages"]) == 1


def test_missing_second_stage_receipt_retains_unknown_usage(tmp_path):
    calls = []
    def execute(stage,ledger):
        calls.append(stage["call_id"])
        if len(calls) == 1:
            return completed(stage,ledger)
        budget_action({"action":"reserve","task_id":stage["task_id"],"lease_id":stage["call_id"],
                       "model":stage["model"],"estimated_credits":stage["estimated_credits"]},ledger)
        raise OSError("no terminal receipt")
    app = service(tmp_path,execute)
    identifier = app.preview(packet())["id"]
    assert app.execute(identifier,approved=True)["status"] == "unknown_usage"
    result = app.reconcile(identifier,approved=True)
    assert result["status"] == "unknown_usage" and result["recovered"] is False
    assert budget_action({"action":"status","task_id":identifier},app.ledger)["reserved_credits"] > 0
    assert len(calls) == 2


def test_confirmed_canceled_stage_is_persisted_without_erasing_prior_cost(tmp_path):
    calls = []
    def execute(stage,ledger):
        calls.append(stage["call_id"])
        return completed(stage,ledger) if len(calls) == 1 else {"status":"canceled_before_dispatch"}
    app = service(tmp_path,execute)
    identifier = app.preview(packet())["id"]
    result = app.execute(identifier,approved=True)
    assert result["status"] == "stopped_between_stages" and result["estimated_credits"] == .1
    from premium_model_budget_governor.database import connection
    with connection(app.database) as db:
        assert db.execute("SELECT status FROM run_stages WHERE task=? ORDER BY id",(identifier,)).fetchall() == [("started",),("not_dispatched",)]


@pytest.mark.parametrize("terminal_written", [False, True])
@pytest.mark.parametrize("crash_stage", [0, 1], ids=["first-stage", "second-stage"])
def test_real_process_exit_mid_workflow_recovers_only_recorded_usage(tmp_path, terminal_written, crash_stage):
    script = r'''
import os, runpy, sys
from pathlib import Path
from premium_model_budget_governor.runtime_lock import RuntimeLock
from premium_model_budget_governor.leases import budget_action
from premium_model_budget_governor.host import _claim_dispatch
helpers = runpy.run_path(sys.argv[1])
root = Path(sys.argv[2])
calls = []
def execute(stage, ledger):
    calls.append(stage['call_id'])
    if len(calls) - 1 < int(sys.argv[4]):
        return helpers['completed'](stage, ledger)
    if sys.argv[3] == 'yes':
        try:
            helpers['completed'](stage, ledger, crash=True)
        except OSError:
            os._exit(29)
    budget_action({'action':'reserve','task_id':stage['task_id'],'lease_id':stage['call_id'],
                   'model':stage['model'],'estimated_credits':stage['estimated_credits']}, ledger)
    _claim_dispatch(ledger, stage['task_id'], stage['call_id'])
    os._exit(29)
with RuntimeLock(root / 'data'):
    app = helpers['service'](root, execute)
    app.execute(app.preview(helpers['packet']())['id'], approved=True)
'''
    env = {**os.environ, "PYTHONPATH":os.pathsep.join(sys.path)}
    child = subprocess.run([sys.executable,"-c",script,str(Path(__file__).resolve()),str(tmp_path),"yes" if terminal_written else "no",str(crash_stage)],
                           env=env,capture_output=True,timeout=30)
    assert child.returncode == 29, "crash fixture did not reach its intended boundary"
    from premium_model_budget_governor.runtime_lock import RuntimeLock
    with RuntimeLock(tmp_path / "data") as ownership:
        app = Workbench({"p":tmp_path / "project"},tmp_path / "data",
                        executor=lambda *args: pytest.fail("recovery replayed a stage"))
        assert app.recover_interrupted(ownership) == 1
        identifier = app.history()[0]["id"]
        result = app.reconcile(identifier,approved=True)
        accounting = budget_action({"action":"status","task_id":identifier},app.ledger)
        if terminal_written:
            assert result["status"] == "usage_recovered"
            assert accounting["spent_credits"] == pytest.approx(.1 if crash_stage == 0 else .35)
            assert accounting["reserved_credits"] == 0
            assert len(result["stages"]) == crash_stage + 1
        else:
            assert result["status"] == "unknown_usage"
            assert accounting["spent_credits"] == (0 if crash_stage == 0 else .1)
            assert accounting["reserved_credits"] > 0
        assert len(accounting["leases"]) == crash_stage + 1
