# Adoption Guide

This guide is for teams or individual builders who want to reduce premium model
overhead while preserving substantive Astra capabilities.

## Start With One Workflow

Pick one recurring workflow:

- release readiness review
- architecture review
- security patch review
- large refactor planning
- production incident analysis

Do not start by routing every agent call. Start where premium spend is visible
and the decision boundary is clear.

## Define A Project Profile

Record requested model, acceptance criteria, source snapshot, required tools,
images and reasoning, permissions and whole-workflow budget. Use supported
[planner and profile contracts](ASTRA_PREFERRED.md), not invented configuration
keys. Example numbers are not measurement or spending approval.

Compare equally focused direct Astra first. Capsules, cheaper helpers and shadow
review are optional candidates, not prerequisites for access to Astra. Do not
silently replace its model, reasoning or capabilities to fit an estimate.

## Measure Before And After

For each run, record prompt-free telemetry only:

- task type
- selected route
- estimated or actual token counts
- blocked reasons
- preparation, retry, verification and recovery overhead
- whether required capabilities and task quality were preserved
- final outcome

Avoid storing raw prompts, private files, logs, credentials, or customer data.

## Evaluate Optional Workflows

Use direct Astra as the reference. A helper-plus-review workflow is worth adopting
only when its total measured cost and quality justify it. Keep negative, canceled
and missing outcomes; do not rerun an unknown-spend call to get a cleaner result.
Freeze criteria and use the [independent validation protocol](INDEPENDENT_VALIDATION.md).
Developer fixtures and screenshots do not establish independent quality or usability.

## Success Criteria

The governor is working when:

- required work is completed with tested capabilities and quality preserved
- any cost improvement includes all preparation and verification overhead
- users understand measured, estimated, unavailable and actually governed data
- blocked premium calls are understandable
- team members can reproduce the decision
- quality regressions are visible in evals or review notes

Fewer calls, smaller prompts or later Astra involvement are not success criteria
by themselves. Retain direct Astra when an optimization adds cost or loses quality.
Connected MCP tools do not automatically control every existing chat.

## Failure Signals

Revisit the policy when:

- users bypass it manually
- every capsule scores as high quality
- no premium call is ever allowed
- the same task type repeatedly benefits from premium review but stays blocked
- actual token telemetry diverges sharply from estimates

