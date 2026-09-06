# Case Studies

These proof tests were run on private local projects and sanitized for public
sharing. They are not universal benchmarks. They show the intended behavior:
premium models are preserved for moments where they are likely to change the
decision.

## Case 1: Emergency Architecture Review

Scenario: a private architecture project was operating at about 12 percent
remaining weekly model capacity. The task was important, but the selected
evidence did not show an unresolved architectural conflict or repeated Sol
failure.

| Item | Result |
| --- | --- |
| Recommended model | `gpt-5.6-sol` |
| Routing decision | Sol-first hybrid |
| Budget mode | emergency |
| Astra turns spent | 0 |
| Files modified | 0 |
| Secret findings | 0 |
| Prompt-injection findings | 0 |

The governor withheld Astra because emergency-budget mode requires fresh
approval, cache savings could not be assumed, and focused Sol review was enough
for the current decision.

Interesting detail: a compressed premium capsule appeared cheaper than a broad
Sol pass, but that did not justify premium use by itself. A similarly focused
Sol review was cheaper still.

## Case 2: Release/Security Readiness Review

Scenario: a private release/security project had current qualification evidence
and bounded security closure evidence. Weekly capacity was again about 12
percent remaining.

| Item | Result |
| --- | --- |
| Recommended model | `gpt-5.6-sol` |
| Routing decision | Sol-only for now |
| Governor decision | Block premium Shadow Mode |
| Astra turns spent | 0 |
| Reset credits used | 0 |
| Files modified | 0 |

The governor blocked premium Shadow Mode because adding a premium review after
Sol would raise total workflow cost for the current evidence state. Premium
review was reserved for a later immutable launch candidate or an unresolved
high-consequence security disagreement.

## Public Lesson

The governor is not anti-premium-model. It is anti-waste.

Sometimes the highest-value frontier-model decision is:

```text
Do not call the frontier model yet.
```

## Reproducibility

The exact private files are not published. To reproduce the pattern on your own
project:

1. Run a Sol/Terra review first.
2. Select two to five authoritative evidence files.
3. Run `pm-bg route` with baseline and premium capsule token estimates.
4. Run `pm-bg capsule` and `pm-bg score` only when routing allows it.
5. Record whether the premium call would have changed the decision.
