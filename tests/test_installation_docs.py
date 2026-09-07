from pathlib import Path
import runpy
import shlex


ROOT = Path(__file__).resolve().parents[1]


def test_published_install_commands_preview_without_writes(tmp_path, monkeypatch):
    installer = runpy.run_path(str(ROOT / "scripts/install_governor.py"))
    monkeypatch.chdir(tmp_path)
    wheel = tmp_path / "premium_model_budget_governor-0.4.0rc3-py3-none-any.whl"
    wheel.write_bytes(b"preview fixture, never installed")
    commands = set()
    for name in ("README.md", "docs/INSTALLATION.md", "docs/MCP.md"):
        source = (ROOT / name).read_text(encoding="utf-8")
        assert "v0.4.0-rc.3" in source
        for line in source.splitlines():
            if line.startswith("python install_governor.py install ") and "--yes" not in line:
                commands.add(line)
    assert len(commands) == 2  # Core and optional MCP, sharing one published wheel.
    for index, line in enumerate(sorted(commands)):
        target = tmp_path / f"runtime-{index}"
        assert installer["main"]([*shlex.split(line)[2:], "--directory", str(target)]) == 0
        assert not target.exists()


def test_mcp_guide_does_not_assume_package_index_publication():
    source = (ROOT / "docs/MCP.md").read_text(encoding="utf-8")
    assert 'pip install "premium-model-budget-governor[mcp]"' not in source
    assert "absolute path of the runtime" in source
