"""Opt-in Codex App Server client. Stdio only; no global configuration changes."""

from collections import deque
import json
import os
from pathlib import Path
from queue import Queue, Empty
import shutil
import signal
import subprocess
from threading import Thread
import time

from .cost import RATES, _token
from .experiments import normalize_receipt
from .host import _claim_dispatch
from .receipt_journal import record_terminal
from .leases import budget_action
from . import __version__


class ExecutionCancelled(Exception):
    """Local stop request; never implies a provider-side billing refund."""


class AppServer:
    def __init__(self, root: Path, timeout: int = 60, *, cancel_event=None):
        self.root = root.resolve(strict=True)
        self.timeout = timeout
        self.pending = deque()
        self.queue = Queue()
        self.sequence = 0
        self.process = None
        self.cancel_event = cancel_event

    def __enter__(self):
        executable = shutil.which("codex.exe") or shutil.which("codex")
        if not executable:
            raise ValueError("Codex CLI is not installed")
        options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
        self.process = subprocess.Popen([executable, "app-server", "--listen", "stdio://"],
            cwd=self.root, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding="utf-8", shell=False, **options)
        self.reader = Thread(target=self._read, daemon=True)
        self.reader.start()
        try:
            self.request("initialize", {"clientInfo": {"name": "pm_bg", "version": __version__}})
            self.send({"method": "initialized", "params": {}})
        except Exception:
            self.__exit__(None, None, None)
            raise
        return self

    def _read(self):
        try:
            for line in self.process.stdout:
                self.queue.put(json.loads(line))
        except (ValueError, OSError):
            self.queue.put({"_transport_error": True})
        finally:
            self.queue.put(None)

    def send(self, message):
        self._check_cancel()
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def _check_cancel(self):
        if self.cancel_event is not None and self.cancel_event.is_set():
            raise ExecutionCancelled()

    def receive(self, timeout=None):
        deadline = time.monotonic() + (self.timeout if timeout is None else max(.001, timeout))
        while True:
            self._check_cancel()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("App Server response timed out")
            try:
                message = self.queue.get(timeout=min(.2, remaining))
                break
            except Empty:
                continue
        if not isinstance(message, dict) or message.get("_transport_error"):
            raise ValueError("App Server transport ended or returned malformed data")
        if "method" in message and "id" in message:
            # Do not approve tools, permissions, credentials, or user questions unattended.
            self.send({"id": message["id"], "error": {"code": -32601, "message": "Governor client does not authorize interactive requests"}})
            raise ValueError("host requested unsupported interactive approval")
        return message

    def request(self, method, params):
        self.sequence += 1
        id = self.sequence
        self.send({"id": id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError("App Server response timed out")
            response = self.receive(deadline - time.monotonic())
            if response.get("id") == id:
                if "error" in response:
                    raise ValueError(f"App Server rejected {method}; details withheld")
                if not isinstance(response.get("result"), dict):
                    raise ValueError("invalid App Server result")
                return response["result"]
            self.pending.append(response)

    def event(self, timeout):
        self._check_cancel()
        return self.pending.popleft() if self.pending else self.receive(timeout)

    def __exit__(self, *args):
        if self.process:
            if self.process.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(self.process.pid), "/T", "/F"], capture_output=True, timeout=15)
                else:
                    try:
                        os.killpg(self.process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                self.process.kill()
            self.process.wait(timeout=15)
            self.reader.join(timeout=2)
            self.process.stdin.close()
            self.process.stdout.close()


def catalog(client):
    rows, cursor, seen = [], None, set()
    for _ in range(20):
        result = client.request("model/list", {"cursor": cursor, "limit": 100})
        if not isinstance(result.get("data"), list):
            raise ValueError("invalid model catalog")
        rows.extend(result["data"])
        cursor = result.get("nextCursor")
        if not cursor:
            return rows
        if not isinstance(cursor, str) or cursor in seen:
            raise ValueError("invalid catalog pagination")
        seen.add(cursor)
    raise ValueError("catalog pagination limit exceeded")


def probe_app_server(root: Path) -> dict:
    with AppServer(root) as client:
        models = catalog(client)
        hook_result = client.request("hooks/list", {"cwds": [str(root.resolve())]})
        return {"connected": True, "model_turns_started": 0,
                "models": [{"model": row["model"], "input_modalities": row.get("inputModalities", []),
                            "reasoning_efforts": [v["reasoningEffort"] for v in row.get("supportedReasoningEfforts", [])]}
                           for row in models if row.get("model") in RATES],
                "hooks_list_supported": True,
                "configured_hook_count": sum(len(r["hooks"]) for r in hook_result["data"]),
                "hook_error_count": sum(len(r["errors"]) for r in hook_result["data"]),
                "hook_execution_verified": False,
                "limitations": "Catalog availability is not successful execution or provider model attestation. No hooks enabled."}


def parse_usage(raw):
    incoming = _token(raw.get("inputTokens"), "inputTokens")
    cached = _token(raw.get("cachedInputTokens"), "cachedInputTokens")
    output = _token(raw.get("outputTokens"), "outputTokens")
    reasoning = _token(raw.get("reasoningOutputTokens", 0), "reasoningOutputTokens")
    writes = _token(raw.get("cacheWriteInputTokens", 0), "cacheWriteInputTokens")
    if cached > incoming or reasoning > output or writes:
        raise ValueError("invalid subsets or unsupported cache-write pricing")
    if _token(raw.get("totalTokens"), "totalTokens") != incoming + output:
        raise ValueError("inconsistent token totals")
    return {"input_tokens": incoming, "cached_tokens": cached, "output_tokens": output}


def require_hooks(client, root: Path, hashes):
    """Admission check only: native hooks may still fail after turn dispatch."""
    if not isinstance(hashes, list) or any(not isinstance(h, str) or len(h) != 71 or not h.startswith("sha256:") or any(c not in "0123456789abcdef" for c in h[7:]) for h in hashes):
        raise ValueError("required_hook_hashes must contain sha256 hashes")
    if len(hashes) != len(set(hashes)):
        raise ValueError("duplicate required hook hash")
    if not hashes:
        return
    inventory = client.request("hooks/list", {"cwds": [str(root)]})
    if any(row.get("errors") for row in inventory["data"]):
        raise ValueError("hook inventory contains errors")
    ready = {h["currentHash"] for row in inventory["data"] for h in row["hooks"]
             if h.get("enabled") is True and h.get("trustStatus") == "trusted"}
    if set(hashes) - ready:
        raise ValueError("required hook is missing, disabled or not trusted")


def execute_app_server(packet: dict, ledger: Path, *, cancel_event=None) -> dict:
    if cancel_event is not None and cancel_event.is_set():
        return {"status": "canceled_before_dispatch", "stop_requested": True}
    try:
        return _execute_app_server(packet, ledger, cancel_event=cancel_event)
    except ExecutionCancelled:
        # The dispatch region catches cancellation separately and retains its reservation.
        return {"status": "canceled_before_dispatch", "stop_requested": True}


def _execute_app_server(packet: dict, ledger: Path, *, cancel_event=None) -> dict:
    for key in ("root", "prompt", "model", "task_id", "call_id"):
        if not isinstance(packet.get(key), str) or not packet[key].strip():
            raise ValueError(f"{key} is required")
    if packet.get("explicit_approval") is not True:
        raise ValueError("explicit_approval required for App Server execution")
    model, effort = packet["model"], packet.get("effort", "low")
    if model not in RATES or not isinstance(effort, str):
        raise ValueError("unsupported model or effort")
    root = Path(packet["root"]).resolve(strict=True)
    timeout = _token(packet.get("timeout_seconds", 300), "timeout_seconds")
    if not 1 <= timeout <= 1800:
        raise ValueError("timeout_seconds must be 1-1800")
    inputs = [{"type": "text", "text": packet["prompt"]}]
    images = packet.get("images", [])
    if not isinstance(images, list) or any(not isinstance(p, str) or not p for p in images):
        raise ValueError("images must be explicit paths")
    for value in images:
        path = Path(value).resolve(strict=True)
        if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"} or path.stat().st_size > 20_000_000:
            raise ValueError("unsupported image path or size")
        inputs.append({"type": "localImage", "path": str(path)})
    base = {"task_id": packet["task_id"], "lease_id": packet["call_id"]}
    with AppServer(root, timeout, **({"cancel_event": cancel_event} if cancel_event is not None else {})) as client:
        available = next((v for v in catalog(client) if v.get("model") == model), None)
        if available is None or effort not in [v["reasoningEffort"] for v in available.get("supportedReasoningEfforts", [])]:
            raise ValueError("model or reasoning effort unavailable on this host")
        if images and "image" not in available.get("inputModalities", []):
            raise ValueError("image capability unavailable on this host")
        require_hooks(client, root, packet.get("required_hook_hashes", []))
        budget_action({**base, "action": "reserve", "model": model,
                       "estimated_credits": packet.get("estimated_credits"), "ttl_seconds": timeout}, ledger)
        _claim_dispatch(ledger, packet["task_id"], packet["call_id"])
        started = time.monotonic()
        try:
            thread = client.request("thread/start", {"cwd": str(root), "model": model,
                "approvalPolicy": "never", "sandbox": "read-only", "ephemeral": True, "serviceTier": "default"})
            if thread.get("model") != model:
                raise ValueError("host model configuration differs from requested model")
            thread_id = thread["thread"]["id"]
            turn = client.request("turn/start", {"threadId": thread_id, "input": inputs,
                "model": model, "effort": effort, "serviceTierForTurn": "default"})
            turn_id = turn["turn"]["id"]
            usage, answer = None, ""
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                message = client.event(deadline - time.monotonic())
                params = message.get("params", {})
                if params.get("threadId") != thread_id or params.get("turnId", turn_id) != turn_id:
                    continue
                if message.get("method") == "hook/completed" and params.get("run", {}).get("status") in {"failed", "blocked"}:
                    raise ValueError("native hook failed or blocked; retain unknown spend")
                if message.get("method") == "thread/tokenUsage/updated":
                    current = parse_usage(params["tokenUsage"]["total"])
                    if usage and any(current[k] < usage[k] for k in usage):
                        raise ValueError("usage counters decreased")
                    usage = current
                if message.get("method") == "item/completed" and params.get("item", {}).get("type") == "agentMessage":
                    answer = params["item"]["text"]
                if message.get("method") == "turn/completed":
                    if params.get("turn", {}).get("id") != turn_id:
                        continue
                    if params["turn"]["status"] != "completed" or usage is None:
                        raise ValueError("incomplete turn or missing usage")
                    credits = normalize_receipt({"call_id": packet["call_id"], "actual_model": model, "usage": usage})["credits"]
                    record_terminal(ledger, task_id=packet["task_id"], call_id=packet["call_id"],
                                    model=model, thread_id=thread_id, turn_id=turn_id, usage=usage)
                    status = budget_action({**base, "action": "settle", "actual_model": model,
                        "actual_credits": credits, "cost_basis": "token_rate_estimate"}, ledger)
                    return {"status": "completed", "requested_model": model, "host_configured_model": thread["model"],
                            "model_identity_source": "App Server configuration, not provider attestation",
                            "call_id": packet["call_id"], "usage": usage, "answer": answer,
                            "estimated_credits": credits, "cost_basis": "token_rate_estimate",
                            "elapsed_seconds": round(time.monotonic()-started, 3), "budget": status}
            raise TimeoutError("turn timed out")
        except ExecutionCancelled:
            return {"status": "unknown_usage", "call_id": packet["call_id"],
                    "reservation_retained": True, "stop_requested": True,
                    "error": "Local execution stopped; reconcile any provider usage before retry"}
        except (ValueError, OSError, TimeoutError, KeyError, TypeError):
            return {"status": "unknown_usage", "call_id": packet["call_id"], "reservation_retained": True,
                    "error": "Incomplete or incompatible host execution; reconcile before retry"}
