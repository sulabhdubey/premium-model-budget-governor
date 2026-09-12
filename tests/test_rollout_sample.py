import json
import pytest

from premium_model_budget_governor.rollout_sample import sample_rollout


def token(n=100):
    return json.dumps({"type": "event_msg", "payload": {"type": "token_count", "info": {
        "total_token_usage": {"input_tokens": n, "cached_input_tokens": 20,
                              "output_tokens": 10, "reasoning_output_tokens": 5,
                              "total_tokens": n + 10}}}}).encode() + b"\n"


def test_large_file_sample_is_unknown_model_cumulative(tmp_path):
    path = tmp_path / "large.jsonl"
    path.write_bytes(b"x" * 10000 + b"\n" + token())
    result = sample_rollout(path, max_bytes=1024)
    assert result["actual_model"] == "unknown"
    assert result["usage"]["input_tokens"] == 100
    assert result["sample_start"] > 0
    assert result["source_bytes"] == 1024
    assert result["coverage"] == "partial_sample"
    assert str(path) not in str(result)


def test_partial_last_line_is_not_parsed(tmp_path):
    path = tmp_path / "active.jsonl"
    path.write_bytes(token() + b'{"PRIVATE":')
    result = sample_rollout(path)
    assert result["usage"]["input_tokens"] == 100
    assert result["trailing_bytes_ignored"] > 0
    assert "PRIVATE" not in str(result)


def test_mixed_model_context_does_not_attribute_cumulative_tokens(tmp_path):
    path = tmp_path / "mixed.jsonl"
    path.write_bytes(b'{"type":"turn_context","payload":{"model":"gpt-6-astra"}}\n' + token())
    assert sample_rollout(path)["actual_model"] == "unknown"


def test_counter_reset_preserves_evidence_without_claiming_continuity(tmp_path):
    path = tmp_path / "reset.jsonl"
    path.write_bytes(token(200) + token(100))
    result = sample_rollout(path)
    assert result["counter_resets"] == 1
    assert result["counter_scope"] == "latest_observed_segment"
    assert result["usage"]["input_tokens"] == 100
    assert result["actual_model"] == "unknown"


def test_no_complete_counter_is_missing(tmp_path):
    path = tmp_path / "missing.jsonl"
    path.write_bytes(b'{"type":"other"}\n')
    with pytest.raises(ValueError, match="no complete"):
        sample_rollout(path)


@pytest.mark.parametrize("bad", [True, 0, -1, 100_000_000])
def test_invalid_bound_fails_without_read(tmp_path, bad):
    with pytest.raises(ValueError, match="size"):
        sample_rollout(tmp_path / "absent", max_bytes=bad)


def test_sample_and_journal_cli_roundtrip(tmp_path, capsys):
    from premium_model_budget_governor.cli import main
    path, journal = tmp_path / "sample.jsonl", tmp_path / "observations.sqlite3"
    path.write_bytes(token())
    assert main(["observe-rollout", "--sample", "--input", str(path),
                 "--journal", str(journal), "--observation-id", "o1",
                 "--work-unit", "w1", "--source-id", "s1"]) == 0
    result = json.loads(capsys.readouterr().out)["result"]["report"]
    record = result["records"]["o1"]
    assert record["usage"]["estimated_credits"] is None
    assert record["provenance"]["sample_end"] == path.stat().st_size
    assert result["totals"] is None


def test_sample_cannot_be_relabelled_final(tmp_path):
    from premium_model_budget_governor.long_work import reconcile_work
    path = tmp_path / "sample.jsonl"
    path.write_bytes(token())
    sample = sample_rollout(path)
    with pytest.raises(ValueError, match="partial samples"):
        reconcile_work({"receipts": [{"receipt_id": "r1", "source_id": "s1",
            "work_unit_id": "w1", "model": "gpt-6-astra", "scope": "exclusive",
            "counter_kind": "final", "usage": sample["usage"], "provenance": sample}]})
