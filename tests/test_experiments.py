from copy import deepcopy

import pytest

from premium_model_budget_governor.experiments import compare_runs, normalize_receipt


def test_codex_cumulative_import_is_prompt_free_and_does_not_sum_snapshots(tmp_path):
    import json
    from premium_model_budget_governor.experiments import import_codex_receipt
    path = tmp_path / "session.jsonl"
    events = [{"type": "turn_context", "payload": {"model": "gpt-6-astra"}},
              {"type": "response_item", "payload": {"secret_prompt": "PRIVATE"}}]
    for n in [10, 20, 20]:
        events.append({"type": "event_msg", "payload": {"type": "token_count", "info": {
            "total_token_usage": {"input_tokens": n, "cached_input_tokens": 5, "output_tokens": 2}}}})
    path.write_text("\n".join(json.dumps(e) for e in events))
    result = import_codex_receipt(path, "call")
    assert result["usage"]["input_tokens"] == 20
    assert result["usage"]["cached_tokens"] == 5
    assert "PRIVATE" not in str(result)
    events.append({"type": "turn_context", "payload": {"model": "gpt-5.6-sol"}})
    path.write_text("\n".join(json.dumps(e) for e in events))
    with pytest.raises(ValueError, match="single-model"):
        import_codex_receipt(path, "call")


def run(arm, cost=1, repeat=0):
    return {"task_id": "task", "snapshot": "snapshot1", "rubric": "rubric1",
            "repeat": repeat, "arm": arm, "passed": True, "complete": True,
            "receipt_source": "host", "expected_calls": 1,
            "calls": [{"call_id": f"{arm}-{repeat}", "actual_model": "gpt-6-astra",
                       "billed_credits": cost}]}


def test_missing_usage_is_not_free_and_small_sample_is_not_a_winner():
    rows = [run("sol"), run("astra")]
    rows[1]["calls"][0].pop("billed_credits")
    result = compare_runs({"baseline": "sol", "runs": rows})
    assert result["comparisons"][0]["matched_cost_pairs"] == 0
    assert result["comparisons"][0]["mean_credit_difference"] is None
    assert result["recommendation"] == "insufficient_evidence"


def test_full_cost_includes_failed_retries_and_never_promotes_a_cheaper_failure():
    rows = [run("sol", 3), run("hybrid", 1)]
    rows[1]["calls"].append({"call_id": "retry", "actual_model": "gpt-6-astra", "billed_credits": 4})
    rows[1]["expected_calls"] = 2
    rows[1]["passed"] = False
    result = compare_runs({"baseline": "sol", "runs": rows})["comparisons"][0]
    assert result["mean_credit_difference"] == 2
    assert result["quality_regressions"] == 1


@pytest.mark.parametrize("change", ["snapshot", "rubric"])
def test_mismatched_inputs_are_not_pairs(change):
    rows = [run("sol"), run("astra")]
    rows[1][change] = "different"
    assert compare_runs({"baseline": "sol", "runs": rows})["comparisons"][0]["matched_quality_pairs"] == 0


def test_duplicate_rows_and_duplicate_calls_rejected():
    row = run("sol")
    with pytest.raises(ValueError):
        compare_runs({"baseline": "sol", "runs": [row, deepcopy(row)]})
    other = run("astra")
    other["calls"][0]["call_id"] = row["calls"][0]["call_id"]
    with pytest.raises(ValueError):
        compare_runs({"baseline": "sol", "runs": [row, other]})


def test_estimated_and_partial_receipts_excluded():
    for key, value in [("receipt_source", "estimate"), ("complete", False), ("expected_calls", 2)]:
        rows = [run("sol"), run("astra")]
        rows[1][key] = value
        assert compare_runs({"baseline": "sol", "runs": rows})["comparisons"][0]["matched_cost_pairs"] == 0


def test_cache_is_subtracted_once_and_reasoning_not_double_counted():
    receipt = normalize_receipt({"call_id": "r", "actual_model": "gpt-6-astra",
        "usage": {"input_tokens": 1000, "output_tokens": 200,
                  "input_tokens_details": {"cached_tokens": 400},
                  "output_tokens_details": {"reasoning_tokens": 100}}})
    assert receipt["credits"] == pytest.approx(.41)
    assert receipt["cost_basis"] == "token_rate_estimate"


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1, True, 1.5])
def test_bad_usage_rejected(bad):
    with pytest.raises(ValueError):
        normalize_receipt({"call_id": "r", "actual_model": "gpt-6-astra",
                           "usage": {"input_tokens": bad, "output_tokens": 1}})


def test_invalid_cache_and_unknown_model_never_create_false_cost():
    with pytest.raises(ValueError):
        normalize_receipt({"call_id": "r", "actual_model": "gpt-6-astra",
            "usage": {"input_tokens": 10, "output_tokens": 1, "cached_tokens": 11}})
    receipt = normalize_receipt({"call_id": "r", "actual_model": "future-model",
                               "usage": {"input_tokens": 10, "output_tokens": 1}})
    assert receipt["credits"] is None


def test_mixed_billing_and_estimation_are_not_cost_pairs():
    rows = [run("sol"), run("astra")]
    rows[1]["calls"][0].pop("billed_credits")
    rows[1]["calls"][0]["usage"] = {"input_tokens": 100, "output_tokens": 100}
    assert compare_runs({"baseline": "sol", "runs": rows})["comparisons"][0]["matched_cost_pairs"] == 0


def test_different_pair_cost_bases_are_never_averaged_together():
    rows = [run("sol", 4), run("astra", 2), run("sol", repeat=1), run("astra", repeat=1)]
    for row, incoming in zip(rows[2:], [1000, 2000]):
        call = row["calls"][0]
        call.pop("billed_credits")
        call["usage"] = {"input_tokens": incoming, "output_tokens": 0}
    result = compare_runs({"baseline": "sol", "runs": rows})["comparisons"][0]
    assert result["matched_cost_pairs"] == 2
    assert result["mean_credit_difference"] is None
    assert result["cost_by_basis"]["host_billed"]["mean_credit_difference"] == -2
    assert result["cost_by_basis"]["token_rate_estimate"]["mean_credit_difference"] == .25


def test_complete_workflow_time_is_optional_and_not_a_quality_claim():
    rows = [run("sol"), run("astra")]
    rows[0]["total_elapsed_seconds"] = 20
    rows[1]["total_elapsed_seconds"] = 12.5
    rows[1]["passed"] = False
    result = compare_runs({"baseline": "sol", "runs": rows})["comparisons"][0]
    assert result["matched_time_pairs"] == 1
    assert result["mean_elapsed_difference_seconds"] == -7.5
    assert result["quality_regressions"] == 1
    rows[1]["complete"] = False
    result = compare_runs({"baseline": "sol", "runs": rows})["comparisons"][0]
    assert result["matched_time_pairs"] == 0
    assert result["mean_elapsed_difference_seconds"] is None


@pytest.mark.parametrize("bad", [-1, True, "10", float("nan"), float("inf")])
def test_invalid_workflow_time_rejected(bad):
    rows = [run("sol"), run("astra")]
    rows[1]["total_elapsed_seconds"] = bad
    with pytest.raises(ValueError):
        compare_runs({"baseline": "sol", "runs": rows})


def test_coverage_reports_missing_baseline_and_candidate_runs():
    rows = [run("sol"), run("astra"), run("sol", repeat=1), run("astra", repeat=2)]
    result = compare_runs({"baseline": "sol", "runs": rows})["comparisons"][0]
    assert result["coverage"] == {"baseline_runs": 2, "arm_runs": 2,
        "baseline_only_runs": 1, "arm_only_runs": 1, "fully_matched": False}


@pytest.mark.parametrize("key,value,reason", [
    ("complete", False, "incomplete_workflow"),
    ("receipt_source", "estimate", "non_host_receipts"),
    ("expected_calls", 2, "call_count_mismatch"),
])
def test_cost_exclusions_are_visible(key, value, reason):
    rows = [run("sol"), run("astra")]
    rows[1][key] = value
    result = compare_runs({"baseline": "sol", "runs": rows})["comparisons"][0]
    assert result["cost_exclusion_reasons"][reason] == 1


def test_task_balancing_and_cheaper_failures_are_explicit():
    rows = []
    for repeat, delta in enumerate([-2, -2, -2, 6]):
        pair = [run("sol", 10, repeat), run("astra", 10 + delta, repeat)]
        for row in pair:
            row["task_id"] = "frequent" if repeat < 3 else "rare"
        pair[1]["passed"] = repeat != 0
        rows.extend(pair)
    result = compare_runs({"baseline": "sol", "runs": rows})["comparisons"][0]
    costs = result["cost_by_basis"]["host_billed"]
    assert costs["mean_credit_difference"] == 0
    assert costs["task_balanced_mean_credit_difference"] == 2
    assert costs["distinct_tasks"] == 2
    assert costs["cheaper_quality_regressions"] == 1
    assert costs["cheaper_both_passed"] == 2
    assert costs["total_baseline_credits"] == costs["total_arm_credits"] == 40
    assert compare_runs({"baseline": "sol", "runs": list(reversed(rows))})["comparisons"][0] == result


def test_same_exclusion_on_both_sides_counts_once_per_pair():
    rows = [run("sol"), run("astra")]
    for row in rows:
        row["complete"] = False
        row["calls"][0].pop("billed_credits")
    result = compare_runs({"baseline": "sol", "runs": rows})["comparisons"][0]
    assert result["cost_exclusion_reasons"] == {"incomplete_workflow": 1, "unknown_cost": 1}
    assert result["cost_by_basis"] == {}


def test_incompatible_pair_basis_is_explained():
    rows = [run("sol"), run("astra")]
    rows[1]["calls"][0].pop("billed_credits")
    rows[1]["calls"][0]["usage"] = {"input_tokens": 10, "output_tokens": 1}
    result = compare_runs({"baseline": "sol", "runs": rows})["comparisons"][0]
    assert result["cost_exclusion_reasons"] == {"incompatible_pair_cost_bases": 1}


def test_empty_receipts_do_not_become_zero_cost_success():
    rows = [run("sol"), run("astra")]
    rows[1].update(calls=[], expected_calls=0)
    result = compare_runs({"baseline": "sol", "runs": rows})["comparisons"][0]
    assert result["cost_exclusion_reasons"] == {"no_expected_calls": 1, "unknown_cost": 1}
    assert result["matched_cost_pairs"] == 0


def test_historical_public_receipts_reproduce_without_model_calls():
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "artifacts/field-trial-2026-09-07/combined-experiment-input.json"
    result = compare_runs(json.loads(path.read_text(encoding="utf-8")))
    by_arm = {row["arm"]: row for row in result["comparisons"]}
    for row in by_arm.values():
        assert row["coverage"]["fully_matched"]
        assert row["matched_cost_pairs"] == 5
        assert row["cost_exclusion_reasons"] == {}
    assert by_arm["prepared"]["cost_by_basis"]["token_rate_estimate"]["cheaper_both_passed"] == 1
    assert by_arm["review"]["mean_credit_difference"] == pytest.approx(3.10534)
    assert result["automatic_promotion"] is False
