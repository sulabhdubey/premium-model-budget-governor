"""Run one explicitly authorized serial comparison stage, storing public fixture answers only."""
import argparse
import json
from pathlib import Path

from premium_model_budget_governor.host import execute_codex
from premium_model_budget_governor.leases import budget_action

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "completed-pilot"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["astra_direct", "sol_direct", "terra_worker", "astra_evidence"], required=True)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    ledger = OUT / "budget.sqlite3"
    budget_action({"action": "open", "task_id": "completed-pilot", "budget_credits": 150, "reserve_credits": 20}, ledger)
    fixture = json.loads((ROOT / "examples/contract_pilot.json").read_text())
    prompt = fixture["prompt"]
    model = "gpt-6-astra"
    if args.arm == "sol_direct":
        model = "gpt-5.6-sol"
    elif args.arm == "terra_worker":
        model = "gpt-5.6-terra"
        prompt += "\nAstra planner handoff captured in the previous stage: available=ceiling-contingency-settled-pending; compare request with available. Cached input is a subset; reasoning is already in total output. Current authoritative releaseAuthorized=false overrides older summaries. Validate type (reject bool), finiteness, and range before int()."
    elif args.arm == "astra_evidence":
        prompt = "You previously requested budget_contract, token_receipt, release_evidence and numeric_contract. All four requested sources are supplied in the questions below. Produce the final answer.\n" + prompt
    result = execute_codex(prompt=prompt, root=ROOT, model=model, effort="low", ledger=ledger,
                           task_id="completed-pilot", call_id=args.arm, estimated_credits=18)
    if result["status"] == "completed":
        try:
            answer = json.loads(result["answer"])
            result["passed"] = answer == fixture["oracle"]
        except (ValueError, TypeError):
            result["passed"] = False
    (OUT / f"{args.arm}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
