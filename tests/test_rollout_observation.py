import json

import pytest

from premium_model_budget_governor.experiments import import_codex_receipt


def events():
    return [{"type": "turn_context", "payload": {"model": "gpt-6-astra"}},
            {"type": "response_item", "payload": {"text": "PRIVATE"}},
            {"type": "event_msg", "payload": {"type": "token_count", "info": {
                "total_token_usage": {"input_tokens": 100, "output_tokens": 10}}}}]


def write_rollout(path, rows=None):
    path.write_text("\n".join(map(json.dumps, events() if rows is None else rows)) + "\n", encoding="utf-8")


def test_import_has_content_digest_not_content(tmp_path):
    from hashlib import sha256
    path = tmp_path / "rollout.jsonl"
    write_rollout(path)
    result = import_codex_receipt(path, "r1")
    assert result["source_digest"] == sha256(path.read_bytes()).hexdigest()
    assert result["source_bytes"] == path.stat().st_size
    assert "PRIVATE" not in str(result)
    assert str(path) not in str(result)


def test_size_limit_fails_before_parse(tmp_path):
    path = tmp_path / "rollout.jsonl"
    write_rollout(path)
    with pytest.raises(ValueError, match="size"):
        import_codex_receipt(path, "r1", max_bytes=10)


def test_malformed_event_does_not_leak_contents(tmp_path):
    path = tmp_path / "rollout.jsonl"
    write_rollout(path, ["PRIVATE"])
    with pytest.raises(ValueError, match="event must be an object"):
        import_codex_receipt(path, "r1")


def test_cli_observation_remains_cumulative(tmp_path, capsys):
    from premium_model_budget_governor.cli import main
    from premium_model_budget_governor.work_journal import read_observation
    path, journal = tmp_path / "rollout.jsonl", tmp_path / "work.sqlite3"
    write_rollout(path)
    assert main(["observe-rollout", "--input", str(path), "--journal", str(journal),
                 "--observation-id", "obs-1", "--work-unit", "w1", "--source-id", "s1"]) == 0
    result = json.loads(capsys.readouterr().out)["result"]
    record = result["report"]["records"]["obs-1"]
    assert record["counter_kind"] == "cumulative"
    assert record["usage"]["input_tokens"] == 100
    assert result["report"]["totals"] is None
    assert record["provenance"]["source_kind"] == "codex_local_rollout"
    assert "PRIVATE" not in str(result)
    assert read_observation(journal, "obs-1") == result
