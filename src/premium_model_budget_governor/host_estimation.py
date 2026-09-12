"""Descriptive host forecasts from explicitly comparable, prompt-free receipts."""
from datetime import datetime, timezone
from statistics import median
from collections.abc import Mapping
from copy import deepcopy


PROFILE_KEYS = ("host", "model", "reasoning", "context", "config_fingerprint",
                "task_family", "scope")


def estimate_host(packet, *, now=None):
    now = now or datetime.now(timezone.utc)
    if not isinstance(packet, Mapping) or not isinstance(packet.get("profile"), Mapping):
        raise ValueError("profile object required")
    profile = packet["profile"]
    if any(not isinstance(profile.get(k), str) or not profile[k].strip() or len(profile[k]) > 128 for k in PROFILE_KEYS):
        raise ValueError("complete host comparison profile required")
    days = packet.get("max_age_days", 7)
    if type(days) is not int or not 1 <= days <= 90:
        raise ValueError("max_age_days must be 1..90")
    rows = packet.get("receipts", [])
    if not isinstance(rows, list) or len(rows) > 10000:
        raise ValueError("receipts must be a bounded list")
    seen, accepted, stale = set(), [], 0
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("profile"), Mapping):
            raise ValueError("receipt and profile objects required")
        identity = row.get("id")
        if not isinstance(identity, str) or not identity or len(identity) > 128 or identity in seen:
            raise ValueError("missing or duplicate receipt identity")
        seen.add(identity)
        values = [row.get(k) for k in ("input_tokens", "cached_tokens", "output_tokens")]
        if row.get("cache_write_tokens", 0) != 0:
            raise ValueError("separate cache-write accounting is not supported by this profile")
        if any(type(v) is not int or v < 0 for v in values) or values[1] > values[0]:
            raise ValueError("complete non-negative token counters required")
        if not isinstance(row.get("recorded_at"), str):
            raise ValueError("receipt timestamp required")
        stamp = datetime.fromisoformat(row["recorded_at"])
        if stamp.tzinfo is None:
            raise ValueError("receipt timestamp must include timezone")
        comparable = all(row.get("profile", {}).get(k) == profile[k] for k in PROFILE_KEYS)
        age = (now - stamp).total_seconds()
        if not comparable or row.get("complete") is not True or age < 0:
            continue
        if age > days * 86400:
            stale += 1
            continue
        accepted.append(dict(input_tokens=values[0], cached_tokens=values[1],
                             uncached_tokens=values[0] - values[1], output_tokens=values[2]))
    result = {"schema_version": 1, "status": "missing", "samples": len(accepted),
              "excluded": len(rows) - len(accepted), "stale_samples": stale,
              "observed_ranges": None, "median_tokens": None, "admission_tokens": None,
              "estimated_credits": None, "savings_proven": False,
              "limitations": ["Observed min/max is not a statistical prediction interval.",
                              "Admission uses observed maxima plus 25 percent, not a hard cap.",
                              "No cache hits are assumed for admission; future work may exceed this range.",
                              "Caller-supplied profile and completeness require source verification."]}
    if not accepted:
        result["status"] = "stale" if stale else "missing"
        return result
    ranges = {k: [min(r[k] for r in accepted), max(r[k] for r in accepted)] for k in accepted[0]}
    result.update(status="empirical" if len(accepted) >= 5 else "insufficient_support",
                  observed_ranges=ranges,
                  median_tokens={k: median(r[k] for r in accepted) for k in ranges},
                  admission_tokens={"input_tokens": (ranges["input_tokens"][1] * 5 + 3) // 4,
                                    "cached_tokens": 0,
                                    "output_tokens": (ranges["output_tokens"][1] * 5 + 3) // 4})
    return result


def plan_calibrated(packet, *, now=None):
    """Apply a single matched per-call profile to every declared workflow stage."""
    from .workflow import plan_workflow

    forecast = estimate_host(packet["calibration"], now=now)
    profile = packet["calibration"]["profile"]
    if profile["scope"] != "per_call":
        raise ValueError("workflow stages require per_call calibration, not task totals")
    workflow = deepcopy(packet["workflow"])
    upper = forecast["admission_tokens"]
    for candidate in workflow.get("candidates", []):
        for stage in candidate.get("stages", []):
            if stage.get("calibration_profile") != profile or stage.get("model") != profile["model"]:
                raise ValueError("each stage must explicitly match the calibrated host profile")
            if upper is not None:
                for field in ("tokens", "tokens_upper"):
                    tokens = stage.setdefault(field, deepcopy(stage["tokens"]))
                    # Existing planner input is uncached plus cached, unlike total-input receipts.
                    incoming = tokens.get("input", 0) + tokens.get("cached_input", 0)
                    tokens.update(input=max(incoming, upper["input_tokens"]), cached_input=0,
                                  output=max(tokens.get("output", 0), upper["output_tokens"]))
    workflow["require_context_calibration"] = True
    workflow["minimum_input_tokens_per_call"] = upper["input_tokens"] if upper else 0
    result = plan_workflow(workflow)
    if forecast["status"] != "empirical":
        for candidate in result["candidates"]:
            candidate["blocks"].append("host_calibration_" + forecast["status"])
        result.update(decision="needs_replan", selected=None, astra_participation="unmet")
    result["host_forecast"] = forecast
    return result
