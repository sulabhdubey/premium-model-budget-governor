"""Offline lab fault injection only. Review this command before trusting it."""
import json
from pathlib import Path
import sys
import time

from premium_model_budget_governor.prompt_gate import main

lab = Path(sys.argv[1]).resolve(strict=True)
mode = json.loads((lab / "control.json").read_text())["mode"]
if mode == "crash":
    raise SystemExit(1)
if mode == "timeout":
    time.sleep(10)
elif mode != "normal":
    raise SystemExit("Unsupported fixture mode")
raise SystemExit(main(["--grant", str(lab / "grant.json")]))
