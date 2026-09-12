from __future__ import annotations

import sys
import json
from pathlib import Path

import pytest
import premium_model_budget_governor


pytest.importorskip("mcp")
anyio = pytest.importorskip("anyio")


def test_mcp_server_routes_model_over_stdio():
    async def scenario():
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "premium_model_budget_governor.mcp_server"],
            env={"PYTHONPATH": str(Path(premium_model_budget_governor.__file__).resolve().parent.parent)},
        )
        async with stdio_client(server) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                tool_names = {tool.name for tool in tools.tools}
                assert "route_model" in tool_names
                assert "plan_model_workflow" in tool_names
                assert "manage_task_budget" in tool_names
                assert "compare_workflow_experiments" in tool_names
                assert "select_requested_evidence" in tool_names
                assert "calibrate_workflow_outcomes" in tool_names
                assert "reconcile_work_observations" in tool_names
                observation = await session.call_tool("reconcile_work_observations", {
                    "packet": {"work_units": ["missing"], "receipts": []}})
                observation_data = getattr(observation, "structured_content", None) or getattr(observation, "structuredContent")
                assert observation_data["totals"] is None
                assert observation_data["missing_work_units"] == ["missing"]
                telemetry = await session.call_tool("normalize_token_telemetry", {"packet": {
                    "model": "gpt-6-astra", "usage": {"input_tokens": 100,
                    "output_tokens": 10, "cache_write_tokens": 20}}})
                telemetry_data = getattr(telemetry, "structured_content", None) or getattr(telemetry, "structuredContent")
                assert telemetry_data["estimated_credits"] is None
                assert telemetry_data["cost_status"] == "unsupported_cache_write_rate"
                calibration = await session.call_tool("calibrate_workflow_outcomes", {"packet": {"pairs": []}})
                calibration_data = getattr(calibration, "structured_content", None) or getattr(calibration, "structuredContent")
                assert calibration_data["automatic_promotion"] is False
                evidence = await session.call_tool("select_requested_evidence", {
                    "packet": {"items": [], "requested_ids": ["missing"]}})
                evidence_data = getattr(evidence, "structured_content", None) or getattr(evidence, "structuredContent")
                assert evidence_data["decision"] == "blocked"
                experiments = await session.call_tool("compare_workflow_experiments", {
                    "packet": {"baseline": "sol", "runs": [{"task_id": "t", "snapshot": "s", "rubric": "r",
                        "arm": "sol", "passed": True, "complete": False, "expected_calls": 1, "calls": []}]}})
                experiments_data = getattr(experiments, "structured_content", None) or getattr(experiments, "structuredContent")
                assert experiments_data["recommendation"] == "insufficient_evidence"
                # Explicit synthetic receipts test transport, not model performance.
                timed_rows = [{"task_id": "timed", "snapshot": "s", "rubric": "r",
                    "arm": arm, "passed": True, "complete": True, "expected_calls": 1,
                    "receipt_source": "host", "total_elapsed_seconds": seconds,
                    "calls": [{"call_id": arm, "actual_model": "gpt-6-astra", "billed_credits": 1}]}
                    for arm, seconds in [("direct", 10), ("prepared", 12)]]
                timed = await session.call_tool("compare_workflow_experiments", {
                    "packet": {"baseline": "direct", "runs": timed_rows}})
                timed_data = getattr(timed, "structured_content", None) or getattr(timed, "structuredContent")
                assert timed_data["comparisons"][0]["mean_elapsed_difference_seconds"] == 2
                assert timed_data["comparisons"][0]["cost_by_basis"]["host_billed"]["matched_pairs"] == 1
                packet = json.loads((Path(__file__).parents[1] / "examples/astra_preferred.json").read_text())
                planned = await session.call_tool("plan_model_workflow", {"packet": packet})
                plan_data = getattr(planned, "structured_content", None) or getattr(planned, "structuredContent")
                assert plan_data["astra_participation"] == "planned"
                assert plan_data["selected"]["estimated_total_credits"] <= packet["budget_credits"]
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
