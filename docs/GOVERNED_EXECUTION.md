# Governed Codex CLI Execution

`pm-bg run` is an explicit execution command. Unlike `plan`, it consumes model
usage. It requires an installed, authenticated Codex CLI and an already opened
task budget. It does not redeem resets or change the active desktop model.

First use the workflow planner with a measured context floor. Then open a budget:

```json
{"action":"open","task_id":"review-001","budget_credits":15,"reserve_credits":2}
```

```sh
pm-bg budget --input open.json --ledger budget.sqlite3
pm-bg run --input run.json --ledger budget.sqlite3
```

Example `run.json` (choose your actual repository root and estimate):

```json
{
  "task_id": "review-001",
  "call_id": "astra-review-001",
  "root": ".",
  "model": "gpt-6-astra",
  "effort": "low",
  "estimated_credits": 10,
  "timeout_seconds": 300,
  "prompt": "Review the specified change and its tests. Report concrete risks. Do not edit files."
}
```

The adapter invokes `codex exec` with inherited configuration and rules, a
read-only sandbox, ephemeral session storage, and JSON event output. It uses
argument arrays and stdin, not shell-built commands. It does not use bypass
flags, disable security policy, or rewrite global configuration. Interactive
approval escalations are denied rather than silently granted.

It reserves before dispatch, claims each call ID only once, records complete
usage, and reconciles projected spend. A failed, timed-out, or unrecognized
response retains its reservation until reconciled. Timeouts terminate the local
process group/tree; remote billing may already have occurred. Reservations cannot
guarantee an in-flight provider call stays inside its estimate.

Responses are returned to the caller. The ledger stores no raw prompts. Benchmark
scripts explicitly save public fixture answers, but that is not a default policy
for private work. CLI JSON gives token usage; requested model and configured
standard pricing remain assumptions unless separately attested by the host.

Read-only execution preserves reasoning and permitted inspection, not every
desktop tool or write capability. Use the original governed workflow for edits,
visual interactions, or integrations that the CLI host does not expose. The
package does not claim automatic model switching inside an existing chat.
