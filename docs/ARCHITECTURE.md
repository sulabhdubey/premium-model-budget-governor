# Architecture

Premium Model Budget Governor is built around one premise: premium model quality
is most valuable at decision boundaries, not during broad context gathering.

## Components

- `cost.py`: provider/model credit rates and Sol-parity estimates
- `policy.py`: deterministic allow/block/route decisions
- `scanners.py`: prompt-injection and secret preflight checks
- `capsule.py`: safe evidence capsules and quality scoring
- `evidence_graph.py`: compact graph summaries of files, tests, and risk signals
- `shadow.py`: Astra Shadow Mode review packets
- `tournament.py`: cheap-model candidate ranking before premium judging
- `distillation.py`: prompt-free doctrine ledger
- `predictor.py`: lightweight benefit prediction from task shape and outcomes
- `telemetry.py`: usage normalization without storing prompts
- `cli.py`: user-facing command line

## Data Boundaries

The project is local-first. Ledgers should store counts, routing decisions,
fingerprints, outcomes, and doctrine summaries. They must not store raw prompts,
API keys, secrets, private logs, or proprietary documents.

## Enforcement Boundary

The package can enforce decisions inside wrapper flows, CI checks, scripts, and
future host hooks. It cannot stop a user from manually selecting an expensive
model in a chat UI unless that host calls the policy before model use.
