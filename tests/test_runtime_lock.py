import importlib.util
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest


def lock_class():
    assert importlib.util.find_spec("premium_model_budget_governor.runtime_lock"), "runtime ownership lock missing"
    from premium_model_budget_governor.runtime_lock import RuntimeLock
    return RuntimeLock


def test_exclusive_lock_releases_cleanly(tmp_path):
    Lock = lock_class()
    with Lock(tmp_path) as held:
        assert held.held
        with pytest.raises(ValueError, match="already"):
            with Lock(tmp_path):
                pass
    assert not held.held
    with Lock(tmp_path) as next_owner:
        assert next_owner.held


def test_recovery_requires_owned_data_directory(tmp_path):
    Lock = lock_class()
    from premium_model_budget_governor.workbench import Workbench
    app = Workbench({"sample": tmp_path}, tmp_path / "data")
    with sqlite3.connect(app.database) as db:
        db.execute("INSERT INTO runs VALUES ('old','running','{}')")
    with Lock(tmp_path / "other") as wrong:
        with pytest.raises(ValueError, match="ownership"):
            app.recover_interrupted(wrong)
    with Lock(app.data) as owned:
        assert app.recover_interrupted(owned) == 1
        assert app.history()[0]["status"] == "unknown_usage"
        assert app.history()[0]["provider_execution_stopped"] is False
        assert app.recover_interrupted(owned) == 0


def test_process_exit_releases_real_os_lock(tmp_path):
    Lock = lock_class()
    code = "from pathlib import Path; import sys; from premium_model_budget_governor.runtime_lock import RuntimeLock; lock=RuntimeLock(Path(sys.argv[1])); lock.__enter__(); print('ready',flush=True); sys.stdin.read()"
    with subprocess.Popen([sys.executable, "-c", code, str(tmp_path)], stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
        try:
            assert process.stdout.readline().strip() == "ready"
            with pytest.raises(ValueError):
                with Lock(tmp_path):
                    pass
        finally:
            process.kill()
            process.communicate(timeout=5)
    with Lock(tmp_path) as current:
        assert current.held
