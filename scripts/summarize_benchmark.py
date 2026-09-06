"""Regrade saved fixture answers; never invokes a model or drops initial grades."""
import json
from pathlib import Path
from statistics import mean

from premium_model_budget_governor.benchmark import grade_suite

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "benchmark-v2"


def main():
    path = OUT / "results.json"
    report = json.loads(path.read_text())
    initial = OUT / "initial-grades.json"
    if not initial.exists():
        initial.write_text(json.dumps(report, indent=2), encoding="utf-8")
    fixture = json.loads((ROOT / "examples/benchmark_v2.json").read_text())
    corrections = []
    for row in report["runs"]:
        response = json.loads((OUT / f'{row["calls"][-1]}.json').read_text())
        new_grade = grade_suite(json.loads(response["answer"]), fixture["oracle"])
        if new_grade != row["grade"]:
            corrections.append({"arm": row["arm"], "repeat": row["repeat"],
                                "reason": "Allow valid local assignment; original grader was too restrictive."})
        row["grade"] = new_grade
    report["grader_corrections"] = report.get("grader_corrections", []) + corrections
    report["summary"] = []
    for arm in sorted({r["arm"] for r in report["runs"]}):
        rows = [r for r in report["runs"] if r["arm"] == arm]
        report["summary"].append({"arm": arm, "runs": len(rows), "passed": sum(r["grade"]["passed"] for r in rows),
            "mean_estimated_credits": mean(r["estimated_credits"] for r in rows),
            "mean_input_tokens": mean(r["input_tokens"] for r in rows),
            "min_estimated_credits": min(r["estimated_credits"] for r in rows),
            "max_estimated_credits": max(r["estimated_credits"] for r in rows)})
    report["total_model_calls"] = sum(len(r["calls"]) for r in report["runs"])
    report["total_projected_credits"] = sum(r["estimated_credits"] for r in report["runs"])
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "corrections": report["grader_corrections"],
                      "total_model_calls": report["total_model_calls"],
                      "total_projected_credits": report["total_projected_credits"]}, indent=2))


if __name__ == "__main__":
    main()
