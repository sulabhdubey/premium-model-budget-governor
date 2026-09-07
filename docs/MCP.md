# MCP Server

Whole-workflow tools: `plan_model_workflow` plans substantive Astra participation
under a complete task budget; `manage_task_budget` atomically reserves and
reconciles caller-reported spend. See [Astra-preferred workflows](ASTRA_PREFERRED.md).

Premium Model Budget Governor includes an optional Model Context Protocol server
so compatible agents can call the governor as tools instead of shelling out to
the CLI.

## Install

Download the installer and wheel from the
[rc.5 prerelease](https://github.com/sulabhdubey/premium-model-budget-governor/releases/tag/v0.4.0-rc.5).
From their folder, use the isolated installation with optional dependencies:

```sh
python install_governor.py install --wheel premium_model_budget_governor-0.4.0rc5-py3-none-any.whl --mcp
python install_governor.py install --wheel premium_model_budget_governor-0.4.0rc5-py3-none-any.whl --mcp --yes
```

Do not reuse an existing runtime folder; see [installation and recovery](INSTALLATION.md).
This guide uses a verified GitHub asset, not an assumed package-index release.

For local development:

```bash
python -m pip install -e ".[dev,mcp]"
```

## Run

```bash
python -m premium_model_budget_governor.mcp_server
```

The server uses stdio transport. Add this to an MCP-compatible client
configuration:

```json
{
  "mcpServers": {
    "premium-model-budget-governor": {
      "command": "python",
      "args": [
        "-m",
        "premium_model_budget_governor.mcp_server"
      ]
    }
  }
}
```

The same example is available at `examples/mcp-config.codex.json`.
Replace `python` in the configuration with the absolute path of the runtime that
contains the optional MCP package: on Windows this is normally
`C:\\Users\\YOUR_USER\\.pm-bg\\runtime\\Scripts\\python.exe`, and on Linux/macOS
`/home/YOUR_USER/.pm-bg/runtime/bin/python` (use your actual home path).
Bare `python` may resolve to a different installation. JSON is an illustrative
MCP client format; apply your client's supported configuration format explicitly.

## Tools

- `plan_model_workflow`: default whole-task Astra-preferred planner with capability and budget checks.
- `manage_task_budget`: reserve, settle, and reconcile local task leases.
- `select_requested_evidence`: integrity, snapshot, expiry, and bounded evidence selection.
- `compare_workflow_experiments`: compare complete matched receipts without inferring absent costs.
- `calibrate_workflow_outcomes`: descriptive family/split outcomes; no automatic promotion.
- `route_model`: allow, block, or route a requested premium model call.
- `scan_untrusted_text`: scan webpage/tool/output text before it enters a
  capsule.
- `score_capsule_text`: score whether a capsule is strong enough to justify
  premium spend.
- `build_capsule_from_files`: create and score a capsule from explicit files.
- `compile_evidence_graph`: create a compact evidence graph.
- `compile_evidence_graph_capsule`: return an evidence graph summary as text.
- `build_shadow_review_packet`: build an approve/reject/patch premium review
  packet.
- `rank_tournament_candidates`: rank cheap-model candidates before a premium
  judging turn.
- `predict_astra_benefit`: estimate whether premium review is likely to help.
- `normalize_token_telemetry`: normalize usage data without storing prompts.

## Runtime Test

The repository includes `tests/test_mcp_runtime.py`. When the optional MCP extra
is installed, this test launches the server over stdio, lists the available
tools, and exercises routing, whole-workflow planning, evidence selection,
experiment comparison, and calibration over a real MCP client session.

```bash
python -m pip install -e ".[dev,mcp]"
python -m pytest tests/test_mcp_runtime.py
```

## Safety Boundary

The MCP server is local-first and does not call model providers. It reads files
only when explicit file paths are supplied by the caller. It does not persist raw
prompts through the telemetry tool.
## Measured Experiments And Evidence

`compare_workflow_experiments(packet)` compares identical task, snapshot, rubric,
and repeat IDs. Supply complete host receipts; missing usage is not zero. Actual
token counts produce rate-based estimates, not subscription consumption proof.

`select_requested_evidence(packet)` accepts explicit items with id, source, text,
sha256 and optional required=true, plus requested_ids and max_chars. Mandatory
and requested content must fit intact; otherwise it returns needs_replan. Hashes
check consistency, not truth. Pattern scans are not a security boundary.

`plan_model_workflow` also supports minimum_input_tokens_per_call and
require_context_calibration. `manage_task_budget` defaults new budgets to
max_pending_leases=1. Reconcile before another call. Higher concurrency must be
explicitly configured when opening a budget. Token-derived settlements carry
cost_basis=token_rate_estimate. These controls require a cooperating host.

Codex rollout import is deliberately CLI-only: `pm-bg receipt --input <path>
--call-id <opaque-id>`. It reads one explicitly chosen local single-model log and
returns counters, not conversation content. See [Experiments](EXPERIMENTS.md).
