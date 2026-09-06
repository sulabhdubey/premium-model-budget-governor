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
python -m premium_model_budget_governor.cli route --input examples/route_packet.json --plain
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
Use Premium Model Budget Governor first. Decide whether this task should run
with a cheap model, Sol-first hybrid, or a premium capsule review. Do not spend
a premium model turn unless the governor permits it and the evidence capsule is
bounded, scanned, and under the Sol-parity ceiling.
```

## Expected Behavior

Most tasks should not start on the premium model:

- broad repo reading: cheaper model
- routine edits: cheaper model
- repeated test failures: cheaper model until evidence narrows
- final architecture/security dispute: premium capsule may be justified
- high budget emergency: explicit approval required

## Current Limitation

Codex must call the policy for enforcement. This package cannot physically stop
manual model selection in a host UI that does not expose a pre-model hook.

