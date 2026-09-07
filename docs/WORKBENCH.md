# Local Workbench Preview

Status: rc.3 published the direct workbench; multi-stage changes below are local
post-rc.3 development, not included in that immutable release. The landing page remains a
separate illustrative demo. This workbench connects to the real local planner
and read-only execution adapter; it is not yet the finished product goal.

## Launch

After installing a version containing the workbench, run once from your project:

```sh
pm-bg serve
```

Or explicitly register one or more project folders:

```sh
pm-bg serve --project /path/to/project --project /path/to/another-project
```

The command chooses an available loopback port and opens a private local session.
Keep the launch link private. It contains a random local session key in its URL
fragment, which the page removes after loading and holds only in memory. Refreshing
requires reopening the original launch link. Reopening that link reconnects to an
active task without submitting it again. The key is not persisted in browser storage;
do not assume refreshing stops an active task.

Use `--no-browser` to suppress browser launch. `--data` chooses the local receipt
directory (default `~/.pm-bg/workbench`). An optional `--session-file` writes a
private launch-link file for local automation; it contains a session secret and
must never be committed or shared. Normal graceful shutdown removes that file;
abrupt termination may leave it behind, although its server token stops working.

## Current Workflow

Choose a registered project, describe the task, select Astra Preferred or Economy,
and preview the budget. Browse files/images to select evidence inside the registered
project. You can also enter project-relative paths, one per line. No JSON file is
required. The picker shows at most 500 entries from the first 1,000 inspected per
directory and clearly labels partial listings; exact path entry remains available.
Project registration is available through Manage projects. Local development adds
an optional native folder chooser; desktop selection validation remains open.

The development workflow selector offers Direct (default), Prepare with Sol then
solve with Astra, or Draft with Sol then review with Astra. Both multi-stage paths
retain original text evidence and actual images, require compatible reasoning
on both models, and show every stage before approval. They are explicit choices,
not automatically inferred improvements. Extra calls may cost more than direct.

The final stage reserves an additional provisional 65,000 input-token allowance
for a bounded serialized handoff and instructions, without assuming caching.
This conservative estimate is not a tokenizer measurement or provider cap.
Empty, flagged or over-64-KB UTF-8 handoffs stop for review, not truncation.
Each stage settles before the next starts; overruns trigger replanning when the
remaining whole workflow no longer fits. Progress counts stages started, not
independently verified answers. Final receipts show per-model stage counters.

Started stage IDs persist before possible host dispatch. Recovery uses each
started stage's local terminal journal; a missing receipt preserves unknown usage
and blocks another run. Recovery never reruns stages or claims answers recovered.

Previews do not run models. Review the estimate and scope, then explicitly approve
the read-only task before execution. Changing form inputs invalidates the preview,
including changes made while a preview response is pending. The result displays
exposed token counts, projected credits and unavailable weekly attribution.

The Usage view reads prompt-free local receipts. Answers are not persisted there.
Do not interpret missing counters as zero. Connection failure does not mean a task
stopped, and no automatic retry occurs. Reconnect to task polls the existing ID.
Stop task sets a local cancellation signal and waits for a terminal result; it
does not guarantee a provider refund. A pre-dispatch stop must have no lease.
After dispatch, unknown usage retains the reservation and blocks further work
until operator reconciliation. The receipt displays the still-reserved estimate.

An OS-backed exclusive lock owns the server data directory. After the old server
exits, the next owner marks abandoned running records as unknown usage without
releasing their reservations. Lock-file presence or a stale task status alone is
not a liveness test. A dead parent does not prove provider work stopped.

## Saved Projects

**Manage projects** accepts an absolute local folder path and explicit access
approval. Saved folders are stored in the workbench's local database and return
after restarting with the same data directory. Adding a folder does not run a
model or write into that folder. In local development, **Choose folder** opens
an optional Tk desktop dialog on the server computer, not on a remote browser's
device. Selecting a folder only fills the path and clears prior access consent;
**Add project** still requires separate approval and normal path checks.

The dialog runs in an isolated child process, with one dialog per server and a
90-second parent-side timeout. Missing Tk or a desktop session, cancellation and
errors leave manual absolute-path entry available. If the server abruptly exits,
an open OS dialog may need to be closed manually. Nothing is automatically added.
Process contracts and browser response fixtures are tested; actual native selection
and platform-specific behavior remain unverified. This feature is newer than the
qualified dev1 wheel and is not in published rc.3. Initial graphical installation
is a separate remaining requirement.

The UI can remove saved registrations without deleting project files or usage
history. Removal invalidates that project's pending previews and is refused
while a run is active. Launch-supplied roots are labeled separately and must be
changed in the launch command. Switching folders clears evidence/image paths.

When a saved folder is also configured at launch, its saved registration remains
visible and removable in the manager, without a duplicate task-selector option.
The UI warns that removing this registration does not revoke launch access.
Even when both registrations have the same ID, removal preserves the launch
configuration. Reusing one ID for different folders is rejected at startup.

Registration excludes home, drive root, known credential directories and governor
data. These checks are not a complete sensitive-folder detector; approve only
folders suitable for the task's read-only tools. Registration is capped at 32
projects. Missing or newly invalid saved folders remain visible in Manage projects
with an unavailable warning and a removal action, but are absent from the task
selector. Restore the folder and restart, or remove and explicitly register the
new location. A changed resolved target is not silently accepted on restart.
Folder identity is rechecked at browsing, host lookup, preview and execution;
these are local boundary checks, not protection from a malicious local OS account.

## Host Options

Task, project, budget, evidence, image and allowance validation can return fixed,
field-specific guidance. The UI focuses the affected field, opens a containing
allowance panel when necessary, and clears the message after editing. Source
excerpts, credentials and raw host exceptions are not included in those messages.
Unexpected errors still use the generic service message.

Reasoning options come from the selected project's live host catalog on connection,
project change and **Check setup**. Mode and image selection filter compatible
models locally. An unavailable previous effort stays visible and invalid until
the user chooses a supported option; it is never silently downgraded. Preview and
execution still recheck host support, so the displayed catalog is not admission
authority. Catalog lookup does not run a model or verify model quality/access.

## Recorded Receipt Recovery

In Usage, **Recover recorded usage** checks locally journaled terminal host
evidence and reconciles the original lease without another model call. Missing
evidence remains unknown, never zero. Recovered accounting does not restore the
answer. See [recovery boundaries](RECEIPT_RECOVERY.md).

## Transport Boundary

Optional launch-link files are created with restrictive permissions before secret
bytes are written, then replaced atomically. Windows uses a protected current-user
DACL; POSIX uses mode 0600 (verified in Ubuntu/WSL, not yet macOS).
Normal shutdown removes the file only if its content still matches the launch
record. The token also appears in the local terminal output; keep that output
private. These controls do not protect against the same OS account or administrators.

- Binds only to `127.0.0.1`; there is no LAN/public bind option.
- API requires a random bearer session token and the exact local Host header.
- POST also requires the exact Origin; cross-site Fetch Metadata is rejected.
- No CORS permission is returned. CSP disallows framing, inline/evaluated scripts,
  external connections and form submission. Static files use an exact allowlist.
- JSON requests have a 64 KB bound; duplicate lengths/transfer encoding are rejected.
- At most 16 HTTP connections are handled concurrently; saturated connections close.
- Source exceptions and host output are not forwarded to the browser.
- Model answers are rendered with textContent, not interpreted as HTML.

This is a single-user local utility using the Python standard HTTP server, not a
hardened internet service. It does not defend against a compromised OS account.
Do not port-forward it, expose it through a public tunnel, or publish launch tokens.
Bounded saturation/recovery is tested; broader security review remains a release gate.

## Verified So Far

**Check setup** opens a status report with recovery actions. **Download setup
report** saves a local JSON file containing only allowlisted version and status
fields. It excludes task text, paths, account identifiers, session tokens, logs
and usage history. Review it before attaching it to an issue; downloading does
not submit anything or start a model call. A failed check clears the previous
report so stale diagnostic data cannot be downloaded as a new result.

- Unit/service tests exercise approval, replay, evidence mutation, image snapshots,
  malformed receipts, cross-instance admission and retained unknown usage.
- Real loopback HTTP tests cover token/Host/Origin checks, request limits, asset
  boundaries and asynchronous execution with an injected executor.
- Browser checks at 1440, 390 and 320 pixels used the live host catalog and planner,
  verified nonblank budget graphics, approval invalidation and no overflow/errors.
- Receipt rendering and stale-response UI behavior were tested using explicit
  browser fixtures, including stop and reconnect. No model turn was executed by those checks. They are not an
  end-to-end real-model savings or quality experiment.
- The rebuilt local wheel includes byte-identical HTML/CSS/JavaScript, setup
  diagnostics and superseded-preview cleanup. Windows and Ubuntu/WSL installed
  regression each passed 254 tests with one platform-specific skip. See
  [Windows qualification](../artifacts/onboarding/windows-preview-lifecycle-regression.json)
  and [Ubuntu/WSL qualification](../artifacts/onboarding/linux-wsl-preview-lifecycle-regression.json).
  This wheel remains unpublished; macOS and real-model qualification are separate.
  Subsequent experiment-reporting and launch-registration fixes are covered by
  checkout tests, not that historical wheel hash; rebuild before release.

Later qualification supersedes that historical package baseline: the dev2 wheel
passed 304 tests with one platform-specific skip on Windows and Ubuntu/WSL,
including optional MCP and removal. See [rc.4 candidate notes](RELEASE_CANDIDATE_RC4.md)
for candidate-specific evidence rather than transferring an older wheel hash.
One approved real UI-to-Astra public text task completed with settled usage;
[its report](../artifacts/approved-astra-ui-smoke-2026-09-07.md) records actual
host counters, estimated credits and Codex-only grading. Multi-stage real calls,
human onboarding and comparative savings are still unproven.

Evidence: [browser reports](../artifacts/workbench-qa/), `tests/test_local_server.py`,
`tests/test_workbench.py`. The complete goal, including real tasks and human trials,
remains tracked in [PRODUCT_GOAL_PROGRESS.md](PRODUCT_GOAL_PROGRESS.md).
