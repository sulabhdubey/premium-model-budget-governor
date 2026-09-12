import pytest

from premium_model_budget_governor.long_work import reconcile_work


def receipt(identity="r1", **updates):
    return {"receipt_id": identity, "work_unit_id": "w1", "source_id": "s1",
            "counter_kind": "final", "scope": "exclusive", "model": "gpt-6-astra",
            "usage": {"input_tokens": 100, "output_tokens": 10}, **updates}


def test_duplicate_receipts_count_once():
    result = reconcile_work({"receipts": [receipt(), receipt()]})
    assert result["totals"]["input_tokens"] == 100
    assert result["duplicate_count"] == 1
    assert result["savings_claim"] is False


def test_conflicting_identity_is_rejected():
    with pytest.raises(ValueError, match="conflicting"):
        reconcile_work({"receipts": [receipt(), receipt(model="gpt-5.6-sol")]})


@pytest.mark.parametrize("updates", [
    {"scope": "includes_children"}, {"counter_kind": "cumulative"},
    {"usage": {}},
])
def test_ambiguous_counters_do_not_become_free_or_additive(updates):
    result = reconcile_work({"receipts": [receipt(**updates)]})
    assert result["totals"] is None
    assert result["coverage"] == "incomplete"


def test_enrolled_missing_work_remains_visible():
    result = reconcile_work({"work_units": ["w1", "w2"], "receipts": [receipt()]})
    assert result["missing_work_units"] == ["w2"]
    assert result["totals"] is None
    assert result["observed_subtotal"]["input_tokens"] == 100


def test_untrusted_content_is_not_copied():
    result = reconcile_work({"receipts": [receipt(prompt="private text", path="private path")]})
    assert "private" not in str(result)


def test_empty_input_is_missing_not_zero_cost():
    result = reconcile_work({"receipts": []})
    assert result["totals"] is None
    assert result["coverage"] == "incomplete"
    assert result["observed_subtotal"] is None


def test_unenrolled_work_is_not_silently_added_to_complete_trial():
    result = reconcile_work({"work_units": [], "receipts": [receipt()]})
    assert result["unexpected_work_units"] == ["w1"]
    assert result["totals"] is None


def test_distinct_receipts_same_source_are_not_assumed_independent():
    result = reconcile_work({"receipts": [receipt(), receipt("r2")]})
    assert result["totals"] is None
    assert "overlapping_source" in result["issues"]


def test_unknown_cost_preserves_token_totals():
    result = reconcile_work({"receipts": [receipt(model="unknown")]})
    assert result["totals"]["input_tokens"] == 100
    assert result["estimated_credits"] is None


def test_private_path_is_not_an_opaque_identifier():
    with pytest.raises(ValueError, match="opaque"):
        reconcile_work({"receipts": [receipt(source_id="C:/private/file")]})


def test_report_preserves_assumptions_without_inventing_reasoning():
    usage = reconcile_work({"receipts": [receipt()]})["records"]["r1"]["usage"]
    assert usage["counter_assumptions"] == [
        "absent_cached_input_assumed_zero", "absent_cache_write_assumed_zero"]
    assert usage["reasoning_output_tokens"] is None
