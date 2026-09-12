import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("tool_trial", Path(__file__).resolve().parents[1] / "scripts/run_tool_skill_trial.py")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)


def test_correct_answer_without_tool_event_does_not_pass():
    receipt = {"status": "completed", "answer": '{"ok":true}'}
    checks = trial.assess(receipt, {"ok": True}, {}, {})
    assert checks["answer_matches"]
    assert not all(checks.values())


def test_observed_tool_and_correct_answer_still_require_unchanged_inputs():
    receipt = {"status": "completed", "answer": '{"ok":true}',
               "activity": {"completed_items": {"commandExecution": 1}}}
    assert all(trial.assess(receipt, {"ok": True}, {"f": "abc"}, {"f": "abc"}).values())
    assert not all(trial.assess(receipt, {"ok": True}, {"f": "abc"}, {"f": "def"}).values())
    receipt["answer"] = '{"ok":1}'
    assert not trial.assess(receipt, {"ok": True}, {}, {})["answer_matches"]


def test_admission_stop_preserves_all_unexecuted_calls(tmp_path, monkeypatch):
    import json
    import sys
    output = tmp_path / "trial"
    monkeypatch.setattr(sys, "argv", ["trial", "--execute", "--ledger", str(tmp_path / "budget"),
                                    "--budget-task", "test", "--output", str(output)])
    monkeypatch.setattr(trial, "budget_action", lambda *a: {"available_credits": 15, "reserved_credits": 0})
    def forbidden(*args):
        raise AssertionError("insufficient allowance must not dispatch")
    monkeypatch.setattr(trial, "execute_app_server", forbidden)
    trial.main()
    report = json.loads((output / "results.json").read_text())
    assert report["stop_reason"] == "budget_or_pending_lease"
    assert len(report["not_executed"]) == 4
    assert report["runs"] == []
    comparison = json.loads((output / "comparison.json").read_text())
    assert comparison["enrollment"]["missing_runs"] == 4
    assert comparison["enrollment"]["complete"] is False


def test_dispatch_exception_preserves_outcome_without_retry(tmp_path, monkeypatch):
    import json
    import sys
    output = tmp_path / "trial"
    monkeypatch.setattr(sys, "argv", ["trial", "--execute", "--ledger", str(tmp_path / "budget"),
                                    "--budget-task", "test", "--output", str(output)])
    monkeypatch.setattr(trial, "budget_action", lambda *a: {"available_credits": 40, "reserved_credits": 0, "spent_credits": 0})
    called = []
    def fail(*args):
        called.append(True)
        raise ValueError("private error detail")
    monkeypatch.setattr(trial, "execute_app_server", fail)
    trial.main()
    raw = (output / "results.json").read_text()
    report = json.loads(raw)
    assert len(called) == 1
    assert len(report["not_executed"]) == 3
    assert report["outcomes"][0]["status"] == "dispatch_error"
    assert "private error detail" not in raw
    comparison = json.loads((output / "comparison.json").read_text())
    assert comparison["enrollment"]["missing_runs"] == 4
