from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
OUT = ROOT / "artifacts/benchmark-v3"


def test_published_pilot_can_be_regraded_without_models():
    fixture = json.loads((ROOT / "examples/benchmark_v3.json").read_text())
    report = json.loads((OUT / "results-planning-v2.json").read_text())
    assert len(fixture["questions"]) == len(fixture["oracle"]) == 24
    assert report["fixture_sha256"] == sha256((ROOT / "examples/benchmark_v3.json").read_bytes()).hexdigest()
    assert report["image_sha256"] == sha256((ROOT / "examples/benchmark_v3.png").read_bytes()).hexdigest()
    assert len(report["runs"]) == 8
    for row in report["runs"]:
        calls = [json.loads((OUT / f"{id}.json").read_text()) for id in row["calls"]]
        assert abs(sum(c["estimated_credits"] for c in calls) - row["estimated_credits"]) < 1e-9
        answer = json.loads(calls[-1]["answer"])
        assert row["grades"] == {k:answer.get(k) == v for k,v in fixture["oracle"].items()}
        if row["arm"] == "astra_led":
            plan = json.loads(calls[0]["answer"])
            assert set(plan) == {"steps"} and 3 <= len(plan["steps"]) <= 6


def test_invalid_role_evidence_is_retained_not_promoted():
    for repeat in (0, 1):
        original = json.loads((OUT / f"r{repeat}-astra_led-plan.json").read_text())
        assert "A1" in json.loads(original["answer"])
    calibration = json.loads((OUT / "calibration.json").read_text())
    assert not calibration["automatic_promotion"]
    assert all(g["independent_tasks"] == 1 and g["status"] == "insufficient_support" for g in calibration["groups"])
