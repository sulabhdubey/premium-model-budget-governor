# Security Policy

## Supported Versions

This project is pre-1.0. Security fixes are applied to the latest public release
and the default branch.

## Reporting a Vulnerability

Please do not open public issues for suspected vulnerabilities involving secret
handling, prompt-injection bypasses, unsafe filesystem behavior, or policy
evasion.

Report privately to the maintainer through GitHub private vulnerability
reporting when enabled, or by opening a minimal issue that says you have a
security report without including exploit details.

## Scope

In scope:

- prompt-injection scanner bypasses with clear impact
- accidental prompt or secret persistence
- path traversal in capsule or evidence graph commands
- unsafe default behavior that could transmit private data
- misleading policy decisions that allow premium model use despite a hard block

Out of scope:

- requests for guaranteed detection of all malicious content
- provider billing disputes
- attacks requiring modification of local source code before execution

## Data Handling

Ledgers are intended to be prompt-free. Do not attach private ledgers, prompts,
API keys, local paths, or proprietary project content to public reports.
