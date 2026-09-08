# Astra Context Pilot: Measured Results

Twelve real Astra calls completed: three bounded tasks, two settings, two repeats.
All 12 passed the frozen exact-JSON checks. No failed or canceled run was removed.
There were six matched pairs and no missing cost receipts. Both arms used Astra
with low reasoning and the standard service tier; no Sol worker was used.

## Results

| Metric | Inherited catalog | Focused catalog |
| --- | ---: | ---: |
| Completed calls / fixed checks passed | 6 / 6 | 6 / 6 |
| Total input tokens, including cached subset | 143,218 | 117,292 |
| Total observed cached-input subset | 6,656 | 19,200 |
| Token-rate estimated credits | 34.70690 | 25.40300 |
| Counterfactual credits with cached subsets priced as uncached | 36.20450 | 29.72300 |

Focused discovery used **18.1% fewer input tokens**, exactly 4,321 fewer per
matched pair. Observed token-rate estimated cost was **26.8% lower overall**.
It was cheaper in five of six pairs, not every pair. One cached inherited call
cost 4.48240 versus 4.89975 for its uncached focused counterpart.

**The 26.8% figure includes unequal cache hits.** Repricing the same observed
tokens as uncached yields a 17.9% lower projection; this is a sensitivity
calculation, not another observed experiment or a promised saving. Cache state
was recorded, not controlled. No cache-warming calls were added to this trial.
Prior unrelated activity can affect cache availability.

Total experiment spend: **60.10990 estimated credits**, under the 120-credit
admission ceiling, with zero pending reserved credits at completion. No reset
was used. This excludes parent-chat engineering and analysis usage. No claim
about actual billed credits or account-wide weekly allowance follows from it.

## Reproducible Evidence

- [Frozen fixture and oracle](../examples/context-trial.json)
- [Protocol and dry-run instructions](CONTEXT_TRIAL.md)
- [All 12 prompt-free counter rows](../artifacts/context-trial-2026-09-08/counters.csv)
- Manifest SHA-256: `c3e6c8b7f394030e09c49cdba760eeecb39fdb088acd7e8c352a524ec20dfcc4`
- Image SHA-256: `db10649d09116b96ce1a6a021348d78306ffe68d9e23cafcbd3b190190d3cce1`

The private manifest includes the fixture, complete enrollment and image hashes.
Full answers and the SQLite ledger remain private. Counter rows are a reviewed
export of host-reported usage, not cryptographic provider attestation. Software
tests recompute their costs and validate enrollment against the fixture.

## What This Does Not Prove

This is an authored synthetic pilot, not independent blinded evaluation. One
visual fixture was reused. Tasks required no tools and short structured answers;
they do not establish equivalent coding, skill discovery, long-horizon research,
security-review quality, or high-reasoning Astra performance. Six matched pairs
are not enough to establish general capability noninferiority.

Keep focused discovery experimental and opt-in. The next validation should test
tasks that actually require skill discovery and tools, plus independent grading.
Do not remove safety instructions or required evidence to reproduce lower input.
No automatic routing-policy change, release, or public deployment was made.
