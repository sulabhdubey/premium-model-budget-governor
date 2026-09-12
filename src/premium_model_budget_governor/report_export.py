"""Content-excluding summaries for explicit human review before sharing."""
from collections.abc import Mapping
from math import isfinite


def _numeric(value):
    return value if type(value) in (int, float) and isfinite(value) else None


def experiment_summary(result: Mapping) -> dict:
    enrollment = result.get("enrollment") or {}
    comparisons = []
    count_fields = ("matched_cost_pairs", "distinct_tasks", "baseline_passes", "arm_passes",
                    "quality_regressions", "quality_improvements", "unmatched_runs", "matched_time_pairs")
    for index, row in enumerate(result.get("comparisons", []), 1):
        coverage = row.get("coverage") or {}
        comparisons.append({"candidate": index,
            **{key: _numeric(row.get(key)) for key in count_fields},
            "mean_credit_difference": _numeric(row.get("mean_credit_difference")),
            "mean_elapsed_difference_seconds": _numeric(row.get("mean_elapsed_difference_seconds")),
            "cost_bases": [basis for basis in row.get("cost_bases", [])
                           if basis in {"host_billed", "token_rate_estimate"}],
            "coverage": {key: _numeric(coverage.get(key)) for key in
                         ("baseline_runs", "arm_runs", "baseline_only_runs", "arm_only_runs")},
            "fully_matched_supplied_runs": coverage.get("fully_matched") is True})
    return {"schema_version": 1, "record_type": "reviewable_experiment_summary",
            "comparisons": comparisons,
            "enrollment": {"complete": enrollment.get("complete") if type(enrollment.get("complete")) is bool else None,
                           **{key: _numeric(enrollment.get(key)) for key in ("missing_runs", "unexpected_runs")}},
            "review_required": True, "savings_proven": False, "independent_grading_verified": False,
            "identifiers_included": False, "automatic_promotion": False,
            "scope": "caller_supplied_descriptive_comparison",
            "privacy_notice": "Content and identifiers omitted; numeric patterns may still identify an experiment."}
