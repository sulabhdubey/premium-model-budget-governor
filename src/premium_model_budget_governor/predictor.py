"""A simple benefit predictor calibrated from prompt-free outcomes."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean


HIGH_VALUE = {"critical_security", "frontier_architecture", "unsolved_after_sol", "final_release_review"}


def predict_benefit(task_shape: dict[str, object], *, ledger: Path | None = None) -> dict[str, object]:
    reasons = {str(item) for item in task_shape.get("reasons", [])} if isinstance(task_shape.get("reasons", []), list) else set()
    base = 0.35 + (0.25 if reasons.intersection(HIGH_VALUE) else 0)
    if task_shape.get("broad_context"):
        base -= 0.2
    if task_shape.get("has_ranked_evidence"):
        base += 0.15
    if task_shape.get("capsule_quality_score") and isinstance(task_shape["capsule_quality_score"], (int, float)):
        base += (float(task_shape["capsule_quality_score"]) - 70) / 200
    observed = _observed_rate(ledger) if ledger else None
    if observed is not None:
        base = (base + observed) / 2
    probability = max(0.0, min(1.0, round(base, 3)))
    if probability >= 0.72:
        recommendation = "use_one_astra_capsule"
    elif probability >= 0.5:
        recommendation = "shadow_mode_only"
    else:
        recommendation = "route_to_sol"
    return {"astra_benefit_probability": probability, "recommendation": recommendation, "observed_rate_used": observed}


def _observed_rate(ledger: Path | None) -> float | None:
    if ledger is None or not ledger.exists():
        return None
    values = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        outcome = str(row.get("outcome", "")).lower()
        if "benefit" in outcome or "saved" in outcome or "unblocked" in outcome:
            values.append(1.0)
        elif "waste" in outcome or "failed" in outcome or "not_needed" in outcome:
            values.append(0.0)
    return None if not values else round(mean(values), 3)
