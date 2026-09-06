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
python -m premium_model_budget_governor.cli route --input examples\route_packet.json --plain
```

## 2. Run The First Decision

```bash
pm-bg route --input examples/route_packet.json --plain
```

The output should include:

- a recommended model
- allow/block/reroute decision
- parity ceiling
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

For broad exploration, docs, implementation, and logs, start with a cheaper
model. Escalate only when all are true:

- the task reaches a decision point
- evidence is bounded and scanned
- the capsule is strong enough
- premium billable tokens stay under the Sol-parity ceiling
- there is a real reason premium judgment may change the outcome

## 5. Verify The Repo

```bash
python -m pytest
python evals/run_synthetic_eval.py
```

