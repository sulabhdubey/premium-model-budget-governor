from datetime import datetime, timezone

import pytest

from premium_model_budget_governor.host_estimation import estimate_host
from premium_model_budget_governor.host_estimation import plan_calibrated


NOW = datetime(2026, 9, 12, tzinfo=timezone.utc)
PROFILE = dict(host="desktop", model="astra", reasoning="low", context="inherited",
               config_fingerprint="abc", task_family="review", scope="complete_task")


def receipt(identity="a", **updates):
    return dict(id=identity, profile=PROFILE, recorded_at=NOW.isoformat(), complete=True,
                input_tokens=100, cached_tokens=80, output_tokens=10, **updates)


def test_missing_and_sparse_are_not_calibrated():
    assert estimate_host(dict(profile=PROFILE, receipts=[]), now=NOW)["status"] == "missing"
    result = estimate_host(dict(profile=PROFILE, receipts=[receipt()]), now=NOW)
    assert result["status"] == "insufficient_support"
    assert result["admission_tokens"]["cached_tokens"] == 0
    assert result["observed_ranges"]["uncached_tokens"] == [20, 20]


def test_only_recent_comparable_complete_receipts():
    rows = [receipt(str(i)) for i in range(5)]
    rows += [{**receipt("old"), "recorded_at": "2020-01-01T00:00:00+00:00"},
             {**receipt("other"), "profile": {**PROFILE, "context": "focused"}},
             {**receipt("partial"), "complete": False}]
    result = estimate_host(dict(profile=PROFILE, receipts=rows), now=NOW)
    assert result["status"] == "empirical"
    assert result["samples"] == 5
    assert result["excluded"] == 3
    assert result["admission_tokens"]["input_tokens"] == 125


@pytest.mark.parametrize("change", [{"cached_tokens": 101}, {"input_tokens": True},
                                    {"output_tokens": -1}, {"recorded_at": "tomorrow"}])
def test_invalid_receipts_rejected(change):
    with pytest.raises(ValueError):
        estimate_host(dict(profile=PROFILE, receipts=[{**receipt(), **change}]), now=NOW)


def test_duplicates_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        estimate_host(dict(profile=PROFILE, receipts=[receipt(), receipt()]), now=NOW)


def test_stale_and_future_do_not_support_estimate():
    row = {**receipt(), "recorded_at": "2020-01-01T00:00:00+00:00"}
    assert estimate_host(dict(profile=PROFILE, receipts=[row]), now=NOW)["status"] == "stale"
    row["recorded_at"] = "2030-01-01T00:00:00+00:00"
    assert estimate_host(dict(profile=PROFILE, receipts=[row]), now=NOW)["status"] == "missing"


def test_calibrated_plan_enforces_support_and_preserves_input():
    profile = {**PROFILE, "model": "gpt-6-astra", "scope": "per_call"}
    packet = {"calibration": {"profile": profile, "receipts": []},
              "workflow": {"budget_credits": 60, "explicit_approval": True,
                           "candidates": [{"id": "direct", "quality_score": 0,
                                           "complete_workflow": True, "stages": [{
                                               "role": "implement", "model": "gpt-6-astra",
                                               "calibration_profile": profile, "evidence_ready": True,
                                               "tokens": {"input": 1, "output": 1}}]}]}}
    assert plan_calibrated(packet, now=NOW)["selected"] is None
    packet["calibration"]["receipts"] = [{**receipt(str(i)), "profile": profile} for i in range(5)]
    result = plan_calibrated(packet, now=NOW)
    assert result["selected"]["stages"][0]["effective_input_tokens"] == 125
    assert packet["workflow"]["candidates"][0]["stages"][0]["tokens"]["input"] == 1
    packet["workflow"]["candidates"][0]["stages"][0]["model"] = "gpt-5.6-sol"
    with pytest.raises(ValueError, match="match"):
        plan_calibrated(packet, now=NOW)
