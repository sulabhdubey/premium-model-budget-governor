"""MCP server for Premium Model Budget Governor.

Run with:

    python -m premium_model_budget_governor.mcp_server

The dependency is optional:

    python -m pip install "premium-model-budget-governor[mcp]"
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .capsule import build_capsule, score_capsule
from .evidence_graph import compile_graph, graph_capsule
from .policy import decide_model
from .predictor import predict_benefit
from .scanners import scan_text
from .shadow import build_shadow_packet
from .telemetry import normalize_usage
from .tournament import rank_candidates
from .workflow import plan_workflow
from .leases import budget_action
from .experiments import compare_runs
from .evidence_demand import evidence_packet
from .calibration import calibrate

try:
    from mcp.server import MCPServer
except ImportError as exc:  # pragma: no cover - only exercised without optional extra
    raise SystemExit(
        "The MCP extra is not installed. Run: python -m pip install 'premium-model-budget-governor[mcp]'"
    ) from exc


mcp = MCPServer("Premium Model Budget Governor")


@mcp.tool()
def calibrate_workflow_outcomes(packet: dict[str, Any]) -> dict[str, Any]:
    """Describe independent matched outcomes by family and split. Never auto-promotes a model."""
    return calibrate(packet)


@mcp.tool()
def compare_workflow_experiments(packet: dict[str, Any]) -> dict[str, Any]:
    """Compare supplied matched-run receipts; does not execute models or infer missing costs."""
    return compare_runs(packet)


@mcp.tool()
def select_requested_evidence(packet: dict[str, Any]) -> dict[str, Any]:
    """Select mandatory and requested content by ID/hash. Scans are heuristic, not a security boundary."""
    return evidence_packet(packet)


@mcp.tool()
def plan_model_workflow(packet: dict[str, Any]) -> dict[str, Any]:
    """Plan Astra participation and all remaining stages under a whole-task budget. Does not execute models."""
    return plan_workflow(packet)


@mcp.tool()
def manage_task_budget(packet: dict[str, Any]) -> dict[str, Any]:
    """Open, reserve, settle, cancel, or inspect local task budgets. Host must call before spending."""
    return budget_action(packet, Path.home() / ".pm-bg" / "budget.sqlite3")


@mcp.tool()
def route_model(packet: dict[str, Any]) -> dict[str, Any]:
    """Decide whether a premium model call should be allowed, blocked, or routed to Sol."""
    return decide_model(packet)


@mcp.tool()
def scan_untrusted_text(text: str) -> dict[str, Any]:
    """Scan untrusted text for prompt-injection and secret patterns before capsule use."""
    return scan_text(text)  # type: ignore[return-value]


@mcp.tool()
def score_capsule_text(capsule_text: str) -> dict[str, Any]:
    """Score a capsule and decide whether it is strong enough for premium-model spend."""
    return score_capsule(capsule_text)  # type: ignore[return-value]


@mcp.tool()
def build_capsule_from_files(
    root: str,
    goal: str,
    decision: str,
    evidence_paths: list[str],
    max_chars: int = 24000,
    output_words: int = 900,
) -> dict[str, Any]:
    """Build and score a safe premium-model capsule from explicit local files."""
    root_path = Path(root).resolve()
    capsule = build_capsule(
        root=root_path,
        goal=goal,
        decision=decision,
        evidence_paths=[Path(item) for item in evidence_paths],
        max_chars=max_chars,
        output_words=output_words,
    )
    return {"capsule": capsule, "quality": score_capsule(capsule)}


@mcp.tool()
def compile_evidence_graph(root: str, evidence_paths: list[str], query: str = "") -> dict[str, Any]:
    """Compile local files into a compact evidence graph for premium-model review."""
    return compile_graph(Path(root).resolve(), [Path(item) for item in evidence_paths], query=query)  # type: ignore[return-value]


@mcp.tool()
def compile_evidence_graph_capsule(root: str, evidence_paths: list[str], query: str = "") -> str:
    """Compile local files into an evidence graph and return a compact capsule text."""
    graph = compile_graph(Path(root).resolve(), [Path(item) for item in evidence_paths], query=query)
    return graph_capsule(graph)


@mcp.tool()
def build_shadow_review_packet(
    draft_answer: str,
    evidence_summary: str,
    contradictions: list[str] | None = None,
    remaining_limit_percent: int | None = None,
    explicit_approval: bool = False,
    sol_baseline_tokens: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Build an Astra Shadow Mode packet that asks a premium model to approve, reject, or patch."""
    return build_shadow_packet(
        draft_answer=draft_answer,
        evidence_summary=evidence_summary,
        contradictions=contradictions or [],
        remaining_limit_percent=remaining_limit_percent,
        explicit_approval=explicit_approval,
        sol_baseline_tokens=sol_baseline_tokens,
    )


@mcp.tool()
def rank_tournament_candidates(candidates: list[dict[str, Any]], top_k: int = 2) -> dict[str, Any]:
    """Rank cheap-model candidate answers before one premium-model judging turn."""
    return rank_candidates(candidates, top_k=top_k)  # type: ignore[return-value]


@mcp.tool()
def predict_astra_benefit(task_shape: dict[str, Any]) -> dict[str, Any]:
    """Predict whether an Astra/premium-model turn is likely to help for this task shape."""
    return predict_benefit(task_shape)  # type: ignore[return-value]


@mcp.tool()
def normalize_token_telemetry(packet: dict[str, Any]) -> dict[str, Any]:
    """Normalize provider usage telemetry without storing prompts."""
    return normalize_usage(packet)


if __name__ == "__main__":
    mcp.run()
