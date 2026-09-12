"""Convert the known App Server runner's final receipt to external accounting."""
from .long_work import reconcile_work


def host_observation(receipt, work_unit):
    identity = receipt.get("host_identity") or {}
    if (receipt.get("status") != "completed" or identity.get("config_stable") is not True
            or identity.get("scope") != "one_turn_in_new_ephemeral_thread"
            or receipt.get("requested_model") != receipt.get("host_configured_model")
            or identity.get("context_requested") != receipt.get("context_profile")):
        raise ValueError("exclusive stable host receipt required")
    row = {"receipt_id": receipt["call_id"], "work_unit_id": work_unit,
           "source_id": identity["source_id"], "model": receipt["host_configured_model"],
           "counter_kind": "final", "scope": "exclusive", "usage": receipt["usage"],
           "rate_contract": receipt["rate_snapshot"]}
    checked = reconcile_work({"work_units": [work_unit], "receipts": [row]})
    if checked["totals"] is None or checked["estimated_credits"] is None:
        raise ValueError("unreconciled host usage")
    return row
