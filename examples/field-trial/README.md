# Field-Trial Starter Tasks

These are authored, public evaluation fixtures, not independent project results.
They establish a fixed starting point for bounded coding, research, writing,
visual and review comparisons. No model runs or human judgments are included.
Do not feed `suite.json` to the model: it contains the grading criteria.

Stage a separate project so the grading criteria are not exposed as evidence:

```sh
python scripts/prepare_trial_task.py --task study-evidence-synthesis --output /existing/parent/new-trial-project
```

The parent must exist and the destination must be new. The script checks frozen
hashes, copies only named inputs and `task.txt`, and never invokes a model. Select
this staged folder, not the suite/repository root, in the workbench. Host tools
and inherited connectors still require a separate permission review; a copied
folder alone is not a security sandbox. Keep oracle access out of experiment arms.

Use each task's prompt and named inputs only. All arms receive the same originals;
preparation and review arms may add intermediate work but may not omit originals
from the final model's available evidence. Preserve images as images.

Before a run, record the suite and input SHA-256 hashes, configured host, reasoning,
tools, cold/warm session conditions, and the requested arm. Preregister order and
budget. One task is not one repeat; five tasks are not a representative population.

Grade final answers blind to model and cost. Every listed criterion is required;
an unresolved criterion is ungraded, not passed. Keep original outputs privately
until an explicit publication review. Do not execute generated code automatically.
Coding patches require inspection and tests in an isolated disposable copy.

After explicit spending approval, execute one call at a time and reconcile each
receipt. Include preparation, retries, abandoned calls and final reviews in the
arm cost. A missing receipt makes cost unknown. The existing `pm-bg experiment`
command can compare completed, externally graded runs; it must not be given
invented host receipts or a guessed `passed` value.

The visual fixture is `queue-chart.png`, generated from `queue-chart.html` by
`scripts/render_trial_fixture.cjs`. Its colored bars intentionally disagree with
one stale note, requiring the model to prioritize the actual plotted state.
The image is a rendered chart, not a screenshot of a real company's operations.

RTA-Net and CircuitProof validation remains a separate gate using fresh bounded
repository snapshots, project authority rules and owner-approved tasks. This
starter suite must not be represented as completing that gate or human trials.
