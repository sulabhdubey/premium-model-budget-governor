import pytest

from premium_model_budget_governor.telemetry import normalize_usage


@pytest.mark.parametrize("bad", [True, False, -1, 1.5, float("nan"), float("inf"), "12"])
def test_invalid_counter_raises_instead_of_becoming_zero(bad):
    with pytest.raises(ValueError):
        normalize_usage({"usage": {"input_tokens": bad, "output_tokens": 1}})


def test_missing_usage_is_unknown():
    result = normalize_usage({"model": "gpt-6-astra"})
    assert result["estimated_credits"] is None
    assert result["input_tokens"] is None


def test_cache_cannot_exceed_input():
    with pytest.raises(ValueError):
        normalize_usage({"usage": {"input_tokens": 1, "cached_tokens": 2, "output_tokens": 1}})
