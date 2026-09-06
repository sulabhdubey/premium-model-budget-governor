import json
from pathlib import Path

import pytest

from premium_model_budget_governor.host import codex_command, parse_events


def test_execution_id_cannot_be_replayed(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from premium_model_budget_governor.host import execute_codex
    from premium_model_budget_governor.leases import budget_action
    import premium_model_budget_governor.host as host
    ledger = tmp_path / "ledger.sqlite3"
    budget_action({"action": "open", "task_id": "t", "budget_credits": 100}, ledger)
    monkeypatch.setattr(host.shutil, "which", lambda _: "codex")
    calls = []
    def fake(*a, **kw):
        calls.append(1)
        return SimpleNamespace(returncode=0, stdout='{"type":"turn.started"}')
    monkeypatch.setattr(host, "_run_process", fake)
    args = dict(prompt="test", root=tmp_path, model="gpt-6-astra", effort="low", ledger=ledger,
                task_id="t", call_id="once", estimated_credits=10)
    execute_codex(**args)
    with pytest.raises(ValueError):
        execute_codex(**args)
    assert len(calls) == 1


def test_command_keeps_config_rules_and_sandbox():
    args = codex_command("codex", Path.cwd(), "gpt-6-astra", "low")
    assert args[args.index("--sandbox") + 1] == "read-only"
    assert "--ignore-user-config" not in args
    assert "--ignore-rules" not in args
    assert not any("dangerously" in arg for arg in args)
    assert "--ephemeral" in args


def test_images_are_explicit_and_preserved(tmp_path):
    path = tmp_path / "chart.png"
    path.write_bytes(b"fixture")
    args = codex_command("codex", tmp_path, "gpt-6-astra", "high", [path])
    assert args[args.index("--image") + 1] == str(path.resolve())
    with pytest.raises(FileNotFoundError):
        codex_command("codex", tmp_path, "gpt-6-astra", "high", [tmp_path / "absent.png"])


def test_ambiguous_io_failure_retains_reservation(tmp_path, monkeypatch):
    import premium_model_budget_governor.host as host
    from premium_model_budget_governor.leases import budget_action
    ledger = tmp_path / "ledger.sqlite3"
    budget_action({"action": "open", "task_id": "t", "budget_credits": 100}, ledger)
    monkeypatch.setattr(host.shutil, "which", lambda _: "codex")
    def fail(*args, **kwargs):
        raise OSError("pipe broke after spawn")
    monkeypatch.setattr(host, "_run_process", fail)
    result = host.execute_codex(prompt="test", root=tmp_path, model="gpt-6-astra", effort="low", ledger=ledger, task_id="t", call_id="x", estimated_credits=10)
    assert result["reservation_retained"]
    assert budget_action({"action": "status", "task_id": "t"}, ledger)["reserved_credits"] == 10


def test_event_usage_counts_every_turn_not_last_only():
    events = [
        {"type": "item.completed", "item": {"type": "agent_message", "text": "answer"}},
        {"type": "turn.completed", "usage": {"input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 3}},
        {"type": "turn.completed", "usage": {"input_tokens": 20, "cached_input_tokens": 4, "output_tokens": 5}},
    ]
    result = parse_events("\n".join(json.dumps(e) for e in events))
    assert result["usage"] == {"input_tokens": 30, "cached_tokens": 6, "output_tokens": 8}
    assert result["answer"] == "answer"


def test_missing_or_corrupt_usage_never_becomes_free():
    assert parse_events('{"type":"turn.started"}')["usage"] is None
    with pytest.raises(ValueError):
        parse_events('not json')
    with pytest.raises(ValueError):
        parse_events('{"type":"turn.completed","usage":{"input_tokens":2,"cached_input_tokens":3,"output_tokens":1}}')


def test_no_arbitrary_model_or_reasoning_config_injection():
    with pytest.raises(ValueError):
        codex_command("codex", Path.cwd(), "invalid", "low")
    with pytest.raises(ValueError):
        codex_command("codex", Path.cwd(), "gpt-6-astra", 'low; rm')


def test_timeout_terminates_local_process():
    import subprocess
    import sys
    from premium_model_budget_governor.host import _run_process
    with pytest.raises(subprocess.TimeoutExpired):
        _run_process([sys.executable, "-c", "import time; time.sleep(60)"], prompt="", timeout=1)
