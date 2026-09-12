"""Context proposals and narrow opt-in overrides, never arbitrary host settings."""

from collections.abc import Mapping
from math import fsum

from .workflow import number


def context_profile_config(profile, *, model, effort):
    if not isinstance(profile, str) or profile not in {"inherit", "focused_catalog"}:
        raise ValueError("unsupported context profile")
    if profile == "inherit":
        return {}
    if model != "gpt-6-astra" or effort != "low":
        raise ValueError("focused context profile requires Astra with low reasoning")
    return {"skills.max_context_tokens": 1024}


def _label(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise ValueError(f"{name} must be a non-empty string of at most 128 characters")
    return value


def _labels(value, name):
    if not isinstance(value, list) or len(value) > 256:
        raise ValueError(f"{name} must be a bounded list")
    result = [_label(item, name) for item in value]
    if len(set(result)) != len(result):
        raise ValueError(f"{name} contains duplicates")
    return set(result)


def compare_context_choices(packet):
    """Compare caller-estimated remaining work without dispatch or admission.

    The caller must include all relevant overhead in four explicit cost stages.
    Preservation declarations and acceptance results are not independently verified.
    This function does not expand the supported context_profile_config overrides.
    """
    if not isinstance(packet, Mapping) or type(packet.get("schema_version")) is not int or packet["schema_version"] != 1:
        raise ValueError("context choices require schema_version 1")
    basis = packet.get("estimate_basis")
    if not isinstance(basis, Mapping) or basis.get("unit") != "estimated_credits":
        raise ValueError("estimate_basis requires unit estimated_credits")
    version = _label(basis.get("version"), "estimate basis version")
    dimensions = ("capabilities", "evidence", "state")
    required = packet.get("required")
    if not isinstance(required, Mapping) or set(required) != set(dimensions):
        raise ValueError("required must declare capabilities, evidence and state")
    required = {key: _labels(required[key], key) for key in dimensions}
    checks = packet.get("acceptance")
    if not isinstance(checks, list) or not 1 <= len(checks) <= 256:
        raise ValueError("acceptance requires 1-256 explicit checks")
    check_ids = set()
    complete = True
    for check in checks:
        if not isinstance(check, Mapping):
            raise ValueError("acceptance check must be an object")
        check_id = _label(check.get("id"), "check id")
        if check_id in check_ids or check.get("status") not in ("pending", "passed", "failed", "unknown"):
            raise ValueError("duplicate acceptance check or unsupported status")
        check_ids.add(check_id)
        complete = complete and check["status"] == "passed"
    baseline = packet.get("baseline")
    candidates = packet.get("candidates")
    if not isinstance(baseline, Mapping) or baseline.get("action") != "continue":
        raise ValueError("baseline must describe focused direct continuation")
    if not isinstance(candidates, list) or len(candidates) > 32:
        raise ValueError("candidates must contain at most 32 choices")
    identities = set()
    rows = []
    for option in [baseline, *candidates]:
        if not isinstance(option, Mapping):
            raise ValueError("each choice must be an object")
        identity = _label(option.get("id"), "choice id")
        if identity in identities:
            raise ValueError("choice IDs must be unique")
        identities.add(identity)
        if option.get("action") not in ("continue", "compact", "restart"):
            raise ValueError("unsupported context action")
        if type(option.get("supported")) is not bool:
            raise ValueError("supported must explicitly be boolean")
        reasons = [] if option["supported"] else ["host_operation_unsupported"]
        for field, reason in (("model", "model_changed"), ("effort", "reasoning_profile_changed"), ("snapshot", "snapshot_changed")):
            _label(option.get(field), field)
            if option[field] != baseline[field]:
                reasons.append(reason)
        missing = {}
        for key in dimensions:
            missing[key] = sorted(required[key] - _labels(option.get(key), key))
            if missing[key]:
                reasons.append("missing_" + key)
        costs = option.get("costs")
        stages = ("preparation", "execution", "verification", "recovery")
        if not isinstance(costs, Mapping) or set(costs) != set(stages):
            raise ValueError("cost stages must be preparation, execution, verification and recovery")
        intervals = []
        for stage in stages:
            interval = costs[stage]
            if interval is None:
                continue
            if not isinstance(interval, list) or len(interval) != 2:
                raise ValueError("cost interval must be [lower, upper] or null")
            lower, upper = [number(value, stage) for value in interval]
            if lower > upper:
                raise ValueError("cost interval lower exceeds upper")
            intervals.append((lower, upper))
        total = None
        if len(intervals) == len(stages):
            try:
                total = [number(fsum(values), "total cost") for values in zip(*intervals)]
            except OverflowError as exc:
                raise ValueError("total cost overflow") from exc
        else:
            reasons.append("unknown_cost")
        rows.append({"id": identity, "action": option["action"], "total": total,
                     "reasons": reasons, "missing": missing})
    reference, alternatives = rows[0], rows[1:]
    eligible = []
    for row in alternatives:
        margin = None
        if reference["reasons"]:
            row["reasons"].append("baseline_not_qualified")
        elif row["total"] is not None:
            margin = reference["total"][0] - row["total"][1]
            if margin <= 0:
                row["reasons"].append("no_separated_cost_advantage")
        row["estimated_margin"] = margin
        if not row["reasons"]:
            eligible.append(row)
    chosen = None
    if complete:
        decision = "stop_at_acceptance"
    elif reference["reasons"]:
        decision = "needs_replan"
    elif eligible:
        chosen = min(eligible, key=lambda row: (row["total"][1], row["total"][0], row["id"]))
        decision = "propose_change"
    else:
        chosen = reference
        decision = "retain_baseline"
    return {
        "schema_version": 1, "decision": decision,
        "recommended_id": chosen["id"] if chosen else None,
        "baseline": reference, "candidates": alternatives,
        "estimate_basis": {"unit": "estimated_credits", "version": version},
        "execution_authorized": False, "savings_proven": False,
        "acceptance_verified": False, "preservation_verified": False,
        "limitations": [
            "Caller estimates must use one common rate basis and include every stage, tool, retry and host overhead.",
            "Intervals are planning bounds, not statistical confidence intervals or provider caps.",
            "Capabilities, source snapshot, state fidelity and acceptance are caller assertions, not runtime proof.",
            "No host settings, model, context, reservation or execution are changed. Use normal admission before dispatch.",
        ],
    }
