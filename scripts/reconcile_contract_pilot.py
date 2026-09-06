"""Reproduce the September 7 pilot from explicit local session counters.

Never exports raw logs. Answer text below is captured from experiment tool results,
not generated from the oracle. Model invocation is intentionally not automated here.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from premium_model_budget_governor.cost import RATES
from premium_model_budget_governor.experiments import compare_runs, import_codex_receipt
from premium_model_budget_governor.leases import budget_action

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "contract-pilot"
SESSIONS = {
    "astra_direct": "01a078d2-e32f-74c1-a260-e6d358b2fdbf",
    "sol_direct": "01a078d2-e3ca-7972-96ba-9454b3a2a2a0",
    "astra_lead": "01a078d2-e4b7-7393-8be6-956f9c4d18fa",
    "astra_demand_start": "01a078d2-e5f4-7c71-b7fe-c174fe218de1",
}
CAPTURED_ANSWERS = {
    "astra_direct": '{"reservation_allowed":false,"available_before_request":1.5,"token_credits":0.37,"release_authorized":false,"validate_before_int":true}',
    "sol_direct": '{"reservation_allowed":false,"available_before_request":1.5,"token_credits":0.37,"release_authorized":false,"validate_before_int":true}',
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-dir", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads((ROOT / "examples/contract_pilot.json").read_text())
    receipts = {}
    for label, id in SESSIONS.items():
        paths = list(args.session_dir.glob(f"*{id}.jsonl"))
        if len(paths) != 1:
            raise ValueError(f"exactly one explicit pilot session required for {label}")
        receipts[label] = import_codex_receipt(paths[0], label)
    ledger = OUT / "reservations.sqlite3"
    base = {"task_id": "contract-pilot-v1"}
    for label, receipt in receipts.items():
        budget_action({**base, "action": "settle", "lease_id": label,
                       "actual_model": receipt["actual_model"], "actual_credits": receipt["credits"],
                       "cost_basis": "token_rate_estimate"}, ledger)
    for label in ("terra_execute", "astra_demand_finish"):
        status = budget_action({**base, "action": "cancel", "lease_id": label,
                                "confirmed_not_executed": True}, ledger)
    snapshot = sha256(fixture["prompt"].encode()).hexdigest()
    runs = []
    for arm, text in CAPTURED_ANSWERS.items():
        answer = json.loads(text)
        passed = all(type(answer.get(k)) is type(v) and
                     (abs(answer[k] - v) < 1e-9 if isinstance(v, float) else answer[k] == v)
                     for k, v in fixture["oracle"].items())
        runs.append({"task_id": fixture["id"], "snapshot": snapshot, "rubric": "exact-contract-v1",
                     "repeat": 0, "arm": arm, "passed": passed, "complete": True,
                     "receipt_source": "host", "expected_calls": 1, "calls": [receipts[arm]]})
    packet = {"baseline": "sol_direct", "runs": runs}
    result = {"date": "2026-09-07", "scope": fixture["scope"], "rate_snapshot": RATES,
              "receipts": receipts, "captured_answers": CAPTURED_ANSWERS,
              "comparison": compare_runs(packet), "budget": status,
              "aborted_arms": {"astra_led_terra": "planner completed, worker canceled",
                               "astra_evidence_demand": "requested all four evidence IDs, final call canceled"},
              "stop_reason": "observed token-rate projection exceeded original pilot budget",
              "weekly_meter": {"before_used_percent": 90, "after_used_percent": 90,
                               "attribution": "shared rounded account meter; cannot isolate pilot cost"},
              "limitations": ["One tiny fixed-order trial; no universal quality or savings conclusion.",
                              "Cache states differed. Token-derived credits are not a billed receipt.",
                              "Four calls were dispatched before the first usage receipt; use serial calibration next time.",
                              "Parent conversation usage is outside this isolated pilot report."]}
    (OUT / "comparison-input.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
    (OUT / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
