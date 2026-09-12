import pytest

from premium_model_budget_governor.task_measurement import measure_task


def plan():
    return [{"id": k, "role": k} for k in ("prepare", "execute", "verify", "report")]


def receipt(stage):
    return {"receipt_id": stage["id"], "work_unit_id": stage["id"],
            "source_id": stage["id"], "model": "gpt-6-astra",
            "counter_kind": "final", "scope": "exclusive",
            "usage": {"input_tokens": 100, "cached_tokens": 20, "output_tokens": 10}}


def test_all_phases_accounted_reporting_separate(tmp_path):
    result = measure_task(plan(), tmp_path / "run", lambda stage: receipt(stage))
    assert result["task"]["totals"]["input_tokens"] == 300
    assert result["reporting"]["totals"]["input_tokens"] == 100
    assert result["status"] == "complete_for_declared_phases"
    assert result["savings_proven"] is False
    assert len(list((tmp_path / "run").glob("phase-*.json"))) == 4


def test_uncertain_usage_stops_before_another_call(tmp_path):
    seen = []
    def invoke(stage):
        seen.append(stage["id"])
        return {**receipt(stage), "scope": "unknown"}
    result = measure_task(plan(), tmp_path / "run", invoke)
    assert seen == ["prepare"]
    assert result["task"]["totals"] is None
    assert result["status"] == "incomplete"


def test_exception_preserved_without_leaking_message(tmp_path):
    def invoke(stage):
        raise ValueError("private prompt and credential")
    result = measure_task(plan(), tmp_path / "run", invoke)
    assert result["outcomes"][0]["status"] == "execution_or_receipt_error"
    assert "credential" not in (tmp_path / "run" / "result.json").read_text()
    with pytest.raises(FileExistsError):
        measure_task(plan(), tmp_path / "run", invoke)


def test_duplicate_sources_stop_even_across_reporting(tmp_path):
    result = measure_task(plan(), tmp_path / "run", lambda s: {**receipt(s), "source_id": "same"})
    assert len(result["outcomes"]) == 2
    assert result["status"] == "incomplete"


def test_unknown_model_cost_stops_dispatch(tmp_path):
    result = measure_task(plan(), tmp_path / "run", lambda s: {**receipt(s), "model": "unknown"})
    assert len(result["outcomes"]) == 1
    assert result["status"] == "incomplete"


@pytest.mark.parametrize("stages", [[], [{"id": "x", "role": "execute"}],
                                   plan() + [{"id": "execute", "role": "retry"}]])
def test_invalid_enrollment_never_invokes(tmp_path, stages):
    with pytest.raises(ValueError):
        measure_task(stages, tmp_path / "run", lambda _: pytest.fail("dispatched"))
