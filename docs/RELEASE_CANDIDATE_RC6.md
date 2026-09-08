# Evaluation Transparency: 0.4.0rc6

Testing prerelease, not stable acceptance or guaranteed savings.

## What Changed

- Matched comparisons now expose bilateral coverage and cost exclusion reasons.
  Task-balanced summaries prevent repeated tasks from silently dominating a mean.
- Host activity receipts count allowlisted event categories without exporting
  commands, paths or tool outputs. A completed event does not prove success.
- Opt-in context and tool/skill trial runners retain failed or uncertain outcomes,
  require approved budget admission and do not silently retry model calls.
- Updated installation links, public evidence and reproducible trial fixtures.

## Evidence

The [context pilot](CONTEXT_TRIAL_RESULTS_2026_09_08.md) has 12 calls on three
authored tasks. Both Astra profiles passed the frozen checks. Focused input tokens
were 18.1% lower; estimated credits were 26.8% lower, partly due to unequal cache
hits. These observations do not establish broad quality equivalence or billed savings.

The [four-call extension](TOOL_SKILL_TRIAL_2026_09_08.md) checks read-only disk
evidence and access to one named synthetic skill. It does not establish general
skill discovery, editing, desktop or connector parity.

Combined experiment spend: 80.19320 token-rate-estimated credits, with no pending
leases or reset. Parent-chat engineering usage is excluded. This release process
adds no paid experiment calls.

Release assets include checksums. Exact rc6 package qualification is recorded in
`artifacts/onboarding/windows-rc6-regression.json` and
`artifacts/onboarding/linux-wsl-rc6-regression.json`: each passed 359 tests with
one platform-specific skip and a real MCP round trip. Hosted CI checks additional
platforms. Earlier rc5 qualification hashes are not evidence for this wheel.

## Still Open

Owner onboarding is awaiting the owner's responses. Independent participants,
blinded grading and broader held-out capability validation remain open.
Execution is read-only; existing Codex chats are not automatically controlled.
Estimated credits are not account billing or weekly allowance measurements.
No empirical routing policy or native hook is automatically enabled.

See the [complete gate register](VALIDATION_GATES_2026_09_08.md) and
[publication privacy limitations](PUBLICATION_PRIVACY.md).
