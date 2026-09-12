from datetime import datetime, timezone
import json
import sqlite3

import pytest

from premium_model_budget_governor.usage_digest import build_digest, digest_preference, set_digest_preference
from premium_model_budget_governor.work_journal import save_observation


def packet(source="private-source", tokens=10):
    return {"receipts": [{"receipt_id": "private-receipt", "work_unit_id": "private-work",
        "source_id": source, "model": "gpt-6-astra", "counter_kind": "cumulative",
        "scope": "unknown", "usage": {"input_tokens": tokens, "cached_tokens": 0, "output_tokens": 1}}]}


def test_disabled_by_default_and_invalid_consent_does_not_write(tmp_path):
    path = tmp_path / "digest.json"
    assert digest_preference(path) == {"schema_version": 1, "enabled": False}
    for approval in (None, False, 1, "yes"):
        with pytest.raises(ValueError):
            set_digest_preference(path, True, approved=approval)
    assert not path.exists()
    assert set_digest_preference(path, True, approved=True)["enabled"] is True
    assert digest_preference(path)["enabled"] is True
    assert set_digest_preference(path, False, approved=True)["enabled"] is False


def test_unknown_preferences_are_not_overwritten(tmp_path):
    path = tmp_path / "digest.json"
    path.write_text('{"schema_version": 999, "enabled": true}')
    before = path.read_bytes()
    with pytest.raises(ValueError):
        digest_preference(path)
    with pytest.raises(ValueError):
        set_digest_preference(path, False, approved=True)
    assert path.read_bytes() == before


def test_empty_digest_is_not_zero_usage(tmp_path):
    path = tmp_path / "missing.sqlite3"
    report = build_digest(path)
    assert report["observation_count"] == 0
    assert report["weekly_tokens"] is None
    assert report["weekly_cost"] is None
    assert report["savings_proven"] is False
    assert not path.exists()


def test_overlapping_observations_show_latest_not_sum_or_difference(tmp_path):
    path = tmp_path / "journal.sqlite3"
    save_observation(path, "old", packet(tokens=10))
    save_observation(path, "new", packet(tokens=30))
    report = build_digest(path)
    assert report["observation_count"] == 2
    assert report["source_count"] == 1
    assert report["latest_sources"][0]["input_tokens"] == 30
    assert report["weekly_tokens"] is None
    encoded = json.dumps(report)
    for private in ("private-source", "private-receipt", "private-work"):
        assert private not in encoded


def test_recorded_window_does_not_claim_execution_dates(tmp_path):
    path = tmp_path / "journal.sqlite3"
    saved = save_observation(path, "one", packet())
    report = build_digest(path, now=datetime(2000, 1, 1, tzinfo=timezone.utc))
    assert report["observation_count"] == 0
    assert report["future_observations"] == 1
    assert report["time_basis"] == "observation_recorded_at_not_execution"
    from datetime import timedelta
    at = datetime.fromisoformat(saved["recorded_at"])
    assert build_digest(path, now=at + timedelta(days=7))["observation_count"] == 1
    assert build_digest(path, now=at + timedelta(days=7, microseconds=1))["observation_count"] == 0


def test_tampered_observation_fails_not_partial_digest(tmp_path):
    path = tmp_path / "journal.sqlite3"
    save_observation(path, "one", packet())
    with sqlite3.connect(path) as db:
        db.execute("UPDATE observations SET checksum='invalid'")
    with pytest.raises(ValueError):
        build_digest(path)


def test_foreign_database_never_migrated(tmp_path):
    path = tmp_path / "foreign.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE unrelated (value TEXT)")
    before = path.read_bytes()
    with pytest.raises(ValueError):
        build_digest(path)
    assert path.read_bytes() == before


def test_limits_fail_explicitly(tmp_path, monkeypatch):
    import premium_model_budget_governor.usage_digest as module
    path = tmp_path / "journal.sqlite3"
    save_observation(path, "one", packet())
    monkeypatch.setattr(module, "MAX_JOURNAL_BYTES", 1)
    with pytest.raises(ValueError, match="bounded"):
        build_digest(path)


def test_naive_timestamp_rejected(tmp_path):
    with pytest.raises(ValueError):
        build_digest(tmp_path / "missing", now=datetime(2026, 1, 1))


def test_workbench_digest_is_opt_in_and_counts_undated_tasks(tmp_path):
    from premium_model_budget_governor.workbench import Workbench
    app = Workbench({"p": tmp_path}, tmp_path / "data")
    assert app.usage_digest()["enabled"] is False
    assert app.usage_digest()["report"] is None
    app.configure_digest({"enabled": True, "approved": True})
    with sqlite3.connect(app.database) as db:
        db.execute("INSERT INTO runs VALUES ('one','unknown_usage','{}')")
    result = app.usage_digest()
    assert result["report"]["undated_tasks_excluded"] == 1
    assert result["report"]["weekly_cost"] is None
    app.configure_digest({"enabled": False, "approved": True})
    assert app.usage_digest()["report"] is None


def test_ambiguous_same_source_in_one_observation_keeps_counters_unknown(tmp_path):
    path = tmp_path / "journal.sqlite3"
    data = packet()
    other = {**data["receipts"][0], "receipt_id": "other-receipt"}
    data["receipts"].append(other)
    save_observation(path, "one", data)
    source = build_digest(path)["latest_sources"][0]
    assert source["ambiguous"] is True
    assert source["input_tokens"] is None


def test_display_limit_is_disclosed_and_not_aggregated(tmp_path):
    path = tmp_path / "journal.sqlite3"
    data = {"receipts": [{**packet(source=f"source-{i}")["receipts"][0], "receipt_id": f"receipt-{i}"} for i in range(101)]}
    save_observation(path, "one", data)
    report = build_digest(path)
    assert report["source_count"] == 101
    assert len(report["latest_sources"]) == 100
    assert report["sources_truncated"] is True
    assert report["weekly_tokens"] is None


def test_disabled_digest_never_reads_invalid_journal(tmp_path):
    from premium_model_budget_governor.workbench import Workbench
    app = Workbench({"p": tmp_path}, tmp_path / "data")
    (app.data / "observations.sqlite3").write_bytes(b"invalid database")
    assert app.usage_digest()["report"] is None


def test_preference_persists_across_workbench_restart(tmp_path):
    from premium_model_budget_governor.workbench import Workbench
    app = Workbench({"p": tmp_path}, tmp_path / "data")
    app.configure_digest({"enabled": True, "approved": True})
    reopened = Workbench({"p": tmp_path}, tmp_path / "data")
    assert reopened.usage_digest()["enabled"] is True


def test_complete_supplied_observation_is_counted_correctly(tmp_path):
    data = packet()
    data["receipts"][0].update(counter_kind="final", scope="exclusive")
    path = tmp_path / "journal"
    save_observation(path, "one", data)
    report = build_digest(path)
    assert report["complete_observation_count"] == 1
    assert report["incomplete_observation_count"] == 0


def test_missing_cache_is_not_displayed_as_observed_zero(tmp_path):
    data = packet()
    del data["receipts"][0]["usage"]["cached_tokens"]
    path = tmp_path / "journal"
    save_observation(path, "one", data)
    source = build_digest(path)["latest_sources"][0]
    assert source["cached_tokens"] is None
    assert source["cache_status"] == "assumed_zero"


def test_explicit_cache_zero_remains_reported_zero(tmp_path):
    path = tmp_path / "journal"
    save_observation(path, "one", packet())
    source = build_digest(path)["latest_sources"][0]
    assert source["cached_tokens"] == 0
    assert source["cache_status"] == "reported"


def test_legacy_cache_without_provenance_stays_unknown(tmp_path):
    from hashlib import sha256
    path = tmp_path / "journal"
    saved = save_observation(path, "one", packet())
    del saved["report"]["records"]["private-receipt"]["usage"]["counter_assumptions"]
    text = json.dumps(saved)
    with sqlite3.connect(path) as db:
        db.execute("UPDATE observations SET payload=?,checksum=?", (text, sha256(text.encode()).hexdigest()))
    before = path.read_bytes()
    source = build_digest(path)["latest_sources"][0]
    assert source["cached_tokens"] is None and source["cache_status"] == "legacy_unknown"
    assert path.read_bytes() == before
