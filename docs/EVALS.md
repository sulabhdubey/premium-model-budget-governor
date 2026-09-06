# Evals

Run the synthetic eval:

```bash
python evals/run_synthetic_eval.py
```

The eval compares:

- premium-only
- cheap-only
- governor hybrid

The included quality numbers are placeholders for launch rehearsal. Before
claiming real-world savings or quality retention, replace them with measured
task outcomes from actual runs.

## Public Benchmark Rule

Only publish claims that include:

- task set
- model versions
- token/credit accounting method
- pass/fail or quality rubric
- raw prompt-free result table
- date of measurement

## Suggested First Public Claim

Avoid a hard universal claim. Use:

> In synthetic and local workflow tests, the governor routed broad work away from
> premium models and preserved premium use for compact review turns. Reproduce
> the eval with `python evals/run_synthetic_eval.py`.
