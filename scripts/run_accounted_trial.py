"""External serial bootstrap and matched pair; dry-run unless explicitly enabled."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import time

from premium_model_budget_governor.app_server import execute_app_server
from premium_model_budget_governor.host_adapter import host_observation
from premium_model_budget_governor.leases import budget_action
from premium_model_budget_governor.task_measurement import measure_task
from premium_model_budget_governor.workflow import plan_workflow


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def run(output, *, execute=False):
    phases = [{"id": "prepare", "role": "prepare", "kind": "local"},
              {"id": "cal-inherit", "role": "prepare"},
              {"id": "cal-focused", "role": "prepare"},
              {"id": "match-focused", "role": "execute"},
              {"id": "match-inherit", "role": "execute"},
              {"id": "verify", "role": "verify", "kind": "local"},
              {"id": "report", "role": "report", "kind": "local"}]
    planning = {"mode": "astra_preferred", "budget_credits": 60, "reserve_credits": 12,
                "explicit_approval": True, "require_context_calibration": False,
                "candidates": [{"id": "bootstrap-and-pair", "quality_score": 0,
                                "complete_workflow": True, "stages": [
                                    {"role": "investigate", "model": "gpt-6-astra", "evidence_ready": True,
                                     "tokens": {"input": 44000, "output": 800}} for _ in range(4)]}]}
    gate = plan_workflow(planning)
    if not execute:
        return {"gate": gate, "model_calls": 0, "bootstrap_not_calibrated": True}
    if gate["selected"] is None:
        raise ValueError("bootstrap admission failed")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    ledger, root = output / "budget.sqlite3", output / "sample"
    outcomes = []
    calibration = 'Input tokens include cache: input=100, cached=80, output=10. Return JSON only with uncached_input and total_input_output.'
    task = 'Audit this savings claim using only these facts. Baseline costs 10 credits. Candidate execution costs 7, preparation 2, failed attempt 3. Claim: candidate saves credits. Return JSON only with total_candidate_credits, baseline_credits, savings_credits (baseline minus complete candidate), claim_supported. No tools or external sources.'
    oracle = {"total_candidate_credits": 12, "baseline_credits": 10, "savings_credits": -2, "claim_supported": False}
    save(output / "protocol.json", {"phases": phases, "gate": gate, "bootstrap_not_calibrated": True,
         "task": task, "oracle": oracle, "calibration_task": calibration,
         "scope": "Declared reproducible fixture pipeline; excludes prior parent design and engineering",
         "registered_at": datetime.now(timezone.utc).isoformat(), "retries_allowed": 0,
         "estimated_credits_per_call": 12, "quality": "fixed authored oracle, not independent review"})
    def invoke(stage):
        if stage["kind"] == "local":
            if stage["id"] == "prepare":
                root.mkdir()
                budget_action({"action": "open", "task_id": "accounted-pilot",
                               "budget_credits": 60, "reserve_credits": 12}, ledger)
            if stage["id"] == "verify":
                if len(outcomes) != 4 or not all(row["passed"] for row in outcomes):
                    raise ValueError("incomplete or failed trial")
                identities = [row["host_identity"] for row in outcomes]
                if (len({v["source_id"] for v in identities}) != 4
                        or len({v["config_fingerprint"] for v in identities}) != 1
                        or any(v["reasoning_requested"] != "low" for v in identities)
                        or outcomes[0]["prompt_sha256"] != outcomes[1]["prompt_sha256"]
                        or outcomes[2]["prompt_sha256"] != outcomes[3]["prompt_sha256"]):
                    raise ValueError("trial identity mismatch")
            return {"local_completed": True}
        arm = "focused_catalog" if "focused" in stage["id"] else "inherit"
        prompt = calibration if stage["id"].startswith("cal-") else task
        expected = {"uncached_input": 20, "total_input_output": 110} if stage["id"].startswith("cal-") else oracle
        receipt = execute_app_server({"root": str(root.resolve()), "prompt": prompt,
            "model": "gpt-6-astra", "effort": "low", "context_profile": arm,
            "task_id": "accounted-pilot", "call_id": stage["id"], "estimated_credits": 12,
            "explicit_approval": True, "capture_identity": True, "timeout_seconds": 180}, ledger)
        save(output / (stage["id"] + ".json"), receipt)
        try:
            passed = json.dumps(json.loads(receipt.get("answer", "")), sort_keys=True) == json.dumps(expected, sort_keys=True)
        except (TypeError, ValueError):
            passed = False
        outcome = {"id": stage["id"], "arm": arm, "status": receipt["status"], "passed": passed,
                   "prompt_sha256": sha256(prompt.encode()).hexdigest(),
                   "estimated_credits": receipt.get("estimated_credits"), "usage": receipt.get("usage"),
                   "host_identity": receipt.get("host_identity")}
        outcomes.append(outcome)
        print(json.dumps(outcome), flush=True)
        if not passed or receipt.get("estimated_credits", float("inf")) > 12:
            raise ValueError("quality or admission estimate exceeded; no retry")
        return host_observation(receipt, stage["id"])
    began = time.monotonic()
    result = measure_task(phases, output / "measurement", invoke)
    save(output / "outcomes.json", {"outcomes": outcomes, "measurement_status": result["status"],
                                  "elapsed_seconds": time.monotonic() - began,
                                  "budget": budget_action({"action": "status", "task_id": "accounted-pilot"}, ledger),
                                  "savings_proven": False})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.output, execute=args.execute), indent=2))
