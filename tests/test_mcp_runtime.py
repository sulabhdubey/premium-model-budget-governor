from __future__ import annotations

import sys

import pytest


pytest.importorskip("mcp")
anyio = pytest.importorskip("anyio")


def test_mcp_server_routes_model_over_stdio():
    async def scenario():
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "premium_model_budget_governor.mcp_server"],
        )
        async with stdio_client(server) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                tool_names = {tool.name for tool in tools.tools}
                assert "route_model" in tool_names
                result = await session.call_tool(
                    "route_model",
                    {
                        "packet": {
                            "requested_model": "gpt-6-astra",
                            "remaining_limit_percent": 12,
                            "reasons": [],
                            "sol_baseline_tokens": {"input": 100000},
                            "premium_plan_tokens": {"input": 70000},
                        }
                    },
                )
                structured = getattr(result, "structured_content", None) or getattr(result, "structuredContent")
                assert structured["decision"] == "block_or_route_to_sol"
                assert structured["recommended_model"] == "gpt-5.6-sol"

    anyio.run(scenario)
