"""Regrade stored fixture outputs and summarize without spending model usage."""
import json
from pathlib import Path
from premium_model_budget_governor.calibration import calibrate
from premium_model_budget_governor.dashboard import export_dashboard

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/benchmark-v3"


def main():
    corrected = OUT / "results-planning-v2.json"
    report = json.loads((corrected if corrected.exists() else OUT / "results.json").read_text())
    fixture = json.loads((ROOT / "examples/benchmark_v3.json").read_text())
    groups = {}
    for row in report["runs"]:
        final = json.loads((OUT / (row["calls"][-1] + ".json")).read_text())
        answer = json.loads(final["answer"])
        assert row["grades"] == {k:answer.get(k) == v for k,v in fixture["oracle"].items()}
        groups.setdefault(row["arm"], []).append(row)
    summary = {arm:{"mean_credits":sum(r["estimated_credits"] for r in rows)/len(rows),
                   "range_credits":[min(r["estimated_credits"] for r in rows),max(r["estimated_credits"] for r in rows)],
                   "passed_runs":sum(r["passed"] for r in rows),"runs":len(rows)} for arm,rows in groups.items()}
    pairs = [{"task_id":"v3-batch", "family":"mixed_contract_batch", "snapshot":report["fixture_sha256"],
              "rubric":"exact-v1", "candidate":arm,"baseline":"sol_direct", "split":"calibration",
              "cost_basis":"token_rate_estimate", "matched":True, "complete":True,
              "candidate_pass":all(r["passed"] for r in groups[arm]),"baseline_pass":all(r["passed"] for r in groups["sol_direct"]),
              "candidate_credits":v["mean_credits"],"baseline_credits":summary["sol_direct"]["mean_credits"]}
             for arm,v in summary.items() if arm != "sol_direct" and (arm != "astra_led" or corrected.exists())]
    (OUT / "calibration-input.json").write_text(json.dumps({"pairs":pairs},indent=2),encoding="utf-8")
    (OUT / "calibration.json").write_text(json.dumps(calibrate({"pairs":pairs}),indent=2),encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    export_dashboard(OUT / "budget.sqlite3", OUT / "dashboard.html")
    print(json.dumps(summary,indent=2))


if __name__ == "__main__":
    main()
