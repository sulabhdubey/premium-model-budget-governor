# Approved Real Astra Workbench Smoke Test

Date: 2026-09-07. Source checkpoint: d27a319, development candidate.
Scope: one real, read-only public-fixture run through the Workbench UI.
This is not a matched savings experiment or independent human validation.

## Execution

- Owner explicitly approved one call, low reasoning, 15 estimated-credit budget.
- Browser automation used real project registration, preview, approval and Run.
  Execution was not mocked. No second arm, retry or reset was used.
- Task: study-evidence-synthesis from governor-field-starter-v1.
- Suite SHA-256: 6545072ecbf5fe8752e80f1e8100ed846f9f1f5e34b215488c5af50f1d9b916f.
- Only public study notes and task text were staged; grading criteria were excluded.
- Run ID: 475c2d7b09bd4b5380633064ff77a8ab.
- Requested and host-configured model: gpt-6-astra; effort: low; strategy: direct.
- Terminal status: completed. Host elapsed: 21.263 seconds; observed execution
  including UI polling: 22.177 seconds.

## Accounting

| Measurement | Result |
| --- | --- |
| Preview, including contingency | 12.13025 estimated credits |
| Approved task budget | 15 estimated credits |
| Host-reported input tokens | 24,076 |
| Host-reported cached tokens | 0 |
| Host-reported output tokens | 386 |
| Actual-token-derived cost | 6.5015 estimated credits |
| Lease settlement | One settled lease; zero reserved credits |
| Over budget | False |
| Attributable weekly allowance debit | Unavailable |

The configured rates reproduce the receipt: 24,076 * 250 / 1,000,000 +
386 * 1,250 / 1,000,000 = 6.5015. Rates are estimates, not provider billing.
The receipt identifies the configured host model, not independent backend attestation.
The admission budget is not a provider-enforced hard spend cap.

## Answer Evaluation

Evaluator: Codex, against the pre-existing seven criteria. Not blinded or human.
Answer length: 229 whitespace-delimited words.

| Criterion | Observed answer | Verdict |
| --- | --- | --- |
| Reject proven weekly-halving claim | Explicitly rejects the claim | Pass |
| Correct incomplete accounting | Uses 12.8, not 7.2; identifies omitted preparation and retry | Pass |
| Notice quality and scope mismatch | Notes 3/4 versus 4/4 and different reviews | Pass |
| Separate account allowance from task attribution | Explains unrelated chats and missing per-task debit | Pass |
| Limit inference from the matched review | Identifies one pair, fixed order and uncontrolled cache | Pass |
| Propose matched next experiment | Two tasks, four runs, matched evidence/settings/rubrics, counterbalanced order, all calls counted | Pass |
| Cite supplied notes, avoid invented sources, stay under 250 words | References A-B, C and D only; 229 words | Pass |

## What This Establishes

One actual Workbench-to-Astra execution completed with a useful bounded answer,
host token counters, correct estimated-cost arithmetic and settled accounting.
The small task nevertheless incurred 24,076 input tokens. Attribution between
task material and host overhead needs a separate controlled measurement; this
receipt alone cannot show how much is removable.

It does not establish Sol parity, governor savings, weekly-limit savings,
multi-stage reliability on real calls, general quality, image/tool capability
equivalence, or technical/nontechnical onboarding success. The full starter suite
remains unexecuted as a matched experiment; this single-arm subset does not change
that status. No learned policy should be promoted from this result.

Raw local execution evidence is retained in ignored build output, not published,
to avoid exposing session details or local project paths. No new release or site
deployment was performed for this smoke test.
