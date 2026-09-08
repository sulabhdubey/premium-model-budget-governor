# Direct Astra Context Trial

Completed pilot: [results and limitations](CONTEXT_TRIAL_RESULTS_2026_09_08.md).

This bounded pilot compares inherited skill discovery with the existing
experimental focused catalog. Both arms request Astra, low reasoning, standard
service tier, identical task text, and identical images. Only the per-thread
`skills.max_context_tokens` override changes. Global configuration and safety
policy are not edited. Host acceptance does not attest internal application.

## Frozen Protocol

[Fixture and answer keys](../examples/context-trial.json) are authored before
execution. The runner writes a manifest containing the fixture, full enrollment,
and image hashes before its first model call. Each of three tasks runs in order
inherited, focused, focused, inherited, forming two matched pairs per task.
This counterbalances position but is not randomized or an independent held-out
benchmark. The chart is an existing fixture. The two text tasks are synthetic.

The model sees the task, not the oracle. Tasks request no tools, so this trial
cannot measure skill discovery, tool use, editing, or real-project completion.
Inherited connector permissions remain unchanged; read-only filesystem mode
is not a connector access restriction.

Exact JSON grading rejects missing/extra fields, wrong types and prose wrappers.
No answer is executed as code. An exact-format failure is retained as a failure,
not necessarily evidence of a reasoning defect. The same oracle checks both arms.
There is no post-answer rubric adjustment or favorable-only retry.

Execution stops on the first quality failure, incomplete/uncertain execution,
or actual estimated credits above the per-call admission estimate. Missing calls
stay listed in enrollment; unknown spend stays reserved by the governor. A
120 estimated-credit budget includes a 12-credit reserve, with 12 credits reserved
per serial call. Admission is not a provider hard cap; overruns can occur.

## Reproduce

Use a fresh private output directory, outside the public checkout. Install this
checkout in a dedicated environment before running; an older installed package
does not include local changes. Dry-run performs no model calls or output writes:

```sh
python scripts/run_context_trial.py --output /private/new-trial
```

Only after approving the model usage for this protocol:

```sh
python scripts/run_context_trial.py --execute --output /private/new-trial
```

The runner refuses an existing output directory and never silently resumes or
retries a dispatched call. Inspect retained receipts and reconcile uncertain
spend before any subsequent experiment. Keep the ledger and full answers private;
publish only reviewed aggregate counters and synthetic task metadata.

## Interpretation

Compare full input, cached input subset, output, estimated credits, elapsed time,
and fixed-check outcomes. Separate cache differences from context reduction.
Elapsed time includes runner invocation through receipt return, not installation,
parent-chat preparation, grading overhead, or independent human review.
The fixed budget likewise excludes parent-chat engineering and analysis usage.

Report every task and repeat, not just the cheapest example. Task-balanced means
do not establish statistical significance or capability noninferiority. Even if
all answers pass, focused discovery remains opt-in: less catalog text may hide
guidance that matters on another task. Do not claim weekly-billing savings,
universal savings, or unchanged general Astra quality from this pilot.
