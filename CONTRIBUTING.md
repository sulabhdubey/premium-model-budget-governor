# Contributing

Thanks for helping make premium model use less wasteful.

## Principles

- Preserve prompt-free telemetry.
- Prefer deterministic policy over opaque magic.
- Keep premium model use bounded and explainable.
- Add tests for every new routing, scanner, or capsule rule.
- Do not add vendor-specific claims without a source and date.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

## Pull Requests

Include:

- the problem being solved
- the model/budget behavior affected
- tests or evals
- any new safety or privacy implications

## Public Claims

Do not claim savings, quality, or security guarantees without a reproducible
benchmark or test case in the repository.
