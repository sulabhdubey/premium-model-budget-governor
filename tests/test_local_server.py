import http.client
import importlib.util
import json
from pathlib import Path
from threading import Event, Thread
import time

import pytest


class App:
    projects = {"sample": Path(".").resolve()}

    def __init__(self):
        self.calls = 0
        self.preview_calls = 0
        self.release = Event()

    def history(self):
        return []

    def project_catalog(self):
        return [{"id": key, "path": str(path), "available": True, "removable": False}
                for key, path in self.projects.items()]

    def host_options(self, project):
        if project != "sample":
            raise ValueError("registered project required")
        return {"project": project, "models": [], "execution_status": "not_executed"}

    def register_project(self, path, *, approved=False):
        if approved is not True:
            raise ValueError("approval required")
        return {"id": "saved-fixture", "path": path, "removable": True}

    def remove_project(self, identifier, *, approved=False):
        if approved is not True:
            raise ValueError("approval required")
        return {"id": identifier, "removed": True, "files_deleted": False}

    def reconcile(self, identifier, *, approved=False):
        if approved is not True:
            raise ValueError("approval required")
        return {"id": identifier, "status": "unknown_usage", "recovered": False}

    def preview(self, request):
        self.preview_calls += 1
        if request.get("task") == "field-error":
            from premium_model_budget_governor.input_errors import InputIssue
            raise InputIssue("budget_invalid")
        if request.get("task") == "error":
            raise ValueError("PRIVATE TOKEN must never reach browser")
        return {"id": "a" * 32, "requires_approval": True}

    def discard_preview(self, identifier):
        return {"discarded": identifier == "a" * 32}

    def execute(self, identifier, *, approved=False, cancel_event=None):
        assert approved is True
        self.calls += 1
        while not self.release.wait(.02):
            if cancel_event is not None and cancel_event.is_set():
                return {"id": identifier, "status": "unknown_usage", "stop_requested": True}
        return {"id": identifier, "status": "completed", "answer": "private local result"}


@pytest.fixture
def local():
    assert importlib.util.find_spec("premium_model_budget_governor.local_server"), "local transport is missing"
    from premium_model_budget_governor.local_server import LocalServer
    app = App()
    server = LocalServer(app, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, app
    finally:
        app.release.set()
        server.shutdown()
        server.server_close()
        thread.join(3)


def test_folder_chooser_requires_auth_origin_and_explicit_action(local, monkeypatch):
    server, app = local
    calls = []
    monkeypatch.setattr(server.folder_picker, "choose", lambda: calls.append(True) or {"status":"canceled"})
    assert call(server, "/api/projects/choose", method="POST", payload={"open":True}, authenticated=False)[0] == 401
    assert call(server, "/api/projects/choose", method="POST", payload={"open":True}, headers={"Origin":"https://example.invalid"})[0] == 403
    for packet in ({}, {"open":1}, {"open":True,"path":"ignored"}):
        assert call(server, "/api/projects/choose", method="POST", payload=packet)[0] == 400
    assert calls == []
    status, _, body = call(server, "/api/projects/choose", method="POST", payload={"open":True})
    assert status == 200 and json.loads(body)["result"] == {"status":"canceled"}
    assert calls == [True] and app.calls == 0


def call(server, path, *, method="GET", payload=None, authenticated=True, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
    values = {"Authorization": "Bearer " + server.token} if authenticated else {}
    body = None if payload is None else json.dumps(payload)
    if method == "POST":
        values.update({"Origin": server.origin, "Content-Type": "application/json"})
    values.update(headers or {})
    connection.request(method, path, body=body, headers=values)
    response = connection.getresponse()
    result = (response.status, dict(response.headers), response.read().decode())
    connection.close()
    return result


def test_preview_only_rejects_execution_before_queue_or_application():
    from premium_model_budget_governor.local_server import LocalServer
    app = App()
    server = LocalServer(app, preview_only=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, _, body = call(server, "/api/preview", method="POST", payload={})
        assert status == 200
        assert json.loads(body)["result"]["execution_disabled"] is True
        status, _, body = call(server, "/api/execute", method="POST",
                               payload={"id": "a" * 32, "approved": True})
        assert status == 403 and "Preview-only" in body
        assert app.calls == 0 and server.jobs.list() == []
    finally:
        app.release.set()
        server.shutdown()
        server.server_close()
        thread.join(3)


def test_preview_only_requires_boolean_before_binding():
    from premium_model_budget_governor.local_server import LocalServer
    with pytest.raises(ValueError, match="boolean"):
        LocalServer(App(), preview_only="false")


def test_api_requires_token_and_exact_host(local):
    server, app = local
    assert call(server, "/api/projects", authenticated=False)[0] == 401
    assert call(server, "/api/projects", headers={"Host": "attacker.example"})[0] == 403
    assert call(server, "/api/projects")[0] == 200
    assert app.calls == 0


def test_comparison_endpoint_is_authenticated_and_never_dispatches(local):
    server, app = local
    packet = {"baseline": "direct", "runs": [], "enrollment": [
        {"task_id": "t", "snapshot": "s", "rubric": "r", "arm": "direct"},
        {"task_id": "t", "snapshot": "s", "rubric": "r", "arm": "focused"}]}
    path = "/api/experiments/compare"
    assert call(server, path, method="POST", payload=packet, authenticated=False)[0] == 401
    assert call(server, path, method="POST", payload=packet, headers={"Origin":"https://example.invalid"})[0] == 403
    status, _, body = call(server, path, method="POST", payload=packet)
    assert status == 200
    assert json.loads(body)["result"]["enrollment"]["missing_runs"] == 2
    assert app.calls == 0 and app.preview_calls == 0


def test_preview_discard_requires_auth_and_only_identifier(local):
    server, app = local
    packet = {"id": "a" * 32}
    assert call(server, "/api/preview/discard", method="POST", payload=packet, authenticated=False)[0] == 401
    assert call(server, "/api/preview/discard", method="POST", payload={**packet, "cancel": True})[0] == 400
    assert call(server, "/api/preview/discard", method="POST", payload={"id": "invalid"})[0] == 400
    status, _, body = call(server, "/api/preview/discard", method="POST", payload=packet)
    assert status == 200 and json.loads(body)["result"] == {"discarded": True}
    assert app.calls == 0


@pytest.mark.parametrize("replaced", [False, True])
def test_launch_file_cleanup_respects_replacement(tmp_path, monkeypatch, capsys, replaced):
    from premium_model_budget_governor.local_server import LocalServer, _serve_owned
    path = tmp_path / "session.json"
    def stopped(server):
        assert json.loads(path.read_text())["url"] == server.origin + "/#session=" + server.token
        if replaced:
            path.write_text("user replacement")
    monkeypatch.setattr(LocalServer, "serve_forever", stopped)
    app = App()
    _serve_owned(app, 0, False, path)
    capsys.readouterr()
    assert app.calls == 0
    if replaced:
        assert path.read_text() == "user replacement"
    else:
        assert not path.exists()


@pytest.mark.parametrize("body", [
    '{"task":"review","task":"different"}',
    '{"task":"review","options":{"approved":false,"approved":true}}',
])
def test_duplicate_json_fields_are_rejected_before_application(local, body):
    server, app = local
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
    connection.request("POST", "/api/preview", body=body,
                       headers={"Authorization": "Bearer " + server.token, "Origin": server.origin,
                                "Content-Type": "application/json"})
    response = connection.getresponse()
    status = response.status
    response.read()
    connection.close()
    assert status == 400
    assert app.preview_calls == 0
    assert app.calls == 0


@pytest.mark.parametrize("length", ["9" * 5000, "\u00b2", "+2", "-1"], ids=["oversized", "non-ascii", "signed", "negative"])
def test_malformed_content_length_returns_controlled_rejection(local, length):
    server, app = local
    status, _, _ = call(server, "/api/preview", method="POST", headers={"Content-Length": length})
    assert status in {400, 413}
    assert app.preview_calls == 0
    assert app.calls == 0


def test_unframed_trailing_body_cannot_reach_application(local):
    server, app = local
    try:
        status, _, _ = call(server, "/api/preview", method="POST", payload={}, headers={"Content-Length": "9" * 5000})
        assert status == 413
    except (ConnectionResetError, ConnectionAbortedError, http.client.RemoteDisconnected):
        # Windows may reset a rejected connection with unread, unframed bytes.
        pass
    assert call(server, "/api/projects")[0] == 200
    assert app.preview_calls == 0
    assert app.calls == 0


@pytest.mark.parametrize("endpoint,packet", [
    ("/api/projects/add", {"path": "fixture"}),
    ("/api/projects/remove", {"id": "saved-fixture"}),
])
def test_project_changes_require_auth_origin_and_approval(local, endpoint, packet):
    server, app = local
    assert call(server, endpoint, method="POST", payload={**packet, "approved": True}, authenticated=False)[0] == 401
    assert call(server, endpoint, method="POST", payload={**packet, "approved": True}, headers={"Origin": "https://example.invalid"})[0] == 403
    assert call(server, endpoint, method="POST", payload=packet)[0] == 400
    assert call(server, endpoint, method="POST", payload={**packet, "approved": True})[0] == 200
    assert app.calls == 0


def test_host_options_require_authenticated_registered_project(local):
    server, app = local
    assert call(server, "/api/host-options", method="POST", payload={"project": "sample"}, authenticated=False)[0] == 401
    assert call(server, "/api/host-options", method="POST", payload={"project": "unknown"})[0] == 400
    status, _, body = call(server, "/api/host-options", method="POST", payload={"project": "sample"})
    assert status == 200 and json.loads(body)["result"]["execution_status"] == "not_executed"
    assert app.calls == 0


def test_recovery_requires_auth_approval_and_never_accepts_caller_counters(local):
    server, app = local
    packet = {"id": "a" * 32, "approved": True}
    assert call(server, "/api/reconcile", method="POST", payload=packet, authenticated=False)[0] == 401
    assert call(server, "/api/reconcile", method="POST", payload={**packet, "approved": False})[0] == 400
    assert call(server, "/api/reconcile", method="POST", payload={**packet, "usage": {"input_tokens": 0}})[0] == 400
    assert call(server, "/api/reconcile", method="POST", payload=packet)[0] == 200
    assert app.calls == 0


def test_cross_origin_and_fetch_site_rejected(local):
    server, _ = local
    assert call(server, "/api/preview", method="POST", payload={}, headers={"Origin": "https://evil.example"})[0] == 403
    assert call(server, "/api/history", headers={"Sec-Fetch-Site": "cross-site"})[0] == 403


def test_preview_does_not_spend_and_errors_are_generic(local):
    server, app = local
    assert call(server, "/api/preview", method="POST", payload={"task": "review"})[0] == 200
    status, headers, body = call(server, "/api/preview", method="POST", payload={"task": "error"})
    assert status == 400 and "PRIVATE" not in body
    assert app.calls == 0
    assert "no-store" in headers["Cache-Control"]
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "Access-Control-Allow-Origin" not in headers


def test_allowlisted_field_error_has_actionable_message(local):
    server, app = local
    status, _, body = call(server, "/api/preview", method="POST", payload={"task": "field-error"})
    result = json.loads(body)
    assert status == 400 and result["ok"] is False
    assert result["field"] == "budget" and result["code"] == "budget_invalid"
    assert "estimated credits" in result["error"]
    assert app.calls == 0


def test_async_execution_requires_approval_and_cannot_replay(local):
    server, app = local
    packet = {"id": "a" * 32, "approved": False}
    assert call(server, "/api/execute", method="POST", payload=packet)[0] == 400
    packet["approved"] = True
    assert call(server, "/api/execute", method="POST", payload=packet)[0] == 202
    assert call(server, "/api/execute", method="POST", payload=packet)[0] == 409
    assert call(server, "/api/jobs/" + "a" * 32)[0] == 200
    app.release.set()
    for _ in range(30):
        row = json.loads(call(server, "/api/jobs/" + "a" * 32)[2])["result"]
        if row["status"] == "completed":
            break
        time.sleep(.02)
    assert row["result"]["answer"] == "private local result"
    assert app.calls == 1


def test_large_and_wrong_content_type_requests_rejected(local):
    server, _ = local
    assert call(server, "/api/preview", method="POST", payload={"task": "x" * 70000})[0] == 413
    assert call(server, "/api/preview", method="POST", payload={}, headers={"Content-Type": "text/plain"})[0] == 415
    assert call(server, "/../../.env")[0] == 404


def test_no_lan_bind_parameter():
    assert importlib.util.find_spec("premium_model_budget_governor.local_server"), "local transport is missing"
    from premium_model_budget_governor.local_server import LocalServer
    with pytest.raises(TypeError):
        LocalServer(App(), host="0.0.0.0")


def test_digest_requires_auth_origin_and_explicit_local_consent(local, tmp_path):
    from premium_model_budget_governor.workbench import Workbench
    server, app = local
    real = Workbench({"p": tmp_path}, tmp_path / "data")
    app.configure_digest = real.configure_digest
    app.usage_digest = real.usage_digest
    assert call(server, "/api/usage-digest", authenticated=False)[0] == 401
    assert json.loads(call(server, "/api/usage-digest")[2])["result"]["enabled"] is False
    endpoint = "/api/usage-digest/settings"
    assert call(server, endpoint, method="POST", payload={"enabled": True, "approved": True}, headers={"Origin": "https://example.invalid"})[0] == 403
    for packet in ({"enabled": True}, {"enabled": True, "approved": 1}, {"enabled": True, "approved": True, "path": "other"}):
        assert call(server, endpoint, method="POST", payload=packet)[0] == 400
    assert call(server, endpoint, method="POST", payload={"enabled": True, "approved": True})[0] == 200
    result = json.loads(call(server, "/api/usage-digest")[2])["result"]
    assert result["enabled"] is True and result["report"]["weekly_cost"] is None
    assert app.calls == 0


def test_ui_assets_are_exact_allowlist_and_never_embed_token(local):
    server, _ = local
    status, headers, html = call(server, "/", authenticated=False)
    assert status == 200
    assert "New task" in html and server.token not in html
    assert headers["Content-Type"].startswith("text/html")
    assert call(server, "/app.js", authenticated=False)[0] == 200
    assert call(server, "/styles.css", authenticated=False)[0] == 200
    assert call(server, "/../workbench.py", authenticated=False)[0] == 404


def test_cancel_and_reconnect_find_existing_job(local):
    server, app = local
    identifier = "b" * 32
    assert call(server, "/api/execute", method="POST", payload={"id":identifier,"approved":True})[0] == 202
    rows = json.loads(call(server, "/api/jobs")[2])["result"]
    assert rows[0]["id"] == identifier
    assert call(server, "/api/cancel", method="POST", payload={"id":identifier})[0] == 202
    for _ in range(30):
        row = json.loads(call(server, "/api/jobs/" + identifier)[2])["result"]
        if row["status"] == "unknown_usage":
            break
        time.sleep(.02)
    assert row["result"]["stop_requested"] is True
    assert app.calls == 1


def test_saturated_transport_recovers_without_extra_threads(local):
    server, _ = local
    for _ in range(16):
        assert server.connection_slots.acquire(blocking=False)
    try:
        with pytest.raises((OSError, http.client.RemoteDisconnected)):
            call(server, "/api/projects")
    finally:
        for _ in range(16):
            server.connection_slots.release()
    assert call(server, "/api/projects")[0] == 200
