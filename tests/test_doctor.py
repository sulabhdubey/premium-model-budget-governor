import json
import subprocess
from importlib import metadata

from premium_model_budget_governor.cli import main


def test_doctor_plain_without_codex(monkeypatch, capsys):
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert main(["doctor"]) == 1
    output = capsys.readouterr().out
    assert "Offline planning: ready" in output
    assert "Model execution: needs attention" in output
    assert "codex login" in output


def test_doctor_json_sanitizes_auth_and_version(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr("shutil.which", lambda name: "/private/path/codex")

    def run(args, **kwargs):
        calls.append(args[1:])
        assert kwargs["timeout"] <= 10
        assert kwargs["shell"] is False
        return subprocess.CompletedProcess(args, 0, "codex-cli 0.153.4\nSECRET_TOKEN", "someone@example.com")

    monkeypatch.setattr(subprocess, "run", run)
    assert main(["doctor", "--json"]) == 0
    output = capsys.readouterr().out
    assert "SECRET_TOKEN" not in output
    assert "someone@" not in output
    assert "/private" not in output
    result = json.loads(output)["result"]
    assert result["codex"]["version"] == "0.153.4"
    assert result["authentication"]["status"] == "available"
    assert result["model_execution"] == "preflight_ready"
    assert result["model_access_verified"] is False
    assert calls == [["--version"], ["login", "status"]]


def test_doctor_unknown_auth_is_not_ready(monkeypatch, capsys):
    monkeypatch.setattr("shutil.which", lambda name: "codex")

    def run(args, **kwargs):
        raise subprocess.TimeoutExpired(args, 10, output="secret")

    monkeypatch.setattr(subprocess, "run", run)
    assert main(["doctor", "--json"]) == 1
    result = json.loads(capsys.readouterr().out)["result"]
    assert result["authentication"]["status"] == "unknown"
    assert result["model_execution"] == "needs_attention"


def test_doctor_offline_never_invokes_host(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("offline doctor must not run a subprocess")

    monkeypatch.setattr(subprocess, "run", forbidden)
    assert main(["doctor", "--offline", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)["result"]
    assert result["authentication"]["status"] == "not_checked"
    assert result["offline_planning"] == "ready"


def test_doctor_missing_optional_mcp_does_not_break_planning(monkeypatch, capsys):
    def missing(name):
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "version", missing)
    assert main(["doctor", "--offline", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)["result"]
    assert result["mcp"]["installed"] is False
    assert result["mcp"]["runtime_verified"] is False


def test_doctor_failed_login_does_not_export_error(monkeypatch, capsys):
    monkeypatch.setattr("shutil.which", lambda name: "codex")
    monkeypatch.setattr(subprocess, "run", lambda args, **kw:
                        subprocess.CompletedProcess(args, 1, "PRIVATE", "PRIVATE"))
    assert main(["doctor", "--json"]) == 1
    output = capsys.readouterr().out
    assert "PRIVATE" not in output
    assert json.loads(output)["result"]["authentication"]["status"] == "unavailable"
