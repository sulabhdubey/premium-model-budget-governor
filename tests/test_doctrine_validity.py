import json

import pytest

from premium_model_budget_governor.distillation import append_doctrine, synthesize_doctrine


def context():
    return {"scope_id": "project-1", "source_snapshot": "source-v1",
            "policy_version": "policy-v1", "permissions": ["read"]}


def record():
    return {"principle": "Verify the existing implementation before introducing another layer.",
            "outcome": "passed", "validity": {**context(), "valid_until": "2099-01-01T00:00:00Z"}}


def test_bound_record_can_be_reused_only_in_declared_context(tmp_path):
    ledger = tmp_path / "doctrine.jsonl"
    append_doctrine(record(), ledger)
    report = synthesize_doctrine(ledger, current_context=context())
    assert report["eligible_records"] == 1
    assert report["top_principles"][0][0] == record()["principle"]
    assert report["validity_verified"] is False


@pytest.mark.parametrize("field,value", [
    ("scope_id", "project-2"), ("source_snapshot", "source-v2"),
    ("policy_version", "policy-v2"), ("permissions", ["read", "write"]),
])
def test_changed_invalidation_condition_excludes_old_advice(tmp_path, field, value):
    ledger = tmp_path / "doctrine.jsonl"
    append_doctrine(record(), ledger)
    current = context()
    current[field] = value
    report = synthesize_doctrine(ledger, current_context=current)
    assert report["eligible_records"] == 0
    assert report["top_principles"] == []
    assert report["excluded_reasons"]["context_changed"] == 1


def test_legacy_and_failed_records_are_not_applicable(tmp_path):
    ledger = tmp_path / "doctrine.jsonl"
    append_doctrine({"principle": "Unbound legacy suggestion"}, ledger)
    failed = record()
    failed["outcome"] = "failed"
    append_doctrine(failed, ledger)
    report = synthesize_doctrine(ledger, current_context=context())
    assert report["eligible_records"] == 0
    assert report["excluded_reasons"] == {"unbound_record": 1, "outcome_not_passed": 1}
    assert synthesize_doctrine(ledger)["mode"] == "inventory_only"


def test_expired_advice_is_excluded(tmp_path):
    ledger = tmp_path / "doctrine.jsonl"
    data = record()
    data["validity"]["valid_until"] = "2000-01-01T00:00:00Z"
    append_doctrine(data, ledger)
    report = synthesize_doctrine(ledger, current_context=context())
    assert report["excluded_reasons"] == {"expired": 1}


@pytest.mark.parametrize("expiry", ["2099-01-01", None, 123, "not-a-date"])
def test_invalid_expiry_never_written(tmp_path, expiry):
    ledger = tmp_path / "doctrine.jsonl"
    data = record()
    data["validity"]["valid_until"] = expiry
    with pytest.raises(ValueError):
        append_doctrine(data, ledger)
    assert not ledger.exists()


def test_existing_malformed_record_is_reported_not_accepted(tmp_path):
    ledger = tmp_path / "doctrine.jsonl"
    ledger.write_text('bad json\n[]\n', encoding="utf-8")
    report = synthesize_doctrine(ledger, current_context=context())
    assert report["malformed_records"] == 2
    assert report["eligible_records"] == 0


def test_secret_in_allowed_field_rejected_before_creation(tmp_path):
    ledger = tmp_path / "doctrine.jsonl"
    data = record()
    data["principle"] = "-----BEGIN PRIVATE KEY-----"
    with pytest.raises(ValueError, match="unsafe"):
        append_doctrine(data, ledger)
    assert not ledger.exists()


def test_free_text_is_not_claimed_prompt_free(tmp_path):
    ledger = tmp_path / "doctrine.jsonl"
    append_doctrine(record(), ledger)
    report = synthesize_doctrine(ledger)
    assert report["prompt_free"] is False
    assert report["raw_prompt_field_stored"] is False


def test_cli_context_summary_does_not_write_ledger(tmp_path, capsys):
    from premium_model_budget_governor.cli import main
    ledger = tmp_path / "doctrine.jsonl"
    append_doctrine(record(), ledger)
    before = ledger.read_bytes()
    source = tmp_path / "context.json"
    source.write_text(json.dumps(context()), encoding="utf-8")
    assert main(["doctrine", "--ledger", str(ledger), "--context", str(source)]) == 0
    assert json.loads(capsys.readouterr().out)["result"]["eligible_records"] == 1
    assert ledger.read_bytes() == before


@pytest.mark.parametrize("kind", ["", "RSA ", "EC ", "DSA ", "OPENSSH ", "ENCRYPTED "])
def test_shared_scanner_recognizes_private_key_headers(kind):
    from premium_model_budget_governor.scanners import scan_text
    report = scan_text(f"-----BEGIN {kind}PRIVATE KEY-----")
    assert report["safe_to_include"] is False
    assert report["findings"][0]["rule"] == "private_key_header"


def test_public_key_header_not_a_private_key():
    from premium_model_budget_governor.scanners import scan_text
    assert scan_text("-----BEGIN PUBLIC KEY-----")["safe_to_include"] is True


def test_bounded_ledger_read_and_append(tmp_path, monkeypatch):
    import premium_model_budget_governor.distillation as module
    ledger = tmp_path / "large.jsonl"
    ledger.write_bytes(b"x" * 101)
    monkeypatch.setattr(module, "MAX_BYTES", 100)
    with pytest.raises(ValueError, match="bounded"):
        synthesize_doctrine(ledger, current_context=context())
    with pytest.raises(ValueError, match="bounded"):
        append_doctrine(record(), ledger)
    assert ledger.read_bytes() == b"x" * 101


def test_unsafe_legacy_record_not_repeated_in_summary(tmp_path):
    ledger = tmp_path / "legacy.jsonl"
    ledger.write_text(json.dumps({"principle": "-----BEGIN PRIVATE KEY-----"}), encoding="utf-8")
    report = synthesize_doctrine(ledger)
    assert report["top_principles"] == []
    assert report["excluded_reasons"] == {"invalid_or_unsafe_record": 1}


def test_unrecognized_invalidation_condition_is_not_silently_ignored(tmp_path):
    ledger = tmp_path / "doctrine.jsonl"
    data = record()
    data["validity"]["dependency_versions"] = {"library": "1"}
    with pytest.raises(ValueError, match="binding fields"):
        append_doctrine(data, ledger)
    assert not ledger.exists()
