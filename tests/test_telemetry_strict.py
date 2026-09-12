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


def test_cache_writes_are_not_silently_priced_as_ordinary_input():
    result = normalize_usage({"model": "gpt-6-astra", "usage": {
        "input_tokens": 100, "output_tokens": 10,
        "input_tokens_details": {"cached_tokens": 20, "cache_write_tokens": 30},
    }})
    assert result["ordinary_input_tokens"] == 50
    assert result["cache_write_tokens"] == 30
    assert result["estimated_credits"] is None
    assert result["cost_status"] == "unsupported_cache_write_rate"


def test_ordinary_usage_has_explicit_estimate_basis():
    result = normalize_usage({"model": "gpt-6-astra", "usage": {
        "input_tokens": 100, "output_tokens": 10, "cached_tokens": 20,
    }})
    assert result["estimated_credits"] == pytest.approx(0.033)
    assert result["cost_basis"] == "token_rate_estimate"
    assert result["rate_version"] == "legacy-configured-v1"
    assert result["provider_billed_cost"] is None


def test_unknown_model_keeps_observed_tokens_without_claiming_cost():
    result = normalize_usage({"model": "unconfigured-model", "usage": {
        "input_tokens": 100, "output_tokens": 10,
    }})
    assert result["input_tokens"] == 100
    assert result["estimated_credits"] is None
    assert result["cost_status"] == "unsupported_model_rate"


@pytest.mark.parametrize("extra", [
    {"prompt_tokens": 101}, {"completion_tokens": 11},
    {"cached_tokens": 20, "input_tokens_details": {"cached_tokens": 21}},
    {"cached_input_tokens": 20, "prompt_tokens_details": {"cached_tokens": 21}},
    {"total_tokens": 111}, {"reasoning_output_tokens": 11},
    {"output_tokens_details": {"reasoning_tokens": 11}},
    {"reasoning_output_tokens": 5, "completion_tokens_details": {"reasoning_tokens": 6}},
    {"input_tokens_details": []}, {"output_tokens_details": "invalid"},
])
def test_conflicting_or_invalid_reported_semantics_rejected(extra):
    with pytest.raises(ValueError):
        normalize_usage({"usage": {"input_tokens": 100, "output_tokens": 10, **extra}})


def test_chat_style_details_and_reasoning_are_subsets():
    result = normalize_usage({"model": "gpt-6-astra", "usage": {
        "prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110,
        "prompt_tokens_details": {"cached_tokens": 20},
        "completion_tokens_details": {"reasoning_tokens": 5}}})
    assert result["cached_tokens"] == 20
    assert result["reasoning_output_tokens"] == 5
    assert result["output_tokens"] == 10
    assert result["counter_assumptions"] == ["absent_cache_write_assumed_zero"]


def test_equal_aliases_are_accepted_and_explicit_zero_has_no_assumption():
    result = normalize_usage({"usage": {"input_tokens": 100, "prompt_tokens": 100,
        "output_tokens": 10, "cached_tokens": 0, "cached_input_tokens": 0,
        "cache_write_tokens": 0}})
    assert result["counter_assumptions"] == []
    assert result["reasoning_output_tokens"] is None
