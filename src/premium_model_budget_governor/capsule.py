"""Astra capsule creation and quality scoring."""

from __future__ import annotations

from pathlib import Path
import re

from .scanners import scan_file


REQUIRED_HEADINGS = [
    "## Budget Contract",
    "## Goal",
    "## Decision Requested",
    "## Selected Evidence",
]


def score_capsule(text: str) -> dict[str, object]:
    score = 100
    warnings: list[str] = []
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in text]
    if missing:
        score -= 12 * len(missing)
        warnings.append("missing_required_sections")
    if len(text) < 1000:
        score -= 15
        warnings.append("capsule_too_thin")
    if len(text) > 32000:
        score -= 20
        warnings.append("capsule_too_large")
    if "CAPSULE TRUNCATED" in text:
        score -= 25
        warnings.append("capsule_truncated")
    if not re.search(r"^## File:", text, re.M):
        score -= 15
        warnings.append("no_file_evidence")
    if re.search(r"\b(entire repo|all files|whole internet|everything)\b", text, re.I):
        score -= 10
        warnings.append("scope_too_broad")
    score = max(0, min(100, score))
    if "capsule_truncated" in warnings or text.startswith("# Astra Capsule Blocked"):
        score = min(score, 69)
    return {"score": score, "grade": "usable" if score >= 70 else "block", "warnings": warnings}


def build_capsule(
    *,
    root: Path,
    goal: str,
    decision: str,
    evidence_paths: list[Path],
    max_chars: int = 24000,
    output_words: int = 900,
) -> str:
    sections = [
        "# Astra Capsule",
        "",
        "## Budget Contract",
        "- Use Astra for one decision turn only.",
        f"- Keep the response under {output_words} words.",
        "- Route execution back to cheaper models.",
        "",
        "## Goal",
        goal,
        "",
        "## Decision Requested",
        decision,
        "",
        "## Selected Evidence",
    ]
    for rel in evidence_paths:
        path = root / rel if not rel.is_absolute() else rel
        scan = scan_file(path)
        if not scan["safe_to_include"]:
            return "# Astra Capsule Blocked\n\nUnsafe evidence was found before capsule creation.\n"
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > 5000:
            sections.append("[CAPSULE TRUNCATED: file excerpt omits content after character 5000; supply focused evidence]")
            text = text[:5000]
        numbered = "\n".join(f"{idx:04d}: {line}" for idx, line in enumerate(text.splitlines(), start=1))
        sections.extend(["", f"## File: {path.relative_to(root) if path.is_relative_to(root) else path}", "", "```text", numbered, "```"])
    capsule = "\n".join(sections).strip() + "\n"
    if len(capsule) > max_chars:
        warning = "\n[CAPSULE TRUNCATED: shrink evidence before spending premium credits]\n"
        capsule = capsule[: max_chars - len(warning)] + warning
    return capsule
