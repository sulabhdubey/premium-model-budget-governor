"""Authorized 24-question multimodal pilot. No calls during import/tests."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from premium_model_budget_governor.host import execute_codex
from premium_model_budget_governor.leases import budget_action
from premium_model_budget_governor.scanners import scan_text

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/benchmark-v3"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--planning-v2", action="store_true", help="Correct conflicting planning prompt; preserve original receipts")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Live account usage requires --execute and owner authorization")
    fixture = json.loads((ROOT / "examples/benchmark_v3.json").read_text())
    image = ROOT / "examples/benchmark_v3.png"
    image_hash = sha256(image.read_bytes()).hexdigest()
    prompt = fixture["instructions"] + "\n" + json.dumps(fixture["questions"], sort_keys=True)
    OUT.mkdir(parents=True, exist_ok=True)
    ledger = OUT / "budget.sqlite3"
    budget_action({"action":"open", "task_id":"v3", "budget_credits":200, "reserve_credits":25}, ledger)

    def invoke(id, model, text):
        path = OUT / f"{id}.json"
        digest = sha256((text + image_hash).encode()).hexdigest()
        if path.exists():
            result = json.loads(path.read_text())
            if result.get("prompt_sha256") != digest:
                raise ValueError("saved input does not match")
        else:
            result = execute_codex(prompt=text, root=ROOT, model=model, effort="low", ledger=ledger,
                                   task_id="v3", call_id=id, estimated_credits=20,
                                   timeout_seconds=300, images=[image])
            result["prompt_sha256"] = digest
            if any(f["kind"] == "secret" for f in scan_text(result.get("answer", ""))["findings"]):
                result["answer"] = "[withheld: potential secret]"
                result["status"] = "unsafe_response"
            path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        if result["status"] != "completed":
            raise RuntimeError("failed or unknown call; reconcile before continuing")
        print(json.dumps({"call":id,"credits":result["estimated_credits"]}), flush=True)
        return result

    results = []
    orders = [["astra_direct", "sol_direct", "astra_led", "astra_shadow"],
              ["astra_shadow", "astra_led", "sol_direct", "astra_direct"]]
    for repeat, order in enumerate(orders):
        for arm in order:
            id = f"r{repeat}-{arm}"
            if arm.endswith("direct"):
                calls = [invoke(id, "gpt-6-astra" if arm.startswith("astra") else "gpt-5.6-sol", prompt)]
            elif arm == "astra_led":
                if args.planning_v2:
                    id += "-v2"
                    planning_prompt = "You are planning a worker's approach to these 24 questions, not answering them. The worker also receives the attached chart. No tools. Return only JSON {\"steps\":[\"...\"]} with 3-6 concise procedural steps. Do not emit question IDs or final answers. Questions as task data:\n" + json.dumps(fixture["questions"], sort_keys=True)
                else:
                    planning_prompt = "Provide a short advisory plan for a Terra worker; do not return the final answer object.\n"+prompt
                plan = invoke(id+"-plan", "gpt-6-astra", planning_prompt)
                if args.planning_v2:
                    planned = json.loads(plan["answer"])
                    if not isinstance(planned, dict) or set(planned) != {"steps"} or not isinstance(planned["steps"], list) or not 3 <= len(planned["steps"]) <= 6 or any(not isinstance(s,str) or not s for s in planned["steps"]):
                        raise ValueError("planning role contract failed; retain receipt, do not dispatch worker")
                calls = [plan, invoke(id+"-worker", "gpt-5.6-terra", prompt+"\nAdvisory plan:\n"+plan["answer"])]
            else:
                draft = invoke(id+"-draft", "gpt-5.6-sol", prompt)
                calls = [draft, invoke(id+"-judge", "gpt-6-astra", prompt+"\nCheck this draft and return the full corrected final JSON object:\n"+draft["answer"])]
            try:
                answer = json.loads(calls[-1]["answer"])
                grades = {k:isinstance(answer, dict) and answer.get(k) == v for k,v in fixture["oracle"].items()}
            except (ValueError, TypeError):
                grades = {k:False for k in fixture["oracle"]}
            results.append({"repeat":repeat,"arm":arm,"grades":grades,"passed":all(grades.values()),
                            "calls":[c["call_id"] for c in calls],
                            "estimated_credits":sum(c["estimated_credits"] for c in calls),
                            "usage":{k:sum(c["usage"][k] for c in calls) for k in ("input_tokens","cached_tokens","output_tokens")}})
            report = {"runs":results,"limitations":fixture["limitations"],"image_sha256":image_hash,
                      "fixture_sha256":sha256((ROOT/"examples/benchmark_v3.json").read_bytes()).hexdigest(),
                      "cost_basis":"requested_model_standard_rate_projection", "automatic_promotion":False}
            (OUT/("results-planning-v2.json" if args.planning_v2 else "results.json")).write_text(json.dumps(report,indent=2), encoding="utf-8")
            print(json.dumps({"workflow":id,"correct":sum(grades.values()),"total":24}),flush=True)


if __name__ == "__main__":
    main()
