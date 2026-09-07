"""Export only prompt-free native hook observations, not private lab diagnostics."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT/"build/native-hook-lab"
OUT = ROOT/"artifacts/native-hook-pilot"


def main():
    history = json.loads((LAB/"observations.json").read_text())
    allowed = {"case","fixture_requests","event_methods","trust_statuses","hook_enabled","hook_statuses"}
    if any(set(row)-allowed for row in history):
        raise ValueError("unexpected fields; review before publishing")
    report = {"codex_version":"0.153.4","account_model_calls":0,"paid_tokens":0,
              "backend":"loopback-only fixture returns HTTP 400; no generation",
              "cases":history,
              "trust_review":"Exact lab hooks reviewed and trusted via native Codex UI; no trust bypass",
              "final_lab_hook_enabled":history[-1].get("hook_enabled"),
              "initial_harness_issue":"One initialization transport failure before the original valid case; rerun only that offline case. Early diagnostics are private, not exported.",
              "limitations":"Tests cover this CLI/App Server build in an isolated home, not all Desktop versions. Requests are local fixture attempts, not successful model calls. Failure/timeout/modified/disabled hooks are not fail-closed enforcement."}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"results.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"cases":len(history),"output":str(OUT/"results.json")}))


if __name__ == "__main__":
    main()
