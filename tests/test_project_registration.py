from pathlib import Path
import sqlite3

import pytest

from premium_model_budget_governor.workbench import Workbench


def app(tmp_path):
    root = tmp_path / "initial"
    root.mkdir(exist_ok=True)
    return Workbench({"initial": root}, tmp_path / "data")


def test_registration_requires_approval_and_persists(tmp_path):
    service = app(tmp_path)
    project = tmp_path / "second"
    project.mkdir()
    with pytest.raises(ValueError, match="approval"):
        service.register_project(str(project), approved=False)
    row = service.register_project(str(project), approved=True)
    assert service.projects[row["id"]] == project
    assert app(tmp_path).projects[row["id"]] == project
    assert not list(project.iterdir())


def test_remove_saved_project_preserves_folder_and_invalidates_previews(tmp_path):
    service = app(tmp_path)
    project = tmp_path / "second"
    project.mkdir()
    (project / "keep.txt").write_text("keep")
    row = service.register_project(str(project), approved=True)
    service.previews["pending"] = {"public": {"project": row["id"]}}
    service.remove_project(row["id"], approved=True)
    assert row["id"] not in service.projects and not service.previews
    assert row["id"] not in app(tmp_path).projects
    assert (project / "keep.txt").read_text() == "keep"


@pytest.mark.parametrize("kind", ["relative", "home", "root", "missing", "data"])
def test_registration_rejects_overbroad_or_invalid_paths(tmp_path, kind):
    service = app(tmp_path)
    paths = {"relative": ".", "home": str(Path.home()), "root": str(Path.cwd().anchor),
             "missing": str(tmp_path / "missing"), "data": str(service.data)}
    with pytest.raises(ValueError):
        service.register_project(paths[kind], approved=True)


def test_duplicate_registration_is_idempotent_and_running_removal_is_rejected(tmp_path):
    service = app(tmp_path)
    project = tmp_path / "second"
    project.mkdir()
    first = service.register_project(str(project), approved=True)
    assert service.register_project(str(project), approved=True) == first
    with sqlite3.connect(service.database) as db:
        db.execute("INSERT INTO runs VALUES ('active','running','{}')")
    with pytest.raises(ValueError, match="running"):
        service.remove_project(first["id"], approved=True)


def test_startup_project_cannot_be_removed_from_persistent_configuration(tmp_path):
    service = app(tmp_path)
    with pytest.raises(ValueError, match="launch"):
        service.remove_project("initial", approved=True)


def test_missing_saved_project_remains_removable_after_restart(tmp_path):
    service = app(tmp_path)
    project = tmp_path / "disappearing"
    project.mkdir()
    row = service.register_project(str(project), approved=True)
    project.rmdir()
    restarted = app(tmp_path)
    assert row["id"] not in restarted.projects
    visible = next(v for v in restarted.project_catalog() if v["id"] == row["id"])
    assert visible["available"] is False and visible["removable"] is True
    restarted.remove_project(row["id"], approved=True)
    assert all(v["id"] != row["id"] for v in app(tmp_path).project_catalog())


def test_live_missing_project_is_not_advertised_as_available(tmp_path):
    service = app(tmp_path)
    project = tmp_path / "disappearing"
    project.mkdir()
    row = service.register_project(str(project), approved=True)
    project.rmdir()
    assert next(v for v in service.project_catalog() if v["id"] == row["id"])["available"] is False
    service.probe = lambda *args: pytest.fail("missing project reached host")
    with pytest.raises(ValueError):
        service.host_options(row["id"])


def test_saved_folder_also_supplied_at_launch_stays_visible_and_removable(tmp_path):
    service = app(tmp_path)
    project = tmp_path / "second"
    project.mkdir()
    saved = service.register_project(str(project), approved=True)
    restarted = Workbench({"launch": project}, tmp_path / "data")
    rows = {row["id"]: row for row in restarted.project_catalog()}
    assert rows[saved["id"]]["removable"] is True
    assert rows[saved["id"]]["selectable"] is False
    assert rows[saved["id"]]["configured_at_launch"] is True
    assert rows["launch"]["selectable"] is True
    restarted.remove_project(saved["id"], approved=True)
    assert restarted.projects["launch"] == project
    assert saved["id"] not in app(tmp_path).saved_projects


def test_same_saved_and_launch_id_removal_preserves_launch_access(tmp_path):
    service = app(tmp_path)
    project = tmp_path / "second"
    project.mkdir()
    saved = service.register_project(str(project), approved=True)
    restarted = Workbench({saved["id"]: project}, tmp_path / "data")
    restarted.remove_project(saved["id"], approved=True)
    assert restarted.projects[saved["id"]] == project
    row = restarted.project_catalog()[0]
    assert row["removable"] is False and row["configured_at_launch"] is True


def test_saved_identifier_collision_with_different_launch_root_is_rejected(tmp_path):
    service = app(tmp_path)
    project = tmp_path / "second"
    project.mkdir()
    saved = service.register_project(str(project), approved=True)
    with pytest.raises(ValueError, match="conflicts"):
        Workbench({saved["id"]: tmp_path / "initial"}, tmp_path / "data")
