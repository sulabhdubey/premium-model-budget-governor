# v0.2.0: Astra-Preferred, Measured Workflows

This release moves beyond a Sol-first premium gate. Astra can be the direct
problem-solver, planner, investigator, or reviewer, with whole-task budgeting.

## Highlights

- Whole-workflow planning, measured context floors, and serial budget reservations.
- Opt-in read-only Codex CLI execution with replay protection and usage reconciliation.
- Evidence-on-demand without silent truncation, and matched experiment accounting.
- Actual-token import, stricter telemetry validation, and explicit unknown-cost handling.
- Updated website demo and installed/plugin guidance.

## Evidence

The repeated benchmark ran 12 model calls across eight complete workflows.
All eight passed one executable bug repair and four bounded contracts after a
documented grader correction. Direct Astra had the lowest mean projected cost
among the Astra strategies tested; Sol was cheaper on average.

A separate same-prompt host comparison recorded 37,051 Astra input tokens on a
desktop subagent and 23,924 through the CLI. No global configuration, rules, or
safety instructions were disabled. Different tool surfaces remain a tradeoff.

See [full results](BENCHMARK_RESULTS.md), including original failed/incomplete
pilot records and the corrected grader. This is limited evidence, not a universal
savings guarantee or proof of an optimal policy.

## Boundaries

Token-based credit projections are not provider-billed credits or subscription
percentages. CLI model identity is requested, not independently attested by its
JSON output. Scanners are heuristic, not a malware or prompt-injection guarantee.
The package cannot switch an existing desktop chat's model, erase its context,
or cap an already in-flight provider call. The execution adapter is read-only.

Idea, research guidance, and product management: **Sulabh Dubey**.
Research synthesis, engineering, testing, and documentation: **Codex by OpenAI**.
Independent project, Apache-2.0, no OpenAI endorsement.
