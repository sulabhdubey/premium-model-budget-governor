# Workbench Candidate: 0.4.0rc4

Status: testing candidate. Not a stable release or completion of the product goal.

## Changes Since rc.3

- Explicit direct, Sol preparation plus Astra, and Sol draft plus Astra review
  workflows in the local Workbench. Direct remains the default; additional stages
  require whole-workflow admission and can cost more.
- Stage receipts retain partial known cost, unknown usage and remaining reservations.
  Missing counters are not replaced with zero; failed or interrupted stages are
  not automatically replayed. Terminal-journal recovery remains available.
- Optional native folder selection with separate registration consent, cancellation,
  and a manual-path fallback. Actual native dialog selection remains unverified.
- Current installation instructions pin released assets rather than assuming a
  public package-index distribution. Optional MCP is tested as a real stdio client.
- One actual approved read-only Astra UI run is now recorded separately from
  mocked browser tests and historical CLI benchmarks.
- Completed five-family/four-arm real comparison, one bounded combined project
  review, and exploratory prompt/catalog experiments. Negative outcomes included.
- Opt-in focused skill catalog for direct Astra at low reasoning, with immutable
  preview binding, scope gates and explicit guidance-loss warning. Default unchanged.

## Evidence And Limits

The real smoke test reported 24,076 input and 386 output tokens, 21.263 seconds,
and 6.5015 estimated credits, with one settled lease and no retry. Seven predefined
answer checks passed in Codex review, not independent human review.
[Report](../artifacts/approved-astra-ui-smoke-2026-09-07.md).

Credits are token-rate estimates, not provider bills or attributable weekly debits.
Budget admission is not a hard in-flight provider cap. Configured model identity
is not independent serving-model attestation. A single arm cannot prove savings.

Execution remains read-only; inherited connector permissions are not revoked.
Desktop-only tools and editing are not silently substituted. Secret/injection
pattern checks do not guarantee detection of malicious content. The loopback
service is not suitable for public hosting; never share its private launch link.

The [expanded pilot](FIELD_TRIAL_2026_09_07.md) contains 39 actual worker calls,
27 workflows and 195.95418 estimated credits, including every stage. Extra
handoffs usually cost more; a four-call, one-task catalog probe reduced mean
estimated cost about 17%. Cache, small samples and Codex grading limit conclusions.
Human onboarding, independent matched project trials, representative savings
evidence and independent security review remain open. No learned policy is promoted.

## Qualification

The exact candidate wheel SHA-256 is
`658065b66e8b7ed3937c7ae6d5b6b661acb962c2a7d4264c2fb16ce09df58428`.
[Windows](../artifacts/onboarding/windows-rc4-regression.json) and
[Ubuntu/WSL](../artifacts/onboarding/linux-wsl-rc4-regression.json) each passed
319 installed-wheel tests with one platform-specific skip, real MCP stdio
initialize/list/call, setup checks and owned uninstall. Qualification used the
same wheel on both systems. Initial stale rc.3/dev2 documentation assertions
were corrected before these passing runs; no product behavior was relaxed.
The earlier rc.4 wheel beginning `6eacbd15` predates the focused profile and is
superseded by this artifact, not published under the same tag.

Updated Workbench preview/approval flows passed browser QA at 1440/390/320 widths,
including focused-profile scope and older-server rejection. These fixture checks
are not human or real-call execution evidence. Remote candidate CI must pass
before publication. Historical dev2 tests are not a substitute for this artifact. The full
[acceptance audit](ACCEPTANCE_AUDIT.md) remains authoritative for open requirements.

## Try And Report

**Volunteers wanted:** one technical and one nontechnical user for formative
onboarding trials. [Open a volunteer issue](https://github.com/sulabhdubey/premium-model-budget-governor/issues/new?title=Volunteer%20for%20an%20onboarding%20trial)
using only your GitHub handle, technical/nontechnical preference and general
environment details. The candidate also includes an onboarding issue template;
it may not appear in the default-branch selector until merged.
No purchase, private repository or account screenshot is requested. Model
execution and recording require separate consent; offline setup/preview trials
are welcome and will be labeled accordingly. No sessions have yet been completed.

Use [installation](INSTALLATION.md), [MCP setup](MCP.md), and the
[Workbench guide](WORKBENCH.md). Report setup friction, unclear approval or receipt
states, and unsupported task capabilities through the repository issue templates.
Review the sanitized setup report before attaching it. Do not publish credentials,
private prompts, account screenshots, launch tokens, local paths or SQLite ledgers.

Idea, research guidance and product management: Sulabh Dubey. Engineering: Codex
under his direction. Apache-2.0; see LICENSE and NOTICE. Independent project,
not an OpenAI product or endorsement.
