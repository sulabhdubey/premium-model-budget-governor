from collections import deque
import pytest

import premium_model_budget_governor.app_server as app
from premium_model_budget_governor.leases import budget_action


def test_usage_counts_total_not_reasoning_twice():
    raw = dict(inputTokens=10, cachedInputTokens=4, outputTokens=8, reasoningOutputTokens=6, totalTokens=18)
    assert app.parse_usage(raw) == dict(input_tokens=10,cached_tokens=4,output_tokens=8)
    for change in ({"cachedInputTokens":11},{"reasoningOutputTokens":9},{"totalTokens":19},{"inputTokens":True},{"cacheWriteInputTokens":1}):
        with pytest.raises(ValueError):
            app.parse_usage({**raw, **change})


class FakeClient:
    methods = []
    missing_usage = False
    def __init__(self, *args):
        self.events = deque([
            {"method":"thread/tokenUsage/updated", "params":{"threadId":"th", "turnId":"tu", "tokenUsage":{"total":dict(inputTokens=100,cachedInputTokens=0,outputTokens=10,reasoningOutputTokens=3,totalTokens=110)}}},
            {"method":"item/completed", "params":{"threadId":"th", "turnId":"tu", "item":{"type":"agentMessage","text":"ok"}}},
            {"method":"turn/completed", "params":{"threadId":"th", "turn":{"id":"tu","status":"completed"}}}])
        if self.missing_usage:
            self.events.popleft()
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def request(self, method, params):
        self.methods.append(method)
        if method == "model/list":
            return {"data":[{"model":"gpt-6-astra", "inputModalities":["text"],"supportedReasoningEfforts":[{"reasoningEffort":"low"}]}]}
        if method == "thread/start":
            assert params["sandbox"] == "read-only" and params["ephemeral"]
            assert params["approvalPolicy"] == "never"
            return {"model":"gpt-6-astra","thread":{"id":"th"}}
        return {"turn":{"id":"tu"}}
    def event(self, timeout): return self.events.popleft()


def packet(tmp_path):
    return dict(root=str(tmp_path),prompt="test",model="gpt-6-astra",task_id="t",call_id="c",estimated_credits=5,explicit_approval=True)


def test_reserves_before_turn_and_settles_usage(tmp_path, monkeypatch):
    monkeypatch.setattr(app,"AppServer",FakeClient)
    ledger = tmp_path/"ledger.sqlite3"
    budget_action({"action":"open","task_id":"t","budget_credits":10},ledger)
    result = app.execute_app_server(packet(tmp_path), ledger)
    assert result["status"] == "completed" and result["budget"]["reserved_credits"] == 0
    with pytest.raises(ValueError):
        app.execute_app_server(packet(tmp_path), ledger)


def test_insufficient_budget_never_starts_thread(tmp_path, monkeypatch):
    monkeypatch.setattr(app,"AppServer",FakeClient)
    monkeypatch.setattr(FakeClient,"methods",[])
    ledger = tmp_path/"ledger.sqlite3"
    budget_action({"action":"open","task_id":"t","budget_credits":1},ledger)
    with pytest.raises(ValueError, match="exhausted"):
        app.execute_app_server(packet(tmp_path),ledger)
    assert "thread/start" not in FakeClient.methods


def test_missing_usage_is_not_free(tmp_path, monkeypatch):
    monkeypatch.setattr(app,"AppServer",FakeClient)
    monkeypatch.setattr(FakeClient,"missing_usage",True)
    ledger = tmp_path/"ledger.sqlite3"
    budget_action({"action":"open","task_id":"t","budget_credits":10},ledger)
    result = app.execute_app_server(packet(tmp_path), ledger)
    assert result["reservation_retained"]


def test_execution_requires_explicit_approval(tmp_path):
    with pytest.raises(ValueError, match="explicit_approval"):
        app.execute_app_server({**packet(tmp_path),"explicit_approval":False},tmp_path/"unused.db")


def test_unavailable_reasoning_never_starts_thread(tmp_path, monkeypatch):
    monkeypatch.setattr(app,"AppServer",FakeClient)
    monkeypatch.setattr(FakeClient,"methods",[])
    with pytest.raises(ValueError, match="unavailable"):
        app.execute_app_server({**packet(tmp_path),"effort":"ultra"},tmp_path/"unused.db")
    assert FakeClient.methods == ["model/list"]


def test_transport_rejects_unsolicited_approval(tmp_path):
    client = app.AppServer(tmp_path)
    sent = []
    client.send = sent.append
    client.queue.put({"id":99,"method":"item/commandExecution/requestApproval","params":{}})
    with pytest.raises(ValueError, match="interactive"):
        client.receive()
    assert "error" in sent[0] and "result" not in sent[0]


def test_catalog_repeated_cursor_fails():
    class Repeating:
        def request(self,*args):
            return {"data":[],"nextCursor":"same"}
    with pytest.raises(ValueError,match="pagination"):
        app.catalog(Repeating())


@pytest.mark.parametrize("enabled,trust", [(False,"trusted"),(True,"modified"),(True,"untrusted")])
def test_required_hook_rejects_unready_inventory(tmp_path, enabled, trust):
    digest = "sha256:" + "a"*64
    class Inventory:
        def request(self,*args):
            return {"data":[{"hooks":[{"currentHash":digest,"enabled":enabled,"trustStatus":trust}],"errors":[]}]}
    with pytest.raises(ValueError,match="required hook"):
        app.require_hooks(Inventory(), tmp_path, [digest])


def test_required_hook_accepts_trusted_hash_only(tmp_path):
    digest = "sha256:"+"a"*64
    class Inventory:
        def request(self,*args):
            return {"data":[{"hooks":[{"currentHash":digest,"enabled":True,"trustStatus":"trusted"}],"errors":[]}]}
    app.require_hooks(Inventory(),tmp_path,[digest])
    with pytest.raises(ValueError):
        app.require_hooks(Inventory(),tmp_path,["sha256:"+"b"*64])
    with pytest.raises(ValueError):
        app.require_hooks(Inventory(),tmp_path,["invalid"])


def test_published_live_receipt_retains_exact_case_failure():
    import json
    from pathlib import Path
    result = json.loads((Path(__file__).parents[1]/"artifacts/app-server-pilot/image-smoke.json").read_text())
    assert result["status"] == "completed"
    assert result["host_configured_model"] == result["requested_model"] == "gpt-6-astra"
    assert result["budget"]["reserved_credits"] == 0
    answer = json.loads(result["answer"])
    assert answer["sol_cold_input"] == 18 and answer["units"].casefold() == "thousands of tokens"
    assert result["smoke_passed"] is False
