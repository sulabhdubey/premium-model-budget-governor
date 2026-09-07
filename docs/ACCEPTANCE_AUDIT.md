# Product Acceptance Audit

Date: 2026-09-07. Engineering checkpoint: d27a319, dev2, draft PR 1.
Decision: the complete product goal is not achieved. The next candidate is rc.4;
see RELEASE_CANDIDATE_RC4.md for artifact qualification and publication status.
REMAINING_VALIDATION.md defines the remaining empirical and human execution gates.

This audit follows the original seven-phase objective. It does not turn software
test results into quality, savings, human usability or general capability claims.

| Requirement | Current evidence | Acceptance decision / next proof |
| --- | --- | --- |
| Honest feature inventory and supported journeys | PRODUCT_BASELINE.md records the starting inventory; WORKBENCH.md and progress checkpoints cover later changes | Implemented surfaces are documented. Representative quality, latency and human setup baselines remain missing. |
| Guided setup, diagnostics, recovery and reversible integration | Preview-first installer, ownership-bound removal, doctor; installed dev2 tests on Windows/WSL and CI on Windows/Linux/macOS | Machine installation/recovery checks pass in the tested environments. User setup success is not inferred. The objective requires guided setup, not a particular GUI toolkit. |
| Everyday task/project/evidence/image/mode/approval/result journey | Local Workbench, immutable previews, tested browser flows at 1440/390/320, explicit stage receipts; one approved real Astra text run | One read-only public-fixture UI-to-host run passed with browser automation. Human operation and broader capabilities remain unverified. Native chooser selection is experimental and not observed. |
| Direct/prepared/review choice based on measured whole-workflow outcomes | Explicit strategies and conservative stage accounting implemented; matched comparison and reviewed-policy machinery tested | No representative benefit evidence. The five-task starter suite remains preregistered_not_executed. Existing audit marks all three pilot comparisons ineligible. Do not activate a policy or promise Astra at Sol cost. |
| Preserve tools, images and reasoning | Host catalog checks, image binding and capability rejection; original evidence retained in both stages | Tested compatible read-only path only. Write/Desktop-only capabilities remain unsupported rather than silently substituted. Broader capability equivalence is not proven. |
| Actual token accounting and robust failures | Journal recovery, cancellation/timeout/replay/concurrency/expiry tests; actual subprocess exits; unknown-spend retention; partial receipt UI; one settled real Astra receipt | Covered accounting tests pass. The real run reported 24,076 input and 386 output tokens, costing 6.5015 estimated credits with zero reservation remaining. Projected credits are not provider bills or weekly allowance attribution; native hooks remain supplementary. |
| Local security and untrusted-content boundaries | Authenticated loopback, Host/Origin checks, private launch files, bounded inputs, pattern scanning and documented limitations | Covered checks pass; no malware/injection guarantee. Abrupt image staging retention and optional-dialog lifecycle limitations remain explicit. No independent security certification is claimed. |
| Independent RTA-Net/CircuitProof and representative tasks | Earlier owner-supplied routing reports and authored public fixtures | Neither constitutes fresh matched governor-executed project validation. Need bounded approved tasks, frozen evidence, complete receipts, scope/quality checks, retries and failures included. |
| Technical and nontechnical onboarding | ONBOARDING_TRIAL.md protocol | No volunteer sessions recorded. Requires consenting participants and observations; an agent cannot stand in for those people. |
| Release materials, candidate and final release | rc.3 published; dev2 draft PR and successful CI; updated site and instructions in that branch | No merge, site deployment or final dev2 release. Final promotion requires the remaining acceptance evidence and accurate scope labels. |

## Direct Evidence Checked

- Before the approved smoke test, a read-only query of build/local-ui-data/workbench.sqlite3: runs grouped by status
  returned an empty list. This applies only to that local workbench store; it does
  not erase historical CLI pilots or prove nobody used another installation.
- Subsequently, owner approval enabled one real low-reasoning Astra run. See
  ../artifacts/approved-astra-ui-smoke-2026-09-07.md for receipts, seven-criterion
  Codex evaluation, scope and limitations. This supersedes the empty-store
  observation as the current execution baseline, not as historical evidence.
- examples/field-trial/suite.json: five authored tasks, status
  preregistered_not_executed, with fixed inputs and criteria.
- artifacts/reviewed-policy/existing-evidence-audit.json and REVIEWED_POLICIES.md:
  existing batched evidence lacks independent calibration/holdout support.
- ONBOARDING_TRIAL.md: no volunteer sessions recorded. No participant results
  were located in the project's artifact inventory.
- The preceding integration inspected CI reports for commit d27a319: core
  installed-package tests on all three operating systems; optional MCP separately
  verified on Linux and locally on Windows/WSL. Native GUI selection is not tested
  by a mocked subprocess response.

## Next Evidence, In Order

1. Completed: approved real, read-only public-sample Astra UI run, low reasoning,
   15 estimated-credit task budget, no reset or retry. Preview passed; run completed.
2. Completed: inspected the result and receipt; one lease settled, no unknown
   spend reported. Seven predefined answer checks passed in Codex review only.
3. Propose separately bounded matched comparisons using the same tasks, evidence,
   quality rubric and whole-workflow accounting. One successful Astra call cannot
   establish savings or equal quality versus Sol.
4. Obtain one technical and one nontechnical volunteer for the existing protocol.
   Include facilitator time and failures; use findings to prioritize setup changes.
5. Complete fresh independent-project validation and remaining capability decisions
   before treating the final release goal as achieved.

No spending approval or participant availability is inferred from an automatic
goal continuation. Do not repeatedly rebuild unchanged packages, add speculative
features or rerun the same green tests as substitutes for these missing outcomes.
This conversation itself consumes account capacity even when no additional model
workers are dispatched.
