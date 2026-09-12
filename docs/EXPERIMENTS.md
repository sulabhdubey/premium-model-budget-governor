# Measure Before Optimizing

Historical v1 pilot, 2026-09-07. Its overrun and incomplete arms are retained here.
The subsequent completion and repeated comparisons are in [v0.2 results](BENCHMARK_RESULTS.md).
No universal winning strategy, Astra-equivalent quality guarantee, or weekly-limit
savings percentage has been established.

## What Actually Ran

The preregistered [fixture](../examples/contract_pilot.json) contains four small
governor-contract questions: budget arithmetic, cached-token accounting, release
authority, and numeric validation. The answer key was written before model calls.
Both direct arms received identical task text, low reasoning, no history fork,
and instructions to use no tools. The controller graded exact fields/types.

| Stage | Total Input | Cached Subset | Total Output | Rate-Based Credits | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| Astra direct | 37,051 | 0 | 73 | 9.35400 | Passed |
| Sol direct | 38,823 | 0 | 109 | 3.93680 | Passed |
| Astra planning for Terra | 37,095 | 35,712 | 230 | 1.52605 | Plan returned; worker canceled |
| Astra evidence request | 36,933 | 35,712 | 23 | 1.22680 | Requested all four sources; final call canceled |

Counters came from each explicitly identified local Codex rollout, not model
self-report. Output includes reasoning; do not add reasoning a second time.
Credit projections use the configured standard rates; the importer does not
verify service-tier multipliers. They are not actual provider-billed credits.
Cached tokens are a subset of input. The rate snapshot and normalized receipts
are in [results.json](../artifacts/contract-pilot/results.json).

The initial pilot estimate was 9.25 credits plus 5 contingency under a 15-credit
ceiling. Observed counters project to **16.04365 credits**, exceeding the entire
ceiling before the two remaining stages. Both unexecuted calls were canceled;
completed spend was recorded rather than hidden. No reset was redeemed.

Four calls had already been dispatched before the first receipt. This is a
real weakness in the v1 dispatch procedure, not evidence of successful budget
enforcement. New task ledgers default to one pending reservation so cooperating
hosts must reconcile before the next call. In-flight spending still cannot be
physically capped by this package.

The rounded shared account meter stayed at 90% used across the pilot snapshots.
That does not mean free execution. Other work, rounding, and reporting latency
prevent task-level attribution. Parent implementation-chat usage is excluded.

## What We Learned

1. Capsule size is not total host input. A tiny task here carried roughly 37k
   tokens. Tool definitions and injected instructions are plausible contributors;
   this pilot did not isolate their individual shares.
2. Cache state matters substantially. Later Astra stages recorded cache hits;
   this does not prove an identical warmed Astra task will beat Sol or that hits
   can be guaranteed. The prompts and outputs of those stages differ.
3. Hybrid orchestration can multiply host overhead. Do not run a tournament or
   evidence-request turn merely to create the appearance of intelligence.
4. This easy pilot cannot distinguish frontier capability. The two incomplete
   workflows are not quality or savings successes and are excluded from paired
   comparison, but their consumed tokens remain in the budget report.

## Built From Those Findings

- `pm-bg receipt`: whitelisted counters from one explicit single-model Codex
  rollout. Uses the final cumulative snapshot, not a sum of overlapping snapshots.
  Rejects mixed-model sessions and counter decreases. Local log formats may change.
- `pm-bg plan`: supports `minimum_input_tokens_per_call` and
  `require_context_calibration: true`. Supply a conservative floor measured on
  the applicable host/model configuration. This is not automatic host inspection.
- `pm-bg budget`: serial reservations by default; estimated reconciliations carry
  `cost_basis: token_rate_estimate`, distinct from `host_billed` receipts.
- `pm-bg experiment`: pairs task/snapshot/rubric/repeat; rejects duplicate calls,
  mismatched cost bases, partial receipt sets, and missing usage as free work.
  Includes retries/failures in cost. Never automatically promotes a model.
- `pm-bg evidence`: selects mandatory/requested items intact by ID and hash,
  blocks unsafe or inconsistent evidence, and exposes omissions. Content remains
  untrusted. Regex scanning is not malware protection or an injection guarantee.

Example commands after installation:

```sh
pm-bg experiment --input artifacts/contract-pilot/comparison-input.json
pm-bg receipt --input /explicit/path/to/single-model-rollout.jsonl --call-id run-001
pm-bg evidence --input examples/evidence_demand.json
python -m pytest -q
```

The evidence example intentionally requests an absent source and demonstrates
the fail-closed response. Supply hashed items to produce a ready evidence packet.

The historical preparation/reconciliation scripts reproduce v1 artifacts only;
they do not invoke models. Do not reuse v1's uncalibrated parallel-dispatch policy.
Raw sessions, private prompts, credentials, and SQLite ledgers must not be published.

## Next Experiment Protocol

### Coverage And Cost-Quality Diagnostics

The comparator also reports `coverage`: baseline-only and candidate-only runs,
their totals, and whether every supplied run matches. This is coverage of the
input packet, not proof that all planned experiments were submitted. An omitted
task on both sides cannot be detected without an independently retained enrollment
manifest. The unreleased enrollment extension below makes that comparison explicit.

### Planned Enrollment (Unreleased)

Optionally supply `enrollment`: a nonempty list of planned run identities using
`task_id`, `snapshot`, `rubric`, `arm`, and `repeat` (defaults to zero). Use opaque
labels, never personal paths or prompts. The same identity cannot be enrolled
twice; the baseline must be included. There is a 10,000-identity limit.

The report's separate `enrollment` section counts missing and unexpected runs,
both overall and per arm. It includes wholly absent arms and tasks omitted from
both sides. An empty `runs` list is accepted only with explicit enrollment, and
produces no invented costs or passing results. Existing inputs without enrollment
return `status: not_supplied` and `complete: null`.

`enrollment.complete` means supplied identities match the supplied plan, not that
every call succeeded, costs are valid, or all workflows completed. Continue to
read quality results, coverage and cost exclusions. Observed pair statistics
remain descriptive even when enrollment is incomplete; unplanned rows are not
silently dropped to make a report look compliant.

The order-independent fingerprint covers only normalized run identities, not
extra fields. It is not a timestamp, signature or proof of preregistration. Retain
the plan independently before execution: editing both the plan and results can
still conceal attrition. No automatic policy promotion is enabled.

Try the intentionally incomplete, no-model example:

```sh
pm-bg experiment --input examples/enrollment-missing.json
```

`cost_exclusion_reasons` counts each reason once per matched pair. A pair can
have several reasons: incomplete workflow, non-host receipts, missing calls,
unknown costs, or incompatible cost bases. Do not sum reason counts as if they
were distinct excluded pairs. Unmatched runs are reported separately in coverage.

Within each cost basis, `task_balanced_mean_credit_difference` averages repeats
within each task ID first, then weights those tasks equally. The ordinary mean
still weights each pair equally. Task IDs must be stable and fixed before trials;
neither average establishes statistical significance or population savings.
Totals cover only matched cost-valid pairs, not total campaign expenditure.

`cheaper_both_passed` counts lower-cost pairs where both supplied grades passed.
`cheaper_quality_regressions` exposes lower-cost candidates that failed while
the baseline passed. Passing a fixed rubric is not general capability equivalence.
These additive diagnostics do not change routing or automatically promote a model.

See the [receipt reanalysis](EVALUATION_REANALYSIS_2026_09_08.md).

### Whole-Workflow Time And Comparable Units

Each run may include `total_elapsed_seconds`: a finite nonnegative JSON number
measured from the start of preparation to completion of final verification,
including waits, handoffs and retries. Preregister whether installation/setup is
inside the measurement window and apply the same boundary to all arms. Do not
sum parallel call durations and label that wall time. Absent timing remains
unknown. Incomplete workflows are not matched completion-time observations.

`matched_time_pairs` and `mean_elapsed_difference_seconds` summarize only pairs
with complete, supplied timing. Negative means the candidate was faster. Timing
is explicitly caller-reported, not host-attested, and includes failed outcomes;
always read it alongside the quality-regression count. A fast wrong answer is
not an equivalent-quality productivity improvement.

`cost_by_basis` separates `token_rate_estimate` and `host_billed` summaries.
`mean_credit_difference` is null when the paired collection contains multiple
bases, even if every individual pair uses matching units. This prevents an
average that mixes projections with billed amounts. Unknown costs remain
excluded rather than zero, and the pair counts reveal missing observations.
Historical receipts without timing remain valid; they acquire no invented time.

Start with existing telemetry, or one explicitly budgeted serial calibration call.
Use the observed host context floor and cold-cache pricing for reservations.
Do not warm a cache merely to make a benchmark look cheaper: include warm-up cost.

Then preregister held-out real tasks: a reproducible bug, cross-module change,
architecture ambiguity, adversarial security review, and a non-code research task.
Use isolated identical snapshots and acceptance tests; include final verification,
failed attempts, handoffs, and preparation. Randomize/counterbalance arm order,
repeat across tasks, record host configuration and cache state, and retain failures.

Compare disciplined Astra-direct, Sol-direct, Astra-led worker execution, and
selective evidence-on-demand. Test direct Astra first-class, not merely as a judge.
Add a minimal-host-context variant only through supported host configuration;
do not remove safety instructions or user policy. Preserve visual evidence where
the task needs it. Stop on quality failures or budget exhaustion, not after finding
a favorable result. No further paid trials are automatically scheduled.

Only after enough matched observations should we calibrate routing by task family.
The present evaluator intentionally reports descriptive results and
`insufficient_evidence`, rather than fabricating a learned optimum.
