# Recorded Usage Recovery

The local workbench's Usage view provides **Recover recorded usage** for an
unknown-usage run. It does not rerun a model, refund unknown spend, or accept
token counts typed into the browser.

The App Server adapter journals validated token counters after receiving the
matching completed-turn event, before settling the budget. The journal lives in
the local budget SQLite database and contains task/call/thread/turn identifiers,
the configured model, tokens and projected credits. Prompts and answers are not
stored there. Model configuration is not provider identity attestation.

Recovery checks journal integrity, dispatch identity, the lease and model, token
validity and configured-rate agreement. It settles the same lease idempotently,
then marks the workbench row `usage_recovered`. A crash between those writes can
be retried without counting the spend twice. The original task ID cannot replay.
The answer is not recovered, and accounting recovery does not imply task quality.

If no terminal receipt was journaled, the run stays `unknown_usage` and blocks
further workbench execution. This includes older runs, missing terminal events,
and crashes before journal commit. Expiry, a stopped local process, or partial
token updates are insufficient to release reservations. No manual zero-spend
override is exposed. Provider-side reconciliation for these cases remains open.

Checksums detect accidental corruption, not a malicious local account rewriting
the database. The journal is same-user local evidence, not signed billing proof.
Token-derived credits remain estimates; weekly-limit attribution is unavailable.

Validation includes injected settlement failures, missing/conflicting/corrupted
receipts, idempotent recovery, replay rejection, API authentication and rejection
of browser-supplied token counters. Browser recovery fixtures test rendering and
interaction separately from host behavior; they are not paid model experiments.
