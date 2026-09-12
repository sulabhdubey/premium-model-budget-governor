from copy import deepcopy
import json

import pytest

from premium_model_budget_governor.context_profile import compare_context_choices


def option(name="direct", action="continue", main=(8, 10)):
    return {
        "id": name, "action": action, "supported": True,
        "model": "gpt-6-astra", "effort": "high", "snapshot": "snapshot-1",
        "capabilities": ["images", "tools", "skills"],
        "evidence": ["image-sha256", "source-sha256"], "state": ["acceptance-v1"],
        "costs": {
            "preparation": [0, 0], "execution": list(main),
            "verification": [1, 2], "recovery": [0, 1],
        },
    }


def packet():
    return {
        "schema_version": 1,
        "estimate_basis": {"unit": "estimated_credits", "version": "test-v1"},
        "required": {"capabilities": ["images", "tools", "skills"],
                     "evidence": ["image-sha256", "source-sha256"],
                     "state": ["acceptance-v1"]},
        "acceptance": [{"id": "tests", "status": "pending"}],
        "baseline": option(), "candidates": [option("compact", "compact", (2, 3))],
    }


def test_preserving_candidate_can_have_lower_whole_cost_without_claiming_savings():
    report = compare_context_choices(packet())
    assert report["recommended_id"] == "compact"
    assert report["decision"] == "propose_change"
    assert report["candidates"][0]["total"] == [3, 6]
    assert report["candidates"][0]["estimated_margin"] == 3
    assert report["execution_authorized"] is False
    assert report["savings_proven"] is False


def test_preparation_and_recovery_can_erase_apparent_capsule_savings():
    data = packet()
    data["candidates"][0]["costs"]["preparation"] = [5, 6]
    data["candidates"][0]["costs"]["recovery"] = [0, 8]
    report = compare_context_choices(data)
    assert report["recommended_id"] == "direct"
    assert "no_separated_cost_advantage" in report["candidates"][0]["reasons"]


@pytest.mark.parametrize("field,value,reason", [
    ("model", "gpt-5.6-sol", "model_changed"),
    ("effort", "low", "reasoning_profile_changed"),
    ("snapshot", "stale-snapshot", "snapshot_changed"),
    ("supported", False, "host_operation_unsupported"),
    ("capabilities", ["tools"], "missing_capabilities"),
    ("evidence", [], "missing_evidence"),
    ("state", [], "missing_state"),
])
def test_no_cost_advantage_can_override_preservation(field, value, reason):
    data = packet()
    data["candidates"][0][field] = value
    report = compare_context_choices(data)
    assert report["recommended_id"] == "direct"
    assert reason in report["candidates"][0]["reasons"]


def test_missing_stage_is_not_free():
    data = packet()
    del data["candidates"][0]["costs"]["recovery"]
    with pytest.raises(ValueError, match="cost stages"):
        compare_context_choices(data)


def test_unknown_cost_stays_unknown():
    data = packet()
    data["candidates"][0]["costs"]["preparation"] = None
    report = compare_context_choices(data)
    assert report["recommended_id"] == "direct"
    assert report["candidates"][0]["total"] is None
    assert "unknown_cost" in report["candidates"][0]["reasons"]


def test_invalid_baseline_requires_replan_not_a_favorable_comparison():
    data = packet()
    data["baseline"]["capabilities"] = []
    report = compare_context_choices(data)
    assert report["decision"] == "needs_replan"
    assert report["recommended_id"] is None


def test_stop_requires_all_explicit_acceptance_checks():
    data = packet()
    data["acceptance"][0]["status"] = "passed"
    report = compare_context_choices(data)
    assert report["decision"] == "stop_at_acceptance"
    assert report["recommended_id"] is None
    assert report["acceptance_verified"] is False
    data["acceptance"].append({"id": "visual", "status": "unknown"})
    assert compare_context_choices(data)["decision"] == "propose_change"


@pytest.mark.parametrize("cost", [[True, 2], [-1, 3], [3, 2], [0, float("inf")], [0, float("nan")]])
def test_invalid_costs_fail(cost):
    data = packet()
    data["candidates"][0]["costs"]["execution"] = cost
    with pytest.raises(ValueError):
        compare_context_choices(data)


def test_sum_overflow_fails():
    data = packet()
    data["baseline"]["costs"] = {name: [1e308, 1e308] for name in data["baseline"]["costs"]}
    with pytest.raises(ValueError):
        compare_context_choices(data)


def test_duplicate_ids_and_empty_acceptance_fail():
    data = packet()
    data["candidates"].append(deepcopy(data["candidates"][0]))
    with pytest.raises(ValueError):
        compare_context_choices(data)
    data = packet()
    data["acceptance"] = []
    with pytest.raises(ValueError):
        compare_context_choices(data)


def test_cli_is_read_only_proposal(tmp_path, capsys):
    from premium_model_budget_governor.cli import main
    source = tmp_path / "choices.json"
    source.write_text(json.dumps(packet()), encoding="utf-8")
    assert main(["context-choices", "--input", str(source)]) == 0
    report = json.loads(capsys.readouterr().out)["result"]
    assert report["recommended_id"] == "compact"
    assert list(tmp_path.iterdir()) == [source]


def test_equal_cost_and_unknown_baseline_do_not_support_a_change():
    data = packet()
    data["candidates"][0]["costs"] = deepcopy(data["baseline"]["costs"])
    assert compare_context_choices(data)["decision"] == "retain_baseline"
    data["baseline"]["costs"]["execution"] = None
    report = compare_context_choices(data)
    assert report["decision"] == "needs_replan"
    assert report["candidates"][0]["estimated_margin"] is None


def test_order_does_not_choose_a_more_expensive_candidate():
    data = packet()
    data["candidates"].append(option("restart", "restart", (0, 1)))
    original = deepcopy(data)
    assert compare_context_choices(data)["recommended_id"] == "restart"
    assert data == original
    data["candidates"].reverse()
    assert compare_context_choices(data)["recommended_id"] == "restart"


@pytest.mark.parametrize("mutation", [
    lambda data: data.update(schema_version=True),
    lambda data: data.update(candidates=[{}] * 33),
    lambda data: data["baseline"].update(action="restart"),
    lambda data: data["baseline"].update(supported="true"),
    lambda data: data["baseline"].update(model=None),
    lambda data: data["baseline"].update(evidence=["duplicate", "duplicate"]),
    lambda data: data["estimate_basis"].update(unit="weekly_percent"),
    lambda data: data["acceptance"].append({"id": "tests", "status": "passed"}),
])
def test_malformed_contract_rejected(mutation):
    data = packet()
    mutation(data)
    with pytest.raises(ValueError):
        compare_context_choices(data)


def test_cli_malformed_input_returns_structured_error(tmp_path, capsys):
    from premium_model_budget_governor.cli import main
    source = tmp_path / "bad.json"
    source.write_text('{"schema_version": true}', encoding="utf-8")
    assert main(["context-choices", "--input", str(source)]) == 2
    assert json.loads(capsys.readouterr().out)["ok"] is False
