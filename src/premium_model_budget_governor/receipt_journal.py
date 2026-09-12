"""Prompt-free terminal host evidence, retained before budget settlement.

Checksums detect accidental corruption, not modification by the local account.
Only the host adapter writes this journal; browser requests cannot supply receipts.
"""
import hashlib
import json
import sqlite3
from .database import connection

from .experiments import normalize_receipt
from .leases import budget_action


def _encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def record_terminal(ledger, *, task_id, call_id, model, thread_id, turn_id, usage, rate_contract=None,
                    host_source="app_server"):
    if host_source not in {"app_server", "codex_cli"}:
        raise ValueError("unsupported terminal host source")
    if host_source == "codex_cli" and (thread_id is not None or turn_id is not None):
        raise ValueError("CLI terminal identifiers must remain unavailable")
    identifiers = (task_id, call_id, model) + ((thread_id, turn_id) if host_source == "app_server" else ())
    for value in identifiers:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("terminal receipt identifiers required")
    normalized = normalize_receipt({"call_id": call_id, "actual_model": model, "usage": usage,
                                    "rate_contract": rate_contract})
    if normalized["credits"] is None:
        raise ValueError("terminal token counters required")
    row = {"schema_version": 2, "task_id": task_id, "call_id": call_id, "model": model,
           "host_source": host_source,
           "thread_id": thread_id, "turn_id": turn_id, "usage": normalized["usage"],
           "estimated_credits": normalized["credits"], "cost_basis": "token_rate_estimate",
           "rate_snapshot": normalized["rate_snapshot"], "rate_fingerprint": normalized["rate_fingerprint"]}
    payload = _encoded(row)
    checksum = hashlib.sha256(payload.encode()).hexdigest()
    with connection(ledger, timeout=15) as db:
        db.execute("CREATE TABLE IF NOT EXISTS terminal_receipts (task TEXT NOT NULL, id TEXT NOT NULL, payload TEXT NOT NULL, checksum TEXT NOT NULL, PRIMARY KEY(task,id))")
        db.execute("BEGIN IMMEDIATE")
        dispatch = db.execute("SELECT 1 FROM dispatches WHERE task=? AND id=?", (task_id, call_id)).fetchone()
        lease = db.execute("SELECT model,status FROM leases WHERE task=? AND id=?", (task_id, call_id)).fetchone()
        if not dispatch or not lease or lease[0] != model or lease[1] not in {"reserved", "settled"}:
            raise ValueError("terminal receipt has no matching dispatch and lease")
        previous = db.execute("SELECT payload,checksum FROM terminal_receipts WHERE task=? AND id=?", (task_id, call_id)).fetchone()
        if previous and previous != (payload, checksum):
            raise ValueError("conflicting terminal receipt")
        db.execute("INSERT OR IGNORE INTO terminal_receipts VALUES (?,?,?,?)", (task_id, call_id, payload, checksum))


def recover_terminal(ledger, task_id, call_id, *, settle=True):
    if type(settle) is not bool:
        raise ValueError("settle must be boolean")
    if not ledger.exists():
        return None
    with connection(ledger.resolve().as_uri() + "?mode=ro", uri=True) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='terminal_receipts'").fetchone():
            return None
        saved = db.execute("SELECT payload,checksum FROM terminal_receipts WHERE task=? AND id=?", (task_id, call_id)).fetchone()
        if saved is None:
            return None
        payload, checksum = saved
        if hashlib.sha256(payload.encode()).hexdigest() != checksum:
            raise ValueError("terminal receipt integrity check failed")
        row = json.loads(payload)
        if type(row.get("schema_version")) is not int or row["schema_version"] not in {1, 2} or row.get("task_id") != task_id or row.get("call_id") != call_id:
            raise ValueError("terminal receipt identity mismatch")
        if not db.execute("SELECT 1 FROM dispatches WHERE task=? AND id=?", (task_id, call_id)).fetchone():
            raise ValueError("terminal receipt dispatch missing")
        lease = db.execute("SELECT model FROM leases WHERE task=? AND id=?", (task_id, call_id)).fetchone()
        if not lease or lease[0] != row.get("model"):
            raise ValueError("terminal receipt model mismatch")
    contract = None
    if row["schema_version"] == 2:
        contract = row.get("rate_snapshot")
        if not isinstance(contract, dict):
            raise ValueError("terminal receipt rate snapshot missing")
    normalized = normalize_receipt({"call_id": call_id, "actual_model": row["model"], "usage": row["usage"],
                                    "rate_contract": contract})
    if row["schema_version"] == 2 and normalized["rate_fingerprint"] != row.get("rate_fingerprint"):
        raise ValueError("terminal receipt rate fingerprint mismatch")
    if normalized["credits"] is None or normalized["credits"] != row["estimated_credits"] or row["cost_basis"] != "token_rate_estimate":
        raise ValueError("terminal receipt rates or counters differ; manual investigation required")
    if not settle:
        return row
    accounting = budget_action({"action": "settle", "task_id": task_id, "lease_id": call_id,
                                "actual_model": row["model"], "actual_credits": row["estimated_credits"],
                                "cost_basis": "token_rate_estimate"}, ledger)
    return {**row, "budget": accounting}
