# Quickstart

This guide gets you from clone to first routing decision in a few minutes.

## Local Workbench Preview

The unreleased source version includes a real local task interface. It is separate
from the public website's illustrative demo and is not in the published rc.2 wheel.
Follow [isolated installation](INSTALLATION.md), then launch the installed command
with `serve --project /absolute/path/to/project` (use your actual folder path).

1. Keep the private browser link and terminal output out of public messages.
2. Describe a read-only task; choose Astra Preferred and a task budget estimate.
3. Select evidence or images, then preview. No model call has started yet.
4. Inspect the model, required reasoning, estimate and uncertainty. Approve only
   when you accept the task and potential spend; estimates are not hard billing caps.
5. Inspect the answer and recorded usage. Stop/reconnect avoids resubmitting the
   same task. Missing terminal usage remains unknown, not zero.
6. Use Manage projects for additional approved folders. Removing a registration
   does not delete that project's files or past usage records.

For CLI-only planning without model execution, continue below. For exact UI scope,
read [WORKBENCH.md](WORKBENCH.md). Technical setup and human usability validation
remain open; this is not yet a one-click product for every user.

## 1. Install

```bash
git clone https://github.com/sulabhdubey/premium-model-budget-governor.git
cd premium-model-budget-governor
python -m pip install -e ".[dev,mcp]"
```

Windows PowerShell:

```powershell
python -m pip install -e ".[dev,mcp]"
python -m premium_model_budget_governor.cli plan --input examples\astra_preferred.json
```

## 2. Run The First Decision

```bash
pm-bg plan --input examples/astra_preferred.json
```

The output should include:

- a selected complete workflow and Astra's roles
- planned or needs_replan decision
- total estimated cost, including all stages and contingency
- blocked reasons, if any

## 3. Build A Capsule

Only build capsules from intentionally selected files.

```bash
pm-bg capsule \
  --root . \
  --goal "Review this architecture decision" \
  --decision "Approve, reject, or patch" \
  --include README.md \
  --include docs/ARCHITECTURE.md \
  --output capsule.md
```

Score it:

```bash
pm-bg score capsule.md
```

## 4. Use The Rule

Compare focused direct Astra with hybrid alternatives. Replace the example's
illustrative costs with task-specific estimates and measured host input. Preserve
required images, tools, and reasoning depth. Delegate only if the whole workflow
benefits; no prior Sol failure is required. If Astra cannot fit, return
needs_replan rather than silently completing on Sol. The older `route` command
is a single-call gate, not the default whole-task policy.

Before execution, open a task budget and reserve calls. See
[governed execution](GOVERNED_EXECUTION.md) and
[capability controls](CAPABILITY_CONTROLS.md) for actual images, project profiles,
upper estimates, expiry, calibration, and dashboard commands. Planning alone
does not switch the active chat model or consume a model call.

## 5. Verify The Repo

```bash
python -m pytest
python evals/run_synthetic_eval.py
```
