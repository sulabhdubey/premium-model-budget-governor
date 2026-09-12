"""Versioned configured estimates, not bills or subscription-quota conversion."""
from collections.abc import Mapping
from datetime import date
from hashlib import sha256
import json
from math import isfinite
import re

from .cost import RATES, RATE_VERSION, _token


def _label(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", value):
        raise ValueError("rate contract needs bounded public identifiers")
    return value


def validate_contract(raw):
    if not isinstance(raw, Mapping):
        raise ValueError("rate_contract must be an object")
    if type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
        raise ValueError("unsupported rate contract schema")
    for key, expected in (("unit", "estimated_credits"),
                          ("input_semantics", "total_includes_cache"),
                          ("output_semantics", "total_includes_reasoning")):
        if raw.get(key) != expected:
            raise ValueError(f"unsupported rate contract {key}")
    effective = raw.get("effective_date")
    if effective is not None:
        if not isinstance(effective, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", effective):
            raise ValueError("effective_date must be an ISO date or null for unknown")
        date.fromisoformat(effective)
    rates = raw.get("per_million")
    if not isinstance(rates, Mapping):
        raise ValueError("per_million rates required")
    clean_rates = {}
    for key in ("input", "cached_input", "cache_write", "output"):
        rate = rates.get(key)
        if key == "cache_write" and rate is None:
            clean_rates[key] = None
            continue
        if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not isfinite(rate) or rate < 0:
            raise ValueError("rates must be finite non-negative numbers")
        clean_rates[key] = rate
    return {"schema_version": 1, **{k: _label(raw.get(k)) for k in
            ("version", "source_id", "model", "service_tier")},
            "effective_date": effective, "unit": "estimated_credits",
            "input_semantics": "total_includes_cache", "output_semantics": "total_includes_reasoning",
            "per_million": clean_rates}


def estimate_observed(model, usage, *, service_tier="default", contract=None):
    incoming, cached, writes, output = (_token(usage.get(k, 0), k) for k in
                                        ("input_tokens", "cached_tokens", "cache_write_tokens", "output_tokens"))
    if cached + writes > incoming:
        raise ValueError("cache subsets cannot exceed total input")
    service_tier = _label(service_tier)
    snapshot = validate_contract(contract) if contract is not None else None
    issue = None
    if snapshot is not None:
        if snapshot["model"] != model:
            issue = "unsupported_model_rate"
        elif snapshot["service_tier"] != service_tier:
            issue = "unsupported_service_tier"
    elif model not in RATES:
        issue = "unsupported_model_rate"
    elif service_tier not in {"default", "fast"} or (service_tier == "fast" and model != "gpt-6-astra"):
        issue = "unsupported_service_tier"
    else:
        multiplier = 2.5 if service_tier == "fast" else 1
        snapshot = {"schema_version": 1, "version": RATE_VERSION,
                    "source_id": "bundled-legacy-estimate", "effective_date": None,
                    "unit": "estimated_credits", "model": model, "service_tier": service_tier,
                    "input_semantics": "total_includes_cache", "output_semantics": "total_includes_reasoning",
                    "per_million": {**{k: v * multiplier for k, v in RATES[model].items()}, "cache_write": None}}
    if not issue and writes and snapshot["per_million"]["cache_write"] is None:
        issue = "unsupported_cache_write_rate"
    amount = None
    if not issue:
        rates = snapshot["per_million"]
        amount = ((incoming - cached - writes) * rates["input"] + cached * rates["cached_input"]
                  + writes * (rates["cache_write"] or 0) + output * rates["output"]) / 1_000_000
        if not isfinite(amount):
            raise ValueError("estimated cost overflow")
    digest = sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()).hexdigest() if snapshot else None
    return {"estimated_credits": amount, "cost_status": issue or "estimated",
            "cost_basis": "token_rate_estimate" if amount is not None else None,
            "rate_version": snapshot["version"] if amount is not None else None,
            "rate_snapshot": snapshot, "rate_fingerprint": digest, "service_tier": service_tier}
