# Product Baseline

Audit date: 2026-09-07. Published starting point: v0.4.0-rc.2,
commit `f0fbee3e7de8d30212dac4579162483282d20d5a`.
This audit distinguishes implemented helpers from executed workflows and user outcomes.

## Capability Inventory

Paths below are relative to `src/premium_model_budget_governor/` and `tests/`.

| Capability | Implementation | Regression evidence | Boundary |
| --- | --- | --- | --- |
| Astra-preferred whole-workflow planning | workflow.py | test_workflow.py, test_workflow_stress.py | Caller estimates and quality signals, not learned optimal selection |
| Single-call parity and routing | policy.py, cost.py | test_core.py, test_telemetry_strict.py | Legacy premium-leg estimate, not total hybrid savings |
| Capsule building and scoring | capsule.py | test_core.py, test_cli.py | Heuristic quality; no correctness guarantee |
| Evidence graph and selection | evidence_graph.py, evidence_demand.py | test_core.py, test_evidence_demand.py | Integrity is not source authority; ranker is heuristic |
| Injection/secret pattern checks | scanners.py | test_core.py | Supplementary regex checks, not a malware scanner or security boundary |
| Shadow review | shadow.py | test_core.py, test_phase_completion.py | Builds a review packet; does not execute a premium review |
| Tournament | tournament.py | test_core.py, test_phase_completion.py | Ranks supplied answers heuristically; does not launch competing models |
| Doctrine and benefit signals | distillation.py, predictor.py | test_core.py | Reusable records and heuristics, not model-weight distillation or trained prediction |
| Token records | telemetry.py, experiments.py | test_experiments.py, test_telemetry_strict.py | Exposed counters only; estimates are not provider bills |
| Reservations, expiry, replay protection | leases.py, host.py | test_leases.py, test_host.py | Cooperating runner admission, not an in-flight provider token cap |
| Capability-aware plans and images | workflow.py, host.py, app_server.py | test_workflow_stress.py, test_host.py, test_app_server.py | Read-only execution; no claim of all Desktop tools or write capability |
| Matched calibration | calibration.py | test_calibration.py | Descriptive, insufficient-support labels; no automatic policy promotion |
| Dashboard | dashboard.py | test_dashboard.py; artifacts/benchmark-v3/dashboard-qa.json | Static ledger export, not a live control app or weekly billing feed |
| CLI execution | host.py | test_host.py; artifacts/benchmark-v2 and benchmark-v3 | Explicit calls, requested-model rates; unknown usage retained |
| App Server discovery/execution | app_server.py | test_app_server.py; artifacts/app-server-pilot | Catalog/configuration observable; serving model not independently attested |
| Optional native hook | prompt_gate.py | test_prompt_gate.py, test_native_hook_results.py | Measured crashes/timeouts/disabled/modified hooks can permit dispatch |
| MCP and plugin | mcp_server.py; plugin/ | test_mcp_runtime.py | Optional dependency; installing tools does not govern all existing chats |
| Landing-page demo | site/ | test_site.py; artifacts/site-qa | Illustrative, not account-connected execution |

The initial regression run passed 133 tests on Windows/Python 3.13 in 4.69 seconds.
This proves covered software behavior, not general savings or product ease of use.

## Supported Journeys

| User/environment | Present support | Missing evidence or capability |
| --- | --- | --- |
| Python-capable developer | Offline CLI planning/scans; explicit JSON workflow execution | Guided setup and plain-language execution flow are being added |
| Codex user with supported local CLI | Read-only runner and experimental App Server path | Must verify local host/catalog; existing chats are not automatically controlled |
| MCP-capable client | Optional local stdio tools | Client configuration and consent remain explicit |
| Nontechnical user | Can inspect landing demo and exported dashboard | Cannot yet reliably install and execute unaided; no volunteer trials |
| Mobile-sized browser | Existing demo/export responsive QA | Not evidence of remote mobile execution; do not expose a local service publicly |
| Ordinary ChatGPT conversation | No automatic integration | Do not advertise universal ChatGPT budget control |

Core declares Python 3.10-3.13, with published Linux CI. Native host experiments
were on Windows and Codex 0.153.4. New installer tests must separately establish
OS/runtime support; import compatibility is not clean-install or native-host proof.

## Measurement Baseline

- Quality: v0.2 bounded source repair plus contract checks; v0.3 one 24-question
  synthetic multimodal batch. See BENCHMARK_RESULTS.md for grading defects and corrections.
- Tokens: recorded per-call usage in published benchmark receipts, including cached
  subsets. Unknown host usage is not zero.
- Cost: v0.3 means were 6.62525 Astra direct, 5.89051 corrected Astra+Terra,
  8.94001 Sol+Astra review, and 2.53180 Sol direct, in projected credit units.
  These comparisons do not establish Astra at Sol cost or weekly savings.
- Time: no representative matched task-latency study yet. Regression runtime and
  isolated setup timing must not be relabeled as human productivity improvement.
- Setup difficulty: no observed technical/nontechnical volunteer baseline yet.
  Track completion, elapsed time, interventions and mistakes in upcoming trials.

## Discovered Product Gaps

README labels for shadow/tournament/scanning overstated execution or protection;
corrected as part of this audit. Legacy single-call policy remains distinct from
Astra-preferred planning. Scanner output can include untrusted excerpts, so a
future shareable diagnostic exporter must strip them rather than forward raw scans.
The product interface, independent tasks, approved policy rollback, volunteer
trials, and new release remain open in PRODUCT_GOAL_PROGRESS.md.
