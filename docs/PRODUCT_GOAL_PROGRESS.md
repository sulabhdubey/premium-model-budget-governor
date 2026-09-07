# Product Goal: Useful and Easy to Use

Owner: Sulabh Dubey. Engineering: Codex under owner direction.
Objective: approachable, evidence-backed Astra use within a whole-workflow budget.
This file tracks the full pinned goal; passing a phase's tests does not complete it.

## Acceptance Register

| Phase | Required outcome | Evidence / current gap |
| --- | --- | --- |
| 1. Baseline | Claims mapped to implementation; supported journeys; quality, tokens, cost, time, setup baselines | PRODUCT_BASELINE.md maps the current surface. Missing human setup and representative task-latency measurements remain explicit. |
| 2. Installation | Guided isolated install, compatibility/auth/MCP checks, recovery, reversible integrations, clean environment tests | Doctor and preview-first installer implemented. Windows and Ubuntu/WSL installed-wheel regression, MCP and removal passed. macOS and remote CI remain unverified. GUI initial setup and human trials remain. |
| 3. Everyday interface | Plain-language task, project/evidence/images, Astra Preferred/Economy, preview/approval/execution/progress/receipt; responsive | Local HTTP/UI, file picker and stop/reconnect implemented. Live preview QA at 1440/390/320 passed; execution UI uses declared fixtures. Real-model full-flow and human validation remain. |
| 4. Optimization | Direct/prepared/review workflows measured end-to-end; preserve capabilities; reviewed calibration and rollback | Reviewed policy proposal/approval/rollback is implemented and tested. No real evidence set qualifies for activation. Representative matched comparisons and prepared/review workbench execution remain open. |
| 5. Controls | Actual usage ledger/UI; honest units; cancellation/crashes/timeouts/retries/concurrency/expiry/unknown usage; local app security | Receipt-journal recovery, unknown-spend retention, process ownership, HTTP boundaries and private launch files are tested. Missing terminal usage still requires reconciliation; independent security review remains. Native hooks stay supplementary. |
| 6. Validation | Fresh bounded RTA-Net/CircuitProof tasks; coding/research/writing/visual/review comparisons; negative results; technical and nontechnical volunteers | Independent real tasks and human onboarding trials not completed. Synthetic cases cannot substitute. |
| 7. Release | Accurate docs, screenshots, demo, license/security notices, release candidate then release, feedback/diagnostics/outreach materials | rc.2 is the baseline, not completion of this new product goal. New product release waits for its acceptance evidence. |

## Working Contract

- Astra Preferred never silently becomes Sol-only. Compare complete workflow cost.
- Estimates are not provider bills; weekly allowance conversion remains unknown.
- Reserve before execution; retain uncertain usage; no reset credits without explicit request.
- Preserve required images, tools and reasoning. Unsupported work gets an explanation,
  not a falsely equivalent capability-reduced result.
- Use relevant skills, test-first changes, full regression, and rendered browser QA.
- Preserve private projects, existing changes and credentials. Publish sanitized evidence only.
- Human recruitment, credentials and unavailable host capabilities are external dependencies.
- Maintain this register through all phases; never redefine the goal to fit current tests.

## Current Checkpoint

2026-09-07: read the complete attached objective. Clean baseline commit
`f0fbee3e7de8d30212dac4579162483282d20d5a`; `python -m pytest -q`:
133 passed in 4.69 seconds. This is regression execution time, not task latency.
No additional paid worker call was needed for baseline inspection.

2026-09-07, onboarding slice:

- Added `pm-bg doctor [--offline] [--json]`, with credential-safe version/login
  categories, optional MCP detection and recovery instructions; no model calls.
- Added preview-first isolated installer and receipt-bound runtime removal.
  Existing directories/configuration are preserved. Failed install recovery is tested.
- Corrected README packet/ranking/security claims against actual implementations.
- Added clean-wheel installation verifier and Windows/Linux/macOS CI definitions.
- Real fresh Windows/Python 3.13.7 core install: 9.673 seconds; full smoke 10.49 seconds.
- Optional MCP fresh install: 62.07 seconds; full smoke 66.69 seconds, including
  stdio initialization, tool listing/call and owned-runtime removal.
- These are machine timings, not human onboarding results. Both reports are in
  `artifacts/onboarding/`; no prompts, credentials or account identifiers included.
- Full local regression: 146 passed, 1 skipped in 4.87 seconds. Windows denied
  symlink creation, so the real symlink test skipped; other protected-path tests passed.
- All verification processes finished; disposable runtimes removed. No extra paid
  model execution or reset. Changes remain local; no new release/push this slice.

## Next Action

2026-09-07, workbench service slice:

- Added `workbench.py`, reusing the planner, App Server adapter and budget ledger.
- Plain-language preview binds project, evidence, images, effort, mode and cost;
  explicit approval is required. Astra Preferred never silently becomes Sol-only.
- Preview expiry, altered evidence, replay and cross-instance simultaneous dispatch
  are tested. Unsupported capabilities are rejected rather than reduced.
- A failing image-mutation test led to dispatching staged approved bytes; a failing
  malformed-receipt test led to validating tokens against ledger settlement.
- History excludes prompts, evidence paths and answers. Unknown spend stops further
  dispatch without refunding reservations. Diagnostic messages withhold source content.
- Default context/image/output allowances are explicitly provisional, not measured.
- Full regression: 162 passed, 1 skipped in 4.85 seconds; diff whitespace check clean.
- These are injected-host service tests, not additional paid Astra runs or rendered
  browser evidence. No new server has been started. Changes remain local.
- Scope, bounds and integration gaps: WORKBENCH_SERVICE.md. A persisted running row
  is not a live-process proof; crash recovery/reconciliation must be built next.

2026-09-07, local transport and UI slice:

- Added local_server.py, a token-protected loopback API with exact Host/Origin,
  bounded JSON, CSP, allowlisted static assets, generic errors and async jobs.
- Added `pm-bg serve` and the packaged task/approval/result/usage interface.
- Generated a design concept; corrected its inaccurate USD labels to estimated
  credits in implementation. Live values come from the Python planner.
- Browser QA: 1440/390/320, no horizontal overflow or page/console errors; nonblank
  budget graphic, live host preview and approval invalidation verified.
- Simulated receipt rendering and delayed-preview mutation were tested separately;
  they did not execute a model task. Image generation was used for design, not a
  workload savings experiment. No model worker runs or resets were started.
- Full regression: 169 passed, 1 skipped in 8.10 seconds. Local wheel includes
  all three UI assets byte-identically (SHA256 recorded by the build output).
- Background development server PID 12720 was started after verified shutdown of
  PID 23024. Before future use, verify the current handle/process and private
  `build/local-ui-session.json`; do not infer liveness from this note alone.
- All QA/test commands completed. Server intentionally remains for trying the UI.
  Session links/logs stay in ignored build files; no public credentials committed.
- Changes are still local, not released. WORKBENCH.md describes exact current limits.

2026-09-07, stop/reconnect and file picking:

- Host cancellation checks between messages and during waits; pre-dispatch cancel
  differs from post-dispatch unknown usage. Reservations are not refunded blindly.
- Workbench validates that a claimed pre-dispatch cancellation has no lease. A
  failing misleading-receipt test exposed and closed that gap.
- Async jobs support stop requests and reconnect lookup without another submission.
  The browser blocks new submission while the existing task's status is uncertain.
- OS-backed runtime exclusivity and crash recovery are tested, including actual
  subprocess termination releasing the lock. Abandoned running rows become unknown,
  never free. This does not prove provider-side processing stopped.
- Project-bound evidence/image picker, filtered navigation, private-path exclusions
  and explicit partial-list bounds are implemented. Manual paths remain optional.
- Sixteen-connection transport bound and saturation recovery tested. Small rejected
  body draining fixed an intermittent Windows reset before the error response.
- Browser QA passed at 1440/390/320: file picker and live image-aware preview;
  desktop stop/reconnect/receipt paths used explicitly simulated responses.
- Full regression: 180 passed, 1 skipped in 9.77 seconds. No paid model task or reset
  was used in this slice. A one-call Astra UI test was requested asynchronously,
  pending the owner's response; do not infer approval from this note.
- Legacy PID 12720 was verified and upgraded to PID 21216. The old job-list endpoint
  returned 404; subsequent authoritative run-table inspection showed no run rows.
  The current session URL is only in ignored build/local-ui-session.json. Verify
  process and jobs before another restart; notes/files alone do not prove liveness.
- All tests/QA commands finished. The development server remains intentionally live.

2026-09-07, reviewed policy verification:

- Added scoped empirical proposals, explicit activation and rollback, expiry,
  integrity checks and current-feasibility checks. No production policy activated.
- Task type is selectable in the workbench. Project, family, mode and host-profile
  fingerprint constrain preference reuse; changed context allowances return to
  the default planner. These assertions were tested with synthetic evidence.
- Existing pilot audit: three comparisons, zero eligible, zero activated. See
  REVIEWED_POLICIES.md and artifacts/reviewed-policy/existing-evidence-audit.json.
- A failing integration test exposed misleading unconditional preview copy about
  learned ranking. The preview now states whether a reviewed preference applied.
- Parameterized tests preserve budget, capacity approval, capability, project-model
  and context-calibration blocks when consulting a reviewed preference.
- Full regression: 201 passed, 1 skipped in 9.64 seconds. Browser QA passed again
  at 1440/390/320 with live previews and no model executions. Stop/reconnect receipt
  checks remain simulated; this is not real-task savings or human-usability proof.
- Development server restarted only after verified identity and empty job list;
  latest PID is 4508. Revalidate process and authenticated jobs before future use.
- Work remains local/unpublished. Reviewed-policy administration currently uses
  CLI JSON; ordinary task execution does not. Real eligible calibration evidence,
  human trials and the broader phase requirements remain open.

2026-09-07, recorded terminal-usage recovery:

- App Server journals prompt-free validated terminal counters before settlement.
  Records bind task/call, configured model, host thread/turn and projected credits.
- Workbench recovery uses only this local journal, requires explicit action and
  never accepts browser-supplied tokens. Matching terminal evidence settles the
  original lease idempotently; the run becomes usage_recovered, not replayable.
- Missing evidence, partial events and old unjournaled runs remain unknown and
  retain their reservations. No blind refund or manual zero-spend override added.
- Injected settlement interruption, conflicting/corrupted records, missing evidence,
  replay and repeated recovery are tested. Checksums are not malicious-local-user
  protection; configured model identity is not provider attestation.
- Full regression: 209 passed, 1 skipped in 10.47 seconds. Browser checks passed
  at 1440/390/320, including simulated recovery controls and receipt rendering.
  No model tasks were executed and no reset was redeemed. Diff check passed.
- Server restarted only after verified identity and empty authenticated job list;
  latest PID 28520 must be revalidated before reuse. Session URL remains private.
- See RECEIPT_RECOVERY.md. Provider reconciliation for cases without terminal
  evidence remains open.
- Local, unpublished changes; real tasks, human trials, supported installation
  environments and the complete release checklist remain unfinished.

2026-09-07, host-driven reasoning options:

- Replaced the fixed UI reasoning menu with project-bound live host options.
  Only supported workbench model metadata is returned; extra host fields are omitted.
- Mode and image filtering preserve the previous effort explicitly when unsupported,
  requiring user choice rather than silently lowering it. Catalog refresh clears
  prior approval; stale asynchronous host results cannot replace newer results.
- Backend rejects malformed/oversized option fields and unregistered projects.
  Preview and dispatch retain their own fresh host checks.
- Full regression before the final transport assertion: 215 passed, 1 skipped in
  10.44 seconds. Final endpoint-focused suite: 11 passed. Browser QA passed at
  1440/390/320 using live initial catalogs plus labeled fixtures for a new max
  option and an incompatible image selection. No model execution or reset.
- Development server PID 49172 was started after verified idle-server shutdown;
  revalidate process and jobs before future restart. Changes remain unpublished.
- Human ease-of-use and real task quality/savings remain unproven; this slice only
  removes a hard-coded capability restriction in the existing read-only workbench.

2026-09-07, actionable field errors:

- Added an allowlisted error contract for project, task, budget, evidence, images,
  host compatibility and token allowances. No raw exception/source text is used
  for browser field messages; unexpected host failures remain generic.
- Inline errors identify and focus the field, expose aria-invalid/description,
  open a containing details panel and clear on edits. Stale asynchronous failures
  do not attach errors to newer task input.
- Full regression: 223 passed, 1 skipped in 11.70 seconds. Browser QA passed at
  1440/390/320 with labeled error fixtures, focus and correction assertions.
  No paid model tasks or reset credits were used. Diff whitespace check passed.
- Development server PID 11056 replaced the verified idle server. Revalidate its
  identity and authenticated job list before reuse; private launch URL is ignored.
- Work remains local. Guided project registration, real-task evaluation, human
  onboarding and release qualification remain required by the full phase register.
- Screenshot inspection exposed focus-scroll mask displacement. QA now replaces
  the project path with a fixed nonprivate label before captures; browser checks
  were rerun and the replacement screenshot inspected. No private path remains
  dependent on a correctly positioned screenshot mask.

2026-09-07, saved project management:

- Added authenticated approved folder registration, local persistence, duplicate
  handling, a 32-project bound, root/home/credential/data exclusions and reversible
  registration removal. Project files and usage history are never deleted.
- UI Manage projects supports explicit folder access approval and saved-project
  removal. Launch roots are identified separately. Project changes clear evidence
  and images; removing a project invalidates pending previews, including a race
  check before a preview can be saved. Running tasks prevent removal.
- Live browser add/remove flows passed at 1440/390/320 against an empty disposable
  build fixture, with no model turns. Existing browser checks remained green.
- Registration/service tests cover persistence and failure boundaries; HTTP tests
  verify auth, origin and explicit approval for both add and remove operations.
- Final full suite: 234 passed, 1 skipped in 12.75 seconds, including the two
  new transport cases. Diff check passed. No model call or reset used.
- Server PID 54072 replaced the verified idle server; verify identity and jobs
  before restarting. Changes remain local, uncommitted and unpublished.
- Remaining usability limits: absolute path entry rather than native folder picker;
  stale invalid saved registrations are omitted from selection but retained in
  storage, with no UI cleanup yet. These are documented in WORKBENCH.md.

2026-09-07, unavailable-project recovery:

- Invalid or missing saved roots now remain listed for explicit removal, while
  excluded from the task selector. Removing one after restart clears registration
  without deleting files. Manager opening refreshes availability.
- Saved path target changes are not silently restored as new authority. Folder
  identity is checked before browsing, host probing, preview and dispatch.
- Full regression: 236 passed, 1 skipped in 12.74 seconds. Browser QA passed at
  1440/390/320, including an unavailable-project rendering fixture and existing
  live project registration/removal checks. Mobile dialog screenshot inspected.
- No paid model tasks or resets used. Server PID 4800 replaced a verified idle
  instance; verify identity and authenticated jobs before any future restart.
- Native folder picking, supported-platform installer verification, real-task
  and human validation, and release qualification remain open. Changes are local.

2026-09-07, isolated package qualification and database lifecycle fix:

- Extended isolated installation checks to import current workbench/recovery/policy
  modules, serve packaged UI assets, reject unauthenticated API access and compare
  installed asset bytes against the checkout. No model host is invoked.
- Initial core and MCP qualification failed at workbench temporary-data cleanup:
  WinError 32 on workbench.sqlite3. SQLite transaction context managers did not
  close connections. This was a real lifecycle defect, not a missing wheel asset.
- Added a shared closing transaction context for workbench, budget, dispatch,
  receipt-journal, dashboard and prompt-gate connections. Regression tests cover
  commit/rollback and closed handles. Reviewed-policy normal paths already close
  connections explicitly. Full suite: 238 passed, 1 skipped in 12.89 seconds.
- Rebuilt wheel SHA256:
  0a6f86ad5050699d00587b5fc737e3cb50c4549770bc3150366182f952712b1e.
  The unchanged rc.2 version label is local only, not a replacement public asset.
- Clean Windows core check passed in 11.688 seconds; optional MCP check passed
  in 49.41 seconds including real stdio initialization/list/call and uninstall.
  Reports and asset hashes are under artifacts/onboarding/windows-workbench-*.json.
- No paid model turns or resets. Diff check passed. Development server PID 4020
  replaced the verified idle server; revalidate process and jobs before reuse.
- Linux/macOS execution, real-task validation, human trials and final public
  release remain open. Local fixes have not been committed or published.

2026-09-07, request-boundary security review:

- Duplicate JSON keys were reproduced as accepted; parser now rejects them at
  every object depth before invoking application code. No auth bypass was claimed.
- Content-Length now requires bounded ASCII digits before integer conversion;
  rejection-body draining follows the same bounded conversion discipline.
- Tests distinguish controlled header-only rejection from Windows reset/abort
  for unread unframed body bytes. Both must leave application handling untouched
  and the service available. Full suite: 245 passed, 1 skipped (final run this turn).
- LOCAL_SECURITY_REVIEW.md records scope, fixed findings, evidence locations and
  remaining launch-file, inherited-permission and crash-recovery limitations.
- No model calls, resets, release or server restart in this slice. Development
  server PID 4020 still loads the prior code; verify identity/jobs before upgrading.
  The previous qualified wheel must be rebuilt before publication.

2026-09-07, private launch files and policy error-path cleanup:

- Added restricted file creation before token writes: protected current-user-only
  Windows DACL via native APIs; POSIX 0600 creation; atomic destination replacement.
  Shutdown preserves a launch file whose contents have been replaced.
- Windows permissions were verified with .NET ACL inspection, avoiding unavailable
  PowerShell security module autoload. Tests confirm exactly one noninherited allow
  rule for the current user. Cross-account trials and POSIX execution remain open.
- Reproduced the reviewed-policy schema-initialization handle leak with a retained
  connection and injected failure; the exception path now closes the connection.
- Full regression: 251 passed, 1 skipped in 16.76 seconds. Diff check passed.
  No paid model calls or reset credits. No new wheel or public release this slice.
- Development server PID 44680 replaced the verified idle server and now loads
  parser and launch-file hardening. Revalidate its process/jobs before reuse.

2026-09-07, installed-wheel Windows and Linux qualification:

- Rebuilt current wheel SHA256:
  c9547b0d335cf7bb5e775e1cf5a21eaa2d1dae016c0504149f2e62d414db9484.
  It remains local/unpublished despite its rc.2 version label.
- Ubuntu/WSL Python 3.12.3 core install/service/uninstall passed in 3.418 seconds.
  The optional-MCP installed-wheel regression passed 251 tests, one Windows-only
  skip, in 15.76 seconds (26.964 seconds total qualification).
- Windows Python 3.13.7 qualification of the same wheel passed 251 tests, one skip,
  in 15.74 seconds (74.188 seconds total), including real MCP stdio and uninstall.
- Regression runs clear checkout import paths and use the isolated interpreter.
  Raw XML stays in ignored build/qualification; public JSON reports retain only
  aggregate results and hashes. Linux's first XML was moved there after completion.
- CI isolated-install jobs now request installed-wheel regression on Windows,
  Linux and macOS. Remote CI and macOS execution have not yet run for these changes.
- No paid model calls, resets, publication or development-server restart. Server
  PID 44680 is historical context only; revalidate before interacting with it.
- WSL evidence does not establish native Linux Codex execution or human usability.
  Real-task comparisons, independent review and the complete release gates remain.

2026-09-07, release-candidate documentation:

- README and quickstart now foreground the actual local workbench, project
  management, approval and receipts, with an explicit unreleased label. Public
  rc.2 is not represented as containing these changes.
- Linked Windows and Ubuntu/WSL installed-wheel evidence, separately from
  unproven quality, savings, human usability and macOS qualification.
- Bug report template now covers workbench and uncertain-usage recovery while
  warning against sharing launch tokens, raw logs, databases or private evidence.
- No paid calls, resets, version changes or publication in this documentation
  slice. These edits do not close the independent-validation or release gates.

2026-09-07, workbench setup diagnostics:

- Check setup now opens recovery guidance and a downloadable allowlisted report.
  Raw API fields, logs, paths, account identifiers and task contents are excluded;
  versions and status categories are constrained before export. No automatic
  submission occurs. Failed checks clear the previous report.
- Browser tests downloaded and parsed the report at 1440/390/320 pixels, proving
  injected private fields were omitted. Existing workbench flows also passed,
  without page/console errors or model calls. Full regression: 251 passed,
  one skipped in 16.66 seconds.
- New web assets need a rebuilt qualified wheel. Earlier installation reports
  remain evidence of their specific hashes, not this subsequent UI change.
- No paid calls, reset credits, commits or publication this slice.

2026-09-07, preview lifecycle and rebuilt-package qualification:

- Extended browser diagnostics tests to verify failed checks clear exportable
  data and recovery guidance. Download allowlisting and failure reset passed
  at 1440/390/320 pixels; screenshots were visually inspected.
- An initial browser run timed out waiting for preview success. Inspection
  identified the bounded eight-preview pool and missing invalidation cleanup.
  Added authenticated, ID-only discard, cleanup on task edits and stale replies,
  and waiting for cleanup before requesting the next preview. Running-task
  records and accounting are not removed. Two focused tests failed before the
  implementation and passed after; HTTP validation has separate coverage.
- The successful browser rerun had no page/console errors, no overflow and no
  model turns. The full checkout suite passed 254 tests, one skipped.
- Final rebuilt wheel SHA256:
  cf7a30fbd50d1b07f2fab34d8d6ce52bc7f991e9ce44fc1ccf821fbc9b9b2f69.
  Windows installed regression: 254 passed, one skipped, 16.44 seconds.
  Ubuntu/WSL installed regression: 254 passed, one skipped, 20.02 seconds.
  Both verified real MCP stdio, packaged assets, import isolation and uninstall.
  Reports: artifacts/onboarding/*-preview-lifecycle-regression.json.
- Verified idle development server restarted as PID 32564. Revalidate identity
  and jobs before future interaction. No paid model calls, reset credits, commit
  or publication. The unchanged rc.2 version label remains local only.
- Acceptance register refreshed to distinguish implemented policy/recovery
  controls from missing empirical benefit, independent review and human trials.

2026-09-07, preregistered field-trial starter material:

- Added five distinct authored tasks for coding, research, writing, release
  review and visual interpretation. Prompts, required grading criteria and
  negative-evidence cases are fixed before any model run in suite.json.
- Rendered and visually inspected an 800-pixel queue chart with a conflicting
  stale note. The PNG is a supplied image, not substituted by extracted text.
- snapshot.json fingerprints the suite and exact inputs. LF attributes preserve
  text byte identity across Git checkouts. Changed inputs require a reviewed
  new version, not silent rubric changes after results.
- prepare_trial_task.py copies only the selected public inputs and prompt into
  a new folder, excluding grading criteria. Focused tests verify hashes, family
  coverage, facts, staging separation and refusal to overwrite existing folders.
- This is preregistration and test infrastructure, not real model results,
  independent project evidence, trained calibration or human trial completion.
  No paid calls, resets or publication; product package source is unchanged.
- Full checkout regression: 258 passed, one skipped in 17.40 seconds. Earlier
  installed-wheel reports retain their original 254-test qualification scope.

2026-09-07, comparable experiment units and workflow timing:

- Reproduced a mixed-unit aggregation bug: internally matched billed and
  token-estimated pairs were averaged together. Seven focused tests failed
  before the fix. Reports now group cost deltas by basis and withhold the
  combined mean when multiple bases occur.
- Optional total_elapsed_seconds records complete workflow wall time with
  finite, nonnegative numeric validation. Missing/incomplete timing stays
  unknown. Timing includes failed outcomes and is labeled caller-reported;
  faster completion never overrides a quality regression.
- Full regression: 265 passed, one skipped in 17.48 seconds. Subsequent MCP
  transport assertions and experiment tests: 23 passed in 2.64 seconds, using
  synthetic receipts over real stdio without model calls.
- Historical contract-pilot input still loads through the CLI with unchanged
  projected cost difference and null time difference. No historical receipts
  were rewritten or supplemented with invented timings.
- Public experiment documentation explains measurement boundaries, parallel
  duration versus wall time, quality checks and separate accounting units.
  Updated package code requires a new wheel qualification before release.
- No paid calls, reset credits, publication or server restart. Independent real
  tasks, human trials, capability integration and remaining release gates stay open.

2026-09-07, saved and launch project identity recovery:

- Three failing tests reproduced hidden saved registrations when their folder
  was also supplied at launch, removal of launch access on equal IDs, and silent
  collisions between one ID and different folders.
- Startup now retains saved registrations for management, suppresses redundant
  selector options, rejects conflicting identities and preserves launch-supplied
  roots during saved-registration removal. UI warnings explain remaining access.
- Focused project tests: 14 passed. Full regression: 268 passed, one skipped in
  17.05 seconds. Browser QA at 1440/390/320 passed with a declared launch-alias
  fixture, real project add/remove flows and no page/console errors or overflow.
  The 320-pixel manager screenshot was visually inspected.
- Verified idle development server restarted as PID 10160; revalidate identity
  and jobs before future interaction. No paid calls, resets or publication.
- The new package source has not been wheel-qualified. Earlier installed reports
  retain their exact historical hashes and scope. Real-task comparisons, human
  trials, capability integration and release remain open.

2026-09-07, distinct rc.3 package and local qualification:

- Confirmed GitHub's latest prerelease is v0.4.0-rc.2. Bumped local package to
  0.4.0rc3 and plugin to 0.4.0-rc.3, with consistency assertions. No existing
  published asset was replaced. Added candidate notes and an unreleased changelog.
- Built candidate wheel SHA256:
  8273260df59499fc37adc94a3a15769ab205c47cfe3b2fb85352a165bfc81ed7.
  Windows installed-package regression: 268 passed, one skipped in 16.25 seconds.
  Ubuntu/WSL installed-package regression: 268 passed, one skipped in 20.53 seconds.
  Both include real MCP stdio, byte-identical web assets and clean uninstall.
- Four focused version/site tests passed after plugin alignment. The candidate
  notes distinguish working read-only direct execution from missing capabilities,
  independent project/model evidence, human onboarding and stable-release gates.
- Targeted credential/private-path patterns found no matches in the new public
  onboarding/policy reports and selected release/progress documents. This is a
  bounded pre-publication check, not a complete independent security assessment.
- Local preparation only: no commits, push, release upload, paid model calls,
  resets or server restart. Remote CI and candidate publication are next release
  steps; the full seven-phase goal and its external validation gates remain open.

Next: candidate public-file review, remote CI and prerelease publication;
continue independent task and human validation without calling them complete.
Run the bounded real
UI task only once explicitly approved. Preserve the full phase register:
capability-aware workflow comparisons, Linux/macOS installation execution,
reviewed calibration/rollback, independent projects, human trials and release
are not complete. Read-only tasks are not substitutes for write/Desktop-only work.
