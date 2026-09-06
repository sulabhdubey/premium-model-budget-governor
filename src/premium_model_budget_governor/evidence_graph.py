"""Compile claims, risks, diffs, files, and tests into a compact evidence graph."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import re
from typing import Iterable


@dataclass(frozen=True)
class EvidenceNode:
    id: str
    kind: str
    label: str
    source: str
    weight: float


def compile_graph(root: Path, paths: Iterable[Path], *, query: str = "") -> dict[str, object]:
    nodes: list[EvidenceNode] = []
    edges: list[dict[str, str]] = []
    query_terms = {part.lower() for part in re.findall(r"[a-zA-Z0-9_]+", query) if len(part) > 2}
    for index, rel in enumerate(paths, start=1):
        path = root / rel if not rel.is_absolute() else rel
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            display = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        except OSError:
            continue
        kind = "test" if "test" in path.name.lower() else "file"
        score = 1.0
        lower = text.lower()
        score += sum(0.2 for term in query_terms if term in lower)
        if re.search(r"\b(assert|pytest|unittest|expect)\b", lower):
            score += 0.5
        file_id = f"f{index}"
        nodes.append(EvidenceNode(file_id, kind, display, display, round(score, 3)))
        for line_no, line in enumerate(text.splitlines(), start=1):
            if re.search(r"\b(TODO|FIXME|SECURITY|bug|risk|fail|error|assert)\b", line, re.I):
                risk_id = f"{file_id}:r{line_no}"
                nodes.append(EvidenceNode(risk_id, "signal", line.strip()[:140], f"{display}:{line_no}", round(score + 0.4, 3)))
                edges.append({"from": file_id, "to": risk_id, "type": "contains"})
    nodes_sorted = sorted(nodes, key=lambda node: node.weight, reverse=True)
    return {
        "node_count": len(nodes_sorted),
        "edge_count": len(edges),
        "nodes": [asdict(node) for node in nodes_sorted[:80]],
        "edges": edges[:120],
    }


def graph_capsule(graph: dict[str, object], *, max_nodes: int = 20) -> str:
    nodes = graph.get("nodes", [])
    if not isinstance(nodes, list):
        nodes = []
    lines = ["# Evidence Graph Summary", "", "Top nodes:"]
    for node in nodes[:max_nodes]:
        if not isinstance(node, dict):
            continue
        lines.append(f"- [{node.get('kind')}] {node.get('label')} ({node.get('source')}, weight={node.get('weight')})")
    return "\n".join(lines) + "\n"
