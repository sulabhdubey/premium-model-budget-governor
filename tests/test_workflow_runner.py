from threading import Event

import pytest

from premium_model_budget_governor.leases import budget_action
from premium_model_budget_governor.workflow_runner import execute_stages


def setup(tmp_path):
    ledger = tmp_path / "budget.sqlite3"
    budget_action({"action":"open", "task_id":"task", "budget_credits":10, "reserve_credits":1}, ledger)
    stages = [{"task_id":"task", "call_id":f"stage-{index}", "root":str(tmp_path),
               "model":model, "prompt":"Review original evidence.", "estimated_credits":2}
              for index, model in enumerate(["gpt-5.6-sol", "gpt-6-astra"])]
    return ledger, stages


def completed(packet, ledger, **kwargs):
    base = {"task_id":packet["task_id"], "lease_id":packet["call_id"]}
    budget_action({**base,"action":"reserve", "model":packet["model"], "estimated_credits":packet["estimated_credits"]}, ledger)
    credits = .1 if packet["model"] == "gpt-5.6-sol" else .25
    budget_action({**base,"action":"settle", "actual_model":packet["model"], "actual_credits":credits,"cost_basis":"token_rate_estimate"}, ledger)
    return {"status":"completed", "host_configured_model":packet["model"],
            "usage":{"input_tokens":1000,"output_tokens":0}, "answer":"Evidence supports the bounded conclusion."}


def test_serial_receipts_and_handoff_preserve_full_cost(tmp_path):
    ledger, stages = setup(tmp_path)
    prompts = []
    def executor(packet, ledger):
        prompts.append(packet["prompt"])
        return completed(packet, ledger)
    result = execute_stages(stages, ledger, executor=executor, approved=True)
    assert result["status"] == "completed" and len(result["stages"]) == 2
    assert result["estimated_credits"] == pytest.approx(.35)
    assert result["budget"]["spent_credits"] == pytest.approx(.35)
    assert "untrusted evidence" in prompts[1] and "bounded conclusion" in prompts[1]
    assert stages[1]["prompt"] == "Review original evidence."
    with pytest.raises(ValueError, match="replay"):
        execute_stages(stages, ledger, executor=executor, approved=True)


def test_unknown_stage_never_dispatches_next(tmp_path):
    ledger, stages = setup(tmp_path)
    calls = []
    def executor(packet, ledger):
        calls.append(packet["call_id"])
        budget_action({"action":"reserve", "task_id":"task", "lease_id":packet["call_id"],
                       "model":packet["model"], "estimated_credits":2}, ledger)
        raise OSError("private host detail")
    result = execute_stages(stages, ledger, executor=executor, approved=True)
    assert result["status"] == "unknown_usage" and result["cost_complete"] is False
    assert result["estimated_credits"] is None
    assert result["budget"]["reserved_credits"] == 2 and calls == ["stage-0"]
    assert "private" not in str(result)


def test_stop_between_stages_preserves_spent_receipt(tmp_path):
    ledger, stages = setup(tmp_path)
    stop = Event()
    def executor(packet, ledger, **kwargs):
        result = completed(packet, ledger)
        stop.set()
        return result
    result = execute_stages(stages, ledger, executor=executor, approved=True, cancel_event=stop)
    assert result["status"] == "stopped_between_stages"
    assert result["budget"]["spent_credits"] == .1 and len(result["stages"]) == 1


def test_invalid_receipt_stops_before_second_stage(tmp_path):
    ledger, stages = setup(tmp_path)
    calls = []
    def executor(packet, ledger):
        calls.append(packet["call_id"])
        result = completed(packet, ledger)
        result["usage"]["input_tokens"] = 1
        return result
    assert execute_stages(stages, ledger, executor=executor, approved=True)["status"] == "unknown_usage"
    assert calls == ["stage-0"]


def test_budget_rechecked_after_first_stage_overruns_estimate(tmp_path):
    ledger, stages = setup(tmp_path)
    def executor(packet, ledger):
        base = {"task_id":"task", "lease_id":packet["call_id"]}
        budget_action({**base,"action":"reserve","model":packet["model"],"estimated_credits":2},ledger)
        budget_action({**base,"action":"settle","actual_model":packet["model"],"actual_credits":8,"cost_basis":"token_rate_estimate"},ledger)
        return {"status":"completed","host_configured_model":packet["model"],"usage":{"input_tokens":80000,"output_tokens":0},"answer":"Done"}
    result = execute_stages(stages, ledger, executor=executor, approved=True)
    assert result["status"] == "needs_replan" and result["budget"]["spent_credits"] == 8
    assert len(result["stages"]) == 1


@pytest.mark.parametrize("case", ["approval", "duplicate", "images", "budget"])
def test_invalid_workflow_rejected_before_executor(tmp_path, case):
    ledger, stages = setup(tmp_path)
    if case == "duplicate":
        stages[1]["call_id"] = stages[0]["call_id"]
    if case == "images":
        stages[0]["images"] = ["chart.png"]
    if case == "budget":
        stages[1]["estimated_credits"] = 10
    with pytest.raises(ValueError):
        execute_stages(stages, ledger, executor=lambda *args: pytest.fail("invalid workflow dispatched"), approved=case != "approval")


@pytest.mark.parametrize("answer", ["x" * 64001, "   ", "\u4e00" * 22000, "\n" * 33000], ids=["oversized", "empty", "utf8", "escaped"])
def test_unusable_handoff_is_not_truncated_or_dispatched(tmp_path, answer):
    ledger, stages = setup(tmp_path)
    calls = []
    def executor(packet, ledger):
        calls.append(packet["call_id"])
        result = completed(packet, ledger)
        result["answer"] = answer
        return result
    result = execute_stages(stages, ledger, executor=executor, approved=True)
    assert result["status"] == "handoff_needs_review" and calls == ["stage-0"]
    assert result["known_estimated_credits"] == .1


@pytest.mark.parametrize("after_first", [False, True])
def test_host_confirmed_predispatch_cancellation_has_known_cost(tmp_path, after_first):
    ledger, stages = setup(tmp_path)
    calls = []
    def executor(packet, ledger):
        calls.append(packet["call_id"])
        if after_first and len(calls) == 1:
            return completed(packet, ledger)
        return {"status":"canceled_before_dispatch", "stop_requested":True}
    result = execute_stages(stages, ledger, executor=executor, approved=True)
    assert result["status"] == ("stopped_between_stages" if after_first else "canceled_before_dispatch")
    assert result["estimated_credits"] == (.1 if after_first else 0)
    assert result["cost_complete"] is True


def test_false_predispatch_cancellation_with_stage_lease_is_unknown(tmp_path):
    ledger, stages = setup(tmp_path)
    def executor(packet, ledger):
        budget_action({"action":"reserve", "task_id":"task", "lease_id":packet["call_id"],
                       "model":packet["model"], "estimated_credits":2}, ledger)
        return {"status":"canceled_before_dispatch"}
    result = execute_stages(stages, ledger, executor=executor, approved=True)
    assert result["status"] == "unknown_usage" and result["estimated_credits"] is None
    assert result["budget"]["reserved_credits"] == 2
