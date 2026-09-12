"""Transactional bounded counter collection from one explicit local rollout."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3

from .cost import _token
from .database import connection
from .rollout_sample import counter_values

APPLICATION_ID = 0x504D4249
MAX_BYTES = 4 * 1024 * 1024


def _encoded(value):
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(text.encode("utf-8")) > 65536:
        raise ValueError("collector record exceeds bounded storage")
    return text, sha256(text.encode("utf-8")).hexdigest()


def _decoded(row):
    if (row is None or not isinstance(row[0], str) or len(row[0].encode("utf-8")) > 65536
            or sha256(row[0].encode("utf-8")).hexdigest() != row[1]):
        raise ValueError("collector integrity check failed")
    try:
        value = json.loads(row[0])
    except (ValueError, RecursionError) as exc:
        raise ValueError("collector payload invalid") from exc
    if not isinstance(value, dict):
        raise ValueError("collector payload must be an object")
    return value


def _schema(db, *, create=False):
    application = db.execute("PRAGMA application_id").fetchone()[0]
    version = db.execute("PRAGMA user_version").fetchone()[0]
    names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
    if not names and application == version == 0 and create:
        db.execute("CREATE TABLE checkpoint (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, checksum TEXT NOT NULL)")
        db.execute("CREATE TABLE observations (id INTEGER PRIMARY KEY, payload TEXT NOT NULL, checksum TEXT NOT NULL)")
        db.execute(f"PRAGMA application_id={APPLICATION_ID}")
        db.execute("PRAGMA user_version=1")
    elif application != APPLICATION_ID or version != 1 or names != {"checkpoint", "observations"}:
        raise ValueError("unrecognized collector database; no migration performed")


def _range(handle, start, length):
    handle.seek(start)
    data = handle.read(length)
    if len(data) != length:
        raise ValueError("source changed during collection")
    return data


def _event(line):
    try:
        event = json.loads(line)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError("malformed complete source event") from exc
    if not isinstance(event, dict) or not isinstance(event.get("payload", {}), dict):
        raise ValueError("source event or payload is not an object")
    payload = event.get("payload", {})
    if event.get("type") != "event_msg" or payload.get("type") != "token_count":
        return False, None
    info = payload.get("info")
    total = info.get("total_token_usage") if isinstance(info, dict) else None
    if not isinstance(total, dict):
        return True, None
    usage = counter_values(total)
    for key, source in (("cached_tokens", "cached_input_tokens"), ("cache_write_tokens", "cache_write_tokens")):
        if source not in total:
            usage[key] = None
    return True, usage


def _difference(previous, current):
    if previous is None or current is None:
        return None
    result = {key: current[key] - previous[key] if current[key] is not None and previous[key] is not None else None for key in current}
    if any(value is not None and value < 0 for value in result.values()):
        return None
    if sum(result[key] or 0 for key in ("cached_tokens", "cache_write_tokens")) > result["input_tokens"]:
        return None
    return result


def _advance(source, cursor, max_bytes):
    with source.open("rb") as handle:
        stat = os.fstat(handle.fileno())
        file_key = sha256(f"{stat.st_dev}:{stat.st_ino}".encode()).hexdigest()
        end = stat.st_size
        bootstrap = cursor is None
        last_counter = None
        gap = False
        if cursor is not None:
            offset = _token(cursor.get("offset"), "cursor offset")
            prefix_bytes = _token(cursor.get("prefix_bytes"), "prefix bytes")
            anchor_start = _token(cursor.get("anchor_start"), "anchor start")
            if (type(cursor.get("schema_version")) is not int or cursor["schema_version"] != 1 or cursor.get("file_key") != file_key or end < offset
                    or prefix_bytes > 4096 or prefix_bytes > offset or anchor_start != max(0, offset - 4096)
                    or type(cursor.get("gap")) is not bool):
                raise ValueError("source identity, size or cursor changed")
            if (sha256(_range(handle, 0, prefix_bytes)).hexdigest() != cursor.get("prefix_hash")
                    or sha256(_range(handle, anchor_start, offset - anchor_start)).hexdigest() != cursor.get("anchor_hash")):
                raise ValueError("source anchor changed")
            last_counter = cursor.get("last_counter")
            if last_counter is not None:
                if not isinstance(last_counter, dict):
                    raise ValueError("invalid source counter checkpoint")
                position = _token(last_counter.get("position"), "counter position")
                length = _token(last_counter.get("length"), "counter length")
                if not 1 <= length <= MAX_BYTES or position + length > offset:
                    raise ValueError("invalid source counter range")
                line = _range(handle, position, length)
                if sha256(line).hexdigest() != last_counter.get("hash") or _event(line) != (True, last_counter.get("usage")):
                    raise ValueError("source counter changed")
            start = offset
            gap = cursor["gap"]
        else:
            start = max(0, end - max_bytes)
        data = _range(handle, start, min(max_bytes, end - start))
        first = data.find(b"\n") + 1 if bootstrap and start else 0
        last = data.rfind(b"\n") + 1
        if last <= first:
            if len(data) == max_bytes:
                raise ValueError("next complete source event exceeds bounded read")
            return None, {"status": "no_new_complete_events", "backlog_bytes": end - start,
                          "counter_difference": None, "actual_model": "unknown", "estimated_credits": None}
        previous = last_counter["usage"] if last_counter else None
        baseline_position = last_counter["position"] if last_counter else None
        before = previous
        resets = missing = counters = 0
        uncertain = gap
        position = start + first
        for line in data[first:last].splitlines(keepends=True):
            if line.strip():
                is_counter, current = _event(line)
                if is_counter:
                    counters += 1
                    if current is None:
                        missing += 1
                        gap = uncertain = True
                    else:
                        if previous is not None and _difference(previous, current) is None:
                            resets += 1
                        previous = current
                        last_counter = {"position": position, "length": len(line), "hash": sha256(line).hexdigest(), "usage": current}
                        gap = False
            position += len(line)
        offset = start + last
        # Re-read the fixed input window. Growth beyond it is permitted, not re-scanned here.
        if _range(handle, start, len(data)) != data:
            raise ValueError("source changed during collection")
        after = source.stat()
        if (after.st_dev, after.st_ino) != (stat.st_dev, stat.st_ino) or after.st_size < offset:
            raise ValueError("source replaced or truncated during collection")
        prefix_bytes = min(offset, 4096)
        anchor_start = max(0, offset - 4096)
        next_cursor = {"schema_version": 1, "file_key": file_key, "offset": offset,
                       "prefix_bytes": prefix_bytes, "prefix_hash": sha256(_range(handle, 0, prefix_bytes)).hexdigest(),
                       "anchor_start": anchor_start, "anchor_hash": sha256(_range(handle, anchor_start, offset - anchor_start)).hexdigest(),
                       "last_counter": last_counter, "gap": gap}
        difference = None if bootstrap or uncertain or resets or not counters else _difference(before, previous)
        return next_cursor, {
            "schema_version": 1, "status": "observed", "bootstrap": bootstrap,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "read_start": start, "consumed_end": offset, "backlog_bytes": after.st_size - offset,
            "source_size_at_open": end, "source_size_at_check": after.st_size,
            "history_before_start_unmeasured": start + first if bootstrap else None,
            "range_sha256": sha256(data[first:last]).hexdigest(), "range_bytes": last - first,
            "counter_events": counters, "missing_counter_events": missing, "counter_resets": resets,
            "counter_difference": difference, "latest_cumulative": previous,
            "counter_interval_line_offsets": {"from": baseline_position, "to": last_counter["position"]} if difference is not None else None,
            "actual_model": "unknown", "estimated_credits": None,
            "coverage": "counter_interval_only", "savings_proven": False,
            "limitations": ["Observed counter positions are not task/goal boundaries or model attribution.",
                            "Missing cache fields remain unknown. Subsets are not added to input/output totals.",
                            "Local anchors/checksums detect bounded changes, not all historical edits or provider attestation.",
                            "No background watcher, model call, budget settlement or weekly billing inference."],
        }


def collect_rollout(source: Path, journal: Path, *, max_bytes=MAX_BYTES):
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_BYTES:
        raise ValueError("collection bound must be 1 byte to 4 MiB")
    source, journal = Path(source).resolve(strict=True), Path(journal).resolve()
    if not source.is_file() or source == journal or (journal.exists() and source.samefile(journal)):
        raise ValueError("source must be a separate explicit file")
    journal.parent.mkdir(parents=True, exist_ok=True)
    try:
        with connection(journal, timeout=30) as db:
            db.execute("BEGIN IMMEDIATE")
            _schema(db, create=True)
            row = db.execute("SELECT payload,checksum FROM checkpoint WHERE id=1").fetchone()
            cursor = _decoded(row) if row else None
            if db.execute("SELECT COUNT(*) FROM observations").fetchone()[0] >= 10000:
                raise ValueError("collector history limit reached; preserve and rotate explicitly")
            next_cursor, report = _advance(source, cursor, max_bytes)
            if next_cursor is not None:
                payload, checksum = _encoded(report)
                db.execute("INSERT INTO observations(payload,checksum) VALUES (?,?)", (payload, checksum))
                payload, checksum = _encoded(next_cursor)
                db.execute("INSERT OR REPLACE INTO checkpoint VALUES (1,?,?)", (payload, checksum))
            return report
    except sqlite3.DatabaseError as exc:
        raise ValueError("collector database unavailable or invalid") from exc


def read_collections(journal: Path):
    path = Path(journal).resolve(strict=True)
    try:
        with connection(path.as_uri() + "?mode=ro", uri=True) as db:
            _schema(db)
            if db.execute("SELECT 1 FROM observations WHERE length(CAST(payload AS BLOB))>65536 LIMIT 1").fetchone():
                raise ValueError("collector record exceeds bounded storage")
            rows = db.execute("SELECT payload,checksum FROM observations ORDER BY id DESC LIMIT 101").fetchall()
            return {"schema_version": 1, "observations": [_decoded(row) for row in rows[:100]],
                    "truncated": len(rows) > 100, "totals": None, "savings_proven": False}
    except sqlite3.DatabaseError as exc:
        raise ValueError("collector database unavailable or invalid") from exc
