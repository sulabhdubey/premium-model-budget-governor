"""Cheap-model tournament ranking before one premium judge call."""

from __future__ import annotations

import re
from typing import Mapping
from .scanners import scan_text


def score_candidate(candidate: Mapping[str, object], rubric_terms: list[str] | None = None) -> dict[str, object]:
    text = str(candidate.get("answer", ""))
    rubric_terms = rubric_terms or ["risk", "test", "evidence", "rollback", "security"]
    score = 0
    reasons: list[str] = []
    for term in rubric_terms:
        if re.search(rf"\b{re.escape(term)}\b", text, re.I):
            score += 8
            reasons.append(f"mentions_{term}")
    if len(text) < 500:
        score += 8
        reasons.append("compact")
    if re.search(r"\b(always|guaranteed|perfect|viral)\b", text, re.I):
        score -= 12
        reasons.append("overclaim_penalty")
    if re.search(r"\b(I need|cannot|not possible)\b", text, re.I):
        score -= 4
        reasons.append("low_agency_penalty")
    return {"id": candidate.get("id"), "model": candidate.get("model"), "score": score, "reasons": reasons}


def rank_candidates(candidates: list[Mapping[str, object]], *, top_k: int = 2, rubric_terms: list[str] | None = None) -> dict[str, object]:
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer")
    if any(not scan_text(str(candidate.get("answer", "")))["safe_to_include"] for candidate in candidates):
        return {"ranked": [], "blocked": "sanitize_candidate_evidence", "astra_judge_packet": None}
    scored = [score_candidate(candidate, rubric_terms) for candidate in candidates]
    finalists = sorted(zip(scored, candidates), key=lambda pair: -int(pair[0]["score"]))[:top_k]
    scored.sort(key=lambda row: int(row["score"]), reverse=True)
    return {
        "ranked": scored,
        "astra_judge_packet": {
            "finalists": [{**row, "answer": str(candidate.get("answer", ""))} for row, candidate in finalists],
            "instruction": "Ask Astra to judge only these finalists and return approve, reject, or merge.",
        },
    }
