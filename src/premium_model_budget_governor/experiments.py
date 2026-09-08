"""Matched, prompt-free experiment accounting. Never infer missing usage as zero."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from hashlib import sha256
from pathlib import Path
from statistics import mean
from typing import Mapping

from .cost import RATES, _token, model_credits
from .workflow import flag, number


def import_codex_receipt(path: Path, call_id: str) -> dict:
    """Import only counters from one explicitly selected single-model rollout.

    The last cumulative snapshot covers the session, not just the latest turn.
    Local log formats are not a stable provider API. Never copy the raw rollout.
    """
    models, latest = set(), None
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            payload = event.get("payload", {})
            if event.get("type") == "turn_context" and payload.get("model"):
                models.add(payload["model"])
            if event.get("type") != "event_msg" or payload.get("type") != "token_count":
                continue
            info = payload.get("info")
            total = info.get("total_token_usage") if isinstance(info, dict) else None
            if not isinstance(total, dict):
                continue
            current = {"input_tokens": _token(total.get("input_tokens"), "input_tokens"),
                       "cached_tokens": _token(total.get("cached_input_tokens", 0), "cached_tokens"),
                       "output_tokens": _token(total.get("output_tokens"), "output_tokens")}
            if latest and any(current[k] < latest[k] for k in current):
                raise ValueError("cumulative counters decreased; split sessions before importing")
            latest = current
    if len(models) != 1 or latest is None:
        raise ValueError("a single-model log with token counters is required")
    model = next(iter(models))
    # Validate without returning any path, prompt, response, or account identifier.
    normalized = normalize_receipt({"call_id": call_id, "actual_model": model, "usage": latest})
    return {"call_id": call_id, "actual_model": model, "usage": latest,
            "credits": normalized["credits"], "cost_basis": normalized["cost_basis"],
            "rate_assumption": "configured standard rates; service tier not verified by importer",
            "source": "codex_local_cumulative_snapshot", "raw_prompts_stored": False,
            "counter_fingerprint": sha256(json.dumps([model, latest], sort_keys=True).encode()).hexdigest()}


def normalize_receipt(call: Mapping) -> dict:
    call_id, model = call.get("call_id"), call.get("actual_model")
    if not isinstance(call_id, str) or not call_id or not isinstance(model, str) or not model:
        raise ValueError("call_id and actual_model are required")
    result = {"call_id": call_id, "actual_model": model, "credits": None, "cost_basis": "unknown"}
    usage = call.get("usage")
    if usage is not None:
        if not isinstance(usage, Mapping):
            raise ValueError("usage must be an object")
        # Total output already includes reasoning. Cached input is a subset of input.
        incoming = _token(usage.get("input_tokens"), "input_tokens")
        outgoing = _token(usage.get("output_tokens"), "output_tokens")
        details = usage.get("input_tokens_details", {})
        if not isinstance(details, Mapping):
            raise ValueError("input_tokens_details must be an object")
        cached = _token(details.get("cached_tokens", usage.get("cached_tokens", 0)), "cached_tokens")
        if cached > incoming:
            raise ValueError("cached input cannot exceed total input")
        result["usage"] = {"input_tokens": incoming, "cached_tokens": cached, "output_tokens": outgoing}
        if model in RATES:
            result.update(credits=model_credits(model, {"input": incoming - cached,
                          "cached_input": cached, "output": outgoing}, fast_mode=flag(call, "fast_mode")),
                          cost_basis="token_rate_estimate")
    if call.get("billed_credits") is not None:
        result.update(credits=number(call["billed_credits"], "billed_credits"), cost_basis="host_billed")
    return result


def compare_runs(packet: Mapping) -> dict:
    """Pair identical task/snapshot/rubric/repeat; include failures and all calls.

    Host provenance and completeness are assertions, not cryptographic attestation.
    Descriptive results are not learned policy and never automatically promote a model.
    """
    baseline, runs = packet.get("baseline"), packet.get("runs")
    if not isinstance(baseline, str) or not baseline or not isinstance(runs, list) or not runs:
        raise ValueError("baseline and non-empty runs are required")
    grouped, seen_calls = defaultdict(dict), set()
    for row in runs:
        if not isinstance(row, Mapping):
            raise ValueError("each run must be an object")
        labels = [row.get(k) for k in ("task_id", "snapshot", "rubric", "arm")]
        if any(not isinstance(v, str) or not v for v in labels):
            raise ValueError("task_id, snapshot, rubric and arm are required")
        task, snapshot, rubric, arm = labels
        repeat = _token(row.get("repeat", 0), "repeat")
        key = (task, snapshot, rubric, repeat)
        if key in grouped[arm]:
            raise ValueError("duplicate run; repeated samples need distinct repeat IDs")
        passed = row.get("passed")
        if not isinstance(passed, bool):
            raise ValueError("passed must be an externally graded boolean")
        calls = row.get("calls", [])
        if not isinstance(calls, list) or any(not isinstance(c, Mapping) for c in calls):
            raise ValueError("calls must be a list of objects")
        receipts = [normalize_receipt(c) for c in calls]
        for receipt in receipts:
            if receipt["call_id"] in seen_calls:
                raise ValueError("duplicate call_id would double-count experiment usage")
            seen_calls.add(receipt["call_id"])
        expected = _token(row.get("expected_calls"), "expected_calls")
        complete = flag(row, "complete")
        elapsed = row.get("total_elapsed_seconds")
        if elapsed is not None:
            elapsed = number(elapsed, "total_elapsed_seconds")
        bases = {c["cost_basis"] for c in receipts}
        exclusions = []
        for invalid, reason in [
            (not complete, "incomplete_workflow"),
            (row.get("receipt_source") != "host", "non_host_receipts"),
            (expected != len(receipts), "call_count_mismatch"),
            (expected == 0, "no_expected_calls"),
            (not bases or "unknown" in bases, "unknown_cost"),
            (len(bases) > 1, "mixed_cost_bases"),
        ]:
            if invalid:
                exclusions.append(reason)
        cost_valid = not exclusions
        grouped[arm][key] = {"passed": passed, "credits": sum(c["credits"] for c in receipts) if cost_valid else None,
                             "basis": next(iter(bases)) if cost_valid else "unknown",
                             "elapsed": elapsed if complete else None, "exclusions": exclusions}
    if baseline not in grouped:
        raise ValueError("baseline has no runs")
    comparisons = []
    for arm in sorted(set(grouped) - {baseline}):
        keys = sorted(set(grouped[baseline]) & set(grouped[arm]))
        pairs = [(grouped[baseline][k], grouped[arm][k]) for k in keys]
        costs = [(a, b) for a, b in pairs if a["credits"] is not None and b["credits"] is not None
                 and a["basis"] == b["basis"]]
        differences = [b["credits"] - a["credits"] for a, b in costs]
        cost_bases = sorted({a["basis"] for a, _ in costs})
        cost_by_basis = {}
        for basis in cost_bases:
            basis_pairs = [(k, a, b) for k, (a, b) in zip(keys, pairs)
                           if a["credits"] is not None and b["credits"] is not None
                           and a["basis"] == b["basis"] == basis]
            per_task = defaultdict(list)
            for k, a, b in basis_pairs:
                per_task[k[0]].append(b["credits"] - a["credits"])
            values = [b["credits"] - a["credits"] for _, a, b in basis_pairs]
            cost_by_basis[basis] = {
                "matched_pairs": len(values), "mean_credit_difference": mean(values),
                "distinct_tasks": len(per_task),
                "task_balanced_mean_credit_difference": mean(mean(v) for v in per_task.values()),
                "total_baseline_credits": sum(a["credits"] for _, a, _ in basis_pairs),
                "total_arm_credits": sum(b["credits"] for _, _, b in basis_pairs),
                "cheaper_both_passed": sum(b["credits"] < a["credits"] and a["passed"] and b["passed"]
                                           for _, a, b in basis_pairs),
                "cheaper_quality_regressions": sum(b["credits"] < a["credits"] and a["passed"] and not b["passed"]
                                                   for _, a, b in basis_pairs),
            }
        # Count each reason once per matched pair; multiple reasons may apply.
        exclusions = Counter()
        for a, b in pairs:
            reasons = set(a["exclusions"]) | set(b["exclusions"])
            if a["credits"] is not None and b["credits"] is not None and a["basis"] != b["basis"]:
                reasons.add("incompatible_pair_cost_bases")
            exclusions.update(sorted(reasons))
        times = [(a, b) for a, b in pairs if a["elapsed"] is not None and b["elapsed"] is not None]
        comparisons.append({"arm": arm, "matched_quality_pairs": len(pairs), "matched_cost_pairs": len(costs),
            "distinct_tasks": len({k[0] for k in keys}),
            "unmatched_runs": len(grouped[arm]) - len(keys),
            "coverage": {"baseline_runs": len(grouped[baseline]), "arm_runs": len(grouped[arm]),
                         "baseline_only_runs": len(grouped[baseline]) - len(keys),
                         "arm_only_runs": len(grouped[arm]) - len(keys),
                         "fully_matched": len(keys) == len(grouped[baseline]) == len(grouped[arm])},
            "cost_exclusion_reasons": dict(sorted(exclusions.items())),
            "baseline_passes": sum(a["passed"] for a, _ in pairs),
            "arm_passes": sum(b["passed"] for _, b in pairs),
            "quality_regressions": sum(a["passed"] and not b["passed"] for a, b in pairs),
            "quality_improvements": sum(not a["passed"] and b["passed"] for a, b in pairs),
            "mean_credit_difference": mean(differences) if len(cost_bases) == 1 else None,
            "cost_bases": cost_bases, "cost_by_basis": cost_by_basis,
            "matched_time_pairs": len(times),
            "mean_elapsed_difference_seconds": mean(b["elapsed"] - a["elapsed"] for a, b in times) if times else None,
            "time_basis": "caller_reported_complete_workflow_wall_time",
            "interpretation": "descriptive_only; negative difference means lower cost, not equivalent quality"})
    return {"schema_version": 1, "baseline": baseline, "comparisons": comparisons,
            "recommendation": "insufficient_evidence", "automatic_promotion": False,
            "limitations": ["No universal winner or weekly-limit conversion is inferred.",
                            "Call completeness, model identity and grading are supplied by the host.",
                            "Timing is caller-reported, includes failed outcomes, and does not establish equivalent quality.",
                            "Different credit bases are reported separately, never averaged together.",
                            "Use preregistered held-out tasks and repeated trials before changing policy."],
            "raw_prompts_stored": False}
