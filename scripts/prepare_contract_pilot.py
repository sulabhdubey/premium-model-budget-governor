"""Historical v1 budget reproduction, not a recommended live dispatch policy.

The v1 pilot underestimated host context. Use serial calibration for new pilots.
This script only reproduces its old estimate; it does not invoke any model.
"""
import json
from pathlib import Path

from premium_model_budget_governor.leases import budget_action
from premium_model_budget_governor.workflow import plan_workflow

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "contract-pilot"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    models = [("astra_direct", "gpt-6-astra"), ("sol_direct", "gpt-5.6-sol"),
              ("astra_lead", "gpt-6-astra"), ("terra_execute", "gpt-5.6-terra"),
              ("astra_demand_start", "gpt-6-astra"), ("astra_demand_finish", "gpt-6-astra")]
    stages = [{"role": "investigate", "model": model, "evidence_ready": True,
               "tokens": {"input": 3000, "output": 1000}} for _, model in models]
    packet = {"mode": "astra_preferred", "budget_credits": 15, "reserve_credits": 5,
              "remaining_limit_percent": 10, "explicit_approval": True,
              "candidates": [{"id": "bounded-four-arm-pilot", "quality_score": 0,
                               "complete_workflow": True, "stages": stages}]}
    plan = plan_workflow(packet)
    if plan["decision"] != "planned":
        raise ValueError("pilot exceeds estimate budget")
    ledger = OUT / "reservations.sqlite3"
    base = {"task_id": "contract-pilot-v1"}
    budget_action({**base, "action": "open", "budget_credits": 15, "reserve_credits": 5,
                   "max_pending_leases": 6}, ledger)
    for (id, model), stage in zip(models, plan["selected"]["stages"]):
        status = budget_action({**base, "action": "reserve", "lease_id": id, "model": model,
                               "estimated_credits": stage["estimated_credits"]}, ledger)
    result = {"plan": plan, "reservations": status,
              "scope": "Six isolated pilot calls only; excludes parent implementation conversation. Estimates do not cap host tokens or weekly usage."}
    (OUT / "preflight.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
