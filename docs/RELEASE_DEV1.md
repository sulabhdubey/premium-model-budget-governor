# 0.5.0.dev1: Accounted Workflows (Development Prerelease)

This is an opt-in development snapshot, not a stable release or an automatic
upgrade of the existing 0.4.0rc6 beta. It includes the pending first-task guidance,
receipt explanations, bounded document intake, observation accounting and host
forecasting work, plus a reproducible external Astra pilot.

## Qualification

- Source regression: 667 passed, 2 skipped.
- Same wheel on Windows/Python 3.13.7: 667 passed, 2 skipped; isolated installation,
  MCP initialize/list/call, DOCX worker and owned uninstall passed.
- Same wheel on Ubuntu/WSL/Python 3.12.3: 667 passed, 2 skipped; same checks passed.
- Browser harness: 1440, 390 and 320 pixels, no overflow or console errors;
  execution fixtures are simulated, not paid runs. Mobile receipt inspected.
- Live Astra pilot: four calls and four fixed checks passed; 20.20115 estimated
  credits from a 60-credit ceiling including a 12-credit reserve.
- Pending-file privacy scan: 115 files inspected without skipped content.
  Runtime secret generation and deliberately empty key-header test fixtures were
  manually reviewed. Wheel configuration secrets were not embedded. Plugin scan
  inspected 16 entries without findings. Pattern scans are not malware guarantees.

The initial isolated regression attempt failed because of a test-only sibling
import. After repairing the test import, the unchanged wheel passed on both
platforms. The failed qualification records remain private, not erased.

## Read Before Using

The [matched pair](ACCOUNTED_TRIAL_2026_09_12.md) used fewer input tokens under
focused discovery but cost more in configured estimated credits because inherited
discovery received cache hits. There is no universal savings claim. The rate
contract is an estimate with an unknown effective date, not a bill.

Host forecasts have too few fresh samples for automatic promotion. Workbench
previews still use explicitly labelled provisional allowances; the calibrated CLI
is opt-in. The UI keeps preview and receipt-based estimates separate, does not
equate completion with quality and does not fabricate a matched baseline.

Independent newcomer trials and independent quality assessment remain open.
macOS and native Linux graphical onboarding have not been verified here.
Existing chats are not automatically intercepted, changed or made cheaper.

## Artifact Identity

Wheel SHA-256:
`06f5e3bba8ad600339525b25c0c52cb22dc476cc87cb7847163174b3874b1a56`

Plugin ZIP SHA-256:
`47f7faebd40fada8da49546b829d0179193a1b31731023eea0023fa8b49b9521`

Use the [installation guide](INSTALLATION.md) with the development wheel supplied
on this release. Keep an existing runtime intact; use a separate runtime directory
when testing. The plugin does not install Python dependencies or modify unrelated
Codex connections. No reset or additional paid model call is needed to install.
