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
