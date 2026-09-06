# Quickstart

This guide gets you from clone to first routing decision in a few minutes.

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
