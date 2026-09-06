# Demo Script

Use this for a short public demo, issue comment, or video walkthrough.

## Two-Minute Demo

1. Show the problem:

```text
I want premium-model quality, but I do not want to spend premium budget on
reading every file and repeating logs.
```

2. Run the route command:

```bash
pm-bg route --input examples/route_packet.json --plain
```

3. Point out the decision:

```text
The governor recommends a cheaper model first and explains why.
```

4. Build a tiny capsule:

```bash
pm-bg capsule --root . --goal "Review launch readiness" --decision "Approve or patch?" --include README.md --include docs/ARCHITECTURE.md --output capsule.md
pm-bg score capsule.md
```

5. Show the principle:

```text
The premium model should judge this capsule, not browse the entire repo.
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
This does not make premium tokens cheaper. It makes premium calls rarer,
smaller, later, and easier to justify.
```

