"""Exercise a wheel in a fresh environment, outside the source tree's import path."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--mcp", action="store_true")
    parser.add_argument("--regression", action="store_true", help="Install pytest in the isolated runtime and test the wheel")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    wheel = args.wheel.resolve(strict=True)
    root = Path(__file__).resolve().parents[1]
    installer = root / "scripts/install_governor.py"
    report = {"schema_version": 1, "platform": platform.system(),
              "python": platform.python_version(), "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
              "optional_mcp_requested": args.mcp, "regression_requested": args.regression,
              "model_calls_started": 0, "checks": []}
    stage = "initialize"
    env = {key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "PYTHONHOME"}}
    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="pm-bg-install-check-") as temporary:
            outside = Path(temporary).resolve()
            target = outside / "isolated runtime"

            def run(command):
                result = subprocess.run(command, cwd=outside, env=env, capture_output=True,
                                        text=True, encoding="utf-8", errors="replace", shell=False,
                                        stdin=subprocess.DEVNULL, timeout=1000)
                if result.returncode:
                    raise RuntimeError("command_failed")
                return result.stdout

            base = [sys.executable, str(installer), "install", "--directory", str(target), "--wheel", str(wheel)]
            if args.mcp:
                base += ["--mcp"]
            stage = "preview"
            run(base)
            assert not target.exists()
            report["checks"].append("preview_created_nothing")
            stage = "install"
            install_started = time.monotonic()
            run([*base, "--yes"])
            report["install_seconds"] = round(time.monotonic() - install_started, 3)
            python = target / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            executable = target / ("Scripts/pm-bg.exe" if os.name == "nt" else "bin/pm-bg")
            stage = "isolation"
            origin = json.loads(run([str(python), "-I", "-c",
                "import json,sys,premium_model_budget_governor as p; print(json.dumps({'prefix':sys.prefix,'module':p.__file__}))"]))
            assert Path(origin["prefix"]).resolve() == target
            assert Path(origin["module"]).resolve().is_relative_to(target)
            report["checks"].append("imports_installed_wheel_not_checkout")
            stage = "doctor"
            diagnosis = json.loads(run([str(executable), "doctor", "--offline", "--json"]))["result"]
            assert diagnosis["offline_planning"] == "ready"
            assert diagnosis["authentication"]["status"] == "not_checked"
            assert diagnosis["mcp"]["installed"] is args.mcp
            report["checks"].append("offline_doctor_outside_checkout")
            stage = "plan"
            planned = json.loads(run([str(executable), "plan", "--input", str(root / "examples/astra_preferred.json")]))["result"]
            assert planned["astra_participation"] == "planned"
            report["checks"].append("astra_preferred_example_plans_without_model_call")
            stage = "installed_workbench"
            installed_assets = json.loads(run([str(python), "-I", "-c", """
import hashlib, http.client, json, tempfile
from pathlib import Path
from threading import Thread
import premium_model_budget_governor as package
from premium_model_budget_governor.local_server import LocalServer
from premium_model_budget_governor.workbench import Workbench
from premium_model_budget_governor.receipt_journal import recover_terminal
from premium_model_budget_governor.reviewed_policy import PolicyStore
from premium_model_budget_governor.input_errors import InputIssue
assets = Path(package.__file__).parent / 'web'
hashes = {name: hashlib.sha256((assets / name).read_bytes()).hexdigest()
          for name in ('index.html', 'app.js', 'styles.css')}
with tempfile.TemporaryDirectory() as temporary:
    base = Path(temporary)
    project = base / 'project'
    project.mkdir()
    def forbidden_executor(*args, **kwargs):
        raise AssertionError('package qualification must not execute a model')
    app = Workbench({'fixture': project}, base / 'data',
                    probe=lambda root: {'models': []}, executor=forbidden_executor)
    server = LocalServer(app)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def get(route, token=None):
        connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
        connection.request('GET', route, headers={'Authorization': 'Bearer ' + token} if token else {})
        response = connection.getresponse()
        status, body = response.status, response.read()
        connection.close()
        return status, body
    try:
        for route, name in (('/', 'index.html'), ('/app.js', 'app.js'), ('/styles.css', 'styles.css')):
            status, body = get(route)
            assert status == 200 and hashlib.sha256(body).hexdigest() == hashes[name]
        assert get('/api/projects')[0] == 401
        status, body = get('/api/projects', server.token)
        assert status == 200 and json.loads(body)['result'][0]['available'] is True
        assert app.history() == []
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
        assert not thread.is_alive()
print(json.dumps(hashes))
"""]))
            expected_assets = {name: hashlib.sha256((root / "src/premium_model_budget_governor/web" / name).read_bytes()).hexdigest()
                               for name in ("index.html", "app.js", "styles.css")}
            assert installed_assets == expected_assets
            report["workbench_asset_sha256"] = installed_assets
            report["checks"].append("installed_workbench_assets_auth_and_modules_outside_checkout")
            if args.mcp:
                stage = "mcp_stdio"
                run([str(python), "-I", "-c", """
import anyio, sys
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
async def check():
    params = StdioServerParameters(command=sys.executable, args=['-I', '-m', 'premium_model_budget_governor.mcp_server'])
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            names = {tool.name for tool in (await session.list_tools()).tools}
            assert 'plan_model_workflow' in names
            result = await session.call_tool('calibrate_workflow_outcomes', {'packet': {'pairs': []}})
            assert not result.is_error
anyio.run(check)
"""])
                report["checks"].append("installed_mcp_stdio_initialize_list_call")
            if args.regression:
                stage = "regression_dependencies"
                run([str(python), "-m", "pip", "install", "pytest>=8"])
                stage = "installed_wheel_regression"
                # Failure traces may contain local paths; keep raw XML out of public artifacts.
                junit = root / "build" / "qualification" / (args.report.stem + ".xml")
                junit.parent.mkdir(parents=True, exist_ok=True)
                summary = run([str(python), "-I", "-m", "pytest", str(root / "tests"), "-q",
                               "-o", "pythonpath=", "--import-mode=importlib", "--junitxml", str(junit)])
                report["regression_summary"] = summary.strip().splitlines()[-1]
                report["checks"].append("regression_against_installed_wheel_without_checkout_imports")
            stage = "uninstall"
            remove = [sys.executable, str(installer), "uninstall", "--directory", str(target)]
            run(remove)
            assert target.is_dir()
            run([*remove, "--yes"])
            assert not target.exists()
            report["checks"].append("preview_preserves_and_uninstall_removes_owned_runtime")
        report["status"] = "passed"
    except (OSError, ValueError, AssertionError, RuntimeError, subprocess.SubprocessError):
        report.update(status="failed", failed_stage=stage)
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
