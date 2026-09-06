import pytest

from premium_model_budget_governor.benchmark import grade_repair


GOOD = '''def normalize_token(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("invalid")
    if not isfinite(value) or value < 0 or int(value) != value:
        raise ValueError("invalid")
    return int(value)
'''


def test_executable_repair_accepts_correct_code():
    assert grade_repair(GOOD)["passed"]


def test_local_assignment_is_valid_python_not_a_model_failure():
    assert grade_repair(GOOD.replace("    return int(value)", "    result = int(value)\n    return result"))["passed"]


def test_real_original_helper_fails_contract():
    code = '''def normalize_token(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        return 0
    return int(value)
'''
    assert not grade_repair(code)["passed"]


@pytest.mark.parametrize("source", ["import os", "def normalize_token(x):\n return x.__class__", "def normalize_token(x):\n while True: pass", "def normalize_token(x):\n return eval(x)"])
def test_untrusted_candidate_cannot_execute_arbitrary_python(source):
    assert grade_repair(source)["status"] == "rejected_source"
