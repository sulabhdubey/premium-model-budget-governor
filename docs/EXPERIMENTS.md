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
