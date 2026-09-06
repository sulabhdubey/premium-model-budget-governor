# Premium Model Budget Governor

Use frontier models for judgment, not waste.

Premium Model Budget Governor is a local-first routing and evidence system for
Codex-style AI work. It keeps expensive frontier models such as GPT-6 Astra on
small, high-leverage review turns while cheaper models do broad exploration,
implementation, tests, and logs.

The core rule is simple:

```text
premium billable token volume <= 40% of the equivalent Sol workflow
```

When Fast mode multiplies premium spend, the ceiling tightens further.

## Why This Exists

Many builders are hitting the same failure mode: the best model is selected for
everything, then a weekly budget disappears in a day. The problem is usually not
the model. It is ungoverned context volume.

This project gives you a practical alternative:

- run cheaper models first
- compress evidence into a capsule
- scan untrusted text and secrets
- ask the premium model to approve, reject, patch, or choose
- record prompt-free telemetry
- learn which tasks actually benefited

## Features

- Sol-parity credit estimator
- Deterministic model routing policy
- Astra Shadow Mode: premium model judges a cheaper model's final answer
- Evidence Graph Compiler: converts files, tests, risks, and claims into compact graph summaries
- Distillation Ledger: converts valuable premium decisions into reusable local doctrine
- Cheap Model Tournament: cheaper models create candidates, premium model judges finalists only
- Benefit Predictor: learns when premium models are likely worth the spend
- Context Poison Firewall: scans untrusted text for prompt-injection and secret exfiltration patterns
- One-click capsule generation and quality scoring
- Prompt-free token telemetry ingestion
- Codex plugin bundle under `plugin/`

## Install

```bash
python -m pip install -e ".[dev]"
```

On Windows, if the `pm-bg` command is not on PATH in the current terminal, use:

```powershell
python -m premium_model_budget_governor.cli route --input examples\route_packet.json
```

## Quick Start

Decide whether to allow a premium model:

```bash
pm-bg route --input examples/route_packet.json
```

Equivalent module form:

```bash
python -m premium_model_budget_governor.cli route --input examples/route_packet.json
```

Build a capsule:

```bash
pm-bg capsule --root . --goal "Review this architecture" --decision "Approve or patch?" --include README.md --output capsule.md
```

Score the capsule:

```bash
pm-bg score capsule.md
```

Compile an evidence graph:

```bash
pm-bg graph --root . --include README.md --query "budget model routing" --capsule
```

Rank cheap-model candidates before one premium judge call:

```bash
pm-bg tournament --input examples/tournament_packet.json
```

Record prompt-free telemetry:

```bash
pm-bg telemetry --input examples/telemetry_packet.json
```

## The Hybrid Pattern

1. Spark, Luna, Terra, or Sol explores the repository.
2. The governor ranks and scans evidence.
3. A compact capsule or graph summary is created.
4. Astra or another premium model gets one small decision turn.
5. Cheaper models execute the approved plan.
6. The ledger records whether the premium turn helped.

## What This Does Not Claim

- It does not magically make premium tokens cheaper.
- It does not bypass provider usage limits.
- It does not guarantee identical quality to premium-model-only workflows.
- It cannot physically stop manual model selection unless your host calls the policy before model use.

It does reduce waste by keeping premium models away from broad, repetitive,
low-leverage context.

## Codex Plugin

The `plugin/` directory contains a Codex plugin bundle with the governor skill.
Use it when you want Codex to load the policy as reusable local workflow
instructions.

## Safety

The scanner is defensive and heuristic. Treat it as a preflight layer, not a
complete security product. Do not send secrets, credentials, personal data,
large logs, or untrusted webpage instructions to a model without review.

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## Roadmap

- Real host-level pre-model hook integration where available
- Dashboard packaging for global task visibility
- Benchmark suite comparing premium-only, cheap-only, and hybrid workflows
- More provider/model profiles
- Stronger prompt-injection classifier
- related local-memory project style local memory integration for project-specific doctrine

## License

Apache-2.0. See [LICENSE](LICENSE).
