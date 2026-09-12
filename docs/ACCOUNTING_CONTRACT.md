# Configured Accounting Contract

Local development feature: telemetry, experiment receipts and long-work observations
can accept `rate_contract`. This is an explicit estimate, not evidence of a bill.
Execution leases still use their existing configured rate path; custom observation
rates do not authorize dispatch or retroactively change settlements.

```json
{
  "schema_version": 1,
  "version": "example-v1",
  "source_id": "synthetic-example",
  "effective_date": "2026-09-08",
  "unit": "estimated_credits",
  "model": "gpt-6-astra",
  "service_tier": "default",
  "input_semantics": "total_includes_cache",
  "output_semantics": "total_includes_reasoning",
  "per_million": {
    "input": 100,
    "cached_input": 10,
    "cache_write": 200,
    "output": 500
  }
}
```

These numbers are synthetic. Maintain a separate source record for real configured
rates. A source ID or date does not prove current provider pricing. Use null for
an unknown effective date and for an unsupported cache-write rate. Do not put
private names or paths into identifiers; format validation cannot anonymize them.

The contract requires total input including disjoint cached-read/write subsets,
and total output including reasoning. It subtracts cache subsets before pricing
ordinary input; reasoning is not added a second time. Adapters must verify their
source counters follow these semantics. Different provider semantics are rejected
as unsupported rather than automatically translated. USD amounts cannot enter a
credit contract; no token-to-weekly-quota conversion is provided.

The outer packet's `service_tier` defaults to `default` as a configured assumption,
not an attestation of actual host tier. A custom contract must match that tier and
model. Unsupported matches retain unknown cost. Known legacy Fast estimates remain
available for Astra in the experiment receipt path. No additional tier is inferred
from a model name or from response latency.

Results retain a normalized `rate_snapshot`, its SHA-256 `rate_fingerprint`, and
`rate_version`. Fingerprints identify the numeric and semantic assumptions, not
their trustworthiness. Historical journal reads return saved values without
repricing. Use a new observation ID for a reanalysis; never sum overlapping versions.

Without a custom contract, the bundled `legacy-configured-v1` table preserves
existing arithmetic and marks its effective date unknown. It is not a newly
verified price catalog. A supplied `billed_credits` value in an experiment receipt
remains `host_billed`, distinct from a computed estimate; supplying that field is
not cryptographic proof that the host billed it.

Validation covers malformed/nonfinite rates, cache subsets, model/tier mismatch,
snapshot mutation and replay, and both normalization paths. Automatic live price
updates, service-specific cache TTL rates, mixed-model attribution and
provider-authoritative billing adapters remain unfinished.

## App Server Settlement Snapshot

The App Server execution packet accepts an optional `rate_contract` matching its
requested model and default service tier. It validates and copies the contract
before host startup. With no supplied contract it captures the bundled estimate
table instead. The resulting snapshot is used for terminal estimation, settlement
and recovery; changing the caller's object or a later bundled table cannot reprice
that saved receipt. This does not select a provider tier or attest actual charges.

New terminal JSON payloads use schema version 2 and include a normalized rate
snapshot and fingerprint. Existing version 1 rows remain readable without a table
migration or rewrite; lacking a stored snapshot, they retain their prior recovery
behavior and fail if current arithmetic differs. A fingerprint and local checksum
are consistency checks, not protection against an account owner rewriting both.

Incompatible contracts fail before dispatch. Missing or conflicting terminal
evidence still retains its reservation. The estimate supplied for admission remains
the caller's whole-call estimate, not a provider hard cap or a calculated guarantee
that the configured price contract will fit.

The CLI `run` packet also accepts `rate_contract`, captured before reservation and
dispatch. It returns its snapshot/fingerprint with the projection and retains the
reservation when reported cache writes lack a configured rate. CLI event parsing
uses the shared counter validator and reports missing-cache assumptions across
completed turns. Defaulted estimates remain conditional, not measured cache usage.
The CLI also stores terminal evidence before settlement, using the existing journal
and frozen-rate recovery. Its host source is `codex_cli`; unavailable thread/turn
identifiers are null, not invented. Failed journal writes or settlement retain the
reservation for reconciliation. Only saved, validated evidence can recover; a crash
before that write still leaves unknown spend. Requested CLI
model identity and inherited service configuration are not provider attestation;
the default-tier contract does not change or verify the provider's actual tier.

### Recover Without Repeating A Call

Use the same ledger, task ID and call ID as the interrupted run. First preview:

```sh
pm-bg recover --ledger budget.sqlite3 --task-id task-1 --call-id call-1
```

Then explicitly reconcile validated evidence:

```sh
pm-bg recover --ledger budget.sqlite3 --task-id task-1 --call-id call-1 --apply
```

Preview validates saved evidence without settling it. Apply revalidates and uses
the existing idempotent settlement checks, without dispatching a model. The result
`no_terminal_evidence` means no qualifying saved terminal receipt exists; it does
not mean the call was free or release its reservation. Corrupt or conflicting
evidence fails rather than settling. Do not edit receipt payloads to force recovery.
Keep output private: prompt-free receipts still contain task and host identifiers.

## Counter Validation

Telemetry and direct experiment-receipt normalization share counter validation.
Both accept input/prompt and output/completion names, cache detail objects
under either naming style, and the local cached_input_tokens alias. Supplied aliases
must agree; malformed detail objects, contradictory totals and reasoning exceeding
output fail rather than silently selecting one counter. Reported reasoning is an
output subset, never an extra charge. Missing reasoning remains null.

For compatibility, this legacy normalization path still assumes absent cache
read/write counts are zero. The returned counter_assumptions list now explicitly
identifies each such assumption, also retained in direct experiment and long-work
receipt records. A normalized counter does not retroactively recover fields lost
by an older importer; source-specific import coverage still needs separate review.
Estimated credits using these defaults are conditional estimates, not measured
cache usage. Explicit zero and missing data are therefore distinguishable. The
incremental collector instead retains absent cache counters as null and produces
no cost estimate. These paths must not be conflated.

Historical saved reports are not rewritten. Reanalysis with newly preserved fields
can conflict with an existing immutable observation ID; use a new ID and preserve
the old record, rather than modifying it or adding both as independent usage.

New local cumulative-log imports preserve absent cache fields rather than writing
explicit zeros into the source receipt. Missing-cache assumptions therefore survive
receipt normalization. Each reported snapshot is validated, and a missing field
does not erase its last reported value for detecting subsequent counter decreases.
That retained value is used only for reset detection, not imputed into final usage.
The importer remains a bounded, single-model session snapshot, not turn attribution
or provider attestation. Previously imported receipts are not repaired automatically.
