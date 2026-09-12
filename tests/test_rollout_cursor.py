import json
from pathlib import Path
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from premium_model_budget_governor.rollout_cursor import collect_rollout, read_collections


def token(incoming=100, outgoing=10, cached=20):
    return json.dumps({"type": "event_msg", "payload": {"type": "token_count", "info": {
        "total_token_usage": {"input_tokens": incoming, "cached_input_tokens": cached,
                              "output_tokens": outgoing, "total_tokens": incoming + outgoing}}}}).encode() + b"\n"


def append(path, data):
    with path.open("ab") as stream:
        stream.write(data)


def test_bootstrap_then_observed_difference_and_noop(tmp_path):
    source, journal = tmp_path / "source.jsonl", tmp_path / "collector.sqlite3"
    source.write_bytes(token())
    first = collect_rollout(source, journal)
    assert first["counter_difference"] is None and first["bootstrap"] is True
    append(source, token(150, 20, 40))
    second = collect_rollout(source, journal)
    assert second["counter_difference"]["input_tokens"] == 50
    assert second["counter_difference"]["output_tokens"] == 10
    assert second["counter_difference"]["cached_tokens"] == 20
    assert second["counter_interval_line_offsets"] == {"from": 0, "to": len(token())}
    assert second["counter_difference"]["cache_write_tokens"] is None
    assert second["actual_model"] == "unknown" and second["estimated_credits"] is None
    assert collect_rollout(source, journal)["status"] == "no_new_complete_events"
    assert len(read_collections(journal)["observations"]) == 2
    assert str(source) not in json.dumps(second)


def test_partial_line_is_resumed_without_loss(tmp_path):
    source, journal = tmp_path / "source", tmp_path / "journal"
    source.write_bytes(token())
    collect_rollout(source, journal)
    following = token(120)
    append(source, following[:30])
    assert collect_rollout(source, journal)["status"] == "no_new_complete_events"
    append(source, following[30:])
    assert collect_rollout(source, journal)["counter_difference"]["input_tokens"] == 20


def test_reset_does_not_create_negative_or_free_usage(tmp_path):
    source, journal = tmp_path / "source", tmp_path / "journal"
    source.write_bytes(token(500))
    collect_rollout(source, journal)
    append(source, token(100) + token(150))
    report = collect_rollout(source, journal)
    assert report["counter_resets"] == 1 and report["counter_difference"] is None
    append(source, token(180))
    assert collect_rollout(source, journal)["counter_difference"]["input_tokens"] == 30


def test_malformed_event_rolls_back_cursor_and_history(tmp_path):
    source, journal = tmp_path / "source", tmp_path / "journal"
    source.write_bytes(token())
    collect_rollout(source, journal)
    before = read_collections(journal)
    append(source, b"bad complete event\n")
    with pytest.raises(ValueError):
        collect_rollout(source, journal)
    assert read_collections(journal) == before


@pytest.mark.parametrize("change", ["truncate", "rewrite", "replace"])
def test_source_changes_require_explicit_new_collection(tmp_path, change):
    source, journal = tmp_path / "source", tmp_path / "journal"
    source.write_bytes(token())
    collect_rollout(source, journal)
    if change == "truncate":
        source.write_bytes(b"")
    elif change == "rewrite":
        source.write_bytes(token(900))
    else:
        replacement = tmp_path / "replacement"
        replacement.write_bytes(token())
        replacement.replace(source)
    with pytest.raises(ValueError, match="source"):
        collect_rollout(source, journal)
    assert len(read_collections(journal)["observations"]) == 1


def test_concurrent_collectors_do_not_duplicate_interval(tmp_path):
    source, journal = tmp_path / "source", tmp_path / "journal"
    source.write_bytes(token())
    collect_rollout(source, journal)
    append(source, token(180))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: collect_rollout(source, journal), range(2)))
    assert sum(result.get("counter_difference") is not None for result in results) == 1
    assert len(read_collections(journal)["observations"]) == 2


def test_foreign_database_preserved(tmp_path):
    source, journal = tmp_path / "source", tmp_path / "journal"
    source.write_bytes(token())
    with sqlite3.connect(journal) as db:
        db.execute("CREATE TABLE private (value TEXT)")
    before = journal.read_bytes()
    with pytest.raises(ValueError):
        collect_rollout(source, journal)
    assert journal.read_bytes() == before


def test_chunk_boundary_continues_and_discloses_backlog(tmp_path):
    source, journal = tmp_path / "source", tmp_path / "journal"
    source.write_bytes(token())
    collect_rollout(source, journal)
    append(source, token(120) + token(140) + token(160))
    first = collect_rollout(source, journal, max_bytes=len(token(120)))
    assert first["backlog_bytes"] > 0
    assert first["counter_difference"]["input_tokens"] == 20
    final = collect_rollout(source, journal)
    assert final["counter_difference"]["input_tokens"] == 40


def test_missing_counter_information_blocks_interval_not_source_progress(tmp_path):
    source, journal = tmp_path / "source", tmp_path / "journal"
    source.write_bytes(token())
    collect_rollout(source, journal)
    append(source, b'{"type":"event_msg","payload":{"type":"token_count","info":null}}\n' + token(160))
    report = collect_rollout(source, journal)
    assert report["counter_difference"] is None and report["missing_counter_events"] == 1


def test_cli_collection_and_readback(tmp_path, capsys):
    from premium_model_budget_governor.cli import main
    source, journal = tmp_path / "source", tmp_path / "journal"
    source.write_bytes(token())
    assert main(["collect-rollout", "--input", str(source), "--journal", str(journal)]) == 0
    assert json.loads(capsys.readouterr().out)["result"]["bootstrap"] is True
    assert main(["collect-rollout", "--journal", str(journal)]) == 0
    assert len(json.loads(capsys.readouterr().out)["result"]["observations"]) == 1


def test_write_failure_after_observation_insert_rolls_back_both(tmp_path, monkeypatch):
    import premium_model_budget_governor.rollout_cursor as module
    source, journal = tmp_path / "source", tmp_path / "journal"
    source.write_bytes(token())
    collect_rollout(source, journal)
    before = read_collections(journal)
    append(source, token(140))
    encode = module._encoded
    def fail_cursor(value):
        if "offset" in value:
            raise ValueError("synthetic checkpoint write failure")
        return encode(value)
    monkeypatch.setattr(module, "_encoded", fail_cursor)
    with pytest.raises(ValueError):
        collect_rollout(source, journal)
    assert read_collections(journal) == before
    monkeypatch.setattr(module, "_encoded", encode)
    assert collect_rollout(source, journal)["counter_difference"]["input_tokens"] == 40
    assert len(read_collections(journal)["observations"]) == 2


def test_append_during_read_is_pending_not_lost(tmp_path, monkeypatch):
    import premium_model_budget_governor.rollout_cursor as module
    source, journal = tmp_path / "source", tmp_path / "journal"
    source.write_bytes(token())
    collect_rollout(source, journal)
    append(source, token(120))
    parse = module._event
    written = False
    def append_after_counter(line):
        nonlocal written
        result = parse(line)
        if result[1] and result[1]["input_tokens"] == 120 and not written:
            append(source, token(140))
            written = True
        return result
    monkeypatch.setattr(module, "_event", append_after_counter)
    report = collect_rollout(source, journal)
    assert report["counter_difference"]["input_tokens"] == 20
    assert report["backlog_bytes"] > 0
    assert collect_rollout(source, journal)["counter_difference"]["input_tokens"] == 20


def test_source_cannot_be_collector_database(tmp_path):
    source = tmp_path / "source"
    source.write_bytes(token())
    before = source.read_bytes()
    with pytest.raises(ValueError, match="separate"):
        collect_rollout(source, source)
    assert source.read_bytes() == before


def test_bad_cache_difference_is_uncertain_even_when_totals_are_valid(tmp_path):
    source, journal = tmp_path / "source", tmp_path / "journal"
    source.write_bytes(token(100, cached=0))
    collect_rollout(source, journal)
    append(source, token(110, cached=90))
    report = collect_rollout(source, journal)
    assert report["counter_difference"] is None


def test_corrupt_checkpoint_fails_without_advancing(tmp_path):
    source, journal = tmp_path / "source", tmp_path / "journal"
    source.write_bytes(token())
    collect_rollout(source, journal)
    append(source, token(140))
    with sqlite3.connect(journal) as db:
        db.execute("UPDATE checkpoint SET checksum='changed'")
    with pytest.raises(ValueError, match="integrity"):
        collect_rollout(source, journal)
    assert len(read_collections(journal)["observations"]) == 1


def test_completed_event_over_bound_never_silently_skipped(tmp_path):
    source, journal = tmp_path / "source", tmp_path / "journal"
    source.write_bytes(token())
    collect_rollout(source, journal)
    append(source, json.dumps({"type": "other", "payload": {"text": "x" * 1000}}).encode() + b"\n" + token(140))
    with pytest.raises(ValueError, match="exceeds bounded"):
        collect_rollout(source, journal, max_bytes=100)
    assert len(read_collections(journal)["observations"]) == 1
    assert collect_rollout(source, journal)["counter_difference"]["input_tokens"] == 40


@pytest.mark.parametrize("size", [True, 0, -1, 99_000_000])
def test_invalid_bounds_fail_before_source_read(tmp_path, size):
    with pytest.raises(ValueError, match="bound"):
        collect_rollout(tmp_path / "missing", tmp_path / "journal", max_bytes=size)
