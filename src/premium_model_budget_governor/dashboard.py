"""Prompt-free, read-only ledger export. No listener, credentials, or remote assets."""

from datetime import datetime, timezone
from html import escape
from pathlib import Path
import sqlite3
import time


def export_dashboard(ledger: Path, output: Path) -> dict:
    source = ledger.resolve(strict=True)
    if output.resolve() == source:
        raise ValueError("dashboard cannot overwrite the ledger")
    with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as db:
        db.execute("BEGIN")
        tasks = db.execute("SELECT id,ceiling,reserve FROM tasks ORDER BY id").fetchall()
        columns = {r[1] for r in db.execute("PRAGMA table_info(leases)")}
        expiry = "expires_at" if "expires_at" in columns else "NULL"
        basis = "cost_basis" if "cost_basis" in columns else "'caller_reported'"
        leases = db.execute(f"SELECT task,model,estimate,actual,status,{basis},{expiry} FROM leases").fetchall()
    rows, spent, reserved, expired = [], 0., 0., 0
    for index, (task, ceiling, reserve) in enumerate(tasks, 1):
        items = [r for r in leases if r[0] == task]
        actual = sum(r[3] for r in items if r[4] == "settled")
        pending = sum(r[2] for r in items if r[4] == "reserved")
        overdue = sum(r[4] == "reserved" and r[6] is not None and r[6] <= time.time() for r in items)
        spent += actual
        reserved += pending
        expired += overdue
        models = ", ".join(sorted({r[1] for r in items})) or "None"
        bases = ", ".join(sorted({r[5] for r in items if r[4] == "settled"})) or "No receipts"
        state = "Over budget" if actual + pending + reserve > ceiling + 1e-9 else "Reconcile expired" if overdue else "Pending" if pending else "Within budget"
        cells = [f"Task {index}", models, f"{ceiling:.4f}", f"{actual:.4f}", f"{pending:.4f}", f"{max(0, ceiling-reserve-actual-pending):.4f}", bases, state]
        rows.append("<tr>" + "".join("<td>" + escape(v) + "</td>" for v in cells) + "</tr>")
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    document = """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Governor Ledger</title><style>
*{box-sizing:border-box}body{margin:0;background:#f5f7f8;color:#172328;font:15px system-ui;letter-spacing:0}main{max-width:1280px;margin:auto;padding:32px 20px}header{border-bottom:3px solid #167d74;padding-bottom:20px}h1{font-size:30px;margin:4px 0}h2{font-size:20px}.metrics{display:flex;flex-wrap:wrap;gap:32px;padding:24px 0;border-bottom:1px solid #c5d1d5}.metrics strong{display:block;font-size:26px;color:#125f59}.table{overflow:auto;border:1px solid #c5d1d5}table{border-collapse:collapse;width:100%;background:white}th,td{padding:12px;text-align:left;border-bottom:1px solid #dce3e5}th{background:#e8eeee;white-space:nowrap}td{min-width:100px;overflow-wrap:anywhere}p{max-width:85ch;line-height:1.6}.notice{border-left:4px solid #b88600;padding-left:12px}footer{margin-top:24px;color:#425960}@media(max-width:480px){main{padding:20px 12px}h1{font-size:25px}.metrics{gap:20px}}
</style><main><header><div>PREMIUM MODEL BUDGET GOVERNOR</div><h1>Ledger Snapshot</h1><p>Generated TIMESTAMP</p></header>
<section class="metrics" aria-label="Ledger totals"><div>Recorded credits<strong>SPENT</strong></div><div>Reserved credits<strong>RESERVED</strong></div><div>Expired reservations<strong>EXPIRED</strong></div><div>Tasks<strong>TASKCOUNT</strong></div></section>
<h2>Task Budgets</h2><div class="table" tabindex="0" role="region" aria-label="Task budgets"><table><thead><tr><th>Task</th><th>Models</th><th>Ceiling</th><th>Recorded</th><th>Reserved</th><th>Available</th><th>Cost basis</th><th>Status</th></tr></thead><tbody>ROWS</tbody></table></div>
<p class="notice">Credits use the basis shown per task. Totals may mix estimates and billed receipts; they are not an account bill. Weekly capacity and saved credits are unknown. Expired reservations still hold funds until reconciled.</p>
<footer>Local snapshot, not a live monitor. Task identifiers and prompts are omitted. Model labels are receipt claims, not independent host attestation.</footer></main></html>"""
    for key, value in {"TIMESTAMP": escape(timestamp), "SPENT": f"{spent:.4f}", "RESERVED": f"{reserved:.4f}", "EXPIRED": str(expired), "TASKCOUNT": str(len(tasks))}.items():
        document = document.replace(key, value)
    document = document.replace("ROWS", "".join(rows) or '<tr><td colspan="8">No tasks</td></tr>')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    return {"output": str(output), "tasks": len(tasks), "read_only": True, "identifiers_exported": False}
