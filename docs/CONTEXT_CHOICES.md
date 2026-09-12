# Continue, Compact Or Restart?

`pm-bg context-choices --input examples/context-choices.json` compares proposed
remaining-work costs without changing any context, host settings or model. The
example is synthetic, not a measured benefit or a published price table. It keeps
focused direct Astra because the candidate's preparation and recovery remove its
apparent advantage. The CLI uses the usual `ok` / `result` JSON envelope.

This is a planning prototype, not automatic compaction or a capability guarantee.
It is CLI-only for now; no extra always-loaded MCP tool or shared configuration
is installed merely to expose an unvalidated optimization.

## Contract

- `schema_version: 1` and a common `estimate_basis` (`estimated_credits`, version)
  describe caller estimates. Reprice every candidate consistently before comparing.
  This is not an account allowance, provider bill or currency conversion.
- `required` lists capability, evidence and state identifiers. Use a frozen task
  contract and versioned source identifiers; empty lists are explicit assertions
  that a category is unnecessary, not discovery results.
- `acceptance` contains 1-256 unique checks with pending/passed/failed/unknown
  status. Only all-passed proposes stopping. Caller results are not independently
  checked. Optional further work needs its own acceptance and cost plan.
- `baseline` is equally focused direct continuation, not an inflated broad review.
  Up to 32 candidates may propose continue, compact or restart. All IDs are unique.
- Each option declares host-operation support, model, effort, source snapshot and
  retained capabilities/evidence/state. Different models, reasoning profiles or
  source snapshots cannot qualify as preserving alternatives here. This does not
  claim that every unchanged profile actually preserves quality.
- Each option explicitly supplies preparation, execution, verification and recovery
  intervals `[lower, upper]`. `null` means unknown, never zero. Include the optimizer,
  retrieval, state transfer, tool overhead, retries, cache changes and human-assisted
  rework where part of the cost scope. Include every expected paid stage exactly once.
  Already-spent identical costs are sunk: account for them in the task ledger, not
  as a misleading advantage of one remaining-work option.

The evaluator adds all four stages. An eligible candidate must have an upper total
strictly below the baseline's lower total. Otherwise it retains the baseline; an
unqualified baseline needs replanning. These are supplied bounds, not statistical
confidence intervals. Omissions or optimistic numbers can invalidate a proposal.
Equal candidates use cost then ID for stable ordering, not a learned quality rank.

## Before Execution

Verify source versions and permission scope again. Use the existing evidence
selector for hashes, expiry, mandatory content and expansion, and manually assess
state fidelity where there is no executable oracle. Do not pretend an evidence ID
alone proves preservation or scanner success proves security.

Probe the actual host for capabilities; never claim `supported: true` from this
example. The proposal does not broaden `focused_catalog`, which remains restricted
to its existing tested Astra/low profile. A high-effort proposal is not a high-effort
host-profile qualification. The planner cannot compact this desktop conversation.

Submit a chosen complete workflow through normal `plan` and budget admission before
any dispatch. This comparison reserves nothing and cannot authorize execution.
Measure actual outcomes and all costs against equally focused direct Astra before
promoting the affected task/host/profile. Report cheaper-but-worse results too.

## What The Tests Establish

Deterministic fixtures check interval accounting, unknowns, capability loss,
reasoning/model changes, stale snapshots, unsupported actions, acceptance stopping,
input validation and CLI behavior. They do not establish savings, actual state
preservation, independent quality or human usability.
