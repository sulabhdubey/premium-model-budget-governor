"""Read-only setup diagnostics. Never export raw host output or credentials."""
from __future__ import annotations

from importlib import metadata
import os
import re
import shutil
import subprocess
import sys

from . import __version__


def _probe(command: list[str]) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=10,
                              shell=False, **({"creationflags": subprocess.CREATE_NO_WINDOW}
                                              if os.name == "nt" else {}))
    except (OSError, subprocess.TimeoutExpired):
        return None


def diagnose(*, offline: bool = False) -> dict:
    executable = shutil.which("codex.exe") or shutil.which("codex")
    version, auth = None, "not_checked" if offline else "missing"
    if executable and not offline:
        probe = _probe([executable, "--version"])
        match = re.search(r"(?m)^codex(?:-cli)? (\d+\.\d+\.\d+(?:[-+][\w.-]+)?)\s*$",
                          probe.stdout) if probe and probe.returncode == 0 else None
        version = match.group(1) if match else None
        probe = _probe([executable, "login", "status"])
        auth = "unknown" if probe is None else "available" if probe.returncode == 0 else "unavailable"
    try:
        mcp_version = metadata.version("mcp")
    except metadata.PackageNotFoundError:
        mcp_version = None
    python_ok = sys.version_info >= (3, 10)
    ready = python_ok and bool(version) and auth == "available"
    return {
        "schema_version": 1, "governor_version": __version__,
        "python": {"version": ".".join(map(str, sys.version_info[:3])), "supported": python_ok},
        "codex": {"found": bool(executable), "version": version},
        "authentication": {"status": auth, "source": "codex_login_status" if executable and not offline else "not_checked"},
        "mcp": {"installed": mcp_version is not None, "version": mcp_version,
                "required_for_planning": False, "runtime_verified": False},
        "offline_planning": "ready" if python_ok else "needs_attention",
        "model_execution": "not_checked" if offline else "preflight_ready" if ready else "needs_attention",
        "model_access_verified": False, "model_calls_started": 0,
        "next_steps": ([] if ready or offline else [
            "Install or update the official Codex CLI and make codex available on PATH.",
            "Run codex login in your own terminal, then rerun pm-bg doctor.",
        ]) + ([] if mcp_version else ["MCP is optional. Use the installer's --mcp option to include it."]),
        "limits": ["Login status does not verify model access, account capacity, or host compatibility.",
                   "No settings changed. No model turn started. Raw host output is not included."],
    }


def format_diagnosis(result: dict) -> str:
    return "\n".join([
        f"Premium Model Budget Governor {result['governor_version']}",
        f"Offline planning: {result['offline_planning']}",
        f"Model execution: {result['model_execution'].replace('_', ' ')}",
        f"Codex: {result['codex']['version'] or ('found; version not verified' if result['codex']['found'] else 'not found')}",
        f"Authentication: {result['authentication']['status'].replace('_', ' ')}",
        f"Optional MCP: {'installed; runtime not checked' if result['mcp']['installed'] else 'not installed'}",
        *result["next_steps"], *result["limits"],
    ])
