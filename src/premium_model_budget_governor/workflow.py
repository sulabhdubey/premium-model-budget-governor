"""Plan complete workflows; estimates never imply model execution or quality proof."""

from __future__ import annotations

from math import isfinite
from typing import Mapping

from .cost import TokenPlan, _token, model_credits

ASTRA = "gpt-6-astra"


def number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return float(value)


def flag(packet: Mapping, name: str) -> bool:
    value = packet.get(name, False)
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


def string_list(value: object, name: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(v, str) or not v for v in value):
        raise ValueError(f"{name} must be a list of non-empty strings")
    return value


def plan_workflow(packet: Mapping[str, object]) -> dict[str, object]:
    """Select caller-estimated complete workflows under an explicit task budget.

    All stage tokens describe remaining work. spent_credits covers completed work.
    quality_score is a caller assessment, not a calibrated model prediction.
    """
    mode = packet.get("mode", "astra_preferred")
    if mode not in {"astra_preferred", "adaptive", "economy"}:
        raise ValueError("unsupported mode")
    budget = number(packet.get("budget_credits"), "budget_credits")
    spent = number(packet.get("spent_credits", 0), "spent_credits")
    reserve = number(packet.get("reserve_credits", 0), "reserve_credits")
    input_floor = _token(packet.get("minimum_input_tokens_per_call", 0), "minimum_input_tokens_per_call")
    require_calibration = flag(packet, "require_context_calibration")
    hosts = packet.get("host_profiles", {})
    project = packet.get("project_profile", {})
    if not isinstance(hosts, Mapping) or not isinstance(project, Mapping):
        raise ValueError("host_profiles and project_profile must be objects")
    allowed_models = string_list(project.get("allowed_models", []), "allowed_models")
    required_roles = string_list(project.get("required_roles", []), "required_roles")
    minimum = number(packet.get("minimum_quality_score", 0), "minimum_quality_score")
    if minimum > 1:
        raise ValueError("minimum_quality_score must be at most 1")
    remaining = packet.get("remaining_limit_percent")
    if remaining is not None and number(remaining, "remaining_limit_percent") > 100:
        raise ValueError("remaining_limit_percent must be at most 100")
    approved = flag(packet, "explicit_approval")
    candidates = packet.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidates must be a non-empty list of complete workflows")
    evaluated = []
    ids = set()
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise ValueError("each candidate must be an object")
        name = candidate.get("id")
        if not isinstance(name, str) or not name or name in ids:
            raise ValueError("candidate IDs must be non-empty and unique")
        ids.add(name)
        quality = number(candidate.get("quality_score"), "quality_score")
        if quality > 1:
            raise ValueError("quality_score must be at most 1")
        stages = candidate.get("stages")
        if not isinstance(stages, list) or not stages:
            raise ValueError("each workflow requires stages")
        total = spent + reserve
        minimum_cost = total
        premium_cost = 0.0
        premium_stages = []
        stage_rows = []
        blocks = []
        for stage in stages:
            if not isinstance(stage, Mapping) or not isinstance(stage.get("tokens"), Mapping):
                raise ValueError("each stage requires a token estimate")
            role = stage.get("role")
            if role not in {"prepare", "plan", "investigate", "implement", "review", "verify", "handoff", "retry"}:
                raise ValueError("unsupported stage role")
            model = stage.get("model")
            capabilities = string_list(stage.get("required_capabilities", []), "required_capabilities")
            host = hosts.get(stage.get("host")) if isinstance(stage.get("host"), str) else None
            if capabilities or stage.get("host") is not None:
                if not isinstance(host, Mapping):
                    blocks.append("missing_host_profile")
                else:
                    available = string_list(host.get("capabilities", []), "host capabilities")
                    models = string_list(host.get("models", []), "host models")
                    if set(capabilities) - set(available):
                        blocks.append("required_capability_unavailable")
                    if model not in models:
                        blocks.append("model_unavailable_on_host")
            if allowed_models and model not in allowed_models:
                blocks.append("project_model_restriction")
            tokens = TokenPlan.from_mapping(stage["tokens"])
            # A host can inject far more context than the user's task prompt contains.
            effective = TokenPlan(max(tokens.input, input_floor - tokens.cached_input),
                                  tokens.cached_input, tokens.output)
            cost = model_credits(model, effective, fast_mode=flag(stage, "fast_mode"))
            minimum_cost += cost
            upper = stage.get("tokens_upper", stage["tokens"])
            if not isinstance(upper, Mapping):
                raise ValueError("tokens_upper must be an object")
            upper_tokens = TokenPlan.from_mapping(upper)
            upper_effective = TokenPlan(max(upper_tokens.input, input_floor - upper_tokens.cached_input), upper_tokens.cached_input, upper_tokens.output)
            upper_cost = model_credits(model, upper_effective, fast_mode=flag(stage, "fast_mode"))
            if upper_cost < cost:
                raise ValueError("upper token estimate cannot cost less than base estimate")
            attempts = _token(stage.get("max_attempts", 1), "max_attempts")
            if not 1 <= attempts <= 16:
                raise ValueError("max_attempts must be 1-16")
            cost = upper_cost * attempts
            if cost <= 0:
                raise ValueError("stage token estimate must have positive cost")
            total += cost
            if model == ASTRA:
                premium_cost += cost
                premium_stages.append(role)
                if not flag(stage, "evidence_ready"):
                    blocks.append("prepare_evidence_before_astra")
                if remaining is None and not approved:
                    blocks.append("unknown_capacity_requires_approval")
                elif remaining is not None and remaining <= 15 and not approved:
                    blocks.append("emergency_requires_approval")
            stage_rows.append({"model": model, "role": role, "estimated_credits": round(cost, 6),
                               "host": stage.get("host"), "required_capabilities": capabilities,
                               "max_attempts": attempts,
                               "effective_input_tokens": effective.input + effective.cached_input})
        if set(required_roles) - {s["role"] for s in stage_rows}:
            blocks.append("project_required_role_missing")
        if require_calibration and input_floor == 0:
            blocks.append("measure_host_context_before_execution")
        if not flag(candidate, "complete_workflow"):
            blocks.append("incomplete_workflow_estimate")
        if quality < minimum:
            blocks.append("below_quality_target")
        if total > budget + 1e-9:
            blocks.append("whole_workflow_over_budget")
        evaluated.append({"id": name, "quality_score": quality,
                          "estimated_min_credits": round(minimum_cost, 6),
                          "estimated_total_credits": round(total, 6),
                          "astra_credits": round(premium_cost, 6), "astra_roles": premium_stages,
                          "stages": stage_rows, "blocks": sorted(set(blocks))})
    feasible = [c for c in evaluated if not c["blocks"]]
    if mode == "astra_preferred":
        feasible = [c for c in feasible if c["astra_roles"]]
    if mode == "economy":
        feasible.sort(key=lambda c: (c["estimated_total_credits"], -c["quality_score"], c["id"]))
    else:
        feasible.sort(key=lambda c: (-c["quality_score"], c["estimated_total_credits"], c["id"]))
    selected = feasible[0] if feasible else None
    return {"schema_version": 2, "mode": mode,
            "decision": "planned" if selected else "needs_replan",
            "astra_participation": ("planned" if selected["astra_roles"] else "not_requested") if selected else "unmet",
            "selected": selected, "candidates": evaluated,
            "budget_credits": budget, "spent_credits": spent, "reserve_credits": reserve,
            "minimum_input_tokens_per_call": input_floor,
            "warnings": ["Host context is uncalibrated; task text alone may understate input."] if input_floor == 0 else [],
            "execution_status": "not_executed", "host_action": "execute_via_host_or_handoff",
            "estimate_basis": "caller_supplied; quality and weekly burn are not guaranteed"}
