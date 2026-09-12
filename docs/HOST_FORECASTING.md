# Host Forecasting (Local Development)

`pm-bg estimate-host --input receipts.json` describes recent comparable receipts.
`pm-bg plan-host --input planning.json` applies that forecast before planning.
Neither command dispatches a model or changes an existing chat. These commands
are a development API, not yet integrated into Workbench previews or the MCP UI.

## Comparison Contract

The input contains `profile` and `receipts`. The profile requires `host`, `model`,
`reasoning`, `context`, `config_fingerprint`, `task_family` and `scope`. Each receipt
contains a unique `id`, matching `profile`, timezone-aware `recorded_at`, explicit
`complete: true`, and integer `input_tokens`, `cached_tokens`, `output_tokens`.
Input includes cached input; output includes reasoning where the host reports it.
Only use this format for hosts without separately accounted cache-write tokens.

The adapter must establish these facts from receipts and configuration, not guess
a fingerprint or change old timestamps to make historical data appear current.
The current implementation trusts the supplied profile; it is not an attestation
or an automatic importer of arbitrary host logs.

Receipts older than seven days (configurable from 1 to 90), future-dated receipts,
incomplete runs and mismatched profiles cannot support the forecast. Bad counters
and duplicate IDs are rejected. Missing, stale and fewer-than-five-sample states
remain explicit. Five samples is a support threshold, not statistical proof.

The report shows observed min/max and median for input, cached input, uncached
input and output. These are descriptive ranges, not prediction intervals. The
admission heuristic uses observed maxima plus 25 percent and assumes no cache hits.
It may still underpredict an unusually difficult task. There is no provider hard
cap, weekly-quota conversion or claim of savings.

## Calibrated Planning

`planning.json` contains `calibration` (the estimator input) and `workflow` (the
existing `pm-bg plan` contract). For this initial integration, all stages must use
one exact profile, with `scope: per_call`, and include that profile in each stage's
`calibration_profile`. Each stage model must match. Mixed profiles must be planned
separately; never relabel focused receipts as inherited or task totals as per-call.

The wrapper raises input/output estimates to the admission heuristic, removes
assumed cache savings, and retains the workflow's retry counts, sunk spend and
reserve. Missing/stale/insufficient calibration blocks selection even when a
caller supplied a nonzero floor. Legacy `pm-bg plan` remains unchanged.

## External Task Measurement

`task_measurement.measure_task(stages, output, invoke)` is a Python integration API
for an external runner. Enroll preparation, execution and verification before work
starts; enroll retries explicitly and place optional reporting phases last. The
trusted callback executes an approved phase and returns its exclusive final receipt
using the existing long-work contract. It must own admission, lease reconciliation,
timeouts and quality decisions; this observer does not authorize arbitrary work.

The output directory must be new. A durable manifest and phase-start markers precede
execution; allowlisted receipt records follow each phase. Failures and unexecuted
phases remain visible. Unknown cost, invalid receipts and reused source identities
stop subsequent calls. Do not restart a crashed directory to retry uncertain work.
Reconcile its started markers and host receipts first.

Task and reporting token totals are separate. File-writing wall time is observer
overhead, not model token usage. `complete_for_declared_phases` does not establish
coverage of a parent chat, hidden workers, earlier task design, or omitted phases.
The host adapter has now been exercised in the [four-call live pilot](ACCOUNTED_TRIAL_2026_09_12.md).
Coverage remains limited to the declared fixture pipeline, not a parent conversation.
The CLI forecast is not automatically applied by Workbench previews.

## Release Gates

- Run broader regression and package checks before publication.
- Preserve all matched trials, failures, cache differences and quality outcomes.
- Obtain independent technical and nontechnical newcomer trials separately.
- Never promote development-only forecasting or synthetic observer tests into a
  claim of demonstrated savings or automatic control of existing chats.
