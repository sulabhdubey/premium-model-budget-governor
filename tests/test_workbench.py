import importlib.util
import json
from pathlib import Path
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from premium_model_budget_governor.leases import budget_action


def service(tmp_path, executor=None):
    assert importlib.util.find_spec("premium_model_budget_governor.workbench"), "workbench service is missing"
    from premium_model_budget_governor.workbench import Workbench
    root = tmp_path / "project"
    root.mkdir(exist_ok=True)
    (root / "proof.txt").write_text("Release needs explicit authorization.")
    probe = lambda root: {"models": [{"model": model, "reasoning_efforts": ["low", "high"],
                                     "input_modalities": ["text", "image"]}
                                    for model in ["gpt-6-astra", "gpt-5.6-sol"]]}
    return Workbench({"sample": root}, tmp_path / "data", probe=probe, executor=executor or completed)


def completed(packet, ledger):
    base = {"task_id": packet["task_id"], "lease_id": packet["call_id"]}
    budget_action({**base, "action": "reserve", "model": packet["model"],
                   "estimated_credits": packet["estimated_credits"]}, ledger)
    budget_action({**base, "action": "settle", "actual_model": packet["model"],
                   "actual_credits": 1.25, "cost_basis": "token_rate_estimate"}, ledger)
    return {"status": "completed", "usage": {"input_tokens": 5000, "cached_tokens": 0, "output_tokens": 0},
            "answer": "PRIVATE ANSWER", "estimated_credits": 1.25, "cost_basis": "token_rate_estimate",
            "host_configured_model": packet["model"]}


def request(**changes):
    return {"project": "sample", "task": "Review the release evidence.", "mode": "astra_preferred",
            "budget_credits": 20, "evidence": ["proof.txt"], **changes}


def test_focused_catalog_preview_binding_and_conservative_estimate(tmp_path):
    calls = []
    def executor(packet, ledger):
        calls.append(packet)
        return completed(packet, ledger)
    app = service(tmp_path, executor)
    inherited = app.preview(request())
    focused = app.preview(request(context_profile="focused_catalog"))
    assert focused["context_profile"] == "focused_catalog"
    assert focused["plan"]["selected"]["estimated_total_credits"] == inherited["plan"]["selected"]["estimated_total_credits"]
    assert focused["policy_scope"]["host_profile"] != inherited["policy_scope"]["host_profile"]
    assert any("skill discovery" in warning for warning in focused["warnings"])
    focused["context_profile"] = "inherit"
    result = app.execute(focused["id"], approved=True)
    assert calls[0]["context_profile"] == "focused_catalog"
    assert result["context_profile"] == "focused_catalog"
    assert app.history()[0]["context_profile"] == "focused_catalog"


@pytest.mark.parametrize("changes", [
    {"context_profile":"bad"}, {"context_profile":None}, {"context_profile":{}},
    {"context_profile":"focused_catalog", "mode":"economy"},
    {"context_profile":"focused_catalog", "strategy":"prepared"},
    {"context_profile":"focused_catalog", "effort":"high"},
])
def test_incompatible_context_profile_never_previews(tmp_path, changes):
    app = service(tmp_path)
    with pytest.raises(ValueError, match="catalog|context profile"):
        app.preview(request(**changes))
    assert app.history() == []


def test_discard_preview_releases_capacity_without_creating_run(tmp_path):
    app = service(tmp_path)
    for _ in range(12):
        identifier = app.preview(request())["id"]
        assert app.discard_preview(identifier) == {"discarded": True}
        assert app.discard_preview(identifier) == {"discarded": False}
        with pytest.raises(ValueError, match="unavailable"):
            app.execute(identifier, approved=True)
    assert app.history() == []
    assert app.previews == {}


def test_discard_preview_does_not_cancel_running_task(tmp_path):
    entered, finish = Event(), Event()
    def slow(packet, ledger):
        entered.set()
        assert finish.wait(5)
        return completed(packet, ledger)
    app = service(tmp_path, slow)
    identifier = app.preview(request())["id"]
    with ThreadPoolExecutor() as pool:
        future = pool.submit(app.execute, identifier, approved=True)
        assert entered.wait(5)
        try:
            assert app.discard_preview(identifier) == {"discarded": False}
        finally:
            finish.set()
        assert future.result()["status"] == "completed"
    assert app.history()[0]["estimated_credits"] == 1.25


def test_recover_terminal_usage_without_replaying_model(tmp_path):
    from premium_model_budget_governor.host import _claim_dispatch
    from premium_model_budget_governor.receipt_journal import record_terminal
    calls = []
    def interrupted(packet, ledger):
        calls.append(packet["call_id"])
        budget_action({"action": "reserve", "task_id": packet["task_id"], "lease_id": packet["call_id"],
                       "model": packet["model"], "estimated_credits": packet["estimated_credits"]}, ledger)
        _claim_dispatch(ledger, packet["task_id"], packet["call_id"])
        record_terminal(ledger, task_id=packet["task_id"], call_id=packet["call_id"], model=packet["model"],
                        thread_id="host-thread", turn_id="host-turn",
                        usage={"input_tokens": 5000, "cached_tokens": 0, "output_tokens": 0})
        raise OSError("crash after terminal event")
    app = service(tmp_path, interrupted)
    identifier = app.preview(request())["id"]
    assert app.execute(identifier, approved=True)["status"] == "unknown_usage"
    with pytest.raises(ValueError, match="approval"):
        app.reconcile(identifier)
    result = app.reconcile(identifier, approved=True)
    assert result["status"] == "usage_recovered"
    assert result["budget"]["spent_credits"] == 1.25
    assert result["budget"]["reserved_credits"] == 0
    assert app.reconcile(identifier, approved=True) == result
    assert calls == [identifier]
    with pytest.raises(ValueError, match="already"):
        app.execute(identifier, approved=True)


def test_unknown_receipt_cannot_be_recovered_without_terminal_evidence(tmp_path):
    app = service(tmp_path, lambda *args: {"status": "unknown_usage"})
    identifier = app.preview(request())["id"]
    app.execute(identifier, approved=True)
    result = app.reconcile(identifier, approved=True)
    assert result["status"] == "unknown_usage" and not result["recovered"]
    assert app.history()[0]["status"] == "unknown_usage"


def test_preview_defaults_to_astra_without_execution(tmp_path):
    app = service(tmp_path, executor=lambda *a: pytest.fail("preview executed a model"))
    preview = app.preview(request())
    assert preview["plan"]["selected"]["stages"][0]["model"] == "gpt-6-astra"
    assert preview["requires_approval"] is True
    assert preview["estimate_basis"] == "provisional_allowances_not_measured"
    assert app.history() == []


@pytest.mark.parametrize("changes,code,field", [
    ({"task": ""}, "task_required", "task"),
    ({"budget_credits": "bad"}, "budget_invalid", "budget"),
    ({"evidence": ["missing.txt"]}, "evidence_invalid", "evidence"),
    ({"images": ["missing.png"]}, "images_invalid", "images"),
    ({"context_allowance_tokens": -1}, "context_invalid", "context"),
    ({"output_allowance_tokens": 1}, "output_invalid", "output"),
])
def test_preview_errors_identify_safe_recovery_field(tmp_path, changes, code, field):
    app = service(tmp_path)
    with pytest.raises(ValueError) as error:
        app.preview(request(**changes))
    assert getattr(error.value, "code", None) == code
    assert getattr(error.value, "field", None) == field


def test_host_options_expose_live_efforts_without_execution(tmp_path):
    app = service(tmp_path, executor=lambda *a: pytest.fail("catalog spent a model call"))
    app.probe = lambda root: {"models": [{"model": "gpt-6-astra", "reasoning_efforts": ["low", "max"],
                                         "input_modalities": ["text", "image"]}]}
    options = app.host_options("sample")
    assert options["models"][0]["reasoning_efforts"] == ["low", "max"]
    assert options["execution_status"] == "not_executed"
    with pytest.raises(ValueError):
        app.host_options("unregistered")


def test_host_options_are_bounded_and_do_not_echo_extra_host_fields(tmp_path):
    app = service(tmp_path)
    app.probe = lambda root: {"models": [{"model": "gpt-6-astra", "reasoning_efforts": ["low"],
                                         "input_modalities": ["text"], "private": "do not expose"}]}
    assert "private" not in json.dumps(app.host_options("sample"))


@pytest.mark.parametrize("efforts", [["low"] * 33, ["x" * 33], ["<script>"], [None]])
def test_host_option_validation_rejects_malformed_values(tmp_path, efforts):
    app = service(tmp_path)
    app.probe = lambda root: {"models": [{"model": "gpt-6-astra", "reasoning_efforts": efforts,
                                         "input_modalities": ["text"]}]}
    with pytest.raises(ValueError, match="options"):
        app.host_options("sample")


def test_low_budget_never_silently_falls_back(tmp_path):
    app = service(tmp_path)
    preview = app.preview(request(budget_credits=5))
    assert preview["plan"]["decision"] == "needs_replan"
    with pytest.raises(ValueError, match="not executable"):
        app.execute(preview["id"], approved=True)


def test_economy_is_explicit(tmp_path):
    preview = service(tmp_path).preview(request(mode="economy"))
    assert preview["plan"]["selected"]["stages"][0]["model"] == "gpt-5.6-sol"


def test_approval_replay_and_prompt_free_history(tmp_path):
    app = service(tmp_path)
    preview = app.preview(request(task="PRIVATE TASK"))
    with pytest.raises(ValueError, match="approval"):
        app.execute(preview["id"], approved=False)
    result = app.execute(preview["id"], approved=True)
    assert result["status"] == "completed"
    assert result["answer"] == "PRIVATE ANSWER"
    assert result["budget"]["spent_credits"] == 1.25
    with pytest.raises(ValueError, match="already"):
        app.execute(preview["id"], approved=True)
    history = json.dumps(app.history())
    assert "PRIVATE TASK" not in history
    assert "PRIVATE ANSWER" not in history
    assert "proof.txt" not in history
    assert "PRIVATE".encode() not in (tmp_path / "data/workbench.sqlite3").read_bytes()


def test_changed_evidence_requires_new_preview(tmp_path):
    app = service(tmp_path)
    preview = app.preview(request())
    (tmp_path / "project/proof.txt").write_text("Different facts")
    with pytest.raises(ValueError, match="changed"):
        app.execute(preview["id"], approved=True)
    assert app.history() == []


@pytest.mark.parametrize("path", ["../outside.txt", ".env", ".git/config"])
def test_evidence_boundaries(tmp_path, path):
    app = service(tmp_path)
    with pytest.raises(ValueError):
        app.preview(request(evidence=[path]))


def test_scan_failure_never_echoes_secret(tmp_path):
    app = service(tmp_path)
    secret = "ghp_" + "a" * 32
    (tmp_path / "project/proof.txt").write_text(secret)
    with pytest.raises(ValueError) as error:
        app.preview(request())
    assert secret not in str(error.value)
    assert "scan" in str(error.value)


def test_required_capability_and_effort_not_silently_reduced(tmp_path):
    app = service(tmp_path)
    with pytest.raises(ValueError, match="capabilit"):
        app.preview(request(required_capabilities=["write"]))
    with pytest.raises(ValueError, match="effort"):
        app.preview(request(effort="unsupported"))


def test_expired_preview(tmp_path, monkeypatch):
    app = service(tmp_path)
    preview = app.preview(request())
    monkeypatch.setattr("premium_model_budget_governor.workbench.time.time", lambda: preview["expires_at"] + 1)
    with pytest.raises(ValueError, match="expired"):
        app.execute(preview["id"], approved=True)


def test_unknown_usage_keeps_reservation_and_blocks_more_runs(tmp_path):
    def unknown(packet, ledger):
        budget_action({"action": "reserve", "task_id": packet["task_id"], "lease_id": packet["call_id"],
                       "model": packet["model"], "estimated_credits": packet["estimated_credits"]}, ledger)
        raise OSError("PRIVATE HOST ERROR")

    app = service(tmp_path, unknown)
    result = app.execute(app.preview(request())["id"], approved=True)
    assert result["status"] == "unknown_usage"
    assert result["budget"]["reserved_credits"] > 0
    assert "PRIVATE" not in json.dumps(result)
    with pytest.raises(ValueError, match="reconcile"):
        app.execute(app.preview(request())["id"], approved=True)


def test_client_cannot_mutate_preview_packet(tmp_path):
    app = service(tmp_path)
    preview = app.preview(request())
    preview["plan"]["selected"]["stages"][0]["model"] = "gpt-5.6-sol"
    result = app.execute(preview["id"], approved=True)
    assert result["requested_model"] == "gpt-6-astra"


def test_image_is_bound_to_approved_bytes_not_live_path(tmp_path):
    original = b"\x89PNG\r\n\x1a\nfixture-image"
    staged = []

    def inspect(packet, ledger):
        (tmp_path / "project/chart.png").write_bytes(b"changed while running")
        path = Path(packet["images"][0])
        staged.append(path)
        assert path.read_bytes() == original
        return completed(packet, ledger)

    app = service(tmp_path, inspect)
    (tmp_path / "project/chart.png").write_bytes(original)
    result = app.execute(app.preview(request(images=["chart.png"]))["id"], approved=True)
    assert result["status"] == "completed"
    assert not staged[0].exists()


def test_concurrent_instances_cannot_dispatch_together(tmp_path):
    entered, release = Event(), Event()

    def wait(packet, ledger):
        entered.set()
        assert release.wait(5)
        return completed(packet, ledger)

    app, other = service(tmp_path, wait), service(tmp_path)
    first, second = app.preview(request()), other.preview(request())
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(app.execute, first["id"], approved=True)
        try:
            assert entered.wait(3)
            with pytest.raises(ValueError, match="reconcile"):
                other.execute(second["id"], approved=True)
        finally:
            release.set()
        assert future.result()["status"] == "completed"


def test_malformed_completed_receipt_is_not_success(tmp_path):
    app = service(tmp_path, lambda packet, ledger: {"status": "completed", "usage": None})
    result = app.execute(app.preview(request())["id"], approved=True)
    assert result["status"] == "unknown_usage"


def test_workbench_cancel_before_execution_has_no_lease(tmp_path):
    app = service(tmp_path, lambda *a: pytest.fail("canceled task executed"))
    event = Event()
    event.set()
    result = app.execute(app.preview(request())["id"], approved=True, cancel_event=event)
    assert result["status"] == "canceled_before_dispatch"
    assert result["budget"]["leases"] == []
    assert app.history()[0]["status"] == "canceled_before_dispatch"


def test_browse_is_project_bound_and_excludes_private_files(tmp_path):
    app = service(tmp_path)
    root = tmp_path / "project"
    (root / ".env").write_text("private")
    (root / "docs").mkdir()
    (root / "chart.png").write_bytes(b"png")
    rows = app.browse("sample", ".")
    names = {row["name"] for row in rows["entries"]}
    assert names == {"proof.txt", "docs", "chart.png"}
    assert {row["name"] for row in app.browse("sample", ".", images=True)["entries"]} == {"docs", "chart.png"}
    with pytest.raises(ValueError):
        app.browse("sample", "../")
    with pytest.raises(ValueError):
        app.browse("unknown", ".")


def test_false_predispatch_cancel_with_reservation_is_unknown(tmp_path):
    def bad(packet, ledger):
        budget_action({"action":"reserve", "task_id":packet["task_id"], "lease_id":packet["call_id"],
                       "model":packet["model"], "estimated_credits":packet["estimated_credits"]}, ledger)
        return {"status":"canceled_before_dispatch"}
    app = service(tmp_path, bad)
    result = app.execute(app.preview(request())["id"], approved=True)
    assert result["status"] == "unknown_usage"
    assert result["budget"]["reserved_credits"] > 0


def test_reviewed_preference_is_scoped_to_actual_workbench_profile(tmp_path):
    app = service(tmp_path)
    before = app.preview(request(mode="economy", family="review"))
    assert before["plan"]["selected"]["stages"][0]["model"] == "gpt-5.6-sol"
    pairs = [{"task_id": f"{split}-{i}", "family":"review", "snapshot":f"snap-{i}", "rubric":"fixture-v1",
              "candidate":"gpt-6-astra-direct", "baseline":"gpt-5.6-sol-direct", "split":split,
              "cost_basis":"token_rate_estimate", "matched":True, "complete":True,
              "candidate_pass":True, "baseline_pass":True, "candidate_credits":2, "baseline_credits":3}
             for split in ["calibration","holdout"] for i in range(20)]
    proposal = app.policies.propose(before["policy_scope"], pairs)
    app.policies.activate(proposal["id"], approved=True, expected_active=None)
    after = app.preview(request(mode="economy", family="review"))
    assert after["plan"]["selected"]["stages"][0]["model"] == "gpt-6-astra"
    assert after["plan"]["policy_application"]["status"] == "applied"
    assert any("Reviewed preference applied" in warning for warning in after["warnings"])
    changed = app.preview(request(mode="economy", family="review", context_allowance_tokens=64000))
    assert changed["plan"]["policy_application"]["status"] == "inactive"
    assert changed["plan"]["selected"]["stages"][0]["model"] == "gpt-5.6-sol"
