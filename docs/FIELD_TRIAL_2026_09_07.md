# Real Workflow Pilot: 2026-09-07

**Result: keep direct Astra as the default.** Adding a cheaper preparation or
draft stage usually increased whole-workflow cost in this pilot. A separate
smaller-catalog experiment showed a useful, narrow reduction worth offering as
an opt-in, not a new universal routing rule.

## Complete Accounting

Owner-approved workers completed **39 calls across 27 workflows**, costing
**195.95418 estimated credits**: 129.77603 in the original 150-credit envelope
and 66.17815 in a separately bounded 100-credit extension after further approval.
Both envelopes ended with zero reservations, no model retry and no reset.
The earlier UI smoke cost 6.5015 separately. Parent-chat engineering, grading
and research consumption is not included in these worker totals.

These are host token counters converted using the governor's rates, not provider
bills, money or attributable weekly-limit debits. Admission is not a hard cap.
All stages count, including Sol preparation and final Astra calls.

## Five Tasks, Four Workflows

| Public task | Direct Astra | Direct Sol | Sol preparation + Astra | Sol draft + Astra review |
| --- | ---: | ---: | ---: | ---: |
| Lease-expiry repair | 7.03475 | 3.33648 | 21.04951 | 11.92912 |
| Study evidence synthesis | 6.40475 | 3.19924 | 9.38291 | 8.77242 |
| Honest launch writing | 6.20575 | 2.41400 | 8.59197 | 8.72240 |
| Release authority review | 6.08150 | 2.35230 | 8.67035 | 9.35846 |
| Visual queue priority | 6.17625 | 2.04372 | 3.74617 | 8.64730 |

Twenty matched workflows used 30 model calls. All final answers passed their
fixed task criteria in **Codex review, not blinded or independent human grading**.
The visual prepared arm benefited from substantial observed cache hits, unlike
the direct Astra arm. Its lower total is not proof of a causal workflow saving.

Inputs and rubrics were frozen in the [starter suite](../examples/field-trial/suite.json).
Its preregistration status remains a historical record; the new execution receipts
are separate. Main task order rotated, but the three arms completed under the
extension ran later. Each task/arm has only one observation. These are authored
fixtures, not representative workloads or a held-out benchmark.

Coding patches were checked in disposable LF-normalized fixtures. Initial patch
application trouble came from the harness's CRLF handling, not invalid patches.
Supplemental huge-number, Decimal and Fraction diagnostics exposed different
numeric-domain choices. Those post-hoc checks are not a preregistered model ranking.

## Two Real Projects, One Bounded Review

One additional read-only Astra call used frozen current RTA-Net and CircuitProof
excerpts. It cost 6.7205 estimated credits and passed six scoped criteria in
Codex review. RTA-Net's conclusion was to deepen the existing runtime with
checkpoint-bound fresh lease authorization, without implying that a facade alone
proves missing enforcement. CircuitProof's local gate passes did not override
`releaseAuthorized: false`.

The source hashes were unchanged afterward. No project file, runtime authority
or release authorization was modified. Private source and answer text are not
published. This is one combined scoped review, **not two independent matched
project benchmarks, a full security audit or human validation**.

## Negative Prompt Experiment

A repeated coding preparation workflow cost 9.86966. Constraining Sol's
preparation to a short evidence-only response reduced that stage's cost, but
the complete workflow rose to 12.62617 because Astra's stage cost increased.
**The prompt change was not adopted.** This single ordered pair is exploratory;
cache and stochastic behavior were not controlled.

## Smaller Catalog Experiment

Four direct Astra, low-reasoning visual calls used ABBA order: inherited catalog,
1024-token catalog, 1024-token catalog, inherited catalog. All reported zero cached
tokens and passed the fixed visual checks in Codex review.

| Profile | Input tokens, two calls | Mean estimated credits |
| --- | --- | ---: |
| Inherited | 24,143 / 24,141 | 6.191125 |
| Catalog budget 1024 | 19,822 / 19,823 | 5.118125 |

Mean input fell about **17.9%**, and mean estimated cost about **17.3%** on this
one task. Global configuration hashes were unchanged. This test used a scoped
adapter override; the packaged integration has unit/service and browser-preview
coverage, not a separate real UI execution of this profile.

The [focused catalog option](FOCUSED_CATALOG.md) therefore ships as experimental.
It may omit useful skill guidance. No reduction is assumed in admission estimates,
no model capability equivalence is promised, and no learned policy is activated.

## Recheck The Evidence

- [Combined counters and stage receipts](../artifacts/field-trial-2026-09-07/combined-results.json)
- [Matched experiment input](../artifacts/field-trial-2026-09-07/combined-experiment-input.json)
- [Comparison output](../artifacts/field-trial-2026-09-07/combined-comparison.json)
- [Public fixture answers](../artifacts/field-trial-2026-09-07/combined-public-fixture-answers.json)
- [Supplemental coding checks](../artifacts/field-trial-2026-09-07/coding-diagnostics.json)

The original `results.json` is the preserved partial 150-credit-envelope
checkpoint, not the final combined result. Independent calibration, held-out
tasks, human onboarding, broader tools and write/Desktop-only support remain open.
