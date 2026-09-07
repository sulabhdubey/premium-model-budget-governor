import json
import subprocess
from threading import Event, Thread

import pytest


def test_selected_folder_is_returned_without_registering_it(tmp_path, monkeypatch):
    from premium_model_budget_governor.folder_picker import FolderPicker
    def run(command, **kwargs):
        assert command[-1] == "--choose"
        assert "-I" in command and kwargs["shell"] is False
        assert kwargs["timeout"] == 90
        return subprocess.CompletedProcess(command, 0, json.dumps({"path":str(tmp_path)}), "")
    monkeypatch.setattr(subprocess, "run", run)
    assert FolderPicker().choose() == {"status":"selected", "path":str(tmp_path)}


@pytest.mark.parametrize("output", ["{}", '{"path":12}', '{"path":"relative"}', 'PRIVATE ERROR'])
def test_invalid_picker_output_has_no_private_details(output, monkeypatch):
    from premium_model_budget_governor.folder_picker import FolderPicker
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess([], 0, output, "PRIVATE ERROR"))
    assert FolderPicker().choose() == {"status":"unavailable"}


def test_cancel_and_timeout_keep_manual_entry_available(monkeypatch):
    from premium_model_budget_governor.folder_picker import FolderPicker
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess([], 0, '{"path":""}', ""))
    picker = FolderPicker()
    assert picker.choose() == {"status":"canceled"}
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("private command", 90)
    monkeypatch.setattr(subprocess, "run", timeout)
    assert picker.choose() == {"status":"unavailable"}
    assert picker.choose() == {"status":"unavailable"}  # Lock was released.


def test_only_one_dialog_can_be_open(monkeypatch):
    from premium_model_budget_governor.folder_picker import FolderPicker
    entered, release = Event(), Event()
    def run(*args, **kwargs):
        entered.set()
        assert release.wait(3)
        return subprocess.CompletedProcess([], 0, '{"path":""}', "")
    monkeypatch.setattr(subprocess, "run", run)
    picker = FolderPicker()
    thread = Thread(target=picker.choose)
    thread.start()
    try:
        assert entered.wait(3)
        assert picker.choose() == {"status":"busy"}
    finally:
        release.set()
        thread.join(3)
    assert not thread.is_alive()
