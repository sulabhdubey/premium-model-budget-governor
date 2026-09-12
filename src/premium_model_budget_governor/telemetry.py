"""Prompt-free telemetry normalization."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping

from .cost import _token
from .accounting import estimate_observed


def _counter_aliases(label, candidates, default=None):
    values = [_num(mapping[key]) for mapping, key in candidates if key in mapping]
    if values and any(value != values[0] for value in values):
        raise ValueError(f"conflicting {label} counters")
    return values[0] if values else default


def normalize_counters(usage: Mapping) -> dict:
    """Validate shared counter semantics without timestamps, rates or identifiers."""
    if not isinstance(usage, Mapping):
        raise ValueError("usage must be an object")
    details = {}
    for key in ("input_tokens_details", "prompt_tokens_details", "output_tokens_details", "completion_tokens_details"):
        value = usage.get(key, {})
        if not isinstance(value, Mapping):
            raise ValueError("token details must be objects")
        details[key] = value
    input_tokens = _counter_aliases("input", [(usage, "input_tokens"), (usage, "prompt_tokens")])
    output_tokens = _counter_aliases("output", [(usage, "output_tokens"), (usage, "completion_tokens")])
    if input_tokens is None or output_tokens is None:
        raise ValueError("input and output counters are required")
    cached = _counter_aliases("cached input", [(usage, "cached_tokens"), (usage, "cached_input_tokens"),
        (details["input_tokens_details"], "cached_tokens"), (details["prompt_tokens_details"], "cached_tokens")])
    writes = _counter_aliases("cache write", [(usage, "cache_write_tokens"),
        (details["input_tokens_details"], "cache_write_tokens"), (details["prompt_tokens_details"], "cache_write_tokens")])
    reasoning = _counter_aliases("reasoning", [(usage, "reasoning_output_tokens"),
        (details["output_tokens_details"], "reasoning_tokens"), (details["completion_tokens_details"], "reasoning_tokens")])
    if reasoning is not None and reasoning > output_tokens:
        raise ValueError("reasoning subset exceeds output")
    if "total_tokens" in usage and _num(usage["total_tokens"]) != input_tokens + output_tokens:
        raise ValueError("total token counter mismatch")
    assumptions = []
    if cached is None:
        assumptions.append("absent_cached_input_assumed_zero")
    if writes is None:
        assumptions.append("absent_cache_write_assumed_zero")
    cached_tokens, cache_write_tokens = cached or 0, writes or 0
    if cached_tokens + cache_write_tokens > input_tokens:
        raise ValueError("cache subsets cannot exceed total input")
    return {"input_tokens": input_tokens, "output_tokens": output_tokens,
            "cached_tokens": cached_tokens, "cache_write_tokens": cache_write_tokens,
            "reasoning_output_tokens": reasoning, "counter_assumptions": assumptions}


def normalize_usage(payload: Mapping[str, object]) -> dict[str, object]:
    usage_obj = payload.get("usage", payload)
    usage = usage_obj if isinstance(usage_obj, Mapping) else {}
    if not any(k in usage for k in ("input_tokens", "prompt_tokens")) or not any(k in usage for k in ("output_tokens", "completion_tokens")):
        return {"record_type": "token_telemetry", "usage_status": "missing",
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "model": str(payload.get("model", "unknown")), "input_tokens": None,
                "output_tokens": None, "estimated_credits": None,
                "cost_status": "missing_usage", "cost_basis": None,
                "rate_version": None, "provider_billed_cost": None,
                "raw_prompt_stored": False}
    counters = normalize_counters(usage)
    input_tokens, output_tokens, cached_tokens, cache_write_tokens = (
        counters[k] for k in ("input_tokens", "output_tokens", "cached_tokens", "cache_write_tokens"))
    reasoning, assumptions = counters["reasoning_output_tokens"], counters["counter_assumptions"]
    model = str(payload.get("model", usage.get("model", "unknown")) or "unknown")
    ordinary_input = max(0, input_tokens - cached_tokens - cache_write_tokens)
    estimate = estimate_observed(model, {"input_tokens": input_tokens, "cached_tokens": cached_tokens,
                                 "cache_write_tokens": cache_write_tokens, "output_tokens": output_tokens},
                                 service_tier=payload.get("service_tier", "default"),
                                 contract=payload.get("rate_contract"))
    credits = estimate["estimated_credits"]
    recorded_at = datetime.now(timezone.utc).isoformat()
    fingerprint = sha256(
        json.dumps(
            {
                "task_label": payload.get("task_label", ""),
                "model": model,
                "date": recorded_at[:10],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return {
        "record_type": "token_telemetry",
        "recorded_at": recorded_at,
        "task_label": payload.get("task_label"),
        "model": model,
        "input_tokens": input_tokens,
        "ordinary_input_tokens": ordinary_input,
        "cached_tokens": cached_tokens,
        "cache_write_tokens": cache_write_tokens,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": reasoning,
        "counter_assumptions": assumptions,
        "cache_hit_rate": 0.0 if input_tokens == 0 else round(cached_tokens / input_tokens, 4),
        "estimated_credits": None if credits is None else round(credits, 6),
        **{key: value for key, value in estimate.items() if key != "estimated_credits"},
        "provider_billed_cost": None,
        "raw_prompt_stored": False,
        "task_fingerprint": fingerprint,
    }


def append_usage(payload: Mapping[str, object], ledger: Path) -> dict[str, object]:
    record = normalize_usage(payload)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def _num(value: object) -> int:
    return _token(value, "token count")
