import importlib.util
import json
from pathlib import Path
import sys


def test_document_discovery_includes_new_nested_guides(tmp_path, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("publication_script", Path(__file__).parents[1] / "scripts/check_publication.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    docs = tmp_path / "docs"
    nested = docs / "new"
    nested.mkdir(parents=True)
    (docs / "one.md").write_text("Public guide", encoding="utf-8")
    (nested / "two.md").write_text("PrivatePhrase", encoding="utf-8")
    terms = tmp_path / "terms.json"
    terms.write_text(json.dumps(["PrivatePhrase"]), encoding="utf-8")
    extra = tmp_path / "README.md"
    extra.write_text("Public readme", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["check_publication", "--docs-root", str(docs), str(extra), "--terms-file", str(terms)])
    assert module.main() == 1
    result = json.loads(capsys.readouterr().out)
    assert result["files_checked"] == 3
    assert result["findings"] == [{"item": "file-1", "rule": "private_term"}]
    assert "PrivatePhrase" not in json.dumps(result)
