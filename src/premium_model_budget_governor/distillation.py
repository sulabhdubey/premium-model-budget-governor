"""Local doctrine inventory with optional source-bound applicability filtering."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping

from .scanners import scan_text


MAX_BYTES = 4 * 1024 * 1024
MAX_LINE_BYTES = 64 * 1024
FIELDS = {"project", "task_shape", "decision", "principle", "risk_pattern",
          "verification_contract", "model", "outcome"}


def _text(value, name, limit=256):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{name} must be a non-empty bounded string")
    return value


def _context(value, *, validity=False):
    if not isinstance(value, Mapping):
        raise ValueError("doctrine context must be an object")
    keys = {"scope_id", "source_snapshot", "policy_version", "permissions"}
    if validity:
        keys.add("valid_until")
    if set(value) != keys:
        raise ValueError("unsupported or missing context binding fields")
    result = {key: _text(value.get(key), key) for key in ("scope_id", "source_snapshot", "policy_version")}
    permissions = value.get("permissions")
    if not isinstance(permissions, list) or len(permissions) > 64:
        raise ValueError("permissions must be a bounded list")
    permissions = [_text(item, "permission") for item in permissions]
    if len(permissions) != len(set(permissions)):
        raise ValueError("duplicate permission")
    result["permissions"] = sorted(permissions)
    return result


def _expiry(value):
    try:
        expiry = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            raise ValueError("timezone required")
        return expiry
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("valid_until must be an ISO timestamp with timezone") from exc


def _record(payload):
    if not isinstance(payload, Mapping):
        raise ValueError("doctrine must be an object")
    record = {key: _text(payload[key], key, 4000) for key in FIELDS if key in payload}
    if "validity" in payload:
        validity = _context(payload["validity"], validity=True)
        validity["valid_until"] = _expiry(payload["validity"].get("valid_until")).isoformat()
        record["validity"] = validity
    if not scan_text(json.dumps(record, sort_keys=True))["safe_to_include"]:
        raise ValueError("unsafe doctrine content; scan findings require local review")
    return record


def append_doctrine(payload: Mapping[str, object], ledger: Path) -> dict[str, object]:
    record = _record(payload)
    record["recorded_at"] = datetime.now(timezone.utc).isoformat()
    record["raw_prompt_field_stored"] = False
    encoded = json.dumps(record, sort_keys=True) + "\n"
    if len(encoded.encode("utf-8")) > MAX_LINE_BYTES:
        raise ValueError("doctrine record exceeds line limit")
    if ledger.exists() and ledger.stat().st_size + len(encoded.encode("utf-8")) > MAX_BYTES:
        raise ValueError("doctrine ledger exceeds bounded inventory limit")
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(encoded)
    return record


def synthesize_doctrine(ledger: Path, *, current_context=None) -> dict[str, object]:
    current = _context(current_context) if current_context is not None else None
    records = []
    malformed = 0
    if ledger.exists():
        with ledger.open("rb") as handle:
            data = handle.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("doctrine ledger exceeds bounded inventory limit")
        for line in data.splitlines():
            try:
                if len(line) > MAX_LINE_BYTES:
                    raise ValueError("doctrine line exceeds limit")
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("record must be an object")
            except (ValueError, UnicodeError, RecursionError):
                malformed += 1
                continue
            records.append(row)
    selected = []
    excluded = Counter()
    now = datetime.now(timezone.utc)
    for row in records:
        try:
            normalized = _record(row)
        except ValueError:
            excluded["invalid_or_unsafe_record"] += 1
            continue
        if current is not None:
            validity = normalized.get("validity")
            if validity is None:
                excluded["unbound_record"] += 1
                continue
            if normalized.get("outcome") != "passed":
                excluded["outcome_not_passed"] += 1
                continue
            if _context(validity, validity=True) != current:
                excluded["context_changed"] += 1
                continue
            if _expiry(validity["valid_until"]) <= now:
                excluded["expired"] += 1
                continue
        selected.append(normalized)
    principles = Counter(row["principle"] for row in selected if row.get("principle"))
    risks = Counter(row["risk_pattern"] for row in selected if row.get("risk_pattern"))
    return {
        "records": len(records),
        "malformed_records": malformed,
        "mode": "applicability_filtered" if current is not None else "inventory_only",
        "eligible_records": len(selected) if current is not None else None,
        "excluded_reasons": dict(excluded),
        "top_principles": principles.most_common(10),
        "top_risks": risks.most_common(10),
        "prompt_free": False,
        "raw_prompt_field_stored": False,
        "validity_verified": False,
        "limitations": [
            "Free-text fields can contain private content. Pattern scans are not a privacy or security guarantee.",
            "Context bindings and passed outcomes are caller assertions; verify current sources before reuse.",
            "Inventory frequency is not applicability, learned routing or model-weight distillation.",
        ],
    }
