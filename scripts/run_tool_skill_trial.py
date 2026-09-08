"""Read-only capability trial using only an explicitly supplied existing budget."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import time

from premium_model_budget_governor.app_server import execute_app_server
from premium_model_budget_governor.experiments import compare_runs
from premium_model_budget_governor.leases import budget_action

ROOT = Path(__file__).resolve().parents[1]


def hashes(root):
    return {str(p.relative_to(root)).replace("\\", "/"): sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def assess(receipt, oracle, before, after):
    try:
        answer = json.loads(receipt.get("answer", ""))
    except (ValueError, TypeError):
        answer = None
    categories = receipt.get("activity", {}).get("completed_items", {})
    checks = {"completed": receipt.get("status") == "completed",
              "answer_matches": json.dumps(answer, sort_keys=True) == json.dumps(oracle, sort_keys=True),
              "local_tool_event_observed": categories.get("commandExecution", 0) > 0,
              "fixture_unchanged": before == after}
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--budget-task", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads((ROOT / "examples/tool-skill-trial/manifest.json").read_text(encoding="utf-8"))
    state = budget_action({"action": "status", "task_id": args.budget_task}, args.ledger)
    if not args.execute:
        print(json.dumps({"planned_calls": 4, "available_credits": state["available_credits"],
                          "estimate_per_call": fixture["estimated_credits_per_call"], "model_calls": 0}))
        return
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "manifest.json").write_text(json.dumps(fixture, indent=2), encoding="utf-8")
    manifest_hash = sha256((output / "manifest.json").read_bytes()).hexdigest()
    runs, outcomes, enrolled = [], [], []
    for task in fixture["tasks"]:
        for profile in task["order"]:
            enrolled.append({"task_id": task["id"], "arm": profile,
                             "call_id": fixture["id"] + "-" + task["id"] + "-" + profile})
    stop = None
    for entry in enrolled:
        state = budget_action({"action": "status", "task_id": args.budget_task}, args.ledger)
        if state["reserved_credits"] or state["available_credits"] < fixture["estimated_credits_per_call"]:
            stop = "budget_or_pending_lease"
            break
        task = next(t for t in fixture["tasks"] if t["id"] == entry["task_id"])
        root = output / entry["call_id"]
        root.mkdir()
        for name, content in task["files"].items():
            path = root / name
            if not path.resolve().is_relative_to(root):
                raise ValueError("fixture file escaped project")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        before = hashes(root)
        start = time.monotonic()
        try:
            receipt = execute_app_server({"root": str(root), "prompt": task["prompt"],
                "model": fixture["model"], "effort": fixture["effort"], "context_profile": entry["arm"],
                "task_id": args.budget_task, "call_id": entry["call_id"], "explicit_approval": True,
                "estimated_credits": fixture["estimated_credits_per_call"], "timeout_seconds": 180}, args.ledger)
        except (ValueError, OSError, TimeoutError):
            receipt = {"status": "dispatch_error", "call_id": entry["call_id"]}
        elapsed = time.monotonic() - start
        checks = assess(receipt, task["oracle"], before, hashes(root))
        (output / (entry["call_id"] + ".json")).write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        outcomes.append({**entry, "checks": checks, "activity": receipt.get("activity"),
                         "input_sha256": before, "status": receipt["status"]})
        if receipt["status"] == "completed":
            runs.append({**entry, "snapshot": manifest_hash, "rubric": "exact-json-tool-event-unchanged-v1",
                         "repeat": 0, "passed": all(checks.values()), "complete": True,
                         "receipt_source": "host", "expected_calls": 1, "total_elapsed_seconds": elapsed,
                         "calls": [{"call_id": entry["call_id"], "actual_model": receipt["host_configured_model"],
                                    "usage": receipt["usage"]}]})
        if not all(checks.values()):
            stop = "quality_capability_or_execution_gate_failed"
        elif receipt["estimated_credits"] > fixture["estimated_credits_per_call"]:
            stop = "cost_estimate_exceeded"
        state = budget_action({"action": "status", "task_id": args.budget_task}, args.ledger)
        report = {"manifest_sha256": manifest_hash, "outcomes": outcomes, "runs": runs,
                  "enrolled": enrolled, "not_executed": enrolled[len(outcomes):], "stop_reason": stop,
                  "budget": state, "limitations": fixture["limitations"], "automatic_promotion": False}
        (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({"call": entry["call_id"], "checks": checks, "spent": state["spent_credits"], "stop": stop}), flush=True)
        if stop:
            break
    # Preserve enrollment and the stop even when admission prevents the next call.
    report = {"manifest_sha256": manifest_hash, "outcomes": outcomes, "runs": runs,
              "enrolled": enrolled, "not_executed": enrolled[len(outcomes):], "stop_reason": stop,
              "budget": state, "limitations": fixture["limitations"], "automatic_promotion": False}
    (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    comparison = compare_runs({"baseline": "inherit", "runs": runs}) if any(r["arm"] == "inherit" for r in runs) else None
    (output / "comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
