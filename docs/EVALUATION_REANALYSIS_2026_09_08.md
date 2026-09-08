# Evaluation Integrity Upgrade

This is a reanalysis of existing public receipts, not a new model experiment.
No new model calls were dispatched for this analysis. Engineering-chat usage is
outside those receipts. Historical inputs and reports were not overwritten.

Source: [combined experiment input](../artifacts/field-trial-2026-09-07/combined-experiment-input.json).
Context and limitations: [original field trial](FIELD_TRIAL_2026_09_07.md).

## What The Improved Comparator Shows

All three comparisons contain five matched tasks, with no unmatched supplied
runs or excluded cost pairs. Direct Astra totals 31.90300 estimated credits for
the five baseline workflows. Each task has one observation per arm, so ordinary
and task-balanced means are identical here.

| Candidate | Total estimated credits | Mean difference vs Astra | Cheaper with both fixed grades passing |
| --- | ---: | ---: | ---: |
| Sol preparation then Astra | 51.44091 | +3.90758 | 1 of 5 |
| Sol draft then Astra review | 47.42970 | +3.10534 | 0 of 5 |
| Direct Sol | 13.34574 | -3.71145 | 5 of 5 |

All supplied fixed grades passed. Grading was by Codex, not independent blinded
review. The one cheaper preparation outcome was cache-confounded. These results
do not establish equal frontier capability, billed savings, or weekly-limit savings.
They support avoiding unnecessary handoffs, not replacing Astra everywhere.

## What Changed In Evaluation

- Missing runs on either side are visible, rather than just candidate attrition.
- Excluded cost observations carry explicit reasons; missing usage is never free.
- Task-balanced means expose averages dominated by repeated easy tasks.
- Cheaper failures are counted separately from cheaper pairs that both passed.
- Historical receipts are replayed by a regression test without calling models.

## Next Prospective Trial

Before running new models, freeze a public, privacy-reviewed task manifest and
acceptance rubric that has not been tuned against trial answers. Keep a record
of every enrolled task, including cancellations and missing receipts. The present
comparator cannot detect tasks omitted from both sides of an input packet.

Primary comparison: ordinary direct Astra versus direct Astra with supported,
task-relevant host-context reduction. Preserve safety policy, required tools,
visual inputs, and mandatory evidence. Do not add handoffs merely to lower a
worker's token count. Treat Sol as a secondary cost reference, not a substitute
for demonstrating preserved Astra capabilities.

Include bug repair, cross-file changes, architecture conflict, security review,
visual inspection, and research synthesis. Freeze task snapshots; counterbalance
arm order; repeat each task; record cache state and all preparation/retry costs.
Use objective checks plus an independent reviewer who does not see arm labels.
Declare quality gates and stopping rules before calls, and retain failed outcomes.
Report per-task results and separate cached from uncached observations.

No new paid trial, independent review, or volunteer onboarding is claimed here.
This protocol is preparation, not completed evidence or automatic authorization.
