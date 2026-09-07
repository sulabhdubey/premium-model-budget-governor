"""Validate authored trial material, never claim model or human outcomes."""
import hashlib
import json
from pathlib import Path
import runpy
import shutil

import pytest


ROOT = Path(__file__).resolve().parents[1] / "examples" / "field-trial"


def test_suite_has_frozen_inputs_and_distinct_task_families():
    suite = json.loads((ROOT / "suite.json").read_text(encoding="utf-8"))
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    assert suite["status"] == "preregistered_not_executed"
    assert suite["id"] == snapshot["suite_id"]
    tasks = suite["tasks"]
    assert len({row["id"] for row in tasks}) == len(tasks) == 5
    assert {row["family"] for row in tasks} == {"coding", "research", "writing", "review", "visual"}
    expected_files = {"suite.json"}
    for row in tasks:
        assert row["prompt"] and len(row["criteria"]) >= 5
        assert row["inputs"] and "suite.json" not in row["inputs"]
        expected_files.update(row["inputs"])
    assert set(snapshot["files"]) == expected_files
    for name, digest in snapshot["files"].items():
        source = (ROOT / name).resolve(strict=True)
        assert source.is_relative_to(ROOT.resolve())
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    assert (ROOT / "queue-chart.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_fixture_facts_match_preregistered_expectations():
    evidence = json.loads((ROOT / "release-evidence.json").read_text(encoding="utf-8"))
    assert evidence["fixture"] is True
    assert evidence["qualification"]["releaseAuthorized"] is False
    assert evidence["qualification"]["revision"] > evidence["campaign"]["revision"]
    assert evidence["qualification"]["local_checks_passed"] == evidence["qualification"]["local_checks_total"]
    assert evidence["qualification"]["independent_recovery_drill"] == "not_completed"
    # This is intentionally defective input for the coding task, not product logic.
    namespace = {}
    exec(compile((ROOT / "lease_check.py").read_text(encoding="utf-8"), "authored_fixture", "exec"), namespace)
    assert namespace["lease_valid"](10, 10) is True


def test_staging_excludes_grading_and_refuses_replacement(tmp_path):
    prepare = runpy.run_path(str(ROOT.parents[1] / "scripts" / "prepare_trial_task.py"))["prepare"]
    target = tmp_path / "trial"
    result = prepare("study-evidence-synthesis", target)
    assert result["model_calls_started"] == 0
    assert result["grading_criteria_included"] is False
    assert {path.name for path in target.iterdir()} == {"task.txt", "study-notes.md"}
    assert (target / "study-notes.md").read_bytes() == (ROOT / "study-notes.md").read_bytes()
    with pytest.raises(FileExistsError):
        prepare("study-evidence-synthesis", target)


def test_staging_rejects_changed_input_before_creating_destination(tmp_path):
    prepare = runpy.run_path(str(ROOT.parents[1] / "scripts" / "prepare_trial_task.py"))["prepare"]
    altered = tmp_path / "fixtures"
    shutil.copytree(ROOT, altered)
    (altered / "study-notes.md").write_text("changed")
    target = tmp_path / "trial"
    with pytest.raises(ValueError, match="changed"):
        prepare("study-evidence-synthesis", target, source=altered)
    assert not target.exists()
