"""Matched, prompt-free experiment accounting. Never infer missing usage as zero."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import os
from hashlib import sha256
from pathlib import Path
from statistics import mean
from typing import Mapping

from .cost import _token
from .accounting import estimate_observed
from .telemetry import normalize_counters
from .workflow import flag, number


def import_codex_receipt(path: Path, call_id: str, *, max_bytes: int = 64 * 1024 * 1024) -> dict:
    """Import only counters from one explicitly selected single-model rollout.

    The last cumulative snapshot covers the session, not just the latest turn.
    Local log formats are not a stable provider API. Never copy the raw rollout.
    """
    if type(max_bytes) is not int or not 1 <= max_bytes <= 64 * 1024 * 1024:
        raise ValueError("invalid rollout size limit")
    models, latest = set(), None
    last_reported = {}
    digest, size = sha256(), 0
    with path.open("rb") as handle:
        before = os.fstat(handle.fileno())
        if before.st_size > max_bytes:
            raise ValueError("rollout exceeds size limit")
        while True:
            line = handle.readline(4 * 1024 * 1024 + 1)
            if not line:
                break
            size += len(line)
            if len(line) > 4 * 1024 * 1024 or size > max_bytes:
                raise ValueError("rollout line or file exceeds size limit")
            digest.update(line)
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("rollout event must be an object")
            payload = event.get("payload", {})
            if not isinstance(payload, dict):
                raise ValueError("rollout payload must be an object")
            if event.get("type") == "turn_context" and payload.get("model"):
                models.add(payload["model"])
            if event.get("type") != "event_msg" or payload.get("type") != "token_count":
                continue
            info = payload.get("info")
            total = info.get("total_token_usage") if isinstance(info, dict) else None
            if not isinstance(total, dict):
                continue
            counters = normalize_counters(total)
            current = {k: counters[k] for k in ("input_tokens", "output_tokens")}
            for key, assumption in (("cached_tokens", "absent_cached_input_assumed_zero"),
                                    ("cache_write_tokens", "absent_cache_write_assumed_zero")):
                if assumption not in counters["counter_assumptions"]:
                    current[key] = counters[key]
            if counters["reasoning_output_tokens"] is not None:
                current["reasoning_output_tokens"] = counters["reasoning_output_tokens"]
            if any(current[k] < last_reported[k] for k in current.keys() & last_reported.keys()):
                raise ValueError("cumulative counters decreased; split sessions before importing")
            last_reported.update(current)
            latest = current
        after = os.fstat(handle.fileno())
        if size != before.st_size or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError("rollout changed during read; retry a stable snapshot")
    if len(models) != 1 or latest is None:
        raise ValueError("a single-model log with token counters is required")
    model = next(iter(models))
    # Validate without returning any path, prompt, response, or account identifier.
    normalized = normalize_receipt({"call_id": call_id, "actual_model": model, "usage": latest})
    return {"call_id": call_id, "actual_model": model, "usage": latest,
            "counter_assumptions": normalized["counter_assumptions"],
            "credits": normalized["credits"], "cost_basis": normalized["cost_basis"],
            "rate_version": normalized["rate_version"], "cost_status": normalized["cost_status"],
            "rate_assumption": "configured standard rates; service tier not verified by importer",
            "source": "codex_local_cumulative_snapshot", "raw_prompts_stored": False,
            "source_digest": digest.hexdigest(), "source_bytes": size,
            "counter_fingerprint": sha256(json.dumps([model, latest], sort_keys=True).encode()).hexdigest()}


def normalize_receipt(call: Mapping) -> dict:
    call_id, model = call.get("call_id"), call.get("actual_model")
    if not isinstance(call_id, str) or not call_id or not isinstance(model, str) or not model:
        raise ValueError("call_id and actual_model are required")
    result = {"call_id": call_id, "actual_model": model, "credits": None, "cost_basis": "unknown",
              "rate_version": None, "cost_status": "missing_usage"}
    usage = call.get("usage")
    if usage is not None:
        if not isinstance(usage, Mapping):
            raise ValueError("usage must be an object")
        # Total output already includes reasoning. Cached input is a subset of input.
        counters = normalize_counters(usage)
        incoming, outgoing, cached, writes = (counters[k] for k in
            ("input_tokens", "output_tokens", "cached_tokens", "cache_write_tokens"))
        result["counter_assumptions"] = counters["counter_assumptions"]
        result["reasoning_output_tokens"] = counters["reasoning_output_tokens"]
        result["usage"] = {"input_tokens": incoming, "cached_tokens": cached, "output_tokens": outgoing}
        if writes:
            result["usage"]["cache_write_tokens"] = writes
        fast = flag(call, "fast_mode")
        if fast and model != "gpt-6-astra":
            raise ValueError("Fast rate is only configured for Astra")
        tier = call.get("service_tier", "fast" if fast else "default")
        if fast and tier != "fast":
            raise ValueError("conflicting fast mode and service tier")
        estimate = estimate_observed(model, result["usage"], service_tier=tier, contract=call.get("rate_contract"))
        result.update({k: v for k, v in estimate.items() if k != "estimated_credits"})
        result["credits"] = estimate["estimated_credits"]
        result["cost_basis"] = estimate["cost_basis"] or "unknown"
    if call.get("billed_credits") is not None:
        result.update(credits=number(call["billed_credits"], "billed_credits"), cost_basis="host_billed",
                      rate_version=None, cost_status="billed_supplied")
    return result


def _run_identity(row: Mapping) -> tuple:
    if not isinstance(row, Mapping):
        raise ValueError("each run identity must be an object")
    labels = [row.get(k) for k in ("task_id", "snapshot", "rubric", "arm")]
    if any(not isinstance(v, str) or not v for v in labels):
        raise ValueError("task_id, snapshot, rubric and arm are required")
    task, snapshot, rubric, arm = labels
    return arm, (task, snapshot, rubric, _token(row.get("repeat", 0), "repeat"))


def compare_runs(packet: Mapping) -> dict:
    """Pair identical task/snapshot/rubric/repeat; include failures and all calls.

    Host provenance and completeness are assertions, not cryptographic attestation.
    Descriptive results are not learned policy and never automatically promote a model.
    """
    baseline, runs = packet.get("baseline"), packet.get("runs")
    if not isinstance(baseline, str) or not baseline or not isinstance(runs, list):
        raise ValueError("baseline and non-empty runs are required")
    planned = None
    if "enrollment" in packet:
        entries = packet["enrollment"]
        if not isinstance(entries, list) or not 1 <= len(entries) <= 10000:
            raise ValueError("enrollment must contain 1 to 10000 run identities")
        identities = [_run_identity(row) for row in entries]
        planned = set(identities)
        if len(planned) != len(identities):
            raise ValueError("duplicate enrollment identity")
        if baseline not in {arm for arm, _ in planned}:
            raise ValueError("enrollment must include the baseline")
    elif not runs:
        raise ValueError("non-empty runs or explicit enrollment are required")
    grouped, seen_calls = defaultdict(dict), set()
    for row in runs:
        arm, key = _run_identity(row)
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
    if baseline not in grouped and planned is None:
        raise ValueError("baseline has no runs")
    enrollment = {"status": "not_supplied", "complete": None}
    if planned is not None:
        observed = {(arm, key) for arm, rows in grouped.items() for key in rows}
        missing, unexpected = planned - observed, observed - planned
        planned_counts = Counter(arm for arm, _ in planned)
        missing_counts = Counter(arm for arm, _ in missing)
        unexpected_counts = Counter(arm for arm, _ in unexpected)
        by_arm = {}
        for arm in sorted({arm for arm, _ in planned | observed}):
            by_arm[arm] = {"planned_runs": planned_counts[arm],
                           "observed_runs": len(grouped[arm]),
                           "missing_runs": missing_counts[arm],
                           "unexpected_runs": unexpected_counts[arm]}
        enrollment = {"status": "compared", "complete": not missing and not unexpected,
                      "planned_runs": len(planned), "observed_runs": len(observed),
                      "missing_runs": len(missing), "unexpected_runs": len(unexpected),
                      "by_arm": by_arm,
                      "fingerprint": sha256(json.dumps(sorted(planned), separators=(",", ":")).encode()).hexdigest(),
                      "provenance": "caller_supplied; not proof of prior registration"}
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
                         "fully_matched": bool(keys) and len(keys) == len(grouped[baseline]) == len(grouped[arm])},
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
            "enrollment": enrollment,
            "recommendation": "insufficient_evidence", "automatic_promotion": False,
            "limitations": ["No universal winner or weekly-limit conversion is inferred.",
                            "Call completeness, model identity and grading are supplied by the host.",
                            "Timing is caller-reported, includes failed outcomes, and does not establish equivalent quality.",
                            "Different credit bases are reported separately, never averaged together.",
                            "Use preregistered held-out tasks and repeated trials before changing policy."],
            "raw_prompts_stored": False}
