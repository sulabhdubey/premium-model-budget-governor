from premium_model_budget_governor.report_export import experiment_summary
from premium_model_budget_governor.experiments import compare_runs


def test_export_omits_identifiers_and_retains_quality_failures():
    rows = [{"task_id": "PRIVATE-TASK", "snapshot": "PRIVATE-SOURCE", "rubric": "PRIVATE-RUBRIC",
             "arm": arm, "passed": passed, "complete": True, "expected_calls": 1,
             "receipt_source": "host", "calls": [{"call_id": arm, "actual_model": "gpt-6-astra",
                                                    "billed_credits": cost}]}
            for arm, passed, cost in [("PRIVATE-BASE", True, 2), ("PRIVATE-CANDIDATE", False, 1)]]
    result = experiment_summary(compare_runs({"baseline": "PRIVATE-BASE", "runs": rows}))
    assert "PRIVATE" not in str(result)
    assert result["comparisons"][0]["quality_regressions"] == 1
    assert result["comparisons"][0]["mean_credit_difference"] == -1
    assert result["comparisons"][0]["candidate"] == 1
    assert result["savings_proven"] is False
    assert result["review_required"] is True


def test_empty_enrollment_is_not_success():
    rows = [{"task_id": "private", "snapshot": "s", "rubric": "r", "arm": arm}
            for arm in ("base", "candidate")]
    result = experiment_summary(compare_runs({"baseline": "base", "runs": [], "enrollment": rows}))
    assert result["enrollment"]["missing_runs"] == 2
    assert result["enrollment"]["complete"] is False
    assert result["comparisons"][0]["mean_credit_difference"] is None


def test_free_text_and_unrecognized_basis_do_not_escape_allowlist():
    result = experiment_summary({"secret": "PRIVATE", "comparisons": [{
        "arm": "PRIVATE", "cost_bases": ["PRIVATE", "host_billed"],
        "cost_by_basis": {"PRIVATE": {"note": "PRIVATE"}}, "coverage": {},
    }]})
    assert "PRIVATE" not in str(result)
    assert result["comparisons"][0]["cost_bases"] == ["host_billed"]
