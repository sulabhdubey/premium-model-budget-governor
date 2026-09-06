"""Bounded executable oracle for the telemetry-helper repair benchmark.

This AST allowlist evaluates only one small straight-line numeric function. It is
not a sandbox for arbitrary Python or a general-purpose code execution service.
"""
import ast
import math


def grade_repair(source: str) -> dict:
    rejected = {"passed": False, "status": "rejected_source", "checks_passed": 0, "checks_total": 0}
    if not isinstance(source, str) or len(source) > 6000:
        return rejected
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return rejected
    allowed = (ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.If, ast.Raise,
               ast.Call, ast.Name, ast.Load, ast.Constant, ast.Return, ast.Compare,
               ast.NotEq, ast.Eq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.BoolOp, ast.Or,
               ast.And, ast.UnaryOp, ast.Not, ast.Tuple, ast.Assign, ast.Store)
    names = {"normalize_token", "value", "isinstance", "isfinite", "int", "float", "bool", "ValueError"}
    callables = names - {"normalize_token", "value"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if (len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name)
                    or node.targets[0].id in callables | {"normalize_token"}
                    or node.targets[0].id.startswith("_") or len(node.targets[0].id) > 64):
                return rejected
            names.add(node.targets[0].id)
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        return rejected
    f = tree.body[0]
    if (f.name != "normalize_token" or f.decorator_list or f.returns or f.args.defaults
            or f.args.kwonlyargs or f.args.vararg or f.args.kwarg or f.args.posonlyargs
            or len(f.args.args) != 1 or f.args.args[0].arg != "value" or f.args.args[0].annotation):
        return rejected
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            return rejected
        if isinstance(node, ast.FunctionDef) and node is not f:
            return rejected
        if isinstance(node, ast.Name) and node.id not in names:
            return rejected
        if isinstance(node, ast.Call) and (not isinstance(node.func, ast.Name) or node.func.id not in callables):
            return rejected
    namespace = {"__builtins__": {}, "isfinite": math.isfinite, "isinstance": isinstance,
                 "int": int, "float": float, "bool": bool, "ValueError": ValueError}
    exec(compile(tree, "<bounded-benchmark-candidate>", "exec"), namespace)
    valid = [0, 1, 17, 10**12, 0.0, 1.0, 1e20] + list(range(100, 150))
    invalid = [True, False, -1, -.5, 1.5, float("nan"), float("inf"), -float("inf"),
               "1", None, [], {}, ()] + [n + .5 for n in range(20)]
    passed = 0
    for value in valid:
        try:
            answer = namespace["normalize_token"](value)
            passed += type(answer) is int and answer == int(value)
        except Exception:
            pass
    for value in invalid:
        try:
            namespace["normalize_token"](value)
        except ValueError:
            passed += 1
        except Exception:
            pass
    total = len(valid) + len(invalid)
    return {"passed": passed == total, "status": "graded", "checks_passed": passed, "checks_total": total}


def grade_suite(answer: dict, oracle: dict) -> dict:
    if not isinstance(answer, dict):
        return {"passed": False, "error": "answer is not an object"}
    repair = grade_repair(answer.get("normalize_token_source", ""))
    # JSON serialization distinguishes booleans from integers, unlike Python equality.
    import json
    fields = {key: json.dumps(answer.get(key), sort_keys=True) == json.dumps(value, sort_keys=True)
              for key, value in oracle.items()}
    return {"passed": repair["passed"] and all(fields.values()), "repair": repair, "contracts": fields}
