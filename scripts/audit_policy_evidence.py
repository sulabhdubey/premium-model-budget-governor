"""Assess published pilot evidence for review eligibility, without activation."""
from collections import defaultdict
import json
from pathlib import Path
import tempfile

from premium_model_budget_governor.reviewed_policy import PolicyStore


def main():
    root = Path(__file__).resolve().parents[1]
    packet = json.loads((root / "artifacts/benchmark-v3/calibration-input.json").read_text())
    groups = defaultdict(list)
    for row in packet["pairs"]:
        groups[(row["family"], row["candidate"], row["baseline"])].append(row)
    results = []
    with tempfile.TemporaryDirectory(prefix="governor-policy-audit-") as temporary:
        store = PolicyStore(Path(temporary) / "audit.sqlite3")
        for (family, candidate, baseline), pairs in groups.items():
            scope = {"project":"published-v3-pilot", "family":family,
                     "host_profile":"historical-cli-pilot", "mode":"astra_preferred"}
            proposal = store.propose(scope, pairs)
            assert store.status(scope)["active_id"] is None
            results.append({"candidate":candidate,"baseline":baseline,
                            "eligible_for_review":proposal["eligible_for_review"],
                            "groups":proposal["report"]["groups"],"activated":False})
    report = {"source":"artifacts/benchmark-v3/calibration-input.json", "model_calls_started":0,
              "results":results, "conclusion":"Existing batched pilot cannot justify activating a learned routing preference."}
    output = root / "artifacts/reviewed-policy"
    output.mkdir(parents=True, exist_ok=True)
    (output / "existing-evidence-audit.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"comparisons":len(results),"eligible":sum(r["eligible_for_review"] for r in results),"activated":0}))


if __name__ == "__main__":
    main()
