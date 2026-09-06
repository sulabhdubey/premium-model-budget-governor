# Completed Comparisons: September 7, 2026

## v0.3 Multimodal Contract Pilot

The next pilot used 24 fixed questions, four each on architecture, bugs, routine
coding, research, visual reading, and release/security. Four questions required an
attached rendered chart. All final responses passed the prewritten exact-answer
oracle. **This is one batched synthetic workload, not 24 independent real tasks.**

| Workflow | Final Answers Passed | Mean Projected Credits | Observed Range |
| --- | ---: | ---: | ---: |
| Astra direct | 48 / 48 | 6.62525 | 6.62525-6.62525 |
| Sol direct | 48 / 48 | 2.53180 | 2.52530-2.53830 |
| Astra plan + Terra execute, corrected prompt | 48 / 48 | 5.89051 | 4.98113-6.79989 |
| Sol draft + Astra review | 48 / 48 | 8.94001 | 8.77297-9.10705 |

Neither Astra workflow achieved Sol cost in the corrected comparison. Planning
was cheaper on average than direct Astra here, unlike v0.2. Cache state and
host-injected context varied; the study cannot isolate their causal contribution.
The governor should compare complete workflows, not hard-code either winner.

### Planning Prompt Defect

The initial planning prompt conflicted with the embedded final-answer instruction.
Astra returned final answers instead of a plan in both rounds. Those runs cost
1.74836 and 1.71039 including Terra, but **are not valid planning-workflow evidence**.
The conflicting instruction was removed, a 3-6-step JSON contract added, and only
the four affected planning/worker calls were rerun under new receipt IDs.
The corrected plans passed the role schema before workers were dispatched.

All original results remain in `artifacts/benchmark-v3/results.json`; corrected
results are in `results-planning-v2.json`. Reused baseline receipts were not rerun.
The correction occurred later, so ordering/cache control is incomplete. Sixteen
unique calls cost **51.43389 projected credits**, including invalid-role runs and
their replacements. The corrected eight-workflow comparison alone costs 47.97514.
No reset was redeemed. Reported credits use requested-model standard-rate
projections, not provider bills or weekly allowance conversion.

The calibration report treats the batch as one task with repeats aggregated.
Every comparison remains `insufficient_support`; no held-out validation or policy
promotion is claimed. Visual reading success is not subjective design-quality
validation. Original fixtures, image, receipts, calibration, and dashboard QA are
in [benchmark-v3](../artifacts/benchmark-v3/). Regenerate summaries without model
calls using `python scripts/summarize_benchmark_v3.py`.

## v0.2 Source-Repair Outcome

Direct Astra is now a first-class workflow, not merely a final judge. In this
bounded benchmark it had the lowest average projected cost of the three Astra
workflows tested. Sol remained cheaper on average. There is no evidence here
for universal Sol-price Astra quality or an optimal policy across all tasks.

| Workflow | Passed | Mean Projected Credits | Observed Range |
| --- | ---: | ---: | ---: |
| Astra direct | 2 / 2 | 2.87605 | 1.03660-4.71550 |
| Sol direct | 2 / 2 | 2.17002 | 2.16902-2.17102 |
| Astra plan + Terra execute | 2 / 2 | 6.25653 | 4.84100-7.67205 |
| Astra request evidence + answer | 2 / 2 | 8.23145 | 5.64140-10.82150 |

All intermediate calls are included: **12 model calls, 8 complete workflows,
39.06809 projected credits**. No reset credit was redeemed by the governor.
These are standard-rate projections from recorded token counters using the
requested CLI model, not provider-billed credits or weekly-percentage savings.
CLI events did not independently attest the serving model or service tier.

### Task Scope

One actual telemetry-helper defect was reproduced and repaired: invalid counters
were coerced to zero, fractional values truncated, and nonfinite inputs mishandled.
Each generated repair passed 90 executable input checks after the grader correction
below. The production normalizer was also fixed and regression-tested.

Four additional contracts covered cross-module cache accounting, a source-derived
mission-runtime architecture choice, adversarial release evidence, and bounded
research synthesis. These are **not five independent real-project deployments**.
Private-project source-derived scenarios were not fresh audits of those repos.

The fixture, answer key, and two opposite workflow orders were written before
calls. Every arm received the same task contract and access to the same evidence.
Demand mode requested evidence before answering; its extra request cost is included.
Calls were serial, read-only, low reasoning, and used inherited Codex configuration.
The code grader permits only a small AST subset, not arbitrary generated Python.

### Grader Correction

The first grader rejected a valid Sol repair because it used a local variable.
Assignments had not been prohibited in the task. A failing regression test exposed
the harness defect; the allowlist was corrected and **every stored answer rescored**.
No model was rerun and no adverse result was dropped. Initial grades remain in
[initial-grades.json](../artifacts/benchmark-v2/initial-grades.json).

## Host Overhead Experiment

The same small contract prompt passed on both hosts:

| Requested Model | Desktop Subagent Input | CLI Input |
| --- | ---: | ---: |
| Astra | 37,051 | 23,924 |
| Sol | 38,823 | 23,031 |

For Astra this is 35.4% fewer input tokens in this one host comparison. It is not
a universal reduction, a controlled breakdown of tool-versus-skill overhead, or
proof that all tasks cost less. The CLI preserved user configuration, execution
rules, and a read-only sandbox. No safety instructions, authentication settings,
global integrations, or installed skills were disabled. CLI and desktop tool
surfaces differ; choosing a host must account for the capabilities a task needs.

The earlier unfinished pilot stages were completed via explicit CLI handoffs:
the Terra worker and final Astra evidence answer both passed. The original
planner/request costs remain counted separately. Because these stages crossed
hosts and time, use the fully repeated v2 benchmark above for workflow comparison,
not these stitched completion runs as a clean matched experiment.

## Product Changes

- Whole-workflow Astra preference, including direct reasoning and implementation
  plans; no mandatory failed Sol attempt.
- Measured context floors and serial reservation/reconciliation by default.
- Opt-in `pm-bg run` read-only CLI adapter with replay protection and timeout cleanup.
- Explicit actual-token versus projected-credit versus missing-usage distinctions.
- Mandatory evidence preservation and bounded on-demand evidence selection.
- Matched experiment accounting, executable repair grading, and public artifacts.
- Updated landing demo: no forced Sol fallback or misleading 40% savings ceiling.

## What Is Not Proven

Two repeats of one small suite do not establish general quality, statistical
significance, multimodal parity, a learned routing policy, or weekly-limit savings.
Cache hits varied substantially and are not assumed in preflight reservations.
The governor cannot reduce the context already attached to this desktop chat,
override Codex account limits, or physically cap an in-flight provider call.
Its CLI adapter is read-only by design; it does not secretly grant write access.

Future evaluation should expand task families and independent repositories, use
held-out acceptance tests, and separately test warm/cold cache and tool-dependent
tasks. This is ongoing product validation, not a claim that every possible test
has been performed or that a globally optimal approach can be certified.

## Reproduce

```sh
python -m pytest -q
python scripts/summarize_benchmark.py
# Only after explicitly authorizing account usage:
python scripts/run_benchmark_v2.py --execute
```

The live runner uses unique dispatch IDs, retains failed/unknown reservations,
and reuses completed artifacts rather than silently billing identical retries.
Use a fresh governed experiment definition for a genuinely new trial. Raw prompts
from private conversations, credentials, and budget databases are not published.

See [the v1 pilot](EXPERIMENTS.md), [v2 receipts and results](../artifacts/benchmark-v2/results.json),
and [governed CLI execution](GOVERNED_EXECUTION.md).
