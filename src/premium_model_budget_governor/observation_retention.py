"""Explicit preview-bound cleanup of the dedicated observation journal only."""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import sqlite3
import tempfile

from .database import connection
from .work_journal import _schema, _decode, _encode


def _time(value):
    if not isinstance(value, str):
        raise ValueError("timezone-aware cutoff required")
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError("timezone-aware cutoff required") from None
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("timezone-aware cutoff required")
    return stamp


def _rows(db):
    _schema(db)
    rows = db.execute("SELECT id,payload,checksum FROM observations ORDER BY id LIMIT 10001").fetchall()
    if len(rows) > 10000:
        raise ValueError("journal exceeds bounded retention preview; no deletion")
    for identity, payload, checksum in rows:
        _decode((payload, checksum), identity)
    return rows


def _plan(rows, before):
    cutoff = _time(before)
    identities = [identity for identity, payload, checksum in rows
                  if _time(_decode((payload, checksum), identity)["recorded_at"]) < cutoff]
    return {"schema_version": 1, "before": before, "observation_ids": identities,
            "remove_count": len(identities),
            "journal_fingerprint": sha256(_encode(rows).encode()).hexdigest(),
            "scope": "observation_journal_only", "backup_required": True}


def preview_retention(path: Path, before: str) -> dict:
    _time(before)
    path = Path(path)
    if not path.is_file():
        raise ValueError("observation journal missing")
    try:
        with connection(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
            return _plan(_rows(db), before)
    except sqlite3.DatabaseError as exc:
        raise ValueError("invalid observation journal") from exc


def apply_retention(path: Path, plan: dict, *, approved=False) -> dict:
    if approved is not True:
        raise ValueError("explicit retention approval required")
    if not isinstance(plan, dict) or not isinstance(plan.get("before"), str):
        raise ValueError("retention preview required")
    path = Path(path)
    if preview_retention(path, plan["before"]) != plan:
        raise ValueError("stale or modified retention preview")
    if not plan["remove_count"]:
        return {"removed": 0, "backup_path": None}
    # Snapshot first; then obtain the write lock and verify live rows still match.
    with tempfile.NamedTemporaryFile(prefix=path.name + ".backup-", suffix=".sqlite3", dir=path.parent, delete=False) as file:
        backup = Path(file.name)
    try:
        with connection(path.resolve().as_uri() + "?mode=ro", uri=True) as source, connection(backup) as destination:
            source.backup(destination)
            if destination.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("retention backup failed integrity verification")
            backup_rows = _rows(destination)
            if _plan(backup_rows, plan["before"]) != plan:
                raise ValueError("stale retention preview; backup retained, nothing deleted")
        with connection(path, timeout=15) as db:
            db.execute("BEGIN IMMEDIATE")
            if _rows(db) != backup_rows:
                raise ValueError("stale retention preview; backup retained, nothing deleted")
            db.executemany("DELETE FROM observations WHERE id=?", [(identity,) for identity in plan["observation_ids"]])
        return {"removed": plan["remove_count"], "backup_path": str(backup),
                "backup_verified": True, "scope": "observation_journal_only"}
    except sqlite3.DatabaseError as exc:
        raise ValueError("retention did not complete; verify journal and retained backup") from exc
