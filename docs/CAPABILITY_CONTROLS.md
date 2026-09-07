# Capability-Preserving Controls

The objective is more useful Astra work per budget, not a mandatory cheap-model
handoff. Use one focused Astra call when planning, delegation, and judging would
repeat more host context than they save. Keep genuine source evidence and images.

## Project and Host Profiles

Add these optional fields to a `pm-bg plan` packet:

```json
{
  "project_profile": {
    "allowed_models": ["gpt-6-astra", "gpt-5.6-sol"],
    "required_roles": ["review"]
  },
  "host_profiles": {
    "local_cli": {
      "models": ["gpt-6-astra", "gpt-5.6-sol"],
      "capabilities": ["text", "image", "read_only_tools"]
    }
  }
}
```

A stage names `host: "local_cli"` and, for example,
`required_capabilities: ["image"]`. Missing host/model/capability blocks that
candidate. A project restriction cannot silently force a Sol fallback in
Astra-preferred mode. Profiles are caller assertions, not runtime discovery or
proof the provider enabled a capability. Keep them current for your installation.

Optional stage `tokens_upper` uses the same format as `tokens`; `max_attempts`
defaults to 1. The planner budgets the upper-cost estimate for every attempt,
plus sunk work and contingency. It reports the single-attempt base estimate
separately. These are planning allowances, not provider-side generation caps.

## Images and Evidence

`pm-bg run` accepts `images: ["/absolute/path/chart.png"]` and forwards actual
files with Codex's image option. PNG/JPEG/WebP paths are explicit and limited to
20 MB each. No image-to-text replacement is performed. The host decodes the file;
extension/size checks are not malware scanning. Do not attach private images
without authorization. Existing user configuration, rules, and read-only sandbox
remain in force. This adapter does not implement audio, video, or write-mode work.

Evidence packets can declare a `snapshot`; each item must match it. Optional
timezone-aware ISO `valid_until` rejects expired items. Positive ordered
`line_start`/`line_end` values preserve source locations. Snapshot labels and
hashes verify supplied consistency, not live repository truth or source authority.
Refresh evidence from the actual checkout before approval.

## Reservations

`reserve` accepts `ttl_seconds` (1 to 86400, default 900). An expired lease cannot
start a new adapter dispatch. It still holds its money because a crashed host
may already have spent it. Reconcile usage, or cancel only after confirming the
call never ran. Ambiguous I/O failures likewise retain funds. Execution cannot
physically prevent an external host or manually selected desktop model spending.

## Calibration

```sh
pm-bg calibrate --input matched-pairs.json
```

Input is an object with `pairs`. Each pair includes `task_id`, `family`, `snapshot`,
`rubric`, distinct `candidate` and `baseline`, `split` (`calibration` or `holdout`),
`cost_basis` (`host_billed` or `token_rate_estimate`), `matched: true`,
`complete: true`, boolean `candidate_pass` and `baseline_pass`, and nonnegative
`candidate_credits` and `baseline_credits`. Each row represents an already-matched
pair of complete workflows, not a single model call.

The report groups outcomes by family, pair, split, and cost basis. It reports
observed wins, quality regressions, average costs, and descriptive Wilson intervals.
Repeated task IDs for the same comparison and train/holdout task leakage are
rejected. Aggregate repeated trials first; keep unique tasks for validation.
Twenty observations are a reporting threshold, not proof of adequate power.
**No automatic promotion occurs.** Matching and provenance remain caller assertions;
this is a conservative analysis tool, not a trained routing model.

The same function is available over MCP as `calibrate_workflow_outcomes`.

## Local Dashboard

```sh
pm-bg dashboard --ledger /path/to/budget.sqlite3 --output /path/to/governor.html
```

Open the resulting HTML directly. It is a read-only snapshot with budgets,
reservations, receipt basis, and expiry warnings. It starts no server, loads no
remote resources, and omits task IDs, call IDs, and prompts. Model labels and
numeric budgets remain visible: review before sharing. It cannot derive weekly
capacity, saved credits, blocked attempts, or account bills from this ledger.

## Limits That Remain

No verified per-generation desktop gate, provider-attested served-model identity,
or reliable subscription-credit conversion is exposed by this integration.
Codex does expose prompt hooks and App Server model selection; see the newer
[integration tests and limitations](HOST_INTEGRATION.md). No universal
Sol-price Astra guarantee is possible. Broad enterprise task quality, subjective
visual quality, and statistically defensible learned routing still require
independent representative evaluation. The bounded pilot is not that evidence.
