import pytest

from premium_model_budget_governor.calibration import calibrate


def pair(**updates):
    return dict(task_id="a", family="bugs", snapshot="abc", rubric="v1", candidate="astra", baseline="sol", split="calibration", cost_basis="token_rate_estimate", matched=True, complete=True, candidate_pass=True, baseline_pass=True, candidate_credits=2, baseline_credits=3, **updates)


def test_small_sample_is_not_promoted():
    result = calibrate({"pairs": [pair()]})
    assert not result["automatic_promotion"]
    assert result["groups"][0]["status"] == "insufficient_support"
    assert result["groups"][0]["win_rate_interval_95"][0] < .5


def test_split_leakage_and_repeated_task_rejected():
    row = pair()
    with pytest.raises(ValueError, match="leakage"):
        calibrate({"pairs": [row, {**row, "split": "holdout"}]})
    with pytest.raises(ValueError, match="repeated"):
        calibrate({"pairs": [row, row]})


def test_regression_is_not_a_win_and_cost_basis_separated():
    row = pair()
    result = calibrate({"pairs": [{**row, "candidate_pass": False}, {**row, "task_id": "b", "cost_basis": "host_billed"}]})
    assert len(result["groups"]) == 2
    assert sum(g["quality_regressions"] for g in result["groups"]) == 1


@pytest.mark.parametrize("changes", [{"complete": False}, {"candidate_credits": -1}, {"candidate_pass": 1}, {"cost_basis": "guess"}])
def test_invalid_data_rejected(changes):
    with pytest.raises(ValueError):
        calibrate({"pairs": [{**pair(), **changes}]})
