# Document-First Read-Only Work

Use the existing Work task and evidence picker for writing, research and document
analysis. A document does not trigger a different model: direct Astra remains the
default in Astra Preferred mode, with the existing scope, budget preview and approval.

Supported input is UTF-8 text (including Markdown) and, with an optional dependency
extra, basic DOCX paragraphs and non-nested tables. The preview displays extracted
DOCX text before approval. Table cells use tab-separated plain text, not the original
layout. Verify this representation is sufficient for the task. No model run starts
merely by parsing a document or viewing its text.

## Optional Installation

The guided installer accepts `--documents`, combinable with `--mcp`:

```text
python scripts/install_governor.py install --documents
```

This is a preview; the installer describes the isolated runtime and asks for the
explicit `--yes` invocation. The extra downloads python-docx and defusedxml plus
their dependencies from the configured package index. It does not install Office,
alter Codex settings or start a model. The core package remains dependency-free.

For an existing deliberately managed Governor Python environment, the corresponding
extra is `premium-model-budget-governor[documents]`. Do not assume the currently
published older release contains this local development feature.

## Boundaries

- Up to eight selected evidence files, with existing project-path/private-file
  checks. DOCX input is at most 2 MB; each extraction is at most 80 KB UTF-8 text,
  with at most 240 KB combined text evidence. No silent text truncation.
- ZIP preflight rejects duplicate/traversing names, unsupported compression,
  encrypted entries, excessive expansion and common embedded/macro structures.
  At most 256 entries, 8 MB declared expanded content, 2 MB per member and 100,000
  XML elements are accepted. XML is parsed with DTD/entities/external expansion
  prohibited before python-docx opens the package.
- Images, headers/footers, footnotes, comments, tracked changes, fields, content
  controls, equations, nested tables, external relationships and other unsupported
  structures are withheld. Use a separately reviewed representation and explicit
  image evidence where appropriate; do not silently replace required visual input.
- A private temporary copy is parsed by a subprocess with a 15-second timeout and
  an allowlisted environment, without the original file path or caller credentials.
  The temporary copy is removed after the worker exits, including timeout failure.
  This is ordinary temporary-file cleanup, not guaranteed secure erasure.
- The worker is NOT an OS security sandbox or a hard memory/egress limit. The library
  path does not intentionally execute macros or fetch links, but dependency
  vulnerabilities remain a risk. No antivirus clearance or malware-free guarantee
  is established by these preflight checks or text patterns.
- Extracted text is untrusted evidence. Pattern scans are heuristic. Error responses
  use allowlisted messages, not parser traces or source snippets. Private text is
  visible in the authenticated local preview and may be sent after run approval.
- Source hash, extracted text/hash and parser version are rechecked before dispatch.
  Changes require a new preview. No source document is edited. Read-only model tools
  retain their disclosed project scope and inherited connector boundaries.

## Deferred Formats

PDF, legacy DOC, DOCM, RTF, ODT, PPTX and XLSX are not supported by this intake path.
They fail explicitly instead of being mistaken for ordinary text. There is no OCR.

Automatic PDF extraction is deferred pending a qualified resource-isolation path
and representative hostile/visual fidelity tests. The pypdf project documents that
text extraction can require memory far exceeding the compressed file size; a file
size cap alone is therefore not enough. [pypdf extraction guidance](https://github.com/py-pdf/pypdf/blob/main/docs/user/extract-text.md).

DOCX parsing reuses python-docx's documented document-order paragraph/table API
and file-like input, not a custom Word parser. [python-docx API](https://python-docx.readthedocs.io/en/latest/_modules/docx/document.html).
The optional dependencies have MIT (python-docx) and PSFL (defusedxml) metadata;
distribution and dependency qualification still belong to the exact release audit.

## Evidence And Remaining Gates

Tests exercise real temporary workers, paragraph/table extraction, common hostile
structures, timeouts, environment filtering, cleanup and source-change approval
invalidation. Optional browser QA (`qualify_workbench.py --documents`) generates
non-sensitive fixtures, previews an actual DOCX and verifies unsupported-format
rejection without dispatch. The expected HTTP 400 is recorded separately from
unexpected browser errors. These tests do not establish document-analysis quality,
unchanged Astra capability across formats, independent usability or general savings.

Installed-package qualification supports `check_installation.py --documents` and
checks the actual installed worker outside the checkout. A CI configuration change
is not proof that remote CI or every supported platform has already passed.
