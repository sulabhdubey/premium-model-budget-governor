"""Optional desktop folder dialog; selecting a path grants no project access."""
import json
from pathlib import Path
import subprocess
import sys
from threading import Lock


class FolderPicker:
    def __init__(self):
        self.lock = Lock()

    def choose(self):
        if not self.lock.acquire(blocking=False):
            return {"status": "busy"}
        try:
            # Tk owns the child main thread, never an HTTP worker's event loop.
            result = subprocess.run(
                [sys.executable, "-I", str(Path(__file__).resolve()), "--choose"],
                shell=False, capture_output=True, text=True, encoding="utf-8",
                stdin=subprocess.DEVNULL, timeout=90,
                **({"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}),
            )
            if result.returncode or len(result.stdout) > 32768:
                return {"status": "unavailable"}
            selected = json.loads(result.stdout).get("path")
            if selected == "":
                return {"status": "canceled"}
            if not isinstance(selected, str) or len(selected) > 4096 or not Path(selected).is_absolute() or not Path(selected).is_dir():
                return {"status": "unavailable"}
            return {"status": "selected", "path": selected}
        except (OSError, ValueError, AttributeError, subprocess.SubprocessError):
            return {"status": "unavailable"}
        finally:
            self.lock.release()


def main():
    if sys.argv[1:] != ["--choose"]:
        return 2
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        try:
            selected = filedialog.askdirectory(parent=root, title="Choose a Governor project folder", mustexist=True)
        finally:
            root.destroy()
        print(json.dumps({"path": selected}, ensure_ascii=True))
        return 0
    except Exception:
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
