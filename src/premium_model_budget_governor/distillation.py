"""Prompt-free distillation ledger for reusable Astra doctrine."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping


def append_doctrine(payload: Mapping[str, object], ledger: Path) -> dict[str, object]:
    allowed = {
        "project",
        "task_shape",
        "decision",
        "principle",
        "risk_pattern",
        "verification_contract",
        "model",
        "outcome",
    }
    record = {key: payload.get(key) for key in allowed if key in payload}
    record["recorded_at"] = datetime.now(timezone.utc).isoformat()
    record["raw_prompt_stored"] = False
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def synthesize_doctrine(ledger: Path) -> dict[str, object]:
    records = []
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                records.append(row)
    principles = Counter(str(row.get("principle")) for row in records if row.get("principle"))
    risks = Counter(str(row.get("risk_pattern")) for row in records if row.get("risk_pattern"))
    return {
        "records": len(records),
        "top_principles": principles.most_common(10),
        "top_risks": risks.most_common(10),
        "prompt_free": True,
    }
