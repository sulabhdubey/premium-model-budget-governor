# MCP Server

Premium Model Budget Governor includes an optional Model Context Protocol server
so compatible agents can call the governor as tools instead of shelling out to
the CLI.

## Install

```bash
python -m pip install "premium-model-budget-governor[mcp]"
```

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

## Tools

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

## Safety Boundary

The MCP server is local-first and does not call model providers. It reads files
only when explicit file paths are supplied by the caller. It does not persist raw
prompts through the telemetry tool.
