# Workbench Candidate: 0.4.0rc4

Status: candidate preparation. Not a stable release or completion of the product goal.

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

Prepared/review workflows have automated execution and recovery coverage, but no
new real multi-stage comparisons. Human onboarding, fresh independent-project
trials, representative quality/savings evidence and independent security review
remain release gates. No learned policy is promoted by this candidate.

## Qualification

The exact candidate wheel SHA-256 is
`6eacbd15685cd9bb0b84b441f447e8a3dd6dff17b1c805853c05513b0420784f`.
[Windows](../artifacts/onboarding/windows-rc4-regression.json) and
[Ubuntu/WSL](../artifacts/onboarding/linux-wsl-rc4-regression.json) each passed
304 installed-wheel tests with one platform-specific skip, real MCP stdio
initialize/list/call, setup checks and owned uninstall. Qualification used the
same wheel on both systems. Initial stale rc.3/dev2 documentation assertions
were corrected before these passing runs; no product behavior was relaxed.

Packaged Workbench assets are byte-identical to the dev2 browser-tested assets
at 1440/390/320 widths. These fixture checks are not human or real-call evidence.
Remote candidate CI must pass before publication. Historical dev2 tests are not
a substitute for checking this artifact. The full
[acceptance audit](ACCEPTANCE_AUDIT.md) remains authoritative for open requirements.

## Try And Report

**Volunteers wanted:** one technical and one nontechnical user for formative
onboarding trials. Open the repository's **Volunteer for an onboarding trial**
issue template using only your GitHub handle and general environment details.
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
