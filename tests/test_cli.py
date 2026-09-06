from pathlib import Path

from premium_model_budget_governor.cli import main


def test_cli_route(tmp_path: Path, capsys):
    packet = tmp_path / "route.json"
    packet.write_text(
        '{"requested_model":"gpt-6-astra","remaining_limit_percent":10,'
        '"sol_baseline_tokens":{"input":100000},"premium_plan_tokens":{"input":70000}}',
        encoding="utf-8",
    )
    assert main(["route", "--input", str(packet), "--plain"]) == 0
    assert "block_or_route_to_sol" in capsys.readouterr().out


def test_cli_capsule(tmp_path: Path):
    evidence = tmp_path / "proof.txt"
    output = tmp_path / "capsule.md"
    evidence.write_text("line one\nline two\n", encoding="utf-8")
    assert main(["capsule", "--root", str(tmp_path), "--goal", "g", "--decision", "d", "--include", "proof.txt", "--output", str(output)]) == 0
    assert output.exists()
    assert "Astra Capsule" in output.read_text(encoding="utf-8")
