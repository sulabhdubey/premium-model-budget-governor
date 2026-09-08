import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("context_trial", Path(__file__).resolve().parents[1] / "scripts/run_context_trial.py")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)


def fixture():
    return {"id": "test", "model": "gpt-6-astra", "effort": "low", "budget_credits": 120,
            "reserve_credits": 12, "estimated_credits_per_call": 12,
            "orders": [["inherit", "focused_catalog"], ["focused_catalog", "inherit"]],
            "tasks": [{"id": "one", "prompt": "Return JSON", "oracle": {"ok": True}}],
            "limitations": ["simulation"]}


def test_dry_run_never_creates_files_or_calls(tmp_path):
    out = tmp_path / "new"
    result = trial.run_trial(fixture(), out, invoke=lambda *_: pytest.fail("dispatch"))
    assert result["planned_calls"] == 4
    assert result["model_calls"] == 0
    assert not out.exists()
    assert [r["arm"] for r in result["enrolled"]] == ["inherit", "focused_catalog", "focused_catalog", "inherit"]


@pytest.mark.parametrize("answer", ['{"ok":1}', '```json\n{"ok":true}\n```', '{"ok":true,"extra":1}', 'invalid'])
def test_strict_grade_rejects_wrong_types_and_extra_output(answer):
    assert not trial.grade(answer, {"ok": True})


def test_quality_failure_retains_receipt_and_unexecuted_enrollment(tmp_path):
    def invoke(packet, ledger):
        return {"status": "completed", "host_configured_model": "gpt-6-astra",
                "usage": {"input_tokens": 10, "output_tokens": 1, "cached_tokens": 0},
                "estimated_credits": 1, "answer": '{"ok": false}'}
    result = trial.run_trial(fixture(), tmp_path / "new", execute=True, invoke=invoke)
    assert result["stop_reason"] == "fixed_quality_gate_failed"
    assert len(result["not_executed"]) == 3
    assert result["runs"][0]["passed"] is False
    assert (tmp_path / "new/one-0-inherit.json").exists()


def test_unknown_usage_stops_without_inventing_cost_pair(tmp_path):
    result = trial.run_trial(fixture(), tmp_path / "new", execute=True,
                             invoke=lambda *_: {"status": "unknown_usage"})
    assert result["stop_reason"] == "execution_or_usage_uncertain"
    assert result["runs"] == []
    assert len(result["not_executed"]) == 3


def test_cannot_overwrite_existing_trial(tmp_path):
    with pytest.raises(FileExistsError):
        trial.run_trial(fixture(), tmp_path, execute=True, invoke=lambda *_: pytest.fail("dispatch"))


def test_frozen_inputs_and_complete_counterbalanced_comparison(tmp_path):
    def invoke(packet, ledger):
        assert "oracle" not in packet["prompt"]
        assert packet["model"] == "gpt-6-astra"
        return {"status": "completed", "host_configured_model": "gpt-6-astra",
                "usage": {"input_tokens": 10, "output_tokens": 1, "cached_tokens": 0},
                "estimated_credits": 1, "answer": '{"ok":true}'}
    out = tmp_path / "new"
    result = trial.run_trial(fixture(), out, execute=True, invoke=invoke)
    assert result["not_executed"] == []
    manifest = json.loads((out / "manifest.json").read_text())
    assert result["manifest_sha256"] == trial.digest(manifest)
    comparison = json.loads((out / "comparison.json").read_text())
    assert comparison["comparisons"][0]["matched_cost_pairs"] == 2
    assert comparison["automatic_promotion"] is False


def test_public_counter_export_matches_enrollment_and_configured_rates():
    import csv
    from premium_model_budget_governor.experiments import normalize_receipt
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "examples/context-trial.json").read_text())
    with (root / "artifacts/context-trial-2026-09-08/counters.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected = trial.enrollment(data)
    assert len(rows) == len(expected) == 12
    for row, planned in zip(rows, expected):
        assert (row["task_id"], int(row["repeat"]), row["arm"]) == (planned["task_id"], planned["repeat"], planned["arm"])
        receipt = normalize_receipt({"call_id": planned["call_id"], "actual_model": data["model"],
            "usage": {k: int(row[k]) for k in ("input_tokens", "cached_tokens", "output_tokens")}})
        assert receipt["credits"] == pytest.approx(float(row["estimated_credits"]))
        assert row["passed"] == "true"
    assert sum(float(row["estimated_credits"]) for row in rows) == pytest.approx(60.1099)
    manifest = {"fixture": data, "enrolled": expected,
                "image_hashes": {t["id"]: trial.sha256((root / t["image"]).read_bytes()).hexdigest()
                                 for t in data["tasks"] if t.get("image")}}
    assert trial.digest(manifest) == "c3e6c8b7f394030e09c49cdba760eeecb39fdb088acd7e8c352a524ec20dfcc4"
