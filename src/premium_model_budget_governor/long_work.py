"""Conservative reconciliation of explicitly supplied, prompt-free work receipts.

This does not collect host events, attest source identity or settle budget leases.
Unsupported counter semantics remain unresolved instead of becoming free usage.
"""
from collections.abc import Mapping
import re

from .telemetry import normalize_usage
from .cost import _token


def _identity(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value):
        raise ValueError("use opaque identifiers of 1-128 letters, digits, underscores or hyphens")
    return value


def reconcile_work(payload: Mapping) -> dict:
    raw = payload.get("receipts")
    enrolled = payload.get("work_units", [])
    if not isinstance(raw, list) or len(raw) > 10000:
        raise ValueError("receipts must be a list with at most 10000 entries")
    if not isinstance(enrolled, list) or len(enrolled) > 10000:
        raise ValueError("work_units must be a bounded list")
    expected = {_identity(value) for value in enrolled}
    records, sources, issues = {}, set(), set()
    duplicates = 0
    for item in raw:
        if not isinstance(item, Mapping):
            raise ValueError("receipt must be an object")
        identity = _identity(item.get("receipt_id"))
        record = {key: _identity(item.get(key)) for key in
                  ("work_unit_id", "source_id", "counter_kind", "scope")}
        model = item.get("model")
        if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", model):
            raise ValueError("model must be a bounded model identifier")
        record["model"] = model
        provenance = item.get("provenance")
        if provenance is not None:
            if (not isinstance(provenance, Mapping) or provenance.get("source_kind") not in {"codex_local_rollout", "codex_local_rollout_sample"}
                    or not isinstance(provenance.get("source_digest"), str)
                    or not re.fullmatch(r"[a-f0-9]{64}", provenance["source_digest"])):
                raise ValueError("unsupported receipt provenance")
            record["provenance"] = {"source_kind": provenance["source_kind"],
                                    "source_digest": provenance["source_digest"],
                                    "source_bytes": _token(provenance.get("source_bytes"), "source_bytes"),
                                    "trust": "local_log_not_provider_attestation"}
            if provenance["source_kind"] == "codex_local_rollout_sample":
                if model != "unknown" or record["counter_kind"] != "cumulative" or record["scope"] != "unknown":
                    raise ValueError("partial samples cannot establish model or final scope")
                for key in ("sample_start", "sample_end", "source_size_at_open", "leading_bytes_ignored", "trailing_bytes_ignored", "counter_resets", "counter_events"):
                    record["provenance"][key] = _token(provenance.get(key), key)
                p = record["provenance"]
                if p["sample_end"] - p["sample_start"] != p["source_bytes"] or p["sample_end"] > p["source_size_at_open"]:
                    raise ValueError("invalid sample interval")
                if provenance.get("counter_scope") != "latest_observed_segment":
                    raise ValueError("unsupported sample counter scope")
                if (p["leading_bytes_ignored"] + p["trailing_bytes_ignored"] > p["source_bytes"]
                        or p["counter_events"] < 1 or p["counter_resets"] >= p["counter_events"]):
                    raise ValueError("invalid sample coverage counters")
                p["counter_scope"] = "latest_observed_segment"
        normalized = normalize_usage({"model": record["model"], "usage": item.get("usage", {}),
                                      "service_tier": item.get("service_tier", "default"),
                                      "rate_contract": item.get("rate_contract")})
        # Exclude timestamps and all caller-supplied free text from the report.
        record["usage"] = {key: normalized.get(key) for key in
                           ("input_tokens", "cached_tokens", "cache_write_tokens",
                            "output_tokens", "estimated_credits", "rate_version", "cost_status",
                            "rate_snapshot", "rate_fingerprint", "service_tier",
                            "reasoning_output_tokens", "counter_assumptions")}
        if identity in records:
            if records[identity] != record:
                raise ValueError("conflicting receipt identity")
            duplicates += 1
            continue
        if record["source_id"] in sources:
            issues.add("overlapping_source")
        sources.add(record["source_id"])
        records[identity] = record

    subtotal = dict.fromkeys(("input_tokens", "cached_tokens", "cache_write_tokens", "output_tokens"), 0)
    observed_units = set()
    costs = []
    for record in records.values():
        if record["counter_kind"] != "final" or record["scope"] != "exclusive":
            issues.add("unsupported_counter_semantics")
            continue
        usage = record["usage"]
        if usage["input_tokens"] is None or usage["output_tokens"] is None:
            issues.add("missing_usage")
            continue
        observed_units.add(record["work_unit_id"])
        for key in subtotal:
            subtotal[key] += usage[key]
        costs.append(usage["estimated_credits"])
    missing = sorted(expected - observed_units)
    unexpected = sorted({record["work_unit_id"] for record in records.values()} - expected) if "work_units" in payload else []
    if missing:
        issues.add("missing_work_units")
    if unexpected:
        issues.add("unexpected_work_units")
    if not records:
        issues.add("no_receipts")
    complete = not issues
    # Even the subtotal is unsafe when distinct receipt IDs cover the same source.
    observed = None if "overlapping_source" in issues or not observed_units else subtotal
    return {"schema_version": 1, "record_type": "long_work_observation",
            "coverage": "complete_for_supplied_receipts" if complete else "incomplete",
            "enrollment_supplied": "work_units" in payload,
            "receipt_count": len(records), "duplicate_count": duplicates,
            "missing_work_units": missing, "unexpected_work_units": unexpected, "issues": sorted(issues),
            "observed_subtotal": observed, "totals": subtotal if complete else None,
            "estimated_credits": round(sum(costs), 6) if complete and all(c is not None for c in costs) else None,
            "cost_basis": "token_rate_estimate", "provider_billed_cost": None,
            "source_authentication": "caller_supplied_not_attested",
            "savings_claim": False, "records": records}
