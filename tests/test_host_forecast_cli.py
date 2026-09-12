import json

from premium_model_budget_governor.cli import main


def test_missing_forecast_cli(tmp_path, capsys):
    packet = {"profile": {k: "unknown" for k in (
        "host", "model", "reasoning", "context", "config_fingerprint", "task_family", "scope")},
              "receipts": []}
    source = tmp_path / "input.json"
    source.write_text(json.dumps(packet))
    assert main(["estimate-host", "--input", str(source)]) == 0
    envelope = json.loads(capsys.readouterr().out)
    assert envelope["ok"] is True
    result = envelope["result"]
    assert result["status"] == "missing"
    assert result["admission_tokens"] is None
