import importlib.util
import json
from pathlib import Path
import subprocess

import pytest


def installer():
    path = Path(__file__).parents[1] / "scripts" / "install_governor.py"
    assert path.is_file(), "guided installer is missing"
    spec = importlib.util.spec_from_file_location("install_governor", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_preview_makes_no_changes(tmp_path, monkeypatch, capsys):
    module = installer()
    target = tmp_path / "runtime with spaces"
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: pytest.fail("preview executed a command"))
    assert module.main(["install", "--directory", str(target)]) == 0
    assert not target.exists()
    assert "--yes" in capsys.readouterr().out


def test_documents_extra_is_explicit_and_not_offline_wheel_mode(tmp_path, monkeypatch, capsys):
    module = installer()
    wheel = tmp_path / "premium_model_budget_governor-test.whl"
    wheel.write_bytes(b"test preview only")
    target = tmp_path / "runtime"
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: pytest.fail("preview executed a command"))
    assert module.main(["install", "--directory", str(target), "--wheel", str(wheel), "--documents"]) == 0
    output = capsys.readouterr().out
    assert "[documents]" in output and "can download" in output
    assert not target.exists()


def test_existing_directory_never_overwritten(tmp_path):
    module = installer()
    (tmp_path / "keep.txt").write_text("keep")
    assert module.main(["install", "--directory", str(tmp_path), "--yes"]) == 2
    assert (tmp_path / "keep.txt").read_text() == "keep"


def test_install_failure_keeps_recovery_receipt(tmp_path, monkeypatch, capsys):
    module = installer()
    target = tmp_path / "runtime"

    def fail(args, **kwargs):
        raise subprocess.CalledProcessError(1, args, output="PRIVATE_TOKEN")

    monkeypatch.setattr(subprocess, "run", fail)
    assert module.main(["install", "--directory", str(target), "--yes"]) == 2
    receipt = json.loads((target / module.MARKER).read_text())
    assert receipt["status"] == "failed"
    assert "PRIVATE_TOKEN" not in capsys.readouterr().out
    assert module.main(["uninstall", "--directory", str(target), "--yes"]) == 0
    assert not target.exists()


def test_uninstall_rejects_unowned_and_relocated_directory(tmp_path):
    module = installer()
    assert module.main(["uninstall", "--directory", str(tmp_path), "--yes"]) == 2
    (tmp_path / module.MARKER).write_text(json.dumps({
        "owner": module.OWNER, "directory": str(tmp_path / "somewhere-else"), "status": "installed",
    }))
    assert module.main(["uninstall", "--directory", str(tmp_path), "--yes"]) == 2
    assert tmp_path.exists()


def test_installer_no_global_config_or_model_commands(tmp_path, monkeypatch):
    module = installer()
    target = tmp_path / "owned runtime"
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        assert kwargs["shell"] is False
        assert kwargs["timeout"] > 0
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(subprocess, "run", run)
    assert module.main(["install", "--directory", str(target), "--yes"]) == 0
    assert calls[0][1:3] == ["-m", "venv"]
    assert calls[1][1:4] == ["-m", "pip", "install"]
    assert calls[2][1:] == ["-m", "premium_model_budget_governor.cli", "doctor", "--offline"]
    assert json.loads((target / module.MARKER).read_text())["status"] == "installed"
    assert module.main(["uninstall", "--directory", str(target)]) == 0
    assert target.exists()
    assert module.main(["uninstall", "--directory", str(target), "--yes"]) == 0
    assert not target.exists()


def test_provenance_flag_keeps_report_inside_owned_runtime(tmp_path, monkeypatch):
    module = installer()
    target = tmp_path / "owned provenance runtime"
    calls = []
    monkeypatch.setattr(module, "_run", lambda args: calls.append(args))
    assert module.main(["install", "--directory", str(target), "--yes", "--provenance"]) == 0
    command = calls[1]
    assert command[command.index("--report") + 1] == str(target / "pip-install-report.json")
    assert json.loads((target / module.MARKER).read_text())["integration_changes"] == []


def test_uninstall_refuses_active_installation(tmp_path):
    module = installer()
    module._write_receipt(tmp_path, "installing")
    assert module.main(["uninstall", "--directory", str(tmp_path), "--yes"]) == 2
    assert tmp_path.is_dir()


def test_home_and_repository_cannot_be_installation_targets():
    module = installer()
    for target in (Path.home(), module.SOURCE, module.SOURCE.parent, Path.home().anchor):
        with pytest.raises(ValueError):
            module._directory(str(target))


def test_mcp_install_emits_exact_runtime_template_not_registration(tmp_path, monkeypatch, capsys):
    module = installer()
    target = tmp_path / "owned runtime with spaces"
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0))
    assert module.main(["install", "--directory", str(target), "--mcp", "--yes"]) == 0
    config = json.loads((target / "governor-mcp-client.json").read_text())
    server = config["mcpServers"]["premium-model-budget-governor"]
    assert Path(server["command"]) == module._python(target)
    assert server["args"] == ["-m", "premium_model_budget_governor.mcp_server"]
    assert "not registered" in capsys.readouterr().out
    assert json.loads((target / module.MARKER).read_text())["integration_changes"] == []


def test_core_only_install_emits_no_mcp_template(tmp_path, monkeypatch):
    module = installer()
    target = tmp_path / "runtime"
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0))
    assert module.main(["install", "--directory", str(target), "--yes"]) == 0
    assert not (target / "governor-mcp-client.json").exists()


def test_symlink_target_cannot_be_removed(tmp_path):
    module = installer()
    real = tmp_path / "real"
    real.mkdir()
    module._write_receipt(real, "installed")
    link = tmp_path / "link"
    try:
        link.symlink_to(real, target_is_directory=True)
    except OSError:
        pytest.skip("host does not permit symlink creation")
    assert module.main(["uninstall", "--directory", str(link), "--yes"]) == 2
    assert real.is_dir()
