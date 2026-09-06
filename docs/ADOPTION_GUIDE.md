# Adoption Guide

This guide is for teams or individual builders who want to reduce premium model
burn without losing premium model judgment.

## Start With One Workflow

Pick one recurring workflow:

- release readiness review
- architecture review
- security patch review
- large refactor planning
- production incident analysis

Do not start by routing every agent call. Start where premium spend is visible
and the decision boundary is clear.

## Define A Project Profile

Write a short profile for the repo:

```json
{
  "project": "example-product",
  "default_model": "gpt-5.6-sol",
  "premium_model": "gpt-6-astra",
  "premium_requires": [
    "bounded capsule",
    "secret scan",
    "prompt-injection scan",
    "capsule quality score",
    "Sol-parity ceiling"
  ],
  "premium_allowed_for": [
    "final architecture dispute",
    "high-consequence security ambiguity",
    "release blocker contradiction"
  ]
}
```

## Measure Before And After

For each run, record prompt-free telemetry only:

- task type
- selected route
- estimated or actual token counts
- blocked reasons
- whether premium review changed the decision
- final outcome

Avoid storing raw prompts, private files, logs, credentials, or customer data.

## Use Shadow Mode First

A strong first deployment pattern:

1. Cheaper model performs exploration and implementation.
2. Cheaper model produces a final answer and evidence list.
3. Governor scans and scores the capsule.
4. Premium model sees only the capsule and returns approve, reject, or patch.
5. Cheaper model executes any patch.

This keeps premium intelligence in the judgment role instead of the search role.

## Success Criteria

The governor is working when:

- premium calls are rarer
- premium prompts are smaller
- premium calls happen later in the workflow
- blocked premium calls are understandable
- team members can reproduce the decision
- quality regressions are visible in evals or review notes

## Failure Signals

Revisit the policy when:

- users bypass it manually
- every capsule scores as high quality
- no premium call is ever allowed
- the same task type repeatedly benefits from premium review but stays blocked
- actual token telemetry diverges sharply from estimates

