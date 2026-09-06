# Codex Setup

Premium Model Budget Governor can be used in Codex in two complementary ways:

- as a local Python CLI
- as a local MCP server plus Codex skill bundle

## Local CLI

Install from the repo:

```bash
python -m pip install -e ".[dev,mcp]"
```

Run a routing decision:

```bash
python -m premium_model_budget_governor.cli plan --input examples/astra_preferred.json
```

## MCP Server

Copy the shape from `examples/mcp-config.codex.json` into your Codex MCP
configuration:

```json
{
  "mcpServers": {
    "premium-model-budget-governor": {
      "command": "python",
      "args": ["-m", "premium_model_budget_governor.mcp_server"]
    }
  }
}
```

Then restart the MCP host so it can load the server.

## Codex Plugin Bundle

The repo includes a ready plugin layout:

```text
plugin/
  .codex-plugin/plugin.json
  .mcp.json
  skills/premium-model-budget-governor/SKILL.md
```

Use this bundle when you want the policy instructions and local tools to travel
together.

## Recommended Codex Prompt

```text
Use Premium Model Budget Governor's whole-workflow planner in Astra-preferred
mode. Compare direct Astra, Astra-led execution, investigation, and review.
Preserve required capabilities and count preparation, host context, workers,
retries, and verification. If no Astra route fits, explain needs_replan rather
than silently switching to Sol. Reserve each authorized call and reconcile usage.
```

## Expected Behavior

- Direct Astra is eligible without a prior Sol failure.
- Hybrid work must justify its full overhead, not just its premium leg.
- Unavailable capabilities and incomplete budgets require replanning.
- Unknown or emergency capacity requires explicit Astra approval.
- Unknown spend stays reserved; a recommendation is not model execution.

## Current Limitation

Codex must call the policy for enforcement. This package cannot physically stop
manual model selection in a host UI that does not expose a pre-model hook.
