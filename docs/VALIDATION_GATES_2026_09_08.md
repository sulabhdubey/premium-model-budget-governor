# Validation Gate Register

## rc6 Publication Addendum

The new rc6 wheel passed **359 tests with one platform-specific skip** in both
isolated Windows/Python 3.13.7 and Ubuntu/WSL/Python 3.12.3 environments, including
real MCP initialize/list/call and owned uninstall. Reports:
[Windows](../artifacts/onboarding/windows-rc6-regression.json) and
[Linux](../artifacts/onboarding/linux-wsl-rc6-regression.json).
Both identify SHA-256
`5525cd5a76602cb534fdac41f7b7e91a0c20f4e9163d8fcdb87c0daca521ae99`.

The updated public tour passed keyboard navigation, playback, reduced motion,
offscreen stop, planner and overflow checks at widths 1440, 390 and 320, with no
page errors. These are automated checks, not human onboarding results.

The privacy review covers changed public text, trial counter exports and release
packages. Retained pattern findings were reviewed: placeholder home paths in the
MCP guide, generic `root/home/repository` wording in installation instructions,
and the source expression `token = secrets.token_urlsafe(32)`. None is an actual
personal path or embedded secret. No scan can establish exhaustive confidentiality.
Private project databases, migration receipts and participant information are not
part of this release. See [rc6 notes](RELEASE_CANDIDATE_RC6.md).

The following earlier local-build record is retained for provenance. Its rc5
wheel hash must not be substituted for the rc6 hash above. All human and broader
capability gates listed below remain open.

Status: local validation work completed for the bounded automated scope below.
**Not all product acceptance gates are closed.** No stable release, deployment,
universal savings claim, or automatic policy activation is authorized by this report.

## Completed In This Validation Session

| Gate | Evidence | Scope |
| --- | --- | --- |
| Astra versus Astra context | 12/12 frozen checks passed | Three authored short-answer tasks, two repeats per profile |
| Read-only tool use | Both profiles passed disk-evidence checks | Correct answer, completed command event, unchanged files |
| Local skill content access | Both profiles returned skill-only marker | One named synthetic skill, not general discovery parity |
| Windows isolated wheel | 357 passed, 1 skipped; MCP round trip passed | Python 3.13.7, installation through uninstall |
| Ubuntu/WSL isolated wheel | 357 passed, 1 skipped; MCP round trip passed | Python 3.12.3, same exact wheel |
| Rendered Workbench QA | 1440, 390, 320 pixels passed | Live previews; execution disabled; error/receipt/dialog states simulated |
| Screenshot inspection | Desktop and narrow mobile inspected | No observed overlap; nonblank chart and responsive layout |

Final source regression after adding admission/error-path tests: **359 passed,
1 skipped**. The Windows skip is symlink creation unavailable on this host.
The installed-wheel runs above used the preceding 357-test snapshot. No package
module changed afterward; the additional tests target the standalone trial runner.
Publication-pattern checks on the six new trial/report files returned no findings;
pattern checks are not exhaustive privacy or security assurance.

Wheel SHA-256:
`48c6a91ca4eb27f8257c153ee401f415d3fbc387facb786d8fe3ed89e68abcb1`.
This is an unpublished local build carrying the existing 0.4.0rc5 version string,
not proof that the currently published rc5 contains these changes. Identify it by
hash; assign a new release version before any future publication.

Windows and Linux have platform-specific skips. Neither qualification spends
model credits. The MCP check starts a real stdio client, initializes the server,
lists tools and calls the calibration tool; it is not merely an import check.
Both environments verify imports come from the installed wheel, not the checkout.

The [tool/skill report](TOOL_SKILL_TRIAL_2026_09_08.md) and
[context report](CONTEXT_TRIAL_RESULTS_2026_09_08.md) retain all outcomes and caveats.
Combined 16-call spend is 80.19320 estimated credits within the approved 120-credit
envelope, zero pending leases, no reset. Parent-chat usage is outside that total.

## Open Or Not Established

| Gate | Status | Required evidence |
| --- | --- | --- |
| Owner onboarding | Invited; awaiting task responses | Owner's own explanations, observed steps and assistance log |
| Native folder choice | Not exercised by a person in this session | Actual selection/cancel on the supported desktop |
| Independent technical/nontechnical onboarding | No participants yet | Separate consenting participants, not one owner counted twice |
| Independent blinded quality grading | No independent reviewer yet | Locked grades before model/profile/cost reveal |
| Broad held-out capability preservation | Not established | Unseen tasks requiring substantive tools, skills and human judgment |
| Reviewed empirical routing activation | Remains gated | Required independent calibration and holdout evidence plus approval |
| Global pre-model enforcement / exact weekly attribution | Platform limits remain | Reliable host support; do not fabricate hooks or telemetry |
| Write and desktop-only workflows | Unsupported scope | Separately approved design, threat model and validation |
| macOS installation/native UI | Not tested in this session | A macOS host and participant |

Native hook crash/timeout behavior was not rerun here; earlier documented
fail-open limitations remain. No hooks were enabled or bypassed. Existing chats
are not automatically governed by these tests. Focused discovery remains opt-in.

The owner may help find defects through a formative trial, but prior involvement
prevents labeling that trial independent. Participant answers and identity details
stay private unless separately approved for sanitized publication.
