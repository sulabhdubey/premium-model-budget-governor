"""Immutable local observations; independent of execution and budget databases.

Checksums detect accidental corruption, not tampering by the local account.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from .database import connection
from .long_work import _identity, reconcile_work


APPLICATION_ID = 0x504D4257
SCHEMA_VERSION = 1


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _schema(db, *, create=False):
    application = db.execute("PRAGMA application_id").fetchone()[0]
    version = db.execute("PRAGMA user_version").fetchone()[0]
    objects = db.execute("SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
    if not objects and application == 0 and version == 0 and create:
        db.execute("CREATE TABLE observations (id TEXT PRIMARY KEY, payload TEXT NOT NULL, checksum TEXT NOT NULL)")
        db.execute(f"PRAGMA application_id={APPLICATION_ID}")
        db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
    elif application != APPLICATION_ID:
        raise ValueError("unrecognized observation database; no migration performed")
    elif version != SCHEMA_VERSION:
        raise ValueError("unsupported observation schema; no migration performed")
    elif objects != [("observations",)]:
        raise ValueError("unrecognized observation schema objects")


def _decode(row, identity):
    if row is None:
        raise ValueError("observation missing")
    payload, checksum = row
    if sha256(payload.encode()).hexdigest() != checksum:
        raise ValueError("observation integrity check failed")
    try:
        value = json.loads(payload)
        valid = (isinstance(value, dict) and value.get("observation_id") == identity
                 and value.get("schema_version") == SCHEMA_VERSION
                 and isinstance(value.get("report"), dict))
    except (TypeError, json.JSONDecodeError):
        valid = False
    if not valid:
        raise ValueError("observation integrity structure mismatch")
    return value


def save_observation(path: Path, observation_id: str, packet: dict) -> dict:
    identity = _identity(observation_id)
    report = reconcile_work(packet)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with connection(path, timeout=15) as db:
            db.execute("BEGIN IMMEDIATE")
            _schema(db, create=True)
            previous = db.execute("SELECT payload,checksum FROM observations WHERE id=?", (identity,)).fetchone()
            if previous:
                saved = _decode(previous, identity)
                if saved["report"] != report:
                    raise ValueError("conflicting observation; use a new ID for reanalysis")
                return saved
            value = {"schema_version": SCHEMA_VERSION, "observation_id": identity,
                     "recorded_at": datetime.now(timezone.utc).isoformat(), "report": report}
            encoded = _encode(value)
            db.execute("INSERT INTO observations VALUES (?,?,?)",
                       (identity, encoded, sha256(encoded.encode()).hexdigest()))
            return value
    except sqlite3.DatabaseError as exc:
        raise ValueError("observation journal unavailable or invalid") from exc


def read_observation(path: Path, observation_id: str) -> dict:
    identity = _identity(observation_id)
    path = Path(path)
    if not path.is_file():
        raise ValueError("observation journal missing")
    try:
        with connection(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
            _schema(db)
            return _decode(db.execute("SELECT payload,checksum FROM observations WHERE id=?", (identity,)).fetchone(), identity)
    except sqlite3.DatabaseError as exc:
        raise ValueError("observation journal unavailable or invalid") from exc


def list_observations(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        return {"observations": [], "truncated": False}
    try:
        with connection(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
            _schema(db)
            rows = db.execute("SELECT id,payload,checksum FROM observations ORDER BY rowid DESC LIMIT 101").fetchall()
            items = []
            for identity, payload, checksum in rows[:100]:
                observation = _decode((payload, checksum), identity)
                report = observation["report"]
                items.append({"observation_id": identity, "recorded_at": observation["recorded_at"],
                              "coverage": report.get("coverage", "unknown"),
                              "receipt_count": report.get("receipt_count"),
                              "estimated_credits": report.get("estimated_credits")})
            return {"observations": items, "truncated": len(rows) > 100}
    except sqlite3.DatabaseError as exc:
        raise ValueError("observation journal unavailable or invalid") from exc


def observe_rollout(path: Path, journal: Path, observation_id: str, work_unit_id: str, source_id: str, *, sample=False) -> dict:
    from .experiments import import_codex_receipt
    for identity in (observation_id, work_unit_id, source_id):
        _identity(identity)
    if sample:
        from .rollout_sample import sample_rollout
        receipt = sample_rollout(path)
        provenance = {key: receipt[key] for key in ("source_kind", "source_digest", "source_bytes",
                      "sample_start", "sample_end", "source_size_at_open", "leading_bytes_ignored", "trailing_bytes_ignored",
                      "counter_resets", "counter_events", "counter_scope")}
    else:
        receipt = import_codex_receipt(path, observation_id)
        provenance = {"source_kind": "codex_local_rollout", "source_digest": receipt["source_digest"],
                      "source_bytes": receipt["source_bytes"]}
    packet = {"work_units": [work_unit_id], "receipts": [{
        "receipt_id": observation_id, "work_unit_id": work_unit_id, "source_id": source_id,
        "counter_kind": "cumulative", "scope": "unknown", "model": receipt["actual_model"],
        "usage": receipt["usage"], "provenance": provenance,
    }]}
    return save_observation(journal, observation_id, packet)
