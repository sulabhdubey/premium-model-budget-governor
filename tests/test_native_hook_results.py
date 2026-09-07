import json
from pathlib import Path


def test_native_observations_keep_fail_open_cases():
    report = json.loads((Path(__file__).parents[1]/"artifacts/native-hook-pilot/results.json").read_text())
    assert report["account_model_calls"] == 0
    cases = report["cases"]
    for case in ("missing","expired"):
        assert any(row["case"] == case and row["hook_statuses"] == ["blocked"] and row["fixture_requests"] == 0 for row in cases)
    for case in ("crash","timeout"):
        assert any(row["case"] == case and row["hook_statuses"] == ["failed"] and row["fixture_requests"] == 1 for row in cases)
    assert any(row["trust_statuses"] == ["modified"] and row["fixture_requests"] == 1 for row in cases)
    assert report["final_lab_hook_enabled"] == [False]
