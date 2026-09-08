"""Run existing rendered Workbench QA on an isolated server that cannot dispatch."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from threading import Thread

from premium_model_budget_governor.local_server import LocalServer
from premium_model_budget_governor.private_file import write_private, remove_if_unchanged
from premium_model_budget_governor.workbench import Workbench


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--node", required=True)
    parser.add_argument("--node-modules", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)

    def forbidden_executor(*args, **kwargs):
        raise RuntimeError("QA server cannot dispatch model calls")

    app = Workbench({"examples": root / "examples"}, output / "data", executor=forbidden_executor)
    server = LocalServer(app)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    session = output / "session.json"
    content = json.dumps({"url": server.origin + "/#session=" + server.token}).encode()
    write_private(session, content)
    env = {**os.environ, "NODE_PATH": args.node_modules, "PM_BG_SESSION_FILE": str(session),
           "PM_BG_QA_OUTPUT": str(output / "screenshots")}
    try:
        result = subprocess.run([args.node, str(root / "scripts/workbench_qa.cjs")],
                                cwd=root, env=env, timeout=600, check=False)
        return result.returncode
    finally:
        server.shutdown()
        server.server_close()
        thread.join(10)
        remove_if_unchanged(session, content)


if __name__ == "__main__":
    raise SystemExit(main())
