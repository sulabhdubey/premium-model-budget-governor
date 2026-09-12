"""Bounded partial observations of long, locally stored Codex sessions."""
from hashlib import sha256
import json
import os
from pathlib import Path

from .cost import _token


def counter_values(total):
    current = {"input_tokens": _token(total.get("input_tokens"), "input_tokens"),
               "cached_tokens": _token(total.get("cached_input_tokens", 0), "cached_tokens"),
               "cache_write_tokens": _token(total.get("cache_write_tokens", 0), "cache_write_tokens"),
               "output_tokens": _token(total.get("output_tokens"), "output_tokens")}
    if current["cached_tokens"] + current["cache_write_tokens"] > current["input_tokens"]:
        raise ValueError("sample cache subsets exceed input")
    if "reasoning_output_tokens" in total and _token(total["reasoning_output_tokens"], "reasoning") > current["output_tokens"]:
        raise ValueError("sample reasoning exceeds output")
    if "total_tokens" in total and _token(total["total_tokens"], "total") != current["input_tokens"] + current["output_tokens"]:
        raise ValueError("sample total counter mismatch")
    return current


def sample_rollout(path: Path, *, max_bytes=4 * 1024 * 1024) -> dict:
    if type(max_bytes) is not int or not 1 <= max_bytes <= 8 * 1024 * 1024:
        raise ValueError("sample size must be between 1 byte and 8 MiB")
    with Path(path).open("rb") as handle:
        end = os.fstat(handle.fileno()).st_size
        start = max(0, end - max_bytes)
        handle.seek(start)
        data = handle.read(end - start)
        # Append-only growth is allowed. Re-read the fixed range to catch changes.
        handle.seek(start)
        if len(data) != end - start or handle.read(end - start) != data:
            raise ValueError("sample changed during read")
    first = data.find(b"\n") + 1 if start else 0
    last = data.rfind(b"\n") + 1
    latest = None
    counter_events = 0
    counter_resets = 0
    if last > first:
        for line in data[first:last].splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise ValueError("malformed complete event in sampled range") from None
            if not isinstance(event, dict):
                raise ValueError("sample event must be an object")
            payload = event.get("payload", {})
            if not isinstance(payload, dict):
                raise ValueError("sample payload must be an object")
            if event.get("type") != "event_msg" or payload.get("type") != "token_count":
                continue
            info = payload.get("info")
            total = info.get("total_token_usage") if isinstance(info, dict) else None
            if not isinstance(total, dict):
                continue
            current = counter_values(total)
            if latest and any(current[k] < latest[k] for k in current):
                counter_resets += 1
            latest = current
            counter_events += 1
    if latest is None:
        raise ValueError("no complete token counter in sampled range")
    return {"source_kind": "codex_local_rollout_sample", "actual_model": "unknown",
            "usage": latest, "coverage": "partial_sample", "counter_events": counter_events,
            "counter_resets": counter_resets, "counter_scope": "latest_observed_segment",
            "source_digest": sha256(data).hexdigest(), "source_bytes": len(data),
            "sample_start": start, "sample_end": end, "source_size_at_open": end,
            "leading_bytes_ignored": first, "trailing_bytes_ignored": len(data) - last,
            "raw_prompts_stored": False}
