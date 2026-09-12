# First Task And Receipt Clarity (Development)

These changes are local development work, not proof that the published beta has them.

## First Task

The optional First task disclosure provides a synthetic arithmetic review prompt.
It never chooses a project, changes reasoning, adds approval or dispatches a model.
Existing task text and attachments are preserved. The selected project remains
within the runner's read-access boundary even when the prompt asks for no tools.
Use a non-sensitive folder. Initial installation still requires a terminal.

## Usage States

- No records: an explanation replaces the empty table and offers Return to Work.
- Preview only: explicitly distinguishes an estimate from consumed usage.
- Preview-only server: explains that execution is disabled in that session.
- Recorded tasks: table and View receipt action are available.
- Unknown usage: explicit recovery remains separate from running a new task.
- Loading failure: explains that refreshing reads receipts; rerunning is not recovery.

This view does not automatically measure other Codex chats. An empty view is not
zero account consumption. The observation journal remains a separate opt-in import.

## What Changed?

New terminal receipts retain configured reasoning, workflow, context profile and
attached document/image counts. They contain no new filenames or source contents.
Counts mean attachment, not verified model attention, comprehension or complete
coverage. Read-only tools may inspect other permitted evidence.

The UI distinguishes requested model from host-configured model, and neither is
independent provider attestation. Missing historical fields remain unknown; in
particular, a missing profile is no longer labelled Inherited by assumption.

Savings remain unknown because no matched baseline is linked to this receipt.
The separate experiment view is still required for comparisons. A preview/result
gap does not establish savings. Historical receipt inspection does not rerun a
task or reconstruct an answer that was not retained in history.

## Validation Boundary

Automated checks cover preservation, direct/multistage persistence, legacy missing
fields, empty states, sample non-approval and receipt navigation. They do not prove
new-user comprehension, independent task quality or cost reduction.
