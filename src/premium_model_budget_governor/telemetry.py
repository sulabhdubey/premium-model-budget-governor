"""Prompt-free telemetry normalization."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping

from .cost import RATES, model_credits


def normalize_usage(payload: Mapping[str, object]) -> dict[str, object]:
    usage_obj = payload.get("usage", payload)
    usage = usage_obj if isinstance(usage_obj, Mapping) else {}
    details_obj = usage.get("input_tokens_details", {})
    details = details_obj if isinstance(details_obj, Mapping) else {}
    input_tokens = _num(usage.get("input_tokens", usage.get("prompt_tokens", 0)))
    output_tokens = _num(usage.get("output_tokens", usage.get("completion_tokens", 0)))
    cached_tokens = _num(details.get("cached_tokens", usage.get("cached_tokens", 0)))
    cache_write_tokens = _num(details.get("cache_write_tokens", usage.get("cache_write_tokens", 0)))
    model = str(payload.get("model", usage.get("model", "unknown")) or "unknown")
    ordinary_input = max(0, input_tokens - cached_tokens - cache_write_tokens)
    token_plan = {"input": ordinary_input + cache_write_tokens, "cached_input": cached_tokens, "output": output_tokens}
    credits = model_credits(model, token_plan) if model in RATES else None
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
        "cache_hit_rate": 0.0 if input_tokens == 0 else round(cached_tokens / input_tokens, 4),
        "estimated_credits": None if credits is None else round(credits, 6),
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
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        return 0
    return int(value)
