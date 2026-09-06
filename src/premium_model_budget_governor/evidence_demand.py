"""Explicit evidence expansion with integrity checks and no silent truncation."""

from hashlib import sha256
from typing import Mapping

from .cost import _token
from .scanners import scan_text
from .workflow import flag


def evidence_packet(packet: Mapping) -> dict:
    items, requested = packet.get("items"), packet.get("requested_ids", [])
    limit = _token(packet.get("max_chars", 16000), "max_chars")
    if not isinstance(items, list) or not isinstance(requested, list) or any(not isinstance(v, str) for v in requested):
        raise ValueError("items and requested_ids must be lists")
    records, required, errors = {}, set(), []
    for item in items:
        if not isinstance(item, Mapping):
            raise ValueError("evidence item must be an object")
        id, text, source = item.get("id"), item.get("text"), item.get("source")
        if not isinstance(id, str) or not id or id in records:
            raise ValueError("evidence IDs must be unique non-empty strings")
        if not isinstance(text, str) or not isinstance(source, str):
            raise ValueError("text and source must be strings")
        digest = sha256(text.encode("utf-8")).hexdigest()
        if item.get("sha256") != digest:
            errors.append("evidence_hash_mismatch")
        # Scan metadata too; never echo unsafe input or scanner snippets on rejection.
        if not scan_text(id + "\n" + source + "\n" + text)["safe_to_include"]:
            errors.append("unsafe_evidence")
        if flag(item, "required"):
            required.add(id)
        records[id] = {"id": id, "text": text, "source": source, "sha256": digest, "trust": "untrusted_data"}
    wanted = required | set(requested)
    if wanted - records.keys():
        errors.append("unknown_evidence_id")
    if errors:
        return {"decision": "blocked", "blocks": sorted(set(errors)), "evidence": []}
    chosen = [records[id] for id in sorted(wanted)]
    chars = sum(len(v["text"]) for v in chosen)
    if chars > limit:
        return {"decision": "needs_replan", "blocks": ["required_and_requested_evidence_exceeds_budget"],
                "evidence": [], "required_chars": chars, "max_chars": limit}
    return {"decision": "ready", "evidence": chosen, "content_chars": chars,
            "omitted_ids": sorted(records.keys() - wanted), "truncated": False,
            "limitations": "Character budget excludes metadata; not a token budget. Hashes prove consistency, not authority. Pattern scans are not a security boundary."}
