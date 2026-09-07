"""Preview-first isolated installer. Requires Python 3.10+, no package imports."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

OWNER = "premium-model-budget-governor-isolated-installer-v1"
MARKER = ".governor-install.json"
SOURCE = Path(__file__).resolve().parents[1]


def _directory(raw: str) -> Path:
    requested = Path(raw).expanduser().absolute()
    if requested.is_symlink() or (requested.exists() and
            getattr(requested.lstat(), "st_file_attributes", 0) & 0x400):
        raise ValueError("Refusing a symlink or junction installation directory.")
    directory = requested.resolve()
    home = Path.home().resolve()
    if directory in {home, *home.parents, SOURCE, *SOURCE.parents}:
        raise ValueError("Choose a dedicated new runtime folder, not your home, repository, or an ancestor.")
    return directory


def _python(directory: Path) -> Path:
    return directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _run(command: list[str]) -> None:
    # Keep output local to the terminal; never copy pip logs into diagnostic receipts.
    sys.stdout.flush()
    subprocess.run(command, check=True, shell=False, timeout=900, stdin=subprocess.DEVNULL)


def _write_receipt(directory: Path, status: str) -> None:
    (directory / MARKER).write_text(json.dumps({
        "owner": OWNER, "directory": str(directory), "status": status,
        "integration_changes": [], "model_calls_started": 0,
    }, indent=2), encoding="utf-8")


def _uninstall(directory: Path, approved: bool) -> None:
    marker = directory / MARKER
    if not marker.is_file() or marker.is_symlink():
        raise ValueError("Not an installer-owned runtime. Nothing removed.")
    receipt = json.loads(marker.read_text(encoding="utf-8"))
    if not isinstance(receipt, dict) or receipt.get("owner") != OWNER or receipt.get("directory") != str(directory):
        raise ValueError("Ownership or location mismatch. Nothing removed.")
    if receipt.get("status") not in {"installed", "failed"}:
        raise ValueError("Installation may still be running. Stop it and inspect the runtime before cleanup.")
    print(f"Remove only this owned runtime: {directory}")
    print("Anything you placed inside this folder will also be removed. Keep projects and ledgers outside it.")
    print("Codex settings, login, and governor data outside this folder are preserved.")
    if approved:
        # Absolute target was validated and bound to the creation receipt above.
        shutil.rmtree(directory)
        print("Runtime removed.")
    else:
        print("Preview only. Repeat with --yes to remove this runtime.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "uninstall"])
    parser.add_argument("--directory", default=str(Path.home() / ".pm-bg" / "runtime"))
    parser.add_argument("--mcp", action="store_true", help="Include optional MCP dependencies (requires package download)")
    parser.add_argument("--wheel", help="Install a locally downloaded governor wheel instead of this checkout")
    parser.add_argument("--yes", action="store_true", help="Approve the displayed install or removal")
    args = parser.parse_args(argv)
    try:
        directory = _directory(args.directory)
        if args.action == "uninstall":
            _uninstall(directory, args.yes)
            return 0
        if sys.version_info < (3, 10):
            raise ValueError("Python 3.10 or newer is required. Install it, then rerun this command.")
        if directory.exists():
            raise ValueError("Directory already exists. Choose a new runtime folder or uninstall the owned runtime first.")
        if args.wheel:
            wheel = Path(args.wheel).resolve(strict=True)
            if not wheel.is_file() or not wheel.name.startswith("premium_model_budget_governor-") or wheel.suffix != ".whl":
                raise ValueError("Choose an explicitly trusted premium_model_budget_governor wheel.")
            source = str(wheel)
        else:
            if not (SOURCE / "pyproject.toml").is_file():
                raise ValueError("Use this script from the repository or supply --wheel.")
            source = str(SOURCE)
        source += "[mcp]" if args.mcp else ""
        print(f"Create isolated Python runtime: {directory}")
        print(f"Install source: {source}")
        print("No changes to PATH, Codex configuration, hooks, login, or other Python environments.")
        print("MCP is not automatically connected. No model calls will be made.")
        if args.wheel and not args.mcp:
            print("Local wheel installation uses no package index.")
        else:
            print("Installation can download build tools and optional dependencies from your configured package index.")
        if not args.yes:
            print("Preview only. Repeat with --yes to install.")
            return 0
        directory.mkdir(parents=True, exist_ok=False)
        _write_receipt(directory, "installing")
        try:
            _run([sys.executable, "-m", "venv", str(directory)])
            command = [str(_python(directory)), "-m", "pip", "install", "--disable-pip-version-check"]
            if args.wheel and not args.mcp:
                command += ["--no-index", "--no-deps"]
            _run([*command, source])
            _run([str(_python(directory)), "-m", "premium_model_budget_governor.cli", "doctor", "--offline"])
        except (OSError, subprocess.SubprocessError):
            _write_receipt(directory, "failed")
            print("Installation failed. Check the local command output for dependency, network, or permission errors.")
            print("Run this script with uninstall and the same --directory to preview cleanup, then add --yes.")
            return 2
        _write_receipt(directory, "installed")
        print("Installed. Next, run this executable with the doctor command:")
        print(directory / ("Scripts/pm-bg.exe" if os.name == "nt" else "bin/pm-bg"))
        return 0
    except (OSError, ValueError) as exc:
        print(f"Setup could not continue: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
