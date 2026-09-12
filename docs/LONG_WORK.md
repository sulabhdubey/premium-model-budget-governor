# Long-work observations (local development)

`pm-bg long-work --input examples/long-work.json` reconciles an explicitly supplied
JSON packet without a model call. The example is synthetic, not a savings result.

Enroll opaque `work_units` before collecting receipts to expose missing work.
Each receipt needs `receipt_id`, `work_unit_id`, `source_id`, `model`,
`counter_kind`, `scope`, and `usage`. A source ID must identify one distinct
nonoverlapping usage interval, not merely a session name. IDs are caller supplied;
this command cannot attest whether they accurately identify host usage.

Only final counters with exclusive scope are additive. Identical duplicate IDs
count once; conflicting identities fail. Multiple IDs for one source, cumulative
counters, parent totals including children, and missing usage keep totals unknown.
The observed subtotal is not the full workflow cost. Without enrolled work units,
coverage says nothing about work omitted from the packet.

Input totals include cached subsets; do not add cached tokens again. Output follows
the existing telemetry contract. This initial reconciler does not independently
normalize different provider reasoning semantics, model reroutes or service tiers.
Only supply counters covered by that contract; other host formats need adapters.
Cache writes retain counts and have unknown cost unless an explicit matching
[rate contract](ACCOUNTING_CONTRACT.md) supplies their rate. Pass `rate_contract`
and `service_tier` on each receipt; the journal retains its snapshot and fingerprint.
Legacy configured rates are estimates, not current provider billing or weekly quota.
Experiment receipt normalization and the local rollout importer also preserve
cache-write uncertainty. An explicitly supplied billed credit amount has its own
basis; it is not derived from the legacy table. Local rollout import recognizes
the documented implementation's `cache_write_tokens` field, not every possible
provider cache schema. Unsupported host formats still require adapters.

No prompts or arbitrary extra fields are copied into the report. Use genuinely
opaque IDs: format validation cannot stop a name from identifying a private project.
Keep source mapping and reports private until export review. The command does not
read host logs automatically, settle leases or enforce this chat's model choice.
Automatic collection, host journal integration, and the remaining
accounting adapters are separate unfinished work. This is observational reporting,
not a controlled comparison or an assertion of savings.

## Retain A Snapshot

Add `--journal <private-observations.sqlite3> --observation-id <opaque-id>` to
reconcile and retain a report. Omit `--input` with those two options to read it
without recalculating historical estimates. Reusing an ID with different content
fails; use a new ID for a later observation or reanalysis. Identical retries return
the original snapshot. Snapshots are not additive: two may cover the same work.

The dedicated SQLite journal has an application ID and schema version. It refuses
foreign databases and unknown versions instead of migrating them. Never point it
at a budget or project-memory database. Transactions serialize writes, and a
checksum detects accidental payload corruption, not malicious local alteration.
Storage uses the operating system's local file permissions; it is not encrypted.
Back up with SQLite's backup API while open, or copy the file after writers close.
The journal has no automatic retention deletion or remote export in this version.

The App Server runner also recognizes `model/rerouted` for its active turn and
retains unknown spend instead of settling mixed-model totals at the original rate.
This behavior has synthetic replay coverage, not a paid live-reroute qualification.
Contract: [official App Server events](https://learn.chatgpt.com/docs/app-server).

## Observe An Explicit Local Rollout

`pm-bg observe-rollout --input <rollout.jsonl> --journal <observations.sqlite3>
--observation-id <snapshot-id> --work-unit <opaque-unit> --source-id <opaque-source>`
collects counters from one explicitly selected single-model local rollout. Keep
source IDs stable for the same session; use a new observation ID for a new snapshot.
The command never discovers or traverses unrelated conversations.

Reads are bounded to 64 MiB per file and 4 MiB per line. Malformed records,
mixed-model histories, decreasing counters and detected changes during the read
fail instead of creating a misleading receipt. A local log can be modified and
the stability check is not adversarial attestation. The report retains a SHA-256
digest and byte count, not the file path or conversation contents. Hashes are not
anonymity guarantees.

The observation is cumulative with unknown parent/child scope. Its raw counters
remain visible in the saved record, but it does not become an additive final
receipt, settle a lease or establish that this goal caused that consumption.
Large or continuously changing sessions can use the explicit sample option below;
do not silently truncate them and then claim complete coverage. This command is
explicit local collection, not background monitoring or universal chat control.

### Large Active Sessions

Add `--sample` to observe a fixed tail range of at most 4 MiB. The reader checks
that range twice for stability, permitting append-only growth beyond it. It
discards incomplete boundary lines and records their byte counts. Complete invalid
events fail; missing counters are not treated as zero. The stored digest identifies
the sampled bytes only, not the entire file.

The sample reports the latest observed cumulative counters and any decreases seen
within the sample. A decrease breaks continuity; the reader does not assume its
cause or combine segments. Offsets, sample size and ignored bytes remain visible.
It does not establish full history, model attribution, parent/child scope, cost,
or consumption of a particular goal. Even a sample containing only Astra contexts
cannot prove that Astra produced the historical cumulative total.

Sample-derived records therefore require unknown model/scope and cumulative counter
kind. The reconciler rejects attempts to relabel them as final exclusive receipts.
They remain useful private observations, not settlements or savings evidence.
This is bounded point-in-time sampling, not yet an incremental cursor collector
or automatic monitoring. Local file mutation cannot be ruled out by a checksum.
