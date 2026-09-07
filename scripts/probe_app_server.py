"""Read-only host discovery; --execute additionally authorizes one image smoke turn."""
import argparse
import json
from pathlib import Path

from premium_model_budget_governor.app_server import probe_app_server, execute_app_server
from premium_model_budget_governor.leases import budget_action
from premium_model_budget_governor.scanners import scan_text
from premium_model_budget_governor.workflow import plan_workflow

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/app-server-pilot"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    probe = probe_app_server(ROOT)
    (OUT/"probe.json").write_text(json.dumps(probe,indent=2),encoding="utf-8")
    print(json.dumps(probe),flush=True)
    if not args.execute:
        return
    path = OUT/"image-smoke.json"
    if path.exists():
        raise ValueError("receipt already exists; inspect it rather than replaying")
    plan = plan_workflow({"mode":"astra_preferred","budget_credits":20,"reserve_credits":2,
        "explicit_approval":True,"require_context_calibration":True,"minimum_input_tokens_per_call":26000,
        "host_profiles":{"app_server":{"models":[m["model"] for m in probe["models"]],"capabilities":["image","text"]}},
        "candidates":[{"id":"image_smoke","quality_score":1,"complete_workflow":True,"stages":[
            {"role":"verify","model":"gpt-6-astra","host":"app_server","required_capabilities":["image"],
             "tokens":{"input":26000,"output":500},"tokens_upper":{"input":50000,"output":1000},"evidence_ready":True}]}]})
    (OUT/"plan.json").write_text(json.dumps(plan,indent=2),encoding="utf-8")
    if plan["decision"] != "planned":
        raise ValueError("workflow did not pass")
    ledger = OUT/"budget.sqlite3"
    budget_action({"action":"open","task_id":"app-server-pilot","budget_credits":20,"reserve_credits":2},ledger)
    result = execute_app_server({"root":str(ROOT), "task_id":"app-server-pilot", "call_id":"image-smoke",
        "model":"gpt-6-astra","effort":"low","estimated_credits":plan["selected"]["stages"][0]["estimated_credits"],
        "explicit_approval":True,"images":[str(ROOT/"examples/benchmark_v3.png")],
        "prompt":"Read the attached chart. Return only JSON {\"sol_cold_input\":number,\"units\":string}. No tools or file reads; use the attached image."},ledger)
    if any(f["kind"] == "secret" for f in scan_text(result.get("answer", ""))["findings"]):
        result["answer"] = "[withheld]"
    try:
        result["smoke_passed"] = result["status"] == "completed" and json.loads(result["answer"]) == {"sol_cold_input":18,"units":"Thousands of tokens"}
    except (KeyError, ValueError):
        result["smoke_passed"] = False
    path.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result),flush=True)


if __name__ == "__main__":
    main()
