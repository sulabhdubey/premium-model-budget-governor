# Host Integration: Tested Scope

## What Changed

The earlier statement that Codex had no usable hooks was too broad.
[Official hooks documentation](https://learn.chatgpt.com/docs/hooks) describes
`UserPromptSubmit` blocking. The
[App Server documentation](https://learn.chatgpt.com/docs/app-server) describes
turn-level model and reasoning selection. These do not establish a gate before
every internal generation or control over unrelated Desktop tasks.

This implementation was checked against locally generated schemas from Codex CLI
0.153.4. Experimental interfaces may change. No global configuration, hook trust,
credentials, installed integrations, or safety instructions were changed.

## Discover Without a Model Turn

```sh
pm-bg host-probe --root /absolute/project/path
```

This starts a separate stdio App Server, initializes it, reads the model catalog
and hook inventory, and shuts down. It does not send `thread/start` or `turn/start`.
The result exports only configured model names, modalities, reasoning options,
and hook counts, not credentials, hook commands, or account identity.

The live probe found Astra, Sol, Terra and Luna, with text/image support. It found
no configured hooks in the tested checkout. Discovery is not provider identity
attestation or evidence that every advertised reasoning option was executed.

## Governed Read-Only Execution

Open a budget with `pm-bg budget`, then supply an explicit execution packet:

```json
{
  "root": "/absolute/project/path",
  "prompt": "Review the supplied evidence and identify the smallest repair.",
  "model": "gpt-6-astra",
  "effort": "low",
  "task_id": "my-task",
  "call_id": "unique-call",
  "estimated_credits": 10,
  "explicit_approval": true,
  "timeout_seconds": 300,
  "images": []
}
```

```sh
pm-bg app-run --input run.json --ledger /absolute/private/budget.sqlite3
```

The client checks the model, reasoning effort and image capability against the
host catalog, reserves before starting a thread, and uses an ephemeral read-only
session with standard service tier. It preserves inherited rules and configuration.
It does not approve interactive permission requests. The read-only sandbox governs
filesystem tools; inherited connector permissions are not a universal read-only
guarantee. Use only tasks authorized for the configured integrations.
No arbitrary model is silently
substituted, and no access to global Desktop tasks is requested.

The client records the host-configured model and cumulative token counters, checks
subset consistency, and settles the lease as a token-rate estimate. Unknown usage,
unsupported cache-write accounting, interrupted turns and protocol failures retain
the reservation. Every call ID is single-use across the CLI and hook dispatch paths.

**Limits:** a reservation is not a provider output-token cap. The agent may make
multiple internal requests before a turn ends. Catalog checking does not enforce
the entire workflow plan: the controller must pass the approved stage's model,
estimate, evidence and task ID. The client does not yet execute multi-stage plans
automatically or support user-approved write workflows. No blanket cost or
capability equivalence with Desktop is claimed.

## Live Smoke Result

One authorized Astra image turn completed and reconciled: 24,471 input tokens,
zero cached input, 19 output tokens, 6.14150 projected credits. The image value
was read correctly. Units were returned in lower case, so the original strict
case-sensitive smoke assertion failed. That failure is retained; the transport,
image delivery, model configuration, and accounting succeeded. This is not a
representative task-quality benchmark, and it was not rerun to obtain a green score.

Artifacts: [app-server-pilot](../artifacts/app-server-pilot/). The script defaults
to discovery only; `--execute` authorizes a paid turn and refuses an existing receipt.

## Optional Prompt Gate

`python -m premium_model_budget_governor.prompt_gate --grant /private/grant.json`
reads one Codex hook event from stdin. A grant must contain `session_id`, `cwd`,
`prompt_sha256`, `ledger`, `task_id`, and `lease_id`. The prompt hash is SHA-256
over the exact UTF-8 prompt. The named lease must already be reserved and unexpired.
The gate binds one prompt/session/turn to that lease with an atomic shared dispatch
claim. Repeated delivery of the same event is idempotent; a new turn needs a new
grant. Invalid or missing grants produce a structured blocking response without
echoing the prompt. Grants and the ledger belong in a private writable location.

The hook does **not** know the served model from this event or settle later usage.
It is a prompt-admission gate, not model-switch enforcement. A cooperating
controller must issue grants and reconcile spend. Do not use the same lease for
`app-run` and a separately installed gate: they intentionally reject double use.

The template [hooks.prompt-gate.json](../examples/hooks.prompt-gate.json) is not
active. To test natively, use an isolated trusted project, set absolute paths,
review the exact command through Codex `/hooks`, and trust it explicitly. Test
missing-grant rejection before allowing any paid prompt. **Do not bypass trust or
install globally as a shortcut.** Untrusted/skipped hooks do not enforce anything;
host timeout/error behavior must also be tested before claiming fail-closed native
enforcement. The Python hook protocol and ledger behavior are tested; native
trusted-hook execution remains pending.

## Next Evidence Gate

Use the measured runner to preregister independent real tasks with immutable
snapshots, acceptance tests, full-workflow receipts and blinded external review.
Keep calibration and held-out projects separate. Implement automatic learned
selection only after those outcomes support it, initially in recommendation mode.
No field trial or external reviewer is fabricated by this release.
