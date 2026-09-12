"""Opt-in, serial Codex CLI execution. Never bypass user config, rules or sandbox."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import signal
import sqlite3
from .database import connection
import time

from .cost import RATES, _token
from .experiments import normalize_receipt
from .accounting import estimate_observed
from .telemetry import normalize_counters
from .receipt_journal import record_terminal
from .leases import budget_action


def _run_process(command: list[str], *, prompt: str, timeout: int):
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding="utf-8", errors="replace", shell=False, **options) as process:
        try:
            out, err = process.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               capture_output=True, shell=False)
            else:
                os.killpg(process.pid, signal.SIGKILL)
            process.kill()
            process.communicate()
            raise
        return subprocess.CompletedProcess(command, process.returncode, out, err)


def _claim_dispatch(ledger: Path, task_id: str, call_id: str) -> None:
    with connection(ledger, timeout=15) as db:
        db.execute("CREATE TABLE IF NOT EXISTS dispatches (task TEXT NOT NULL, id TEXT NOT NULL, PRIMARY KEY(task,id))")
        db.execute("BEGIN IMMEDIATE")
        lease = db.execute("SELECT status,expires_at FROM leases WHERE task=? AND id=?", (task_id, call_id)).fetchone()
        if lease is None or lease[0] != "reserved":
            raise ValueError("a pending reservation is required")
        if lease[1] is not None and lease[1] <= time.time():
            raise ValueError("reservation expired; funds remain reserved pending reconciliation")
        try:
            db.execute("INSERT INTO dispatches VALUES (?,?)", (task_id, call_id))
        except sqlite3.IntegrityError as exc:
            raise ValueError("call ID was already dispatched; reconcile it instead of replaying") from exc


def codex_command(executable: str, root: Path, model: str, effort: str, images: list[Path] | None = None) -> list[str]:
    if not isinstance(model, str) or not isinstance(effort, str) or model not in RATES or effort not in {"low", "medium", "high"}:
        raise ValueError("unsupported model or reasoning effort")
    attachments = []
    for path in images or []:
        path = path.resolve(strict=True)
        if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"} or path.stat().st_size > 20_000_000:
            raise ValueError("images must be explicit PNG/JPEG/WebP files up to 20 MB")
        attachments.extend(["--image", str(path)])
    return [executable, "-a", "never", "exec", "--sandbox", "read-only", "--ephemeral",
            "--json", "--color", "never", "--model", model, "-c", f'model_reasoning_effort="{effort}"',
            "--cd", str(root.resolve()), "--skip-git-repo-check", *attachments, "-"]


def parse_events(stdout: str) -> dict:
    usage, answer, turns, failed = {"input_tokens": 0, "cached_tokens": 0, "output_tokens": 0}, "", 0, False
    assumptions = set()
    for line in stdout.splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError("Codex event must be an object")
        if event.get("type") == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message":
                answer = item.get("text", "")
        if event.get("type") in {"turn.failed", "error"}:
            failed = True
        if event.get("type") == "turn.completed":
            raw = event.get("usage", {})
            counts = normalize_counters(raw)
            assumptions.update(counts["counter_assumptions"])
            incoming, cached, outgoing = (counts[k] for k in ("input_tokens", "cached_tokens", "output_tokens"))
            if counts["cache_write_tokens"]:
                usage["cache_write_tokens"] = usage.get("cache_write_tokens", 0) + counts["cache_write_tokens"]
            for name, n in [("input_tokens", incoming), ("cached_tokens", cached), ("output_tokens", outgoing)]:
                usage[name] += n
            turns += 1
    return {"usage": usage if turns else None, "answer": answer, "completed_turns": turns, "failed": failed,
            "counter_assumptions": sorted(assumptions)}


def execute_codex(*, prompt: str, root: Path, model: str, effort: str, ledger: Path,
                  task_id: str, call_id: str, estimated_credits: float, timeout_seconds: int = 300,
                  images: list[Path] | None = None, rate_contract=None) -> dict:
    """Explicit execution API. Caller opens a task budget and authorizes each call.

    Answers are returned to the caller but not written to the ledger. Partial or
    ambiguous usage retains its reservation. This is not a provider token cap.
    """
    executable = shutil.which("codex.exe") or shutil.which("codex")
    if executable is None:
        raise ValueError("Codex CLI is not installed")
    command = codex_command(executable, root, model, effort, images)
    if not root.is_dir() or not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("existing root and non-empty prompt required")
    timeout = _token(timeout_seconds, "timeout_seconds")
    if not 1 <= timeout <= 1800:
        raise ValueError("timeout_seconds must be between 1 and 1800")
    rate_check = estimate_observed(model, {"input_tokens": 0, "output_tokens": 0}, contract=rate_contract)
    if rate_check["estimated_credits"] is None:
        raise ValueError("rate contract must match requested model and default tier")
    rate_snapshot = rate_check["rate_snapshot"]
    base = {"task_id": task_id, "lease_id": call_id}
    budget_action({**base, "action": "reserve", "model": model, "estimated_credits": estimated_credits}, ledger)
    _claim_dispatch(ledger, task_id, call_id)
    start = time.monotonic()
    try:
        completed = _run_process(command, prompt=prompt, timeout=timeout)
    except OSError:
        # An I/O error may occur after spawn; it does not prove the call was free.
        return {"status": "unknown_usage", "requested_model": model,
                "reservation_retained": True, "error": "host I/O failure; reconcile before retry"}
    except subprocess.TimeoutExpired:
        return {"status": "unknown_usage", "requested_model": model,
                "reservation_retained": True, "error": "timeout; reconcile before retry"}
    try:
        parsed = parse_events(completed.stdout)
    except (ValueError, TypeError, AttributeError):
        return {"status": "unknown_usage", "requested_model": model, "reservation_retained": True,
                "error": "unrecognized event format; reconcile before retry"}
    result = {**parsed, "requested_model": model, "elapsed_seconds": round(time.monotonic() - start, 3),
              "status": "completed" if completed.returncode == 0 and not parsed["failed"] else "failed",
              "model_identity_source": "CLI requested model; provider identity not exposed in JSON events",
              "host": "codex_cli_inherited_config_read_only", "call_id": call_id}
    if parsed["usage"] is not None and completed.returncode == 0 and not parsed["failed"]:
        projection = normalize_receipt({"call_id": call_id, "actual_model": model, "usage": parsed["usage"],
                                        "rate_contract": rate_snapshot})
        result["estimated_credits"] = projection["credits"]
        result["rate_snapshot"] = rate_snapshot
        result["rate_fingerprint"] = rate_check["rate_fingerprint"]
        if projection["credits"] is None:
            result.update(status="unknown_usage", reservation_retained=True,
                          cost_status=projection["cost_status"], cost_basis="unknown")
            return result
        result["cost_basis"] = ("requested_model_contract_rate_projection" if rate_contract is not None
                                else "requested_model_standard_rate_projection")
        try:
            record_terminal(ledger, task_id=task_id, call_id=call_id, model=model,
                            thread_id=None, turn_id=None, usage=parsed["usage"],
                            rate_contract=rate_snapshot, host_source="codex_cli")
            result["budget"] = budget_action({**base, "action": "settle", "actual_model": model,
                "actual_credits": projection["credits"], "cost_basis": "token_rate_estimate"}, ledger)
        except (ValueError, OSError, sqlite3.Error):
            result.update(status="unknown_usage", reservation_retained=True,
                          error="Local receipt or settlement incomplete; recover evidence before retry")
    else:
        result["reservation_retained"] = True
        result["status"] = "unknown_usage" if parsed["usage"] is None else "failed"
    # stderr can contain local paths or configuration details; never persist it.
    return result
