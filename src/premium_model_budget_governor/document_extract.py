"""Bounded DOCX intake in a temporary worker, not an OS security sandbox."""
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED

from .input_errors import InputIssue
from .private_file import write_private
from .scanners import scan_text

MAX_DOCUMENT_BYTES = 2_000_000
MAX_TEXT_BYTES = 80_000


def _extract(data):
    try:
        import docx
        import defusedxml
        from defusedxml.ElementTree import fromstring
        from docx.table import Table
    except ImportError as exc:
        raise InputIssue("document_dependencies") from exc
    if not data.startswith(b"PK\x03\x04"):
        raise InputIssue("document_invalid")
    with ZipFile(BytesIO(data)) as archive:
        members = archive.infolist()
        if len(members) > 256 or sum(info.file_size for info in members) > 8_000_000:
            raise InputIssue("document_limit")
        names, elements = set(), 0
        for info in members:
            name = info.filename.lower()
            if (name in names or "\\" in name or ":" in name or PurePosixPath(name).is_absolute()
                    or ".." in PurePosixPath(name).parts or info.flag_bits & 1
                    or info.compress_type not in (ZIP_STORED, ZIP_DEFLATED)):
                raise InputIssue("document_invalid")
            names.add(name)
            if info.file_size > 2_000_000 or info.file_size > max(1, info.compress_size) * 100:
                raise InputIssue("document_limit")
            if (name.startswith(("word/media/", "word/embeddings/", "word/header", "word/footer", "word/footnotes", "word/endnotes", "word/comments"))
                    or "vba" in name or name.endswith((".bin", ".exe"))):
                raise InputIssue("document_unsupported")
            if info.is_dir() or name.startswith("docprops/thumbnail."):
                continue
            if not name.endswith((".xml", ".rels")):
                raise InputIssue("document_unsupported")
            with archive.open(info) as stream:
                content = stream.read(2_000_001)
            if len(content) > 2_000_000:
                raise InputIssue("document_limit")
            tree = fromstring(content, forbid_dtd=True, forbid_entities=True, forbid_external=True)
            for element in tree.iter():
                elements += 1
                if elements > 100000:
                    raise InputIssue("document_limit")
                local = element.tag.rsplit("}", 1)[-1]
                if local in {"drawing", "pict", "object", "altChunk", "ins", "del", "instrText", "fldSimple", "footnoteReference", "endnoteReference", "commentReference", "txbxContent", "sdt", "smartTag", "customXml", "subDoc", "oMath", "oMathPara"}:
                    raise InputIssue("document_unsupported")
                if local == "Relationship" and element.get("TargetMode", "").lower() == "external":
                    raise InputIssue("document_unsupported")
                if local == "gridSpan":
                    span = element.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "1")
                    if not span.isdigit() or not 1 <= int(span) <= 64:
                        raise InputIssue("document_limit")
        if "word/document.xml" not in names or "[content_types].xml" not in names:
            raise InputIssue("document_invalid")
    document = docx.Document(BytesIO(data))
    blocks, size = [], 0

    def add(text):
        nonlocal size
        size += len(text.encode("utf-8")) + 1
        if size > MAX_TEXT_BYTES:
            raise InputIssue("document_limit")
        blocks.append(text)

    for block in document.iter_inner_content():
        if isinstance(block, Table):
            if len(block.rows) > 2000 or len(block.columns) > 64:
                raise InputIssue("document_limit")
            for row in block.rows:
                if any(cell.tables for cell in row.cells):
                    raise InputIssue("document_unsupported")
                add("\t".join(cell.text for cell in row.cells))
        else:
            add(block.text)
    text = "\n".join(blocks)
    if not text.strip():
        raise InputIssue("document_empty")
    if not scan_text(text)["safe_to_include"] or "\x00" in text:
        raise InputIssue("document_scan")
    return {"text": text, "text_sha256": sha256(text.encode("utf-8")).hexdigest(),
            "parser": f"python-docx/{docx.__version__};defusedxml/{defusedxml.__version__}",
            "truncated": False, "representation": "paragraphs_and_tables_plain_text"}


def extract_docx(data: bytes):
    if not isinstance(data, bytes) or len(data) > MAX_DOCUMENT_BYTES:
        raise InputIssue("document_limit")
    with tempfile.TemporaryDirectory(prefix="pm-bg-doc-") as directory:
        # Only this private copy reaches the parser, not the original project path.
        write_private(Path(directory) / "input.docx", data)
        env = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "LANG", "LC_ALL") if key in os.environ}
        env.update({"PYTHONPATH": str(Path(__file__).resolve().parent.parent), "TEMP": directory, "TMP": directory})
        try:
            result = subprocess.run([sys.executable, "-m", "premium_model_budget_governor.document_extract", "--worker"],
                                    cwd=directory, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, timeout=15, check=False,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise InputIssue("document_worker") from exc
    if result.returncode != 0 or len(result.stdout) > 600_000:
        raise InputIssue("document_worker")
    try:
        value = json.loads(result.stdout)
        if not isinstance(value, dict):
            raise InputIssue("document_invalid")
        if value.get("ok") is not True:
            code = value.get("code")
            if code not in ("document_dependencies", "document_invalid", "document_limit", "document_unsupported", "document_empty", "document_scan"):
                code = "document_invalid"
            raise InputIssue(code)
        extracted = value["result"]
        text = extracted["text"]
        if (not isinstance(text, str) or len(text.encode("utf-8")) > MAX_TEXT_BYTES
                or sha256(text.encode("utf-8")).hexdigest() != extracted["text_sha256"]
                or extracted.get("truncated") is not False or not scan_text(text)["safe_to_include"]):
            raise InputIssue("document_invalid")
        return extracted
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise InputIssue("document_invalid") from exc


if __name__ == "__main__":
    try:
        if sys.argv[1:] != ["--worker"]:
            raise InputIssue("document_invalid")
        with Path("input.docx").open("rb") as stream:
            data = stream.read(MAX_DOCUMENT_BYTES + 1)
        if len(data) > MAX_DOCUMENT_BYTES:
            raise InputIssue("document_limit")
        print(json.dumps({"ok": True, "result": _extract(data)}))
    except InputIssue as exc:
        print(json.dumps({"ok": False, "code": exc.code}))
    except Exception:
        print(json.dumps({"ok": False, "code": "document_invalid"}))
