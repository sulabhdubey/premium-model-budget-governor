"""Astra Shadow Mode packets."""

from __future__ import annotations

from .capsule import score_capsule
from .policy import decide_model
from .scanners import scan_text


def build_shadow_packet(
    *,
    draft_answer: str,
    evidence_summary: str,
    contradictions: list[str] | None = None,
    remaining_limit_percent: int | None = None,
    explicit_approval: bool = False,
    sol_baseline_tokens: dict | None = None,
) -> dict[str, object]:
    contradictions = contradictions or []
    capsule = "\n".join(
        [
            "# Astra Shadow Review",
            "",
            "## Budget Contract",
            "- Do not redo the work.",
            "- Judge only approve, reject, or patch.",
            "- Keep response under 500 words.",
            "",
            "## Goal",
            "Review a cheaper model's completed draft for correctness and risk.",
            "",
            "## Decision Requested",
            "Approve, reject, or patch the draft. Include only blocking reasons and the smallest fix.",
            "",
            "## Draft",
            draft_answer.strip(),
            "",
            "## Selected Evidence",
            evidence_summary.strip(),
            "",
            "## Contradictions",
            "\n".join(f"- {item}" for item in contradictions) if contradictions else "- None supplied.",
        ]
    )
    quality = score_capsule(capsule)
    if not scan_text("\n".join([draft_answer, evidence_summary, *contradictions]))["safe_to_include"]:
        return {"capsule": "# Astra Shadow Review Blocked\nUnsafe evidence requires sanitization.",
                "quality": {"score": 0, "grade": "block"},
                "route": {"decision": "block_or_route_to_sol", "blocks": ["sanitize_evidence"],
                          "recommended_model": "gpt-5.6-sol"}}
    route = decide_model(
        {
            "requested_model": "gpt-6-astra",
            "remaining_limit_percent": remaining_limit_percent,
            "reasons": ["final_release_review"],
            "explicit_approval": explicit_approval,
            "capsule_quality_score": quality["score"],
            "sol_baseline_tokens": sol_baseline_tokens,
            "premium_plan_tokens": {"input": max(1, len(capsule) // 4), "output": 700},
        }
    )
    return {"capsule": capsule, "quality": quality, "route": route}
