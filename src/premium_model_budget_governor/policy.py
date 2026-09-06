"""Deterministic routing policy."""

from __future__ import annotations

from typing import Mapping

from .cost import estimate_parity
from .workflow import flag, number


ASTRA_REASONS = {
    "critical_security",
    "frontier_architecture",
    "large_cross_system_recovery",
    "high_consequence_strategy",
    "unsolved_after_sol",
    "final_release_review",
}
LOW_LEVERAGE_TASKS = {
    "repo_exploration",
    "broad_repo_exploration",
    "bulk_file_reading",
    "mechanical_edits",
    "test_log_iteration",
    "formatting",
}


def decide_model(payload: Mapping[str, object]) -> dict[str, object]:
    requested_model = str(payload.get("requested_model", "") or "")
    remaining = payload.get("remaining_limit_percent")
    reasons = {str(item) for item in payload.get("reasons", [])} if isinstance(payload.get("reasons", []), list) else set()
    explicit_approval = flag(payload, "explicit_approval")
    fast_mode = flag(payload, "fast_mode")
    broad_context = bool(payload.get("broad_context", False))
    sensitive = bool(payload.get("suspected_sensitive_data", False))
    injection = bool(payload.get("prompt_injection_detected", False))
    capsule_quality = payload.get("capsule_quality_score")
    if remaining is not None and number(remaining, "remaining_limit_percent") > 100:
        raise ValueError("remaining_limit_percent must be at most 100")
    if capsule_quality is not None and number(capsule_quality, "capsule_quality_score") > 100:
        raise ValueError("capsule_quality_score must be at most 100")
    remaining_int = int(remaining) if remaining is not None else None
    quality = int(capsule_quality) if capsule_quality is not None else None
    task_kind = str(payload.get("task_kind", "") or "").strip().lower()

    blocks: list[str] = []
    asks: list[str] = []
    if requested_model != "gpt-6-astra":
        return {
            "decision": "allow_non_premium",
            "recommended_model": requested_model or "gpt-5.6-sol",
            "blocks": blocks,
            "approval_reasons": asks,
            "scope": "single_call; use plan to reserve Astra participation",
        }
    if broad_context:
        blocks.append("compress_context_before_astra")
    if quality is None:
        blocks.append("missing_capsule_quality")
    if not isinstance(payload.get("sol_baseline_tokens"), Mapping) or not isinstance(payload.get("premium_plan_tokens"), Mapping):
        blocks.append("missing_cost_estimates")
    if task_kind in LOW_LEVERAGE_TASKS and not reasons.intersection({"unsolved_after_sol", "critical_security"}):
        blocks.append("low_leverage_task_shape_route_to_sol")
    if sensitive:
        blocks.append("sanitize_sensitive_data")
    if injection:
        blocks.append("sanitize_prompt_injection")
    if quality is not None and quality < 70:
        blocks.append("capsule_quality_too_low")
    if fast_mode:
        asks.append("fast_mode_requires_explicit_approval")
    if remaining_int is None:
        asks.append("unknown_budget_assume_conserve")
    elif remaining_int <= 15 and not explicit_approval:
        asks.append("emergency_budget_requires_approval")
    elif remaining_int <= 30 and not reasons.intersection(ASTRA_REASONS) and not explicit_approval:
        asks.append("conserve_budget_requires_high_value_reason")

    parity = None
    if isinstance(payload.get("sol_baseline_tokens"), Mapping) and isinstance(payload.get("premium_plan_tokens"), Mapping):
        parity = estimate_parity(
            sol_baseline=payload["sol_baseline_tokens"],  # type: ignore[arg-type]
            premium_plan=payload["premium_plan_tokens"],  # type: ignore[arg-type]
            fast_mode=fast_mode,
        )
        if not parity["sol_parity_met"]:
            blocks.append("premium_plan_exceeds_sol_parity")

    if blocks:
        decision = "block_or_route_to_sol"
        recommended = "gpt-5.6-sol"
    elif asks and not explicit_approval:
        decision = "ask_explicit_approval"
        recommended = "gpt-5.6-sol"
    else:
        decision = "allow_premium_capsule"
        recommended = "gpt-6-astra"
    return {
        "decision": decision,
        "recommended_model": recommended,
        "blocks": blocks,
        "approval_reasons": asks,
        "parity": parity,
    }
