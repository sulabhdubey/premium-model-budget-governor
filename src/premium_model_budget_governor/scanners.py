"""Prompt-injection and secret scanners for capsule inputs."""

from __future__ import annotations

import re
from pathlib import Path


SECRET_PATTERNS = [
    ("private_key_header", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----", re.I)),
    ("openai_key", re.compile(r"\bsk-(?:proj|live|test)?-[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("generic_secret_assignment", re.compile(r"\b(?:api[_-]?key|token|password|secret)\s*=\s*[^\s]{12,}", re.I)),
]

INJECTION_PATTERNS = [
    ("ignore_higher_priority", "critical", re.compile(r"\b(ignore|disregard|override)\b.{0,80}\b(previous|system|developer|higher[- ]priority)\b", re.I)),
    ("secret_exfiltration", "critical", re.compile(r"\b(print|dump|send|reveal|exfiltrate)\b.{0,80}\b(secret|token|api[_ -]?key|credential|env)\b", re.I)),
    ("tool_coercion", "high", re.compile(r"\b(run|execute|install|curl|wget|powershell|cmd\.exe|bash)\b.{0,80}\b(silently|without asking|now)\b", re.I)),
    ("policy_bypass", "high", re.compile(r"\b(disable|bypass|ignore)\b.{0,80}\b(safety|policy|approval|sandbox)\b", re.I)),
]


def scan_text(text: str, *, source: str = "<inline>") -> dict[str, object]:
    findings = []
    for name, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            findings.append({"kind": "secret", "rule": name, "severity": "critical", "source": source, "offset": match.start()})
    for name, severity, pattern in INJECTION_PATTERNS:
        for match in pattern.finditer(text):
            snippet = text[max(0, match.start() - 40): min(len(text), match.end() + 40)].replace("\n", " ")
            findings.append({"kind": "prompt_injection", "rule": name, "severity": severity, "source": source, "offset": match.start(), "snippet": snippet[:220]})
    unsafe = any(item["severity"] in {"high", "critical"} for item in findings)
    return {"safe_to_include": not unsafe, "finding_count": len(findings), "findings": findings}


def scan_file(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if b"\x00" in data:
        return {"safe_to_include": False, "finding_count": 1, "findings": [{"kind": "binary", "severity": "high", "source": str(path)}]}
    return scan_text(data.decode("utf-8", errors="replace"), source=str(path))
