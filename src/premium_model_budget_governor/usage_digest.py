"""Opt-in local recorded-observation digest, never a weekly billing calculation."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3

from .cost import RATES
from .database import connection
from .private_file import write_private
from .work_journal import _schema, _decode


MAX_JOURNAL_BYTES = 16 * 1024 * 1024
MAX_OBSERVATIONS = 10000
MAX_RECORDS = 50000


def digest_preference(path: Path):
    path = Path(path)
    if not path.exists():
        return {"schema_version": 1, "enabled": False}
    if path.is_symlink():
        raise ValueError("digest preferences must be a regular owned file")
    with path.open("rb") as handle:
        data = handle.read(4097)
    try:
        value = json.loads(data)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid digest preferences") from exc
    if (len(data) > 4096 or not isinstance(value, dict) or set(value) != {"schema_version", "enabled"}
            or type(value["schema_version"]) is not int or value["schema_version"] != 1
            or type(value["enabled"]) is not bool):
        raise ValueError("unsupported digest preferences; no migration performed")
    return value


def set_digest_preference(path: Path, enabled, *, approved=False):
    if approved is not True or type(enabled) is not bool:
        raise ValueError("explicit digest preference approval and boolean required")
    digest_preference(path)
    value = {"schema_version": 1, "enabled": enabled}
    write_private(Path(path), json.dumps(value, sort_keys=True).encode("utf-8"))
    return value


def _timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError("timezone required")
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("invalid observation timestamp") from exc


def _counter(value):
    if value is None:
        return None
    if type(value) is not int or not 0 <= value <= 9007199254740991:
        raise ValueError("invalid or unsupported display counter")
    return value


def build_digest(path: Path, *, now=None):
    end = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(end, datetime) or end.tzinfo is None:
        raise ValueError("digest time requires a timezone")
    end = end.astimezone(timezone.utc)
    start = end - timedelta(days=7)
    included = complete = future = entries = 0
    latest = {}
    path = Path(path)
    if path.exists():
        try:
            with connection(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
                db.execute("BEGIN")
                _schema(db)
                count, size = db.execute("SELECT COUNT(*),COALESCE(SUM(length(CAST(payload AS BLOB))),0) FROM observations").fetchone()
                if count > MAX_OBSERVATIONS or size > MAX_JOURNAL_BYTES:
                    raise ValueError("journal exceeds bounded digest limits; reviewed maintenance required")
                for rowid, identity, payload, checksum in db.execute("SELECT rowid,id,payload,checksum FROM observations ORDER BY rowid"):
                    observation = _decode((payload, checksum), identity)
                    stamp = _timestamp(observation.get("recorded_at"))
                    if stamp > end:
                        future += 1
                        continue
                    if stamp < start:
                        continue
                    included += 1
                    report = observation["report"]
                    complete += report.get("coverage") == "complete_for_supplied_receipts"
                    records = report.get("records")
                    if not isinstance(records, dict):
                        raise ValueError("invalid observation records")
                    entries += len(records)
                    if entries > MAX_RECORDS:
                        raise ValueError("records exceed bounded digest limits")
                    for record in records.values():
                        if not isinstance(record, dict) or not isinstance(record.get("source_id"), str):
                            raise ValueError("invalid observation source")
                        source = record["source_id"]
                        order = (stamp, rowid)
                        previous = latest.get(source)
                        if previous is None or order > previous[0]:
                            latest[source] = (order, record, False)
                        elif order == previous[0]:
                            latest[source] = (order, record, True)
        except sqlite3.DatabaseError as exc:
            raise ValueError("observation journal unavailable") from exc
    sources = []
    ordered = sorted(latest.values(), key=lambda row: row[0], reverse=True)
    for index, (order, record, ambiguous) in enumerate(ordered[:100], 1):
        usage = record.get("usage")
        if not isinstance(usage, dict):
            raise ValueError("invalid observation usage")
        tokens = {name: None if ambiguous else _counter(usage.get(name))
                  for name in ("input_tokens", "cached_tokens", "output_tokens")}
        assumptions = usage.get("counter_assumptions")
        if assumptions is not None and (not isinstance(assumptions, list) or any(
                not isinstance(value, str) or value not in {"absent_cached_input_assumed_zero", "absent_cache_write_assumed_zero"}
                for value in assumptions)):
            raise ValueError("invalid observation counter assumptions")
        cache_status = ("ambiguous" if ambiguous else "legacy_unknown" if assumptions is None
                        else "assumed_zero" if "absent_cached_input_assumed_zero" in assumptions
                        else "reported" if tokens["cached_tokens"] is not None else "unknown")
        if cache_status != "reported":
            tokens["cached_tokens"] = None
        sources.append({
            "source": f"Source {index}", "recorded_at": order[0].isoformat(),
            "recorded_model": record.get("model") if record.get("model") in RATES else "unknown",
            "counter_kind": record.get("counter_kind") if record.get("counter_kind") in {"final", "cumulative", "delta"} else "unknown",
            "ambiguous": ambiguous, "cache_status": cache_status, **tokens,
        })
    return {
        "schema_version": 1, "window_start": start.isoformat(), "window_end": end.isoformat(),
        "time_basis": "observation_recorded_at_not_execution",
        "observation_count": included, "complete_observation_count": complete,
        "incomplete_observation_count": included - complete, "future_observations": future,
        "record_entries": entries, "source_count": len(latest), "latest_sources": sources,
        "sources_truncated": len(latest) > 100, "weekly_tokens": None, "weekly_cost": None,
        "weekly_allowance_remaining": None, "savings_proven": False, "coverage": "observations_only",
        "model_identity_verified": False,
        "limitations": [
            "Seven-day window uses recording dates, not execution dates; imported counters may describe older work.",
            "Latest saved counters per source are not additive, weekly usage, provider bills or savings. Source labels are local ordinals.",
            "Other chats, missing receipts, deleted observations and unrecorded work are not covered. Source identity is caller supplied.",
            "No model call, background collection, network upload, email or scheduled delivery is performed.",
        ],
    }
