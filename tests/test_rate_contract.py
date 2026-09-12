from copy import deepcopy
import pytest

from premium_model_budget_governor.telemetry import normalize_usage
from premium_model_budget_governor.experiments import normalize_receipt


def contract():
    return {"schema_version": 1, "version": "example-v1", "source_id": "synthetic",
            "effective_date": "2026-09-08", "unit": "estimated_credits",
            "model": "gpt-6-astra", "service_tier": "default",
            "input_semantics": "total_includes_cache", "output_semantics": "total_includes_reasoning",
            "per_million": {"input": 100, "cached_input": 10, "cache_write": 200, "output": 500}}


def usage():
    return {"input_tokens": 100, "cached_tokens": 20, "cache_write_tokens": 30, "output_tokens": 10}


def test_custom_contract_prices_cache_categories_once_in_both_paths():
    rates = contract()
    telemetry = normalize_usage({"model": "gpt-6-astra", "usage": usage(), "rate_contract": rates})
    receipt = normalize_receipt({"call_id": "r1", "actual_model": "gpt-6-astra",
                                 "usage": usage(), "rate_contract": rates})
    assert telemetry["estimated_credits"] == pytest.approx(0.0162)
    assert receipt["credits"] == pytest.approx(0.0162)
    assert telemetry["rate_snapshot"] == receipt["rate_snapshot"] == rates
    assert telemetry["rate_version"] == "example-v1"


@pytest.mark.parametrize("field,value", [
    ("model", "other-model"), ("service_tier", "priority"),
])
def test_mismatched_contract_is_not_applied(field, value):
    rates = contract()
    rates[field] = value
    result = normalize_usage({"model": "gpt-6-astra", "usage": usage(), "rate_contract": rates})
    assert result["estimated_credits"] is None


@pytest.mark.parametrize("field,value", [
    ("schema_version", True), ("schema_version", 2), ("unit", "USD"),
    ("effective_date", "yesterday"), ("input_semantics", "ordinary_only"),
    ("output_semantics", "excludes_reasoning"),
])
def test_unsupported_contract_is_rejected(field, value):
    rates = contract()
    rates[field] = value
    with pytest.raises(ValueError):
        normalize_usage({"model": "gpt-6-astra", "usage": usage(), "rate_contract": rates})


@pytest.mark.parametrize("bad", [True, -1, float("nan"), float("inf"), "10"])
def test_invalid_rates_fail(bad):
    rates = contract()
    rates["per_million"]["input"] = bad
    with pytest.raises(ValueError):
        normalize_usage({"model": "gpt-6-astra", "usage": usage(), "rate_contract": rates})


def test_custom_contract_snapshot_not_mutated_by_caller():
    rates = contract()
    result = normalize_usage({"model": "gpt-6-astra", "usage": usage(), "rate_contract": rates})
    original = deepcopy(result["rate_snapshot"])
    rates["per_million"]["input"] = 999
    assert result["rate_snapshot"] == original


def test_unknown_tier_does_not_use_default_rates():
    result = normalize_usage({"model": "gpt-6-astra", "service_tier": "unconfigured",
                              "usage": {"input_tokens": 100, "output_tokens": 10}})
    assert result["estimated_credits"] is None
    assert result["cost_status"] == "unsupported_service_tier"


def test_contract_extra_fields_not_copied():
    rates = contract()
    rates["private_note"] = "SECRET"
    result = normalize_usage({"model": "gpt-6-astra", "usage": usage(), "rate_contract": rates})
    assert "SECRET" not in str(result)


def test_saved_rate_snapshot_can_be_replayed():
    packet = {"model": "gpt-6-astra", "usage": {"input_tokens": 100, "output_tokens": 10}}
    first = normalize_usage(packet)
    second = normalize_usage({**packet, "rate_contract": first["rate_snapshot"]})
    assert second["estimated_credits"] == first["estimated_credits"]
    assert second["rate_fingerprint"] == first["rate_fingerprint"]


def test_work_journal_preserves_custom_contract(tmp_path):
    from premium_model_budget_governor.work_journal import save_observation, read_observation
    path = tmp_path / "work.sqlite3"
    packet = {"work_units": ["w1"], "receipts": [{
        "receipt_id": "r1", "work_unit_id": "w1", "source_id": "s1",
        "counter_kind": "final", "scope": "exclusive", "model": "gpt-6-astra",
        "rate_contract": contract(), "usage": usage(),
    }]}
    result = save_observation(path, "obs-1", packet)
    assert result["report"]["estimated_credits"] == pytest.approx(0.0162)
    assert result["report"]["records"]["r1"]["usage"]["rate_snapshot"] == contract()
    assert read_observation(path, "obs-1") == result
