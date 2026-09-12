from io import StringIO
from threading import Thread, Event
from types import SimpleNamespace

import pytest

from premium_model_budget_governor import app_server as app


@pytest.mark.parametrize("content", ['{"text":"' + 'x' * 100 + '"}\n', '[]\n', '{broken}\n'])
def test_bad_or_oversized_line_fails_explicitly(tmp_path, monkeypatch, content):
    monkeypatch.setattr(app, "MAX_LINE_CHARACTERS", 32)
    client = app.AppServer(tmp_path)
    client.process = SimpleNamespace(stdout=StringIO(content))
    client._read()
    assert client.reader_done.is_set()
    with pytest.raises(ValueError, match="transport failed"):
        client.receive()


def test_eof_drains_valid_events_then_fails_without_waiting(tmp_path):
    client = app.AppServer(tmp_path)
    client.process = SimpleNamespace(stdout=StringIO('{"id":1,"result":{}}\n'))
    client._read()
    assert client.receive()["id"] == 1
    with pytest.raises(ValueError, match="ended"):
        client.receive()


def test_full_queue_backpressure_can_be_stopped(tmp_path, monkeypatch):
    monkeypatch.setattr(app, "MAX_QUEUED_EVENTS", 2)
    reached = Event()
    class Stream(StringIO):
        count = 0
        def readline(self, limit):
            self.count += 1
            assert limit == app.MAX_LINE_CHARACTERS + 1
            if self.count == 3:
                reached.set()
            return super().readline(limit)
    client = app.AppServer(tmp_path)
    stream = Stream('{"method":"notice"}\n' * 100)
    client.process = SimpleNamespace(stdout=stream)
    reader = Thread(target=client._read)
    reader.start()
    try:
        assert reached.wait(2)
        assert client.queue.qsize() == 2
    finally:
        client.reader_stop.set()
        reader.join(2)
    assert not reader.is_alive()
    assert stream.count == 3
    assert not client.transport_error


def test_deferred_notification_flood_fails_not_unbounded(tmp_path, monkeypatch):
    monkeypatch.setattr(app, "MAX_PENDING_EVENTS", 2)
    client = app.AppServer(tmp_path)
    monkeypatch.setattr(client, "send", lambda message: None)
    monkeypatch.setattr(client, "receive", lambda timeout: {"method": "notice"})
    with pytest.raises(ValueError, match="deferred event limit"):
        client.request("model/list", {})
    assert len(client.pending) == 2
