import json

import pytest

from premium_model_budget_governor.observability import observability_preview


def packet(**usage):
    return {"receipts": [{"receipt_id": "privateReceipt", "source_id": "privateSource",
        "work_unit_id": "privateUnit", "model": "privateModel", "counter_kind": "final",
        "scope": "exclusive", "prompt": "SECRET-CONTENT", "usage": {
            "input_tokens": 100, "output_tokens": 10, **usage}}]}


def attributes(result):
    log = result["otlp"]["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]
    return {row["key"]: row["value"] for row in log["attributes"]}


def test_allowlist_omits_content_identity_and_unmeasured_cache():
    result = observability_preview(packet())
    encoded = json.dumps(result)
    assert "private" not in encoded and "SECRET" not in encoded
    attrs = attributes(result)
    assert attrs["pm_bg.supplied_total.input_tokens"] == {"intValue": "100"}
    assert "pm_bg.supplied_total.cached_tokens" not in attrs
    assert attrs["pm_bg.absent_cached_input_assumed_zero"] == {"intValue": "1"}
    assert result["network_requests"] == 0 and result["review_required"]


def test_measured_cache_subset_is_separate_not_added():
    attrs = attributes(observability_preview(packet(cached_tokens=20, cache_write_tokens=0)))
    assert attrs["pm_bg.supplied_total.input_tokens"] == {"intValue": "100"}
    assert attrs["pm_bg.supplied_total.cached_tokens"] == {"intValue": "20"}


@pytest.mark.parametrize("mode", ["missing", "overlap", "empty", "cumulative"])
def test_incomplete_coverage_omits_totals(mode):
    data = packet()
    if mode == "missing":
        data["work_units"] = ["privateUnit", "missing"]
    elif mode == "overlap":
        data["receipts"].append({**data["receipts"][0], "receipt_id": "second"})
    elif mode == "empty":
        data["receipts"] = []
    else:
        data["receipts"][0]["counter_kind"] = "cumulative"
    assert not any("supplied_total" in key for key in attributes(observability_preview(data)))


def test_does_not_invent_execution_time_or_trace():
    log = observability_preview(packet())["otlp"]["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]
    assert int(log["observedTimeUnixNano"]) > 0
    assert not {"timeUnixNano", "traceId", "spanId"} & log.keys()


def test_duplicate_receipt_not_added_again():
    data = packet()
    data["receipts"] *= 2
    attrs = attributes(observability_preview(data))
    assert attrs["pm_bg.duplicate_count"] == {"intValue": "1"}
    assert attrs["pm_bg.supplied_total.input_tokens"] == {"intValue": "100"}


def test_cli_preview(tmp_path, capsys):
    from premium_model_budget_governor.cli import main
    path = tmp_path / "input.json"
    path.write_text(json.dumps(packet()), encoding="utf-8")
    assert main(["observability-preview", "--input", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["result"]["format"] == "otlp-json-logs"


def test_optional_official_protobuf_parser():
    logs = pytest.importorskip("opentelemetry.proto.collector.logs.v1.logs_service_pb2")
    from google.protobuf.json_format import ParseDict
    request = ParseDict(observability_preview(packet())["otlp"], logs.ExportLogsServiceRequest())
    restored = logs.ExportLogsServiceRequest.FromString(request.SerializeToString())
    assert len(restored.resource_logs) == 1
    record = restored.resource_logs[0].scope_logs[0].log_records[0]
    assert record.observed_time_unix_nano > 0
    assert not record.trace_id and not record.span_id and record.time_unix_nano == 0
