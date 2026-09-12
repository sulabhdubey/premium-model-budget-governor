# Local Seven-Day Observation Digest

The Workbench has an opt-in digest in Usage. Enable or disable it in Settings.
The preference survives a local Workbench restart. It is off by default and does
not start a model, collection daemon, email, upload or scheduled delivery. It is
calculated when opened or refreshed, and after an observation import or cleanup.

## What It Measures

The rolling seven-day window uses the observation journal's `recorded_at` timestamp.
These are saving dates, not task execution dates. Imported counters may describe
older work. The report shows observations, incomplete observations, sources seen,
undated Workbench tasks excluded and each source's latest saved counters.

It never adds or subtracts overlapping observations. Two different receipts for
one source in the same latest observation are ambiguous and display unknown
counters. Counters from a cumulative source can cover much more than seven days.
Weekly tokens, cost, allowance and savings remain unknown. Recorded model labels
are not verified model identities. Caller source IDs do not establish attribution.

Current Workbench task records do not carry trustworthy execution dates, so they
are counted as excluded, not assigned invented dates. The digest does not cover
other chats, deleted records, missing receipts or unrecorded activity. A complete
observation is not proof that the entire account or week was observed.

## Privacy And Failure Behavior

Only the Workbench's own observation journal is read. Browsers cannot supply a
database path. Digest endpoints require the existing session authentication and
same-origin controls; changing the setting requires explicit approval. Disabling
does not delete receipts, backups or budgets. No report is saved or shared merely
by enabling the display. Source labels are temporary ordinals rather than the raw
source, work-unit or receipt IDs. Numeric patterns can still be identifying.

The journal is read in one SQLite read transaction, with identity/checksum/schema
validation. Unknown schemas are not migrated. Up to 10,000 observations, 16 MiB of
payloads and 50,000 included record entries are supported; larger input requires
reviewed maintenance instead of a silently partial digest. Display is limited to
100 latest sources with a visible truncation flag. Future-dated observations are
excluded and counted. Database checksums are not local-attacker authentication.

An invalid journal produces an error, not zero usage. The UI clears stale digest
rows on failure. An uncertain preference save must be refreshed before changing it
again. Preference writes use the existing atomic private-file helper; unknown
preference versions are not overwritten. This is a local display preference, not
permission to collect more data or modify a shared connector.

## Verified Scope

Unit tests cover opt-in persistence, consent, recorded-time boundaries, overlapping
and ambiguous sources, display limits, corruption, unknown schemas and read bounds.
Local HTTP tests cover authentication, origin, exact request fields and zero
model dispatch. Browser QA exercises the actual local opt-in/display/disable path,
plus a labeled simulated digest-fetch failure and recovery at desktop/mobile sizes.
Human understanding and full-work attribution remain separate open validation gates.

The digest recognizes the journal's `complete_for_supplied_receipts` status; this
means supplied receipt coverage, not complete account or weekly coverage. Cached
input is displayed only when the normalized receipt marks it as reported. An
assumed zero or an older record without assumption provenance displays Unknown.
This does not rewrite historical records. Explicit reported zero remains zero.
