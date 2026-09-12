import importlib.util
from pathlib import Path
import shutil
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]


def builder():
    spec = importlib.util.spec_from_file_location("build_plugin", ROOT / "scripts/build_plugin.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_package_is_repeatable_complete_and_does_not_overwrite(tmp_path):
    module = builder()
    first, second = tmp_path / "first.zip", tmp_path / "second.zip"
    result = module.build(ROOT, first)
    assert result == module.build(ROOT, second)
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        names = set(archive.namelist())
        assert "LICENSE" in names and "NOTICE" in names
        assert "examples/astra_preferred.json" in names
        assert "docs/HOST_INTEGRATION.md" in names
        assert ".codex-plugin/plugin.json" in names
        assert not any("__pycache__" in name or "outputs/" in name for name in names)
        assert archive.testzip() is None
    with pytest.raises(FileExistsError):
        module.build(ROOT, first)


def test_rejects_escaped_input_before_creating_archive(tmp_path):
    module = builder()
    with pytest.raises(ValueError, match="source"):
        module.read_source(ROOT, "../outside.txt")


def test_missing_source_leaves_no_partial_archive(tmp_path):
    module = builder()
    output = tmp_path / "absent.zip"
    with pytest.raises((ValueError, FileNotFoundError)):
        module.build(tmp_path, output)
    assert not output.exists()


def test_unlisted_local_files_are_never_bundled(tmp_path):
    module = builder()
    source = tmp_path / "source"
    for relative in module.SOURCES.values():
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    (source / "plugin/private-notes.txt").write_text("DO_NOT_PUBLISH")
    archive_path = tmp_path / "plugin.zip"
    module.build(source, archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == set(module.SOURCES)
        assert all(b"DO_NOT_PUBLISH" not in archive.read(name) for name in archive.namelist())
