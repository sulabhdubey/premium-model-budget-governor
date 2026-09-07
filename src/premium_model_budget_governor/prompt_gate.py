"""Optional trusted UserPromptSubmit hook. Grants bind a prompt, session and lease."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys
import time


def check_prompt(event: dict, grant: dict) -> dict:
    """Consume a pre-reserved grant. Never infer model identity from prompt text."""
    if event.get("hook_event_name") != "UserPromptSubmit":
        raise ValueError("unsupported hook event")
    for key in ("session_id", "turn_id", "cwd", "prompt"):
        if not isinstance(event.get(key), str) or not event[key]:
            raise ValueError("incomplete hook event")
    for key in ("session_id", "cwd", "prompt_sha256", "ledger", "task_id", "lease_id"):
        if not isinstance(grant.get(key), str) or not grant[key]:
            raise ValueError("incomplete grant")
    if event["session_id"] != grant["session_id"] or Path(event["cwd"]).resolve(strict=True) != Path(grant["cwd"]).resolve(strict=True):
        raise ValueError("grant context mismatch")
    digest = sha256(event["prompt"].encode("utf-8")).hexdigest()
    if digest != grant["prompt_sha256"]:
        raise ValueError("grant prompt mismatch")
    ledger = Path(grant["ledger"]).resolve(strict=True)
    with sqlite3.connect(ledger.as_uri() + "?mode=rw", uri=True, timeout=5) as db:
        db.execute("BEGIN IMMEDIATE")
        lease = db.execute("SELECT status,expires_at FROM leases WHERE task=? AND id=?", (grant["task_id"], grant["lease_id"])).fetchone()
        if lease is None or lease[0] != "reserved" or lease[1] is None or lease[1] <= time.time():
            raise ValueError("missing, expired or inactive reservation")
        limits = db.execute("SELECT ceiling,reserve FROM tasks WHERE id=?", (grant["task_id"],)).fetchone()
        committed = db.execute("SELECT COALESCE(SUM(CASE WHEN status='settled' THEN actual WHEN status='reserved' THEN estimate ELSE 0 END),0) FROM leases WHERE task=?", (grant["task_id"],)).fetchone()[0]
        if limits is None or committed + limits[1] > limits[0] + 1e-9:
            raise ValueError("task over budget")
        db.execute("CREATE TABLE IF NOT EXISTS prompt_grants (task TEXT, lease TEXT, session TEXT, turn TEXT, digest TEXT, PRIMARY KEY(task,lease))")
        prior = db.execute("SELECT session,turn,digest FROM prompt_grants WHERE task=? AND lease=?", (grant["task_id"], grant["lease_id"])).fetchone()
        identity = (event["session_id"], event["turn_id"], digest)
        if prior and prior != identity:
            raise ValueError("grant already consumed by another turn")
        if prior is None:
            db.execute("CREATE TABLE IF NOT EXISTS dispatches (task TEXT NOT NULL, id TEXT NOT NULL, PRIMARY KEY(task,id))")
            try:
                db.execute("INSERT INTO dispatches VALUES (?,?)", (grant["task_id"], grant["lease_id"]))
            except sqlite3.IntegrityError as exc:
                raise ValueError("lease already dispatched through another path") from exc
        db.execute("INSERT OR IGNORE INTO prompt_grants VALUES (?,?,?,?,?)", (grant["task_id"], grant["lease_id"], *identity))
    return {"continue": True}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Optional prompt gate; never auto-installs or auto-trusts")
    parser.add_argument("--grant", required=True)
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError("oversized hook input")
        event = json.loads(raw)
        grant = json.loads(Path(args.grant).read_text(encoding="utf-8"))
        if not isinstance(event, dict) or not isinstance(grant, dict):
            raise ValueError("object required")
        result = check_prompt(event, grant)
    except (ValueError, OSError, sqlite3.Error, TypeError):
        result = {"decision": "block", "reason": "Governor requires a matching, unexpired reserved prompt grant. Reconcile or replan before submitting."}
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
