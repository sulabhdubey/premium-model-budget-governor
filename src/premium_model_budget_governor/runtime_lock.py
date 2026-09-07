"""OS-backed lifetime lock; a file's presence is never a process-liveness test."""
import os
from pathlib import Path


class RuntimeLock:
    def __init__(self, data: Path):
        self.data = data.resolve()
        self.handle = None
        self.held = False

    def __enter__(self):
        self.data.mkdir(parents=True, exist_ok=True)
        self.handle = (self.data / "server.lock").open("a+b")
        try:
            self.handle.seek(0, os.SEEK_END)
            if not self.handle.tell():
                self.handle.write(b"0")
                self.handle.flush()
            self.handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.handle.close()
            self.handle = None
            raise ValueError("a server already owns this data directory or the lock is unavailable") from exc
        self.held = True
        return self

    def __exit__(self, *args):
        if self.handle:
            # Closing the descriptor releases the lock, including when the process exits.
            self.handle.close()
            self.handle = None
        self.held = False
