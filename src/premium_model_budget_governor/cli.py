"""Command line interface for Premium Model Budget Governor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .capsule import build_capsule, score_capsule
from .distillation import append_doctrine, synthesize_doctrine
from .evidence_graph import compile_graph, graph_capsule
from .policy import decide_model
from .predictor import predict_benefit
from .scanners import scan_file, scan_text
from .shadow import build_shadow_packet
from .telemetry import append_usage
from .tournament import rank_candidates


DEFAULT_LEDGER = Path.home() / ".pm-bg" / "ledger.jsonl"
DEFAULT_DOCTRINE = Path.home() / ".pm-bg" / "doctrine.jsonl"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pm-bg", description="Govern premium model use with capsules, routing, and telemetry.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    route = sub.add_parser("route", help="Decide whether a requested model should be allowed")
    route.add_argument("--input", required=True)
    route.add_argument("--plain", action="store_true", help="Print a compact human-readable decision")

    capsule = sub.add_parser("capsule", help="Build a safe premium-model capsule")
    capsule.add_argument("--root", default=".")
    capsule.add_argument("--goal", required=True)
    capsule.add_argument("--decision", required=True)
    capsule.add_argument("--include", action="append", default=[])
    capsule.add_argument("--max-chars", type=int, default=24000)
    capsule.add_argument("--output")

    score = sub.add_parser("score", help="Score capsule quality")
    score.add_argument("path")

    scan = sub.add_parser("scan", help="Scan text or files for secrets and injection")
    scan.add_argument("paths", nargs="*")
    scan.add_argument("--text")

    graph = sub.add_parser("graph", help="Compile an evidence graph")
    graph.add_argument("--root", default=".")
    graph.add_argument("--include", action="append", required=True)
    graph.add_argument("--query", default="")
    graph.add_argument("--capsule", action="store_true")

    shadow = sub.add_parser("shadow", help="Create an Astra shadow review packet")
    shadow.add_argument("--draft", required=True)
    shadow.add_argument("--evidence", required=True)
    shadow.add_argument("--remaining", type=int)

    tournament = sub.add_parser("tournament", help="Rank cheap-model candidate answers")
    tournament.add_argument("--input", required=True)

    predict = sub.add_parser("predict", help="Predict whether Astra is likely to help")
    predict.add_argument("--input", required=True)
    predict.add_argument("--ledger")

    telemetry = sub.add_parser("telemetry", help="Append prompt-free token usage")
    telemetry.add_argument("--input", required=True)
    telemetry.add_argument("--ledger", default=str(DEFAULT_LEDGER))

    doctrine = sub.add_parser("doctrine", help="Append or summarize distilled doctrine")
    doctrine.add_argument("--input")
    doctrine.add_argument("--ledger", default=str(DEFAULT_DOCTRINE))

    args = parser.parse_args(argv)
    try:
        result = _dispatch(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    if args.cmd == "route" and getattr(args, "plain", False):
        print(_plain_route(result))
    elif isinstance(result, str):
        print(result, end="" if result.endswith("\n") else "\n")
    else:
        print(json.dumps({"ok": True, "result": result}, indent=2, sort_keys=True))
    return 0


def _plain_route(result: object) -> str:
    if not isinstance(result, dict):
        return str(result)
    lines = [
        f"decision: {result.get('decision')}",
        f"recommended_model: {result.get('recommended_model')}",
    ]
    parity = result.get("parity")
    if isinstance(parity, dict):
        lines.extend(
            [
                f"premium_plan_credits: {parity.get('premium_plan_credits')}",
                f"premium_to_sol_ratio: {parity.get('premium_to_sol_ratio')}",
                f"sol_parity_met: {parity.get('sol_parity_met')}",
            ]
        )
    blocks = result.get("blocks")
    if blocks:
        lines.append(f"blocks: {', '.join(str(item) for item in blocks)}")
    return "\n".join(lines)


def _load_json(path: str) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON input must be an object")
    return payload


def _dispatch(args: argparse.Namespace) -> object:
    if args.cmd == "route":
        return decide_model(_load_json(args.input))
    if args.cmd == "capsule":
        text = build_capsule(
            root=Path(args.root).resolve(),
            goal=args.goal,
            decision=args.decision,
            evidence_paths=[Path(item) for item in args.include],
            max_chars=args.max_chars,
        )
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
            return {"output": args.output, "quality": score_capsule(text)}
        return text
    if args.cmd == "score":
        return score_capsule(Path(args.path).read_text(encoding="utf-8"))
    if args.cmd == "scan":
        if args.text is not None:
            return scan_text(args.text)
        return [scan_file(Path(path)) for path in args.paths]
    if args.cmd == "graph":
        compiled = compile_graph(Path(args.root).resolve(), [Path(item) for item in args.include], query=args.query)
        return graph_capsule(compiled) if args.capsule else compiled
    if args.cmd == "shadow":
        return build_shadow_packet(
            draft_answer=Path(args.draft).read_text(encoding="utf-8"),
            evidence_summary=Path(args.evidence).read_text(encoding="utf-8"),
            remaining_limit_percent=args.remaining,
        )
    if args.cmd == "tournament":
        payload = _load_json(args.input)
        candidates = payload.get("candidates", [])
        if not isinstance(candidates, list):
            raise ValueError("candidates must be a list")
        return rank_candidates(candidates)  # type: ignore[arg-type]
    if args.cmd == "predict":
        return predict_benefit(_load_json(args.input), ledger=Path(args.ledger) if args.ledger else None)
    if args.cmd == "telemetry":
        return append_usage(_load_json(args.input), Path(args.ledger))
    if args.cmd == "doctrine":
        ledger = Path(args.ledger)
        if args.input:
            return append_doctrine(_load_json(args.input), ledger)
        return synthesize_doctrine(ledger)
    raise ValueError(f"unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
