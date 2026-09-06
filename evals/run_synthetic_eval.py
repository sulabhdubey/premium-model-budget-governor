"""Synthetic budget eval for premium-only, cheap-only, and governor-hybrid workflows."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from premium_model_budget_governor.cost import model_credits  # noqa: E402
from premium_model_budget_governor.policy import decide_model  # noqa: E402


TASKS = [
    {
        "name": "broad_repo_exploration",
        "sol": {"input": 160000, "output": 12000},
        "premium": {"input": 160000, "output": 12000},
        "hybrid": {"input": 28000, "output": 1200},
        "reasons": [],
        "quality": {"premium_only": 0.86, "cheap_only": 0.74, "hybrid": 0.82},
    },
    {
        "name": "critical_security_review",
        "sol": {"input": 90000, "output": 9000},
        "premium": {"input": 90000, "output": 9000},
        "hybrid": {"input": 26000, "output": 1400},
        "reasons": ["critical_security"],
        "quality": {"premium_only": 0.91, "cheap_only": 0.78, "hybrid": 0.89},
    },
    {
        "name": "test_log_iteration",
        "sol": {"input": 60000, "output": 5000},
        "premium": {"input": 60000, "output": 5000},
        "hybrid": {"input": 6000, "output": 600},
        "reasons": [],
        "quality": {"premium_only": 0.79, "cheap_only": 0.76, "hybrid": 0.77},
    },
]


def run_eval() -> dict[str, object]:
    rows = []
    totals = {"premium_only": 0.0, "cheap_only": 0.0, "hybrid": 0.0}
    qualities = {"premium_only": [], "cheap_only": [], "hybrid": []}
    for task in TASKS:
        premium_only = model_credits("gpt-6-astra", task["premium"])
        cheap_only = model_credits("gpt-5.6-sol", task["sol"])
        route = decide_model(
            {
                "requested_model": "gpt-6-astra",
                "remaining_limit_percent": 50,
                "reasons": task["reasons"],
                "task_kind": task["name"],
                "explicit_approval": True,
                "capsule_quality_score": 85,
                "sol_baseline_tokens": task["sol"],
                "premium_plan_tokens": task["hybrid"],
            }
        )
        hybrid = cheap_only + (model_credits("gpt-6-astra", task["hybrid"]) if route["decision"] == "allow_premium_capsule" else 0)
        totals["premium_only"] += premium_only
        totals["cheap_only"] += cheap_only
        totals["hybrid"] += hybrid
        for key, value in task["quality"].items():
            qualities[key].append(value)
        rows.append(
            {
                "task": task["name"],
                "premium_only_credits": round(premium_only, 4),
                "cheap_only_credits": round(cheap_only, 4),
                "hybrid_credits": round(hybrid, 4),
                "hybrid_route": route["decision"],
                "hybrid_vs_premium_savings_percent": round((1 - hybrid / premium_only) * 100, 2),
            }
        )
    summary = {
        "tasks": rows,
        "totals": {key: round(value, 4) for key, value in totals.items()},
        "avg_quality": {key: round(sum(value) / len(value), 3) for key, value in qualities.items()},
        "hybrid_vs_premium_savings_percent": round((1 - totals["hybrid"] / totals["premium_only"]) * 100, 2),
        "note": "Synthetic eval for regression and launch demonstration. Replace quality values with measured task outcomes before making public benchmark claims.",
    }
    return summary


if __name__ == "__main__":
    print(json.dumps(run_eval(), indent=2, sort_keys=True))
