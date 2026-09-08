# Bounded Tool And Skill Validation

Four real Astra calls completed using low reasoning, standard tier and read-only
filesystem execution. One disk-evidence task and one local-skill task ran under
both inherited and focused discovery, reversing order between the tasks.

All four passed the frozen checks: completed response, exact JSON answer, at
least one host-reported completed command event, and unchanged fixture hashes.
The local-skill answers included a marker available in the skill body but absent
from the user task prompt. This supports skill-content access in these two runs,
not a claim about the exact discovery path or all skills in a large catalog.

| Task | Inherited estimated credits | Focused estimated credits |
| --- | ---: | ---: |
| Read local evidence | 5.15050 | 2.67090 |
| Apply local skill | 6.69560 | 5.56630 |
| Total | 11.84610 | 8.23720 |

All four calls had cache hits, with unequal cached subsets. The observed cost
difference is cache-confounded and must not be marketed as a general saving.
Focused calls also took about 1.98 seconds longer on average in this tiny trial.
Both costs and elapsed times include the runner's tool-bearing turn; parent-chat
engineering, fixture preparation, grading, and human review are outside them.

This extension cost **20.08330 estimated credits**. Combined with the earlier
12-call pilot, the shared ledger settled **80.19320 of 120 estimated credits**,
with zero pending reservations and no reset. Unused allowance is not spent merely
to exhaust the budget. Estimated credits are not currency or weekly-limit units.

## Evidence And Reproduction

- [Fixture, order, files and answer keys](../examples/tool-skill-trial/manifest.json)
- [All four counter rows](../artifacts/tool-skill-trial-2026-09-08/counters.csv)
- [Runner](../scripts/run_tool_skill_trial.py), dry-run unless `--execute` is set
- Private manifest SHA-256: `d2c8f636e0f53a4b6d433cc0a25af2c82da5ea2d40bbf5b2b4ecbefa60c400b3`

Pass an explicitly approved existing ledger, its task ID, and a new private output
directory. The runner does not open or increase budgets. It checks admission
before each call, preserves not-executed enrollment, refuses output overwrite,
and stops on a failed gate or uncertain execution. The per-call estimate is 16
credits, not a provider cap. Full answers, project folders and ledgers stay private.

Activity counters expose allowlisted categories only, never commands, outputs,
paths, or arbitrary event labels. Duplicated item IDs are counted once; events
without IDs cannot be deduplicated. A completed command event can represent a
failed command, so it is not by itself proof of tool success. The separate exact
answer and unchanged-source checks provide the bounded outcome evidence here.

## Gates Still Open

No independent reviewer participated. These are authored fixtures, one observation
per task/profile, and only read-only local command use. Unprompted skill selection,
large-catalog retrieval, repository edits, external connectors, desktop interaction,
high reasoning levels, and broad task-quality equivalence are not established.
No policy was activated and focused discovery remains experimental and opt-in.
