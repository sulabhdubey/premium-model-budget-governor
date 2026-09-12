# Development Support Matrix

This describes the current unreleased checkout, not a claim that every addition is
in the published release. Detection, automated qualification and human usability
are different evidence levels. Recheck the exact artifact before upgrading.

| Surface | Evidence | Boundary |
| --- | --- | --- |
| Core CLI | Windows Python 3.12/3.13 and Ubuntu WSL Python 3.12 isolated-wheel checks | Declares Python 3.10+; native Linux desktop, macOS and remaining Python versions still need their own evidence |
| Optional MCP | Actual local stdio initialize/list/call in qualification | Requires a configured compatible client; does not control unrelated chats |
| Codex App Server | Live catalog/hooks discovery on CLI 0.153.4; prior bounded execution trials | Current discovery starts no model turn; advertised options are not all executed or provider-attested |
| Existing Codex desktop task | Advisory policy and explicit local log observations | No universal pre-model enforcement or automatic removal of existing context |
| Workbench | Prior rendered Windows browser checks at desktop/mobile widths | Small viewport is not remote/mobile-host support; unaided human setup remains unproven |
| Document intake | Basic DOCX worker/extraction/preview tests | Not full layout, arbitrary Office/PDF support or an OS-level malware sandbox |
| Local observations | Transactional CLI/journal tests, real bounded counter intervals | Not whole-account billing, guaranteed model attribution or savings evidence |
| OTLP preview | Official protobuf JSON parse and binary round trip | No live Collector/backend, network delivery or automatic tracing |
| Ordinary ChatGPT and other hosts | No controlled adapter qualification | Unsupported for automatic budget enforcement; no capability implied by an API gateway |

The latest local host probe advertised text/image and low through ultra reasoning
for Astra, Sol and Terra, and low through max for Luna. It found no configured hooks
in the checked project. These are one host's detected values, not universal product
guarantees. Required capabilities must still be checked at dispatch; do not replace
requested Astra work with a cheaper model simply because a feature is untested.

## Dependency Scope

Core has no runtime dependencies. The optional MCP integration uses the MCP 2.x
library directly; its separate CLI extras are not needed by Governor's module entry
point. A future major SDK version requires explicit compatibility qualification.
Document parsing is a separate opt-in extra. Normal package resolution can change
transitive versions; a successful dependency resolution is not an installation,
vulnerability audit or reproducible lockfile.

The official protobuf library used to test OTLP wire shape is a development-only
check, not a new default dependency or telemetry endpoint. MCP may itself depend on
an observability API package; that dependency alone does not mean Governor has
enabled telemetry delivery.

## Remaining Release Evidence

Local Linux qualification uses WSL2 and a fresh temporary virtual environment,
not the system Python packages. It covers actual stdio MCP, DOCX worker, collector,
loopback asset serving, regression and owned uninstall. It does not establish
native Linux browser/folder-picker behavior, Linux Codex execution, macOS support
or a hosted CI result. Platform-specific skipped checks remain explicitly excluded.

Qualify the exact new wheel and plugin after final changes. Run the declared CI
matrix, inspect dependency licenses and current advisories, complete privacy/media
review and collect actual owner/independent usability evidence. Signed installers,
additional hosts, network observability and write-enabled execution need separately
justified designs and tests; they are not implied by this matrix.

The local CI definition now requests installed regression, actual MCP and document
qualification on Ubuntu, Windows and macOS in the same isolated-install job.
Editing that matrix is not a hosted result: unexecuted platform cells remain open.
