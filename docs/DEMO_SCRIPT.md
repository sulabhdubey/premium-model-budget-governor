# Demo Script

Use this for a short public demo, issue comment, or video walkthrough.

## Two-Minute Demo

1. Show the problem:

```text
I want premium-model quality, but I do not want to spend premium budget on
reading every file and repeating logs.
```

2. Run the whole-workflow planner:

```bash
pm-bg plan --input examples/astra_preferred.json
```

3. Point out the decision:

```text
The governor selects an Astra workflow that fits the example budget, including
all stages. These are illustrative estimates, not executed calls.
```

4. Build a tiny capsule:

```bash
pm-bg capsule --root . --goal "Review launch readiness" --decision "Approve or patch?" --include README.md --include docs/ARCHITECTURE.md --output capsule.md
pm-bg score capsule.md
```

5. Show the principle:

```text
Give Astra the actual evidence it needs to plan, investigate, implement, or
review. Do not add handoffs unless the complete workflow benefits.
```

6. Run the eval:

```bash
python evals/run_synthetic_eval.py
```

## Decision Record Template

```text
Task:
Budget remaining:
Requested model:
Recommended model:
Decision:
Blocked reasons:
Evidence files:
Capsule score:
Premium turns spent:
Would premium judgment change the outcome:
```

## Honest Closing Line

```text
This does not change premium token prices. It compares complete ways of using
Astra, accounts for overhead, and makes budget and capability tradeoffs explicit.
```
