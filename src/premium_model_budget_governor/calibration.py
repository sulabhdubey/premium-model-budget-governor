"""Descriptive calibration from independent matched tasks, never auto-promotion."""

from collections import defaultdict
from math import sqrt

from .workflow import number


def calibrate(packet: dict) -> dict:
    rows = packet.get("pairs")
    if not isinstance(rows, list):
        raise ValueError("pairs must be a list")
    groups, seen, splits = defaultdict(list), set(), {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each pair must be an object")
        for key in ("task_id", "family", "snapshot", "rubric", "candidate", "baseline"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"{key} must be a non-empty string")
        split = row.get("split")
        if split not in ("calibration", "holdout"):
            raise ValueError("split must be calibration or holdout")
        task = row["task_id"]
        if task in splits and splits[task] != split:
            raise ValueError("task leakage between calibration and holdout")
        splits[task] = split
        key = (task, row["candidate"], row["baseline"])
        if key in seen:
            raise ValueError("repeated tasks must be aggregated before calibration")
        seen.add(key)
        if row["candidate"] == row["baseline"]:
            raise ValueError("candidate and baseline must differ")
        if row.get("cost_basis") not in ("host_billed", "token_rate_estimate"):
            raise ValueError("comparable measured cost basis required")
        if row.get("matched") is not True or row.get("complete") is not True:
            raise ValueError("only complete matched workflows are eligible")
        for key in ("candidate_pass", "baseline_pass"):
            if not isinstance(row.get(key), bool):
                raise ValueError(f"{key} must be boolean")
        a = number(row.get("candidate_credits"), "candidate_credits")
        b = number(row.get("baseline_credits"), "baseline_credits")
        groups[(row["family"], row["candidate"], row["baseline"], split, row["cost_basis"])].append((row["candidate_pass"], row["baseline_pass"], a, b))
    results = []
    for (family, candidate, baseline, split, basis), values in sorted(groups.items()):
        n = len(values)
        wins = sum(a and (not b or x < y) for a, b, x, y in values)
        regressions = sum(b and not a for a, b, _, _ in values)
        p, z = wins / n, 1.96
        center = (p + z*z/(2*n)) / (1 + z*z/n)
        radius = z * sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1 + z*z/n)
        results.append({"family": family, "candidate": candidate, "baseline": baseline,
                        "split": split, "cost_basis": basis, "independent_tasks": n,
                        "quality_regressions": regressions, "observed_wins": wins,
                        "win_rate_interval_95": [max(0, center-radius), min(1, center+radius)],
                        "candidate_mean_credits": sum(v[2] for v in values)/n,
                        "baseline_mean_credits": sum(v[3] for v in values)/n,
                        "status": "insufficient_support" if n < 20 else "manual_review_required"})
    return {"groups": results, "automatic_promotion": False,
            "limitations": "Descriptive Wilson intervals assume independent representative tasks. Caller asserts matching and split integrity. No causal savings claim, capability guarantee, or weekly-limit prediction."}
