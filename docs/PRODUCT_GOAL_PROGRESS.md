# Product Goal: Useful and Easy to Use

Owner: Sulabh Dubey. Engineering: Codex under owner direction.
Objective: approachable, evidence-backed Astra use within a whole-workflow budget.
This file tracks the full pinned goal; passing a phase's tests does not complete it.

## Acceptance Register

| Phase | Required outcome | Evidence / current gap |
| --- | --- | --- |
| 1. Baseline | Claims mapped to implementation; supported journeys; quality, tokens, cost, time, setup baselines | PRODUCT_BASELINE.md maps the current surface. Missing human setup and representative task-latency measurements remain explicit. |
| 2. Installation | Guided isolated install, compatibility/auth/MCP checks, recovery, reversible integrations, clean environment tests | Doctor and preview-first installer implemented. Dev2 passed Windows/WSL local qualification and Windows/Linux/macOS CI installation at d27a319; optional MCP tested locally and in Linux CI. Native desktop selection, GUI initial setup and human trials remain. |
| 3. Everyday interface | Plain-language task, project/evidence/images, Astra Preferred/Economy, preview/approval/execution/progress/receipt; responsive | One real approved Astra UI run passed. Live preview QA at 1440/390/320 includes opt-in focused catalog; failure/multi-stage UI uses declared fixtures. Human and native-dialog operation remain unverified. |
| 4. Optimization | Direct/prepared/review workflows measured end-to-end; preserve capabilities; reviewed calibration and rollback | Five-family/four-arm real pilot completed; direct Astra default retained. Smaller catalog showed a narrow one-task reduction and ships opt-in, with guidance-loss warning. Independent holdout and broad capability validation remain; no policy promoted. |
| 5. Controls | Actual usage ledger/UI; honest units; cancellation/crashes/timeouts/retries/concurrency/expiry/unknown usage; local app security | Receipt-journal recovery, unknown-spend retention, process ownership, HTTP boundaries and private launch files are tested. Missing terminal usage still requires reconciliation; independent security review remains. Native hooks stay supplementary. |
| 6. Validation | Fresh bounded private-project tasks; coding/research/writing/visual/review comparisons; negative results; technical and nontechnical volunteers | Five public fixture families and one fresh combined two-project read-only review completed. Public-fixture negative findings published; private-project findings withheld. Not independent matched project benchmarks; no human participants yet. |
| 7. Release | Accurate docs, screenshots, demo, license/security notices, release candidate then release, feedback/diagnostics/outreach materials | rc.3 is published. rc.4 qualification/publication is tracked in RELEASE_CANDIDATE_RC4.md; draft PR 1 and main-site promotion are distinct. Stable acceptance still requires missing human and broader evidence. |

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

2026-09-07, public candidate and remote qualification:

- Committed the reviewed candidate as efd3bcbdbb2ebe762c1259d4142e3aeeca251cbb
  on release/workbench-rc3 and pushed it. Opened draft integration PR #1; main
  and stable release were not changed by this branch publication.
- Push CI 34116571722 and PR CI 34116635180 both completed successfully.
  All Python 3.10-3.13 jobs passed. Remote installed-wheel core regression passed
  on Windows (268 passed, one skipped) and Linux/macOS (267 passed, two skipped).
  Linux also passed optional MCP installation/runtime verification. Downloaded
  sanitized reports were inspected, not inferred from a green job badge alone.
- Published v0.4.0-rc.3 at the exact tested commit as a prerelease, not latest
  stable. Wheel, installer and plugin archive digests match their local files.
  Public URL: https://github.com/sulabhdubey/premium-model-budget-governor/releases/tag/v0.4.0-rc.3
- GitHub Actions emitted Node 20 action-runtime deprecation notices but jobs
  passed. These are maintenance follow-ups, not failed application tests.
- Independent real tasks, human onboarding, capability integration and full
  stable-release acceptance remain open. No model calls or resets were used.
- This status update is newer than the immutable candidate tag. Current local
  documentation edits need their own follow-up commit; do not replace assets
  merely to alter release-status prose inside the wheel metadata.

2026-09-07, serial workflow execution core (not yet UI-integrated):

- Added an internal one-to-three-stage runner for server-held packets, with
  one task/root, unique call IDs, explicit approval, full estimate admission and
  serial ledger/receipt verification. It retains original image inputs across
  stages and stops for empty, oversized or flagged handoffs rather than truncating.
- Completed stage costs persist on cancellation or a need to replan after an
  overrun. Unknown usage stops dispatch and has a null total, separately from
  known completed costs. The core does not claim cross-process ownership or
  crash persistence; those remain required Workbench integration responsibilities.
- Eleven focused injected-executor tests passed. A large parametrized fixture
  initially produced Windows test-environment errors; short explicit test IDs
  fixed the harness issue. Final full regression: 279 passed, one skipped in
  16.82 seconds. No actual model stages ran.
- Not exposed through UI/MCP/CLI and not published: next integrate stored plans,
  persisted stage identities, stage-aware reconciliation, capability/evidence
  checks, approval/progress/receipts and browser tests. Do not advertise prepared
  workflows as ready merely because this internal core passes tests.
- Published rc.3 assets and tag remain unchanged; current work is local and
  uncommitted. No paid model calls, resets or development-server restart.

2026-09-07, multi-stage workbench integration (local, not in rc.3):

- Added explicit direct/prepared/review strategies to stored previews. Direct
  remains default; prepared and review use Sol then Astra, preserve original
  evidence/images and require host support on both stages. No automatic learned
  strategy promotion or savings inference.
- Integrated serial execution under existing atomic workbench admission, with
  durable planned/started stage IDs, per-stage host receipts, cancellation,
  remaining-budget checks and stage-aware terminal-journal reconciliation.
  Missing started-stage receipts retain unknown usage; no recovery reruns work.
- Added UI workflow choice, per-stage cost preview, started-stage progress and
  per-model receipts. Browser tests exercise live two-stage planning but intercept
  execution explicitly; no real multi-stage model result is claimed.
- Bounded serialized UTF-8 handoffs at 64 KB, with an additional conservative
  65,000 final-stage input allowance. Original data is preserved or rejected,
  never silently truncated; the allowance is not a provider cap.
- Full regression: 286 passed, one skipped in 16.98 seconds. Browser QA passed
  at 1440/390/320 with no page/console errors or overflow. The prepared mobile
  preview was visually inspected. Live execution still awaits bounded approval.
- Verified idle development server refreshed as PID 14704; revalidate before
  reuse. No paid calls, resets, commits or publication; rc.3 assets are unchanged.
- Further crash-boundary and multi-stage recovery auditing, empirical strategy
  comparisons, human usability and new package qualification remain required.

2026-09-07, multi-stage interruption verification (local, not in rc.3):

- Confirmed the cancellation boundary fix: a host-reported pre-dispatch stop
  becomes known cancellation only when lease and spending state are unchanged.
  Prior completed costs remain recorded; an unexpected lease retains unknown usage.
- Verified durable not_dispatched stage status for confirmed cancellation.
  Added real subprocess exits at first and second stages, both before terminal
  usage and after terminal usage but before settlement. The fixtures claim dispatch
  before exiting, release the OS runtime lock through process death, and recover
  under a new owner. Missing usage retains reservations; journaled usage settles
  without replay, including when later stages were only planned.
- Focused runner/workbench tests: 26 passed in 1.64 seconds. Full regression:
  294 passed, one skipped in 19.20 seconds. git diff --check passed with existing
  line-ending warnings. Removed an unused test import.
- Corrected outdated service documentation that described local multi-stage UI
  integration as absent. Published rc.3 remains direct-only and unchanged.
- No real model calls, resets, publication, server restart or new browser run.
  The four subprocess fixtures test simulated-host crash/accounting behavior,
  not provider execution, model quality, savings or human usability.
- Next: qualify the new package and real workflows after bounded approval;
  remaining interruption windows, image staging cleanup, broader comparisons,
  human onboarding and complete release acceptance remain open.

2026-09-07, development-wheel qualification:

- Advanced local package/source to 0.4.0rc4.dev1 and plugin to
  0.4.0-rc.4.dev.1; updated version assertions. Published rc.3 was not changed.
- Initial no-build-isolation attempt failed because the base Python had no
  Hatchling backend. Normal isolated pip wheel building succeeded without a
  global backend installation. Local wheel SHA-256:
  57143221d32c9c906ed3133de4e46281ff8cb3b20add39424cbaf1ac2137dea0.
- Tested that identical wheel outside checkout imports in disposable Windows
  Python 3.13.7 and Ubuntu/WSL Python 3.12.3 environments. Each passed 294 tests
  with one skip, actual MCP stdio initialize/list/call, packaged UI hash/auth
  checks, offline planning/diagnostics, preview-only installation and clean uninstall.
  Reports: artifacts/onboarding/windows-rc4-dev1-regression.json and
  artifacts/onboarding/linux-wsl-rc4-dev1-regression.json. Total qualification
  elapsed time was 73.804 seconds and 28.949 seconds respectively.
- Updated checkout README to distinguish published rc.3 direct execution from
  local multi-stage development and to link current package evidence. This prose
  edit occurred after the tested wheel was built: its embedded README metadata
  still has older preview text. Rebuild with aligned documentation and qualify
  the final bytes before publication; this wheel is an internal test artifact.
- No model calls, resets, host configuration edits, server restart, commit or
  publication. These results do not establish macOS behavior for the new code,
  real multi-stage benefit, human usability or stable-release readiness.
- Next: finish release-document alignment, real workflow/participant gates,
  and remaining user-experience gaps. Do not repeat synthetic qualification as
  a substitute for the outstanding empirical and human evidence.

2026-09-07, understandable complete and partial receipts:

- A rendered regression reproduced completed multi-stage headline input tokens
  displaying Unknown instead of the recorded total of 2000. The display now sums
  stage counters only when every participating counter is a nonnegative safe integer.
  Missing cached counts remain Unknown rather than being invented as zero.
- Incomplete usage explicitly labels recorded totals as Known, keeps overall
  projected credits Unknown, and separates known projected costs from reservations.
  No accounting records, settlements or provider cost calculations were changed.
- Browser fixtures verify complete, partial, missing-counter and empty unknown
  receipts at 1440/390/320. Execution was intercepted; direct renderer variants
  did not submit additional jobs. Full browser QA passed with no page/console
  errors or horizontal overflow. Results now explicitly name this coverage.
- Mobile screenshot inspection caught a separate short-status wrapping defect;
  the completed label no longer splits across three lines. Added a rendered
  single-line assertion for this short status, then reran QA and inspected the
  final partial-receipt mobile screenshot.
- Python regression: 294 passed, one skipped in 19.33 seconds. Browser validation
  used the existing Playwright harness because the Browser plugin/skill was not
  listed; the separate CUA capability was not used. Existing server PID 14704 was
  verified; static assets were reread without restarting it.
- Local frontend changes are newer than the qualified dev1 wheel. Do not treat
  its installation reports as evidence for these new asset bytes. No model calls,
  resets, publication or server configuration changes. Human receipt comprehension
  and real model benefits remain unverified.

2026-09-07, optional folder chooser with separate access approval:

- Added an optional Tk folder dialog in a child main thread/process, avoiding
  Tk interaction from HTTP worker threads. One chooser per server, 90-second
  subprocess timeout, bounded parsed output, and generic unavailable/canceled
  responses. Selecting a path neither registers it nor executes any model.
- Authenticated same-origin POST requires exactly open:true. Tests cover absent
  auth, wrong origin, absent/extra fields and numeric truthy input. UI selection
  clears previous consent; registration retains existing explicit approval/path
  checks. Cancellation and unavailable desktop/Tk preserve manual path entry.
- Seven initial process-contract tests failed before implementation. All now
  pass. Fixed a test-helper unpacking mistake in the HTTP test, not a product
  defect. Full regression: 302 passed, one skipped in 19.28 seconds.
- Browser QA passed at 1440/390/320 with selected/canceled/unavailable response
  fixtures, consent reset, no model dispatch, no page/console errors or overflow.
  Native-dialog response was intercepted, not actual desktop selection. Public
  chooser screenshots omit local project paths.
- Verified PID 14704 identity and empty authenticated job list before refreshing
  the server to PID 20148. Verified the current chooser endpoint rejects open:false
  with HTTP 400 without opening a dialog. Reran browser QA against the refreshed
  server. Revalidate its identity/jobs before any future restart.
- Not packaged or published. Actual native desktop selection, platform support,
  initial graphical installation, real-task comparisons and human trials remain
  open. Abrupt server exit may leave an OS dialog requiring manual close; the
  parent-side timeout is not a crash-proof OS window lifecycle guarantee.

2026-09-07, release-specific installation instructions:

- Verified live GitHub release v0.4.0-rc.3 remains a published prerelease, with
  the exact standalone installer, wheel and plugin assets. GitHub asset digests
  still match the recorded release hashes; no upload or mutation was performed.
- Corrected README and installation instructions to use explicit rc.3 asset
  downloads with --wheel, rather than implying default-branch code contains
  unpublished features. Pinned the source example to the rc.3 tag and separated
  developer checkout behavior. Removal instructions now match standalone versus
  source installer locations.
- Removed MCP instructions assuming package-index publication. Optional MCP uses
  the verified wheel and isolated installer; client configuration must point at
  that runtime's absolute Python path, not an unrelated bare-python installation.
- Updated installation evidence to distinguish rc.3 (268 passing tests), the
  older dev1 wheel (294), and subsequent unqualified asset changes. Kept native
  desktop, macOS development and human onboarding gaps explicit.
- Added regression checks executing documented core/MCP preview command arguments
  with a never-installed fixture wheel. Both return successfully and create no
  runtime. Full regression: 304 passed, one skipped in 19.40 seconds.
- No paid calls, resets, server changes, commit or publication. Public landing
  installation copy still needs alignment and visual verification before release;
  new final package bytes still require qualification. Documentation correctness
  does not establish actual model savings or human setup success.

2026-09-07, landing-page release alignment:

- Replaced the unpinned package install command and unmeasured one-minute setup
  promise with the published rc.3 installer/wheel download links and a preview-only
  command. The page now states terminal prerequisites, optional MCP downloads,
  direct-run scope, unpublished multi-stage work and unproven onboarding/savings.
- Installation CTA points to exact rc.3 release notes/assets and versioned source,
  rather than implying that default-branch source contains local development work.
- The new release-copy assertion failed before the edit. Full Python regression
  then passed: 304 passed, one skipped in 19.61 seconds.
- Browser QA at 1440/390/320 passed demo interactions, responsive bounds, loaded
  hero asset, version-specific copied command and simulated clipboard rejection.
  No page/console errors. Screenshots revealed sticky-header occlusion on mobile;
  added section scroll margin and verified native scrollIntoView keeps the heading
  below the header. Prevented the short --yes option splitting across lines.
- Final browser rerun and mobile screenshot inspection passed. Site QA uses local
  file navigation, not a deployment or package installation. Clipboard behavior is
  explicitly stubbed; no claim about every browser's permissions is made.
- No model calls, resets, server restart, commit or deployment. Published site
  remains unchanged until a deliberate release integration. Final package bytes,
  native dialog use, independent real tasks and human trials remain open.

2026-09-07, consolidated dev2 package qualification:

- Created 0.4.0rc4.dev2 (plugin 0.4.0-rc.4.dev.2) with current receipt UI,
  optional chooser, serial workflow execution and aligned embedded README.
  Manifest inspection confirmed required modules, current version, release-pinned
  installation prose and no unexpected wheel paths.
- Wheel SHA-256: aa238b973a8aeae4e09c14c58a965d03c522ea974bacd2da8b168a74f95645ae.
  Identical bytes passed isolated Windows/Python 3.13.7 and Ubuntu/WSL/Python
  3.12.3 qualification: 304 tests passed, one skipped on each; actual MCP stdio
  initialize/list/call, packaged UI hashes/auth checks and clean uninstall passed.
  Reports: artifacts/onboarding/windows-rc4-dev2-regression.json (71.93 seconds)
  and artifacts/onboarding/linux-wsl-rc4-dev2-regression.json (27.552 seconds).
- git diff --check passed with existing line-ending warnings. No published asset
  was replaced, and no live site/server/configuration was changed this turn.
- Requested one explicitly bounded real read-only Astra workbench run using public
  inputs, low reasoning, 15 estimated credits and no reset. No response was received
  during this turn; no additional model worker was started. This does not mean the
  active Codex conversation is free: it continues consuming host account capacity.
- Real task quality/cost, human onboarding, native dialog selection, new macOS
  qualification, initial graphical setup and full release acceptance remain open.
  Do not launch the pending real run without approval or substitute another round
  of synthetic tests for the missing empirical evidence.

2026-09-07, draft-PR integration and cross-platform CI:

- Reviewed pending development changes and scanned 33 text files for credential
  patterns (zero matches); public JSON reports had no checked local-user/session
  patterns. This is a scoped check, not a secret-detection guarantee. Restored
  screenshot path redaction after project-manager loading and reran browser QA.
- Committed 66 files as d27a319b439b415b8def8dbec043f21e88cbf8b7 and pushed the
  existing release/workbench-rc3 branch. PR 1 remains OPEN and draft at that SHA.
  Main, published rc.3 assets and live Pages were not changed.
- Push CI 34122808518 and PR CI 34122812185 both passed all seven jobs: Python
  3.10-3.13 tests and isolated Windows/Linux/macOS installation. Exact run:
  https://github.com/sulabhdubey/premium-model-budget-governor/actions/runs/34122808518
- Downloaded sanitized reports into ignored build/ci-34122808518 and inspected
  checks rather than relying only on badges. Core installed regression: Windows
  304 passed/one skipped; Linux and macOS 303 passed/two skipped. Linux's separate
  optional-MCP install initialized/listed/called stdio tools and uninstalled.
- Remote Linux/macOS wheel hash:
  7aca4f4c422c65b8fd62da16d353ba918a2e0d71059dd6dffa70900b0bb6c1e7.
  Remote Windows wheel hash:
  305c6f8c1e1722484a6d1f225292d2a8d08f3d9ff375eb8f999e8b7de9f36c5b.
  They differ from the locally qualified wheel; do not claim byte-reproducible
  cross-host builds. Existing Node 20 action-runtime warnings remain maintenance work.
- Added a public PR checkpoint separating fixture/software checks from unverified
  model benefits and human usability. No new release, merge, paid model worker or
  reset. This evidence closes the new-code CI installation gap, not native dialog
  interaction, real tasks, initial graphical setup or volunteer validation.
- This progress note is newer than the pushed commit and remains local until the
  next substantive integration; do not launch another CI run solely to log CI.

2026-09-07, requirement-level acceptance audit:

- Added ACCEPTANCE_AUDIT.md mapping the full seven-phase objective to current
  implementation, direct evidence, unsupported capabilities and missing outcomes.
  The prior turn made substantive progress by integrating dev2 and verifying CI.
- Read-only local workbench aggregate query returned zero run rows. The authored
  suite is still preregistered_not_executed; existing calibration audit remains
  ineligible; onboarding protocol has no recorded volunteer sessions.
- Distinguished the original guided-installation requirement from a speculative
  requirement to build a particular graphical installer before observing users.
  Human setup success remains required; no GUI implementation is accepted as a
  substitute for evidence that people can complete the supported journey.
- Next meaningful empirical action is the pending one-run approval, then bounded
  matched comparisons and consenting volunteers. No new worker or reset started.
  No package rebuild or repeated regression was needed for this documentation audit.
- This is the first explicit external-evidence dependency audit after CI completion,
  not a claim that the goal is complete or that every remaining engineering choice
  is impossible. The full acceptance scope remains intact.

2026-09-07, external-evidence dependency recheck (second consecutive audit):

- Re-read the complete objective. The prior turn produced the acceptance audit;
  this turn's read-only aggregate query still finds no local workbench runs.
- No answer to the bounded real-run approval or participant request has arrived.
  The evidence condition is unchanged. This is not a verified running-job wait:
  no empirical worker has been started, and no participant session is live.
- No further test rerun, rebuild, feature addition or publication was justified
  by new evidence. Current work is at the empirical-validation dependency, with
  the full goal incomplete. This recheck is no implementation progress, not a
  new milestone. Keep the goal active until the required blocked audit threshold
  or an actual owner response changes the next action.

2026-09-07, third consecutive external-evidence audit:

- The previous turn was no progress, not a live-job wait. Re-read the complete
  objective and verified the same empty local workbench run aggregate again.
  No bounded-run approval or consenting participant results have arrived.
- The same empirical-validation dependency has now persisted across three
  consecutive goal turns. Further unchanged software tests or speculative features
  cannot provide the missing real outcomes. Marking the goal blocked, not complete.
- Resume with the bounded real-run approval and/or participant availability, then
  follow the acceptance audit. Preserve the full objective and all remaining
  independent-project, matched-comparison, capability and release requirements.
  Draft PR 1 and qualified development artifacts remain available; no paid worker,
  reset, merge or new release was started during this recheck.

Next: follow ACCEPTANCE_AUDIT.md's evidence sequence, preserving all
accounting and evidence gates; also integrate candidate documentation;
continue independent task and human validation without calling them complete.
The bounded real UI task was subsequently approved and completed once, as recorded
below. Preserve the full phase register:
capability-aware workflow comparisons, Linux/macOS installation execution,
reviewed calibration/rollback, independent projects, human trials and release
are not complete. Read-only tasks are not substitutes for write/Desktop-only work.

2026-09-07, approved real Astra Workbench execution:

- Owner approved one public-fixture read-only call, low reasoning, 15 estimated
  credits, no reset. Actual browser registration/preview/approval/run completed;
  no execution mock, retry, second arm or additional worker was used.
- Host-configured gpt-6-astra completed in 21.263 seconds, reporting 24,076 input,
  zero cached and 386 output tokens. Token-rate estimate: 6.5015 credits. One lease
  settled; zero reserved; not over budget. Weekly task debit remains unavailable.
- The 229-word response passed all seven fixed study-synthesis criteria in Codex
  review. This is not independent human grading or evidence of comparative savings.
- Sanitized report: artifacts/approved-astra-ui-smoke-2026-09-07.md. Raw local
  result remains ignored. ACCEPTANCE_AUDIT.md now reflects one real execution.
- This closes the single-run integration evidence gap only. Matched experiments,
  real-project validation, human trials and full capability/release gates remain.
  No policy promotion, commit, publication or further spending follows implicitly.

2026-09-07, owner-directed end-to-end continuation:

- Owner approved 150 estimated credits for broader matched experiments, separately
  from the prior one-call smoke test. No reset is approved or used. A one-shot
  real Workbench-service trial uses a shared 150-credit envelope, 15-credit
  contingency, one pending lease, per-call receipts and no automatic retries.
  Current results must be read from its terminal report, not inferred from launch.
- Owner has no volunteers yet and requested recruitment through publication.
  Added an opt-in onboarding issue template and candidate invitation. No participant
  session, human validation or endorsement is claimed.
- Prepared rc.4 metadata and pinned install instructions. The exact final wheel
  6eacbd15685cd9bb0b84b441f447e8a3dd6dff17b1c805853c05513b0420784f
  passed installed regression (304 passed, one skip), real optional MCP and owned
  uninstall on Windows and Ubuntu/WSL. Stale version assertions were corrected.
- Remaining empirical, capability, human and final promotion gates are explicit
  in REMAINING_VALIDATION.md. Native/Desktop-only support is not manufactured by
  relaxing read-only safety, and weekly attribution is not invented from tokens.

2026-09-07, expanded pilot and focused-catalog qualification:

- Further owner approval funded a separately bounded 100-credit extension. Final
  totals are 129.77603 + 66.17815 = 195.95418 estimated worker credits, 39 calls,
  27 workflows, zero outstanding reservations, model retries or resets. The
  earlier 6.5015 UI smoke and parent-chat engineering/grading are separate.
- All five public task families now have four workflow arms, with complete stage
  counters and Codex-graded fixed criteria. One fresh combined read-only review
  across two private projects passed scoped criteria with unchanged source hashes.
  Neither authored fixtures nor this one project call establish independent
  representative quality. FIELD_TRIAL_2026_09_07.md includes negative findings.
- A shorter Sol preparation prompt reduced its stage cost but raised the complete
  workflow cost; it was not adopted. Direct Astra remains the default.
- A four-call ABBA visual probe reduced average input about 17.9% and estimated
  credits about 17.3% with no cached tokens and the same correct answers. The
  narrow per-thread catalog cap is opt-in, direct Astra/low only. It may omit
  skill guidance; no global config, tools or safety settings were disabled.
- Fifteen new tests first failed, then passed with the implementation. Updated
  live-preview browser QA passed at 1440/390/320, including incompatible profiles,
  stale approval and legacy-server rejection; model execution in that QA was
  mocked. The paid catalog probe used the experimental adapter, not the UI.
- Final wheel 658065b66e8b7ed3937c7ae6d5b6b661acb962c2a7d4264c2fb16ce09df58428
  passed 319 installed tests with one skip on both Windows and Ubuntu/WSL,
  real MCP initialize/list/call and owned uninstall. This supersedes the earlier
  rc.4 wheel; release assets include the installer, plugin dotfiles and checksums.
- Public text scans found zero secrets or private paths. One narrative release-note
  sentence triggered the heuristic tool-coercion scanner; it was reviewed as a
  benign description, not an instruction. No scanner was disabled or weakened.
- Human participants are not available yet. Candidate recruitment is prepared;
  no onboarding outcome, independent audit, stable promotion or broad savings
  proof is invented. Draft PR/main-site promotion remain separate from rc.4.

2026-09-07, publication privacy hardening and independent-validation preparation:

- Removed remaining unnecessary private-project references from current tracked
  documentation and the older live candidate release notes. Rewrote stale
  Sol-first outreach copy to match the measured direct-Astra direction.
- A private, verified Git bundle and historical inventory cover 16 reachable
  snapshots and 11 uploaded assets. All snapshots contain at least one term from
  the owner's private audit list. One candidate wheel contains a private-reference
  match in README metadata. Generic-secret matches in two wheels were reviewed as
  token-generation source code, not exposed credentials. No complete erasure claim.
- Added bounded publication checks for text, decoded JSON and wheel/ZIP metadata;
  reports omit matched content and names. Uninspected content requires manual
  review. Fifteen new tests passed; full suite: 334 passed, one skip. CI also runs
  public-text checks, without uploading the private terms list.
- Current selected publication documents pass both public patterns and local
  private-term checks. This is not a semantic confidentiality or malware guarantee.
- Independent validation now has explicit task intake, blinded grading, scope,
  consent, whole-workflow cost and failure-reporting instructions. No new worker
  call, human session or independent result was fabricated to fill missing evidence.
- History rewriting and affected binary withdrawal/replacement require the owner's
  specific disposition after inventory. No force push, tag change or asset deletion
  occurred in this hardening work. Stable promotion/site deployment and creator
  contact remain on hold; volunteer availability and independent results remain open.

2026-09-07, approved history cleanup and rc.5 qualification:

- Owner explicitly approved backed-up history and affected-release cleanup. A
  separate mirror was rewritten and checked before an atomic, exact-lease update
  of two public branches and eight tags. The original checkout was preserved and
  ordinary pushes disabled there to prevent recontamination. A fresh sanitized
  working checkout is now authoritative for new changes.
- The old draft PR was closed. Seven mutable release descriptions were updated;
  the affected rc.4 wheel and its checksum manifest were withdrawn. Cached/PR refs
  and external copies require GitHub/collaborator handling; no total-erasure claim.
- The separately versioned rc.5 wheel passed 334 installed tests with one skip on
  Windows and Ubuntu/WSL, real MCP initialization/tool call and owned uninstall.
  Its private-term package scan has no matches; the retained generic-token finding
  was reviewed as random-token generation code, not a credential literal.
- Candidate page installation/proof copy was corrected and browser-checked at
  1440/390/320 widths with no overflow or page errors. Human onboarding and
  independent quality equivalence remain unproven. No further paid worker or reset
  was used for this cleanup. Candidate publication is distinct from stable acceptance.
