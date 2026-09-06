"""Deterministic synthetic invariants, not model-quality experiments."""
from copy import deepcopy
import json
from pathlib import Path
import random

from premium_model_budget_governor.workflow import plan_workflow


def test_one_thousand_seeded_budget_and_context_scenarios():
    template = json.loads((Path(__file__).parents[1] / "examples/astra_preferred.json").read_text())
    rng = random.Random(20260907)
    for _ in range(1000):
        packet = deepcopy(template)
        packet.update(budget_credits=rng.uniform(0, 100), spent_credits=rng.uniform(0, 10),
                      reserve_credits=rng.uniform(0, 10), remaining_limit_percent=rng.choice([None, 0, 10, 50, 100]),
                      explicit_approval=rng.choice([True, False]),
                      minimum_input_tokens_per_call=rng.randrange(0, 100000))
        result = plan_workflow(packet)
        if result["selected"]:
            assert not result["selected"]["blocks"]
            assert result["selected"]["estimated_total_credits"] <= packet["budget_credits"] + 1e-6
            assert result["selected"]["astra_roles"]
            assert packet["explicit_approval"] or (packet["remaining_limit_percent"] or 0) > 15
        larger = deepcopy(packet)
        larger["minimum_input_tokens_per_call"] += 5000
        expanded = plan_workflow(larger)
        for before, after in zip(result["candidates"], expanded["candidates"]):
            assert after["estimated_total_credits"] >= before["estimated_total_credits"]


def test_strict_context_calibration_blocks_missing_measurement():
    packet = json.loads((Path(__file__).parents[1] / "examples/astra_preferred.json").read_text())
    packet["require_context_calibration"] = True
    result = plan_workflow(packet)
    assert result["decision"] == "needs_replan"
    assert all("measure_host_context_before_execution" in c["blocks"] for c in result["candidates"])
