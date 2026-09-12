import pytest

from premium_model_budget_governor.experiments import normalize_receipt


def call(usage, **extra):
    return {"call_id": "r1", "actual_model": "gpt-6-astra", "usage": usage, **extra}


@pytest.mark.parametrize("usage", [
    {"input_tokens": 100, "output_tokens": 10, "cache_write_tokens": 20},
    {"input_tokens": 100, "output_tokens": 10,
     "input_tokens_details": {"cache_write_tokens": 20}},
])
def test_receipt_does_not_invent_cache_write_rate(usage):
    result = normalize_receipt(call(usage))
    assert result["credits"] is None
    assert result["usage"]["cache_write_tokens"] == 20
    assert result["cost_status"] == "unsupported_cache_write_rate"


@pytest.mark.parametrize("writes", [True, -1, 1.2, "20", 101])
def test_invalid_cache_write_counters_fail(writes):
    with pytest.raises(ValueError):
        normalize_receipt(call({"input_tokens": 100, "output_tokens": 10, "cache_write_tokens": writes}))


def test_cached_subsets_cannot_overlap_total():
    with pytest.raises(ValueError):
        normalize_receipt(call({"input_tokens": 100, "output_tokens": 10,
                                "cached_tokens": 80, "cache_write_tokens": 30}))


def test_billed_cost_does_not_need_invented_rate():
    result = normalize_receipt(call({"input_tokens": 100, "output_tokens": 10,
                                     "cache_write_tokens": 20}, billed_credits=3))
    assert result["credits"] == 3
    assert result["cost_basis"] == "host_billed"
    assert result["rate_version"] is None


def test_rate_assumption_identified_on_estimated_receipt():
    result = normalize_receipt(call({"input_tokens": 100, "output_tokens": 10}))
    assert result["rate_version"] == "legacy-configured-v1"


@pytest.mark.parametrize("extra", [
    {"cached_tokens": 1, "input_tokens_details": {"cached_tokens": 2}},
    {"cache_write_tokens": 1, "input_tokens_details": {"cache_write_tokens": 2}},
    {"prompt_tokens": 101},
    {"total_tokens": 111},
    {"reasoning_output_tokens": 11},
])
def test_receipt_rejects_contradictory_counter_evidence(extra):
    with pytest.raises(ValueError):
        normalize_receipt(call({"input_tokens": 100, "output_tokens": 10, **extra}))


def test_receipt_reports_absent_cache_assumptions():
    result = normalize_receipt(call({"input_tokens": 100, "output_tokens": 10}))
    assert result["counter_assumptions"] == [
        "absent_cached_input_assumed_zero", "absent_cache_write_assumed_zero"]


def test_rollout_import_preserves_cache_write_uncertainty(tmp_path):
    import json
    from premium_model_budget_governor.experiments import import_codex_receipt
    path = tmp_path / "rollout.jsonl"
    events = [
        {"type": "turn_context", "payload": {"model": "gpt-6-astra"}},
        {"type": "event_msg", "payload": {"type": "token_count", "info": {
            "total_token_usage": {"input_tokens": 100, "output_tokens": 10,
                                  "cache_write_tokens": 30}}}},
    ]
    path.write_text("\n".join(map(json.dumps, events)), encoding="utf-8")
    result = import_codex_receipt(path, "r1")
    assert result["credits"] is None
    assert result["usage"]["cache_write_tokens"] == 30


@pytest.mark.parametrize("cache", [{}, {"cached_input_tokens": 0, "cache_write_tokens": 0}])
def test_rollout_cache_presence_survives_receipt_roundtrip(tmp_path, cache):
    import json
    from premium_model_budget_governor.experiments import import_codex_receipt
    path = tmp_path / "presence.jsonl"
    events = [{"type": "turn_context", "payload": {"model": "gpt-6-astra"}},
              {"type": "event_msg", "payload": {"type": "token_count", "info": {
                  "total_token_usage": {"input_tokens": 10, "output_tokens": 2, **cache}}}}]
    path.write_text("\n".join(map(json.dumps, events)), encoding="utf-8")
    imported = import_codex_receipt(path, "r1")
    expected = [] if cache else ["absent_cached_input_assumed_zero", "absent_cache_write_assumed_zero"]
    assert imported["counter_assumptions"] == expected
    assert normalize_receipt(imported)["counter_assumptions"] == expected


def test_rollout_import_rejects_inconsistent_total(tmp_path):
    import json
    from premium_model_budget_governor.experiments import import_codex_receipt
    path = tmp_path / "invalid.jsonl"
    events = [{"type": "turn_context", "payload": {"model": "gpt-6-astra"}},
              {"type": "event_msg", "payload": {"type": "token_count", "info": {
                  "total_token_usage": {"input_tokens": 10, "output_tokens": 2, "total_tokens": 99}}}}]
    path.write_text("\n".join(map(json.dumps, events)), encoding="utf-8")
    with pytest.raises(ValueError, match="total"):
        import_codex_receipt(path, "r1")


def test_missing_cache_snapshot_does_not_hide_later_counter_reset(tmp_path):
    import json
    from premium_model_budget_governor.experiments import import_codex_receipt
    path = tmp_path / "reset.jsonl"
    events = [{"type": "turn_context", "payload": {"model": "gpt-6-astra"}}]
    for incoming, cache in [(10, {"cached_input_tokens": 5}), (20, {}),
                            (30, {"cached_input_tokens": 4})]:
        events.append({"type": "event_msg", "payload": {"type": "token_count", "info": {
            "total_token_usage": {"input_tokens": incoming, "output_tokens": 2, **cache}}}})
    path.write_text("\n".join(map(json.dumps, events)), encoding="utf-8")
    with pytest.raises(ValueError, match="decreased"):
        import_codex_receipt(path, "r1")
