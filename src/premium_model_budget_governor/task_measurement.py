"""External phase observer for runner integrations, not a model dispatcher.

The trusted callback owns admission and execution. Run this outside the measured
model process; no counter subtraction from this observer's own conversation.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from time import monotonic

from .long_work import _identity, reconcile_work


def _save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def measure_task(stages, output, invoke):
    """Observe explicitly enrolled phases; never retry or settle spend implicitly.

    invoke receives only id/role and must return one exclusive final receipt.
    Failed attempts with known usage can be represented by a returned receipt;
    the caller must still record their quality outcome in its experiment ledger.
    """
    if not isinstance(stages, list) or not 3 <= len(stages) <= 100:
        raise ValueError("enroll 3..100 phases before execution")
    manifest, identities = [], set()
    roles = {"prepare", "execute", "verify", "retry", "report"}
    for stage in stages:
        identity = _identity(stage.get("id"))
        role = stage.get("role")
        if identity in identities or role not in roles:
            raise ValueError("unique phase IDs and supported roles required")
        identities.add(identity)
        kind = stage.get("kind", "model")
        if kind not in {"model", "local"}:
            raise ValueError("phase kind must be model or local")
        manifest.append({"id": identity, "role": role, "kind": kind})
    sequence = [s["role"] for s in manifest]
    if (sequence[0] != "prepare" or "execute" not in sequence or "verify" not in sequence
            or sequence.index("verify") < sequence.index("execute")
            or ("report" in sequence and any(r != "report" for r in sequence[sequence.index("report"):]))):
        raise ValueError("prepare, execute, verify required in order; reporting must be last")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    _save(output / "manifest.json", {"schema_version": 1, "phases": manifest,
                                    "started_at": datetime.now(timezone.utc).isoformat()})
    receipts, outcomes, sources, receipt_ids = [], [], set(), set()
    started = monotonic()
    for index, stage in enumerate(manifest):
        _save(output / f"started-{index:03}.json", stage)
        begin = monotonic()
        try:
            raw = invoke(dict(stage))
            if stage["kind"] == "local":
                if raw != {"local_completed": True}:
                    raise ValueError("local phase completion not confirmed")
                row = {**stage, "status": "observed", "model_calls": 0,
                       "elapsed_seconds": monotonic() - begin}
                outcomes.append(row)
                _save(output / f"phase-{index:03}.json", row)
                continue
            checked = reconcile_work({"work_units": [stage["id"]], "receipts": [raw]})
            identity = raw["receipt_id"]
            record = checked["records"][identity]
            if record["work_unit_id"] != stage["id"]:
                raise ValueError("receipt is for another phase")
            overlap = identity in receipt_ids or record["source_id"] in sources
            receipt_ids.add(identity)
            sources.add(record["source_id"])
            # Save only the reconciler's allowlisted counters and identifiers.
            counters = record["usage"]
            reusable = {"receipt_id": identity, **record,
                        "usage": {k: counters[k] for k in ("input_tokens", "cached_tokens",
                                  "cache_write_tokens", "output_tokens", "reasoning_output_tokens")
                                  if counters[k] is not None},
                        "service_tier": counters["service_tier"],
                        "rate_contract": counters["rate_snapshot"]}
            if not overlap:
                receipts.append((stage["role"], reusable))
            status = "observed" if checked["totals"] is not None and checked["estimated_credits"] is not None and not overlap else "usage_uncertain"
            row = {**stage, "status": status, "receipt": checked,
                   "elapsed_seconds": monotonic() - begin}
        except (ValueError, TypeError, KeyError, OSError, TimeoutError):
            row = {**stage, "status": "execution_or_receipt_error", "elapsed_seconds": monotonic() - begin}
        outcomes.append(row)
        _save(output / f"phase-{index:03}.json", row)
        if row["status"] != "observed":
            break
    def aggregate(reporting):
        units = [s["id"] for s in manifest if s["kind"] == "model" and (s["role"] == "report") == reporting]
        if not units:
            return None
        return reconcile_work({"work_units": units,
                               "receipts": [r for role, r in receipts if (role == "report") == reporting]})
    all_observed = len(outcomes) == len(manifest) and all(r["status"] == "observed" for r in outcomes)
    result = {"schema_version": 1, "status": "complete_for_declared_phases" if all_observed else "incomplete",
              "task": aggregate(False), "reporting": aggregate(True), "outcomes": outcomes,
              "not_executed": manifest[len(outcomes):], "elapsed_seconds": monotonic() - started,
              "savings_proven": False, "weekly_debit": None,
              "limitations": ["Coverage is only the declared phases, not this parent chat or undeclared workers.",
                              "Receipt exclusivity and finality are supplied by the trusted execution adapter.",
                              "Observer file I/O adds wall time, not measured model tokens.",
                              "Admission, quality checks and budget settlement belong to the execution adapter."]}
    _save(output / "result.json", result)
    return result
