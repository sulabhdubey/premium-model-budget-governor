# Resumable Local Counter Observations

`collect-rollout` reads one explicitly selected local Codex JSONL file and records
bounded observations in a dedicated collector database. It does not scan all chats,
start a watcher, dispatch a model or settle a budget.

```text
pm-bg collect-rollout --input <explicit-rollout.jsonl> --journal <new-collector.sqlite3>
pm-bg collect-rollout --journal <collector.sqlite3>
```

The second form reads the newest 100 saved observations, with a truncation flag.
Use a separate database, not a budget ledger, observation journal or project brain.
Unknown databases/schemas are rejected without migration. The input must not be
the database, including through a hard link.

## Collection Contract

The first collection bootstraps from at most the last 4 MiB. History before that
point is unmeasured, not free. It stores a cumulative baseline but no difference.
Later calls resume after the last complete JSONL line and read at most 4 MiB per
call. An unfinished line waits for the next collection; a line exceeding the bound
fails explicitly rather than being silently skipped. Backlog bytes describe the
observed file-size check, not a guarantee no more events arrived afterward.

Each observation and its next checkpoint commit in one SQLite transaction. A
rollback cannot save one without the other. Concurrent collectors serialize; an
unchanged file creates no duplicate observation. Reads are verified against the
fixed range, file identity, prefix/end anchors and the previous counter line.
Replacement, truncation and changes to these checked regions require explicit
investigation and a new collection after preserving existing evidence.

Checksums/anchors are local consistency evidence, not authentication, a complete
historical file audit or provider attestation. Edits outside checked historical
regions may not be detected. Rewriting a log while collecting is unsupported.
Collector history is bounded to 10,000 observations, with 64 KiB per saved payload;
preserve and rotate explicitly instead of silently deleting history.

## What A Difference Means

`counter_difference` is the difference between two observed cumulative counter
positions, not a task/goal boundary, independent model turn receipt or total bill.
`counter_interval_line_offsets` identifies those two source lines when a difference
is available; it is not necessarily the same as the byte range read by that call.
Missing cache fields remain null. Cached tokens are an input subset, not additional
input. Counter decreases or incompatible cache differences invalidate that interval;
the latest valid baseline can support a later interval. Missing token-event
information also prevents claiming a complete interval.

The current collector leaves actual model identity and estimated credits unknown.
Do not infer model attribution from a nearby context message or combine these
observations with existing parent/worker receipts without a proven coverage map.
Output counters include their reported reasoning subset; they must not be summed
with reasoning again. Separate reasoning attribution remains outside this version.

No raw source lines, task text, source paths or account tokens are copied into the
collector. Numeric usage, local identity hashes and timings can still be sensitive;
keep the database private. It is not encrypted and is not a public export.

## Verified Scope

Tests cover actual JSONL reads, partial lines, chunk boundaries, append-during-read,
counter discontinuities, missing fields, duplicate/no-op calls, concurrent collectors,
rollback after observation insertion, changed sources and foreign databases.
These are not a power-loss hardware test, weekly-cost validation or proof of savings.
This advanced CLI collector is separate from the Workbench observation digest;
automatic cross-source attribution and an opt-in background monitor remain open.
