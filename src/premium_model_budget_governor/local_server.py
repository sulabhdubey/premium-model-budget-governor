"""Authenticated loopback transport. Not an internet-facing web server."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import secrets
from threading import Lock, Event, BoundedSemaphore

from .doctor import diagnose
from .folder_picker import FolderPicker
from .input_errors import InputIssue, ISSUES
from .private_file import write_private, remove_if_unchanged

IDENTIFIER = re.compile(r"^[a-f0-9]{32}$")
CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


class Jobs:
    def __init__(self, app):
        self.app = app
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="governor-task")
        self.lock = Lock()
        self.rows = {}
        self.future = None
        self.cancel_events = {}

    def start(self, identifier):
        with self.lock:
            if identifier in self.rows or (self.future is not None and not self.future.done()):
                raise RuntimeError("busy_or_replayed")
            if len(self.rows) >= 100:
                oldest = next(iter(self.rows))
                self.rows.pop(oldest)
                self.cancel_events.pop(oldest, None)
            self.rows[identifier] = {"id": identifier, "status": "queued"}
            self.cancel_events[identifier] = Event()
            self.future = self.pool.submit(self._execute, identifier)
            return deepcopy(self.rows[identifier])

    def _execute(self, identifier):
        with self.lock:
            self.rows[identifier] = {"id": identifier, "status": "running"}
        try:
            result = self.app.execute(identifier, approved=True, cancel_event=self.cancel_events[identifier])
            row = {"id": identifier, "status": result["status"], "result": result}
        except Exception:
            # Never forward exception strings, source excerpts or host output to the browser.
            row = {"id": identifier, "status": "needs_attention",
                   "error": "Execution could not complete. Inspect the receipt before starting another task."}
        with self.lock:
            self.rows[identifier] = row

    def get(self, identifier):
        with self.lock:
            row = deepcopy(self.rows.get(identifier))
        if row and row["status"] in {"running","stop_requested"} and hasattr(self.app,"stage_progress"):
            row["stage_progress"] = self.app.stage_progress(identifier)
        return row

    def list(self):
        with self.lock:
            return deepcopy(list(self.rows.values()))

    def cancel(self, identifier):
        with self.lock:
            row = self.rows.get(identifier)
            if row is None:
                raise ValueError("unknown task")
            if row["status"] in {"queued", "running", "stop_requested"}:
                self.cancel_events[identifier].set()
                row["status"] = "stop_requested"
            return deepcopy(row)

    def close(self):
        for event in self.cancel_events.values():
            event.set()
        self.pool.shutdown(wait=True)


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, app, *, port=0, preview_only=False):
        if type(preview_only) is not bool:
            raise ValueError("preview_only must be boolean")
        self.app = app
        self.preview_only = preview_only
        self.token = secrets.token_urlsafe(32)
        self.jobs = Jobs(app)
        self.folder_picker = FolderPicker()
        self.connection_slots = BoundedSemaphore(16)
        super().__init__(("127.0.0.1", port), Handler)
        self.origin = f"http://127.0.0.1:{self.server_port}"
        self.expected_host = f"127.0.0.1:{self.server_port}"

    def process_request(self, request, client_address):
        if not self.connection_slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.connection_slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.connection_slots.release()

    def server_close(self):
        super().server_close()
        self.jobs.close()


class Handler(BaseHTTPRequestHandler):
    server_version = "GovernorLocal"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(10)
        self.body_read = False

    def log_message(self, *args):
        pass

    def _reply(self, status, result=None, *, error=None, issue=None, content_type="application/json; charset=utf-8", raw=None):
        if status >= 400 and self.command == "POST" and not self.body_read and hasattr(self, "headers"):
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) == 1 and len(lengths[0]) <= 6 and lengths[0].isascii() and lengths[0].isdigit() and int(lengths[0]) <= 131072:
                # Drain only a small bounded body; otherwise Windows can reset before the rejection arrives.
                self.connection.settimeout(.2)
                try:
                    self.rfile.read(int(lengths[0]))
                except OSError:
                    pass
                finally:
                    self.connection.settimeout(10)
                    self.body_read = True
        payload = {"ok": error is None, "result": result} if error is None else {"ok": False, "error": error}
        if issue in ISSUES:
            field, message = ISSUES[issue]
            payload = {"ok": False, "error": message, "code": issue, "field": field}
        data = raw if raw is not None else json.dumps(payload, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def send_error(self, code, message=None, explain=None):
        self._reply(code, error="Request rejected.")

    def _authorize(self):
        hosts = self.headers.get_all("Host", [])
        origins = self.headers.get_all("Origin", [])
        if hosts != [self.server.expected_host] or self.headers.get("Sec-Fetch-Site") == "cross-site":
            self._reply(403, error="Local origin required.")
            return False
        if (origins and origins != [self.server.origin]) or (self.command == "POST" and origins != [self.server.origin]):
            self._reply(403, error="Local origin required.")
            return False
        auth = self.headers.get_all("Authorization", [])
        expected = ("Bearer " + self.server.token).encode()
        if len(auth) != 1 or len(auth[0]) > 256 or not secrets.compare_digest(auth[0].encode("utf-8"), expected):
            self._reply(401, error="Open the current local session to continue.")
            return False
        return True

    def do_GET(self):
        if self.path == "/favicon.ico":
            self._reply(204, raw=b"")
            return
        assets = {"/": ("index.html", "text/html; charset=utf-8"),
                  "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                  "/styles.css": ("styles.css", "text/css; charset=utf-8")}
        if self.path in assets:
            if self.headers.get_all("Host", []) != [self.server.expected_host]:
                self._reply(403, error="Local origin required.")
                return
            filename, kind = assets[self.path]
            self._reply(200, content_type=kind, raw=(Path(__file__).parent / "web" / filename).read_bytes())
            return
        if not self.path.startswith("/api/"):
            self._reply(404, error="Not found.")
            return
        if not self._authorize():
            return
        if self.path == "/api/projects":
            self._reply(200, self.server.app.project_catalog())
        elif self.path == "/api/history":
            self._reply(200, self.server.app.history())
        elif self.path == "/api/observations":
            try:
                self._reply(200, self.server.app.observation_history())
            except (ValueError, OSError):
                self._reply(400, error="Observation journal unavailable.")
        elif self.path == "/api/usage-digest":
            try:
                self._reply(200, self.server.app.usage_digest())
            except (ValueError, OSError):
                self._reply(400, error="Usage digest unavailable. No records changed.")
        elif self.path == "/api/jobs":
            self._reply(200, self.server.jobs.list())
        elif self.path.startswith("/api/jobs/") and IDENTIFIER.fullmatch(self.path[len("/api/jobs/"):]):
            row = self.server.jobs.get(self.path[len("/api/jobs/"):])
            self._reply(200, row) if row is not None else self._reply(404, error="Task not found in this session.")
        else:
            self._reply(404, error="Not found.")

    def do_POST(self):
        if not self._authorize():
            return
        if self.path not in {"/api/preview", "/api/preview/discard", "/api/execute", "/api/doctor", "/api/cancel", "/api/files", "/api/reconcile", "/api/host-options", "/api/projects/add", "/api/projects/remove", "/api/projects/choose", "/api/experiments/compare", "/api/observations/preview", "/api/observations/import", "/api/observations/retention", "/api/usage-digest/settings"}:
            self._reply(404, error="Not found.")
            return
        if self.headers.get_content_type() != "application/json":
            self._reply(415, error="JSON content required.")
            return
        lengths = self.headers.get_all("Content-Length", [])
        if self.headers.get("Transfer-Encoding") is not None or len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
            self._reply(400, error="A single request length is required.")
            return
        if len(lengths[0]) > 8:
            self._reply(413, error="Request length exceeds supported bounds.")
            return
        length = int(lengths[0])
        if length > 65536:
            self._reply(413, error="Request exceeds 64 KB.")
            return
        try:
            self.body_read = True
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError("incomplete body")
            packet = json.loads(raw, object_pairs_hook=unique_object,
                                parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
            if not isinstance(packet, dict):
                raise ValueError("object required")
            if self.path == "/api/preview":
                self._reply(200, {**self.server.app.preview(packet),
                                  "execution_disabled": self.server.preview_only})
            elif self.path == "/api/experiments/compare":
                from .experiments import compare_runs
                from .report_export import experiment_summary
                result = compare_runs(packet)
                self._reply(200, {**result, "export_preview": experiment_summary(result)})
            elif self.path == "/api/observations/preview":
                self._reply(200, self.server.app.preview_observation(packet))
            elif self.path == "/api/observations/import":
                self._reply(200, self.server.app.import_observation(packet))
            elif self.path == "/api/observations/retention":
                self._reply(200, self.server.app.observation_retention(packet))
            elif self.path == "/api/usage-digest/settings":
                self._reply(200, self.server.app.configure_digest(packet))
            elif self.path == "/api/preview/discard":
                identifier = packet.get("id")
                if set(packet) != {"id"} or not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
                    raise ValueError("discard accepts only a preview ID")
                self._reply(200, self.server.app.discard_preview(identifier))
            elif self.path == "/api/doctor":
                self._reply(200, diagnose())
            elif self.path == "/api/host-options":
                self._reply(200, self.server.app.host_options(packet.get("project")))
            elif self.path == "/api/projects/add":
                self._reply(200, self.server.app.register_project(packet.get("path"), approved=packet.get("approved")))
            elif self.path == "/api/projects/choose":
                if packet != {"open": True} or packet.get("open") is not True:
                    raise ValueError("explicit dialog request required")
                self._reply(200, self.server.folder_picker.choose())
            elif self.path == "/api/projects/remove":
                self._reply(200, self.server.app.remove_project(packet.get("id"), approved=packet.get("approved")))
            elif self.path == "/api/files":
                self._reply(200, self.server.app.browse(packet.get("project"), packet.get("directory", "."), images=packet.get("images", False)))
            elif self.path == "/api/reconcile":
                identifier = packet.get("id")
                if set(packet) != {"id", "approved"} or not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
                    raise ValueError("receipt recovery accepts only ID and approval")
                self._reply(200, self.server.app.reconcile(identifier, approved=packet.get("approved")))
            elif self.path == "/api/cancel":
                identifier = packet.get("id")
                if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
                    raise ValueError("preview ID required")
                self._reply(202, self.server.jobs.cancel(identifier))
            else:
                if self.server.preview_only:
                    self._reply(403, error="Preview-only session. Model execution is disabled.")
                    return
                identifier = packet.get("id")
                if packet.get("approved") is not True or not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
                    raise ValueError("explicit approval and preview ID required")
                self._reply(202, self.server.jobs.start(identifier))
        except InputIssue as error:
            self._reply(400, issue=error.code)
        except RuntimeError:
            self._reply(409, error="A task is active or this preview has already been submitted.")
        except (ValueError, OSError):
            self._reply(400, error="Request could not be accepted. Review the project, evidence, budget and approval.")
        except Exception:
            self._reply(500, error="Local service needs attention. No automatic retry was started.")


def serve(projects, data, *, port=0, open_browser=True, session_file=None, preview_only=False):
    import webbrowser
    from .workbench import Workbench
    from .runtime_lock import RuntimeLock
    with RuntimeLock(data) as ownership:
        app = Workbench(projects, data)
        app.recover_interrupted(ownership)
        return _serve_owned(app, port, open_browser, session_file, preview_only=preview_only)


def _serve_owned(app, port, open_browser, session_file, *, preview_only=False):
    import webbrowser
    with LocalServer(app, port=port, preview_only=preview_only) as server:
        url = server.origin + "/#session=" + server.token
        session_bytes = json.dumps({"url": url}).encode("utf-8")
        if session_file:
            write_private(session_file, session_bytes)
        print("Governor local session: " + url, flush=True)
        print("Keep this session link private. Ctrl+C requests local cancellation; unknown spend is retained.", flush=True)
        if open_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            if session_file:
                remove_if_unchanged(session_file, session_bytes)
