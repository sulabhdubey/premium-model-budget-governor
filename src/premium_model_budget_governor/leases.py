"""Atomic local reservations for hosts that consult the governor before calls."""

from __future__ import annotations

from pathlib import Path
import sqlite3

from .workflow import number
from .cost import _token


def budget_action(packet: dict, ledger: Path) -> dict:
    action = packet.get("action")
    if action not in {"open", "reserve", "settle", "cancel", "status"}:
        raise ValueError("unknown budget action")
    task = packet.get("task_id")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("task_id is required")
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(ledger, timeout=15) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, ceiling REAL NOT NULL, reserve REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS leases (
                task TEXT NOT NULL, id TEXT NOT NULL, model TEXT NOT NULL,
                estimate REAL NOT NULL, actual REAL, status TEXT NOT NULL,
                PRIMARY KEY(task, id));
        """)
        db.execute("BEGIN IMMEDIATE")
        if "cost_basis" not in {row[1] for row in db.execute("PRAGMA table_info(leases)")}:
            db.execute("ALTER TABLE leases ADD COLUMN cost_basis TEXT NOT NULL DEFAULT 'caller_reported'")
        if "max_pending" not in {row[1] for row in db.execute("PRAGMA table_info(tasks)")}:
            db.execute("ALTER TABLE tasks ADD COLUMN max_pending INTEGER NOT NULL DEFAULT 1")
        if action == "open":
            ceiling = number(packet.get("budget_credits"), "budget_credits")
            reserve = number(packet.get("reserve_credits", 0), "reserve_credits")
            max_pending = _token(packet.get("max_pending_leases", 1), "max_pending_leases")
            if max_pending < 1:
                raise ValueError("max_pending_leases must be positive")
            if reserve > ceiling:
                raise ValueError("reserve exceeds budget")
            existing = db.execute("SELECT ceiling,reserve,max_pending FROM tasks WHERE id=?", (task,)).fetchone()
            if existing and existing != (ceiling, reserve, max_pending):
                raise ValueError("task budget already exists with different limits")
            db.execute("INSERT OR IGNORE INTO tasks (id,ceiling,reserve,max_pending) VALUES (?,?,?,?)", (task, ceiling, reserve, max_pending))
        limits = db.execute("SELECT ceiling,reserve,max_pending FROM tasks WHERE id=?", (task,)).fetchone()
        if limits is None:
            raise ValueError("open the task budget first")
        if action in {"reserve", "settle", "cancel"}:
            lease = packet.get("lease_id")
            if not isinstance(lease, str) or not lease.strip():
                raise ValueError("lease_id is required")
            existing = db.execute("SELECT model,estimate,actual,status,cost_basis FROM leases WHERE task=? AND id=?", (task, lease)).fetchone()
            if action == "reserve":
                estimate = number(packet.get("estimated_credits"), "estimated_credits")
                model = packet.get("model")
                if estimate <= 0 or not isinstance(model, str) or not model:
                    raise ValueError("positive estimate and model required")
                if existing:
                    if existing[:2] != (model, estimate) or existing[3] != "reserved":
                        raise ValueError("lease ID already used; use a new ID for a new call")
                else:
                    pending = db.execute("SELECT COUNT(*) FROM leases WHERE task=? AND status='reserved'", (task,)).fetchone()[0]
                    if pending >= limits[2]:
                        raise ValueError("pending call limit reached; reconcile before dispatching another call")
                    used = db.execute("SELECT COALESCE(SUM(CASE WHEN status='settled' THEN actual WHEN status='reserved' THEN estimate ELSE 0 END),0) FROM leases WHERE task=?", (task,)).fetchone()[0]
                    if used + estimate + limits[1] > limits[0] + 1e-9:
                        raise ValueError("whole task budget exhausted; call not reserved")
                    db.execute("INSERT INTO leases (task,id,model,estimate,actual,status) VALUES (?,?,?,?,NULL,'reserved')", (task, lease, model, estimate))
            else:
                if existing is None:
                    raise ValueError("lease does not exist")
                if action == "cancel":
                    if packet.get("confirmed_not_executed") is not True:
                        raise ValueError("only confirmed unexecuted calls may release a reservation")
                    if existing[3] == "settled":
                        raise ValueError("settled spend cannot be canceled")
                    db.execute("UPDATE leases SET status='canceled' WHERE task=? AND id=?", (task, lease))
                else:
                    actual = number(packet.get("actual_credits"), "actual_credits")
                    basis = packet.get("cost_basis", "caller_reported")
                    if basis not in {"caller_reported", "token_rate_estimate", "host_billed"}:
                        raise ValueError("unsupported settlement cost_basis")
                    model = packet.get("actual_model")
                    if not isinstance(model, str) or not model:
                        raise ValueError("actual_model from host receipt is required")
                    if existing[3] == "canceled":
                        raise ValueError("cannot settle a canceled lease")
                    if existing[3] == "settled" and (existing[:3:2] != (model, actual) or existing[4] != basis):
                        raise ValueError("settlement receipt conflicts with recorded spend")
                    db.execute("UPDATE leases SET model=?,actual=?,cost_basis=?,status='settled' WHERE task=? AND id=?", (model, actual, basis, task, lease))
        rows = db.execute("SELECT id,model,estimate,actual,status,cost_basis FROM leases WHERE task=? ORDER BY id", (task,)).fetchall()
        spent = sum(row[3] for row in rows if row[4] == "settled")
        reserved = sum(row[2] for row in rows if row[4] == "reserved")
        return {"task_id": task, "budget_credits": limits[0], "spent_credits": spent,
                "max_pending_leases": limits[2],
                "reserved_credits": reserved, "contingency_credits": limits[1],
                "available_credits": max(0, limits[0] - limits[1] - spent - reserved),
                "over_budget": spent + reserved + limits[1] > limits[0] + 1e-9,
                "astra_receipts": sum(row[1] == "gpt-6-astra" and row[4] == "settled" for row in rows),
                "receipt_source": "caller_reported; host must supply trustworthy actual usage",
                "leases": [dict(zip(("id", "model", "estimate", "actual", "status", "cost_basis"), row)) for row in rows]}
