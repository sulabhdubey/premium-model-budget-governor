"""Local OTLP log preview; no exporter endpoint, prompt content or host tracing."""
from time import time_ns

from .long_work import reconcile_work


def _attribute(name, value):
    if type(value) is bool:
        encoded = {"boolValue": value}
    elif type(value) is int:
        if not 0 <= value < 2**63:
            raise ValueError("observation exceeds OTLP signed integer range")
        encoded = {"intValue": str(value)}
    else:
        encoded = {"stringValue": value}
    return {"key": "pm_bg." + name, "value": encoded}


def observability_preview(packet):
    report = reconcile_work(packet)
    values = {
        "export_schema_version": 1,
        "coverage": report["coverage"],
        "receipt_count": report["receipt_count"],
        "duplicate_count": report["duplicate_count"],
        "missing_work_units": len(report["missing_work_units"]),
        "unexpected_work_units": len(report["unexpected_work_units"]),
        "issue_count": len(report["issues"]),
        "savings_proven": False,
        "source_attested": False,
        "review_required": True,
        "observation_kind": "supplied_receipt_reconciliation",
    }
    assumptions = {key: sum(key in (row["usage"].get("counter_assumptions") or [])
                           for row in report["records"].values())
                   for key in ("absent_cached_input_assumed_zero", "absent_cache_write_assumed_zero")}
    values.update(assumptions)
    # Publish no partial or overlapping subtotal as a complete workflow total.
    if report["totals"] is not None:
        for key, count in report["totals"].items():
            if key == "cached_tokens" and assumptions["absent_cached_input_assumed_zero"]:
                continue
            if key == "cache_write_tokens" and assumptions["absent_cache_write_assumed_zero"]:
                continue
            values["supplied_total." + key] = count
    log = {"observedTimeUnixNano": str(time_ns()),
           "body": {"stringValue": "Governor supplied-receipt observation"},
           "attributes": [_attribute(key, value) for key, value in values.items()]}
    otlp = {"resourceLogs": [{"resource": {"attributes": [
        {"key": "service.name", "value": {"stringValue": "premium-model-budget-governor"}}]},
        "scopeLogs": [{"scope": {"name": "pm_bg.observation_export", "version": "1"},
                       "logRecords": [log]}]}]}
    return {"schema_version": 1, "format": "otlp-json-logs", "otlp": otlp,
            "review_required": True, "network_requests": 0, "identifiers_included": False,
            "warning": "Numeric patterns and observation time may identify work. Review before external sharing. "
                       "This is not a bill, execution trace, savings proof or additive time series. "
                       "Repeated previews can describe the same receipts; do not sum them."}
