# Privacy-Corrected Candidate: 0.4.0rc5

Testing prerelease, not stable acceptance or guaranteed Astra-quality savings.

## Changes

- Bounded publication checks inspect UTF-8 text, decoded JSON and ZIP/wheel
  metadata. Reports contain opaque positions and input hashes, not private terms,
  names or source excerpts. Uninspected content needs manual review.
- Current public reporting and outreach avoid private-project identities and
  internal findings. Independent task and human onboarding protocols remain
  protocols, not fabricated outcomes.
- Owner-approved backed-up history cleanup updated two branches and eight tags.
  The old PR was closed. The affected rc.4 wheel and checksum manifest were
  withdrawn, not silently replaced under their old version or hashes.
- GitHub-managed cached/PR references and external clones may retain copies.
  Reclone after the history change; do not merge old history back into the repo.

## Evidence And Remaining Gates

The sanitized source passed 334 tests with one platform-specific skip before
candidate packaging. Exact-wheel qualification is recorded in
`artifacts/onboarding/windows-rc5-regression.json` and
`artifacts/onboarding/linux-wsl-rc5-regression.json`; release assets have checksums.
Do not substitute an older package's results for this version.
Both recorded installed-wheel runs passed 334 tests with one skip, real MCP stdio
and owned uninstall. Wheel SHA-256:
`a5bec67c17517f0a6d344a202530309e56e55c476809086d462724dad7880064`.
The retained scanner finding and manual source-code review are in
[the publication audit](../artifacts/publication/rc5-audit.json).

The earlier 39-call pilot remains scoped development evidence. Direct Astra stays
default. The focused catalog's approximately 17% estimated-cost reduction came
from one four-call visual experiment; it may omit useful skill guidance. No
broader quality equivalence, weekly-limit saving or automatic policy promotion
is claimed. Execution remains read-only; existing chats are not automatically
controlled and inherited connector permissions are not revoked.

Technical/nontechnical volunteer sessions, independent held-out task evaluation,
broader capability decisions and independent security review remain open. The
candidate can be tested without declaring the full pinned goal complete.

See [publication privacy](PUBLICATION_PRIVACY.md),
[independent validation](INDEPENDENT_VALIDATION.md),
[onboarding](ONBOARDING_TRIAL.md), and [acceptance](ACCEPTANCE_AUDIT.md).
Creator outreach asks for independent testing, not promised coverage or endorsement.
