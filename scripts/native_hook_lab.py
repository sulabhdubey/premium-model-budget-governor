"""Isolated native hook lab. No account credentials or hook-trust bypass."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import tomllib
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from premium_model_budget_governor.app_server import AppServer
from premium_model_budget_governor.leases import budget_action

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "build/native-hook-lab"
HOME = LAB / "home"
PROJECT = LAB / "project"


def prepare():
    HOME.mkdir(parents=True, exist_ok=True)
    PROJECT.mkdir(parents=True, exist_ok=True)
    command = subprocess.list2cmdline([sys.executable, "-m", "premium_model_budget_governor.prompt_gate", "--grant", str(LAB/"grant.json")])
    hook = {"description":"Isolated governor lab: missing grant must block; no paid provider.",
            "hooks":{"UserPromptSubmit":[{"hooks":[{"type":"command","command":command,"timeout":5,"statusMessage":"Checking isolated governor grant"}]}]}}
    config = '''model = "fixture-no-model"
model_provider = "local_fixture"
approval_policy = "never"
sandbox_mode = "read-only"
[model_providers.local_fixture]
name = "Offline hook fixture"
base_url = "http://127.0.0.1:18767/v1"
wire_api = "responses"
requires_openai_auth = false
request_max_retries = 0
stream_max_retries = 0
'''
    for path, text in [(HOME/"config.toml",config),(HOME/"hooks.json",json.dumps(hook,indent=2))]:
        if not path.exists():
            path.write_text(text,encoding="utf-8")
    return {"lab":str(LAB),"hook_command":command,"uses_account_credentials":False,"trust_bypassed":False}


def environment():
    env = dict(os.environ)
    env["CODEX_HOME"] = str(HOME)
    for key in ("OPENAI_API_KEY","CODEX_API_KEY","CHATGPT_API_KEY","OPENAI_BASE_URL", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        env.pop(key,None)
    env["NO_PROXY"] = "127.0.0.1,localhost"
    return env


def native_tests(cases):
    config = tomllib.loads((HOME/"config.toml").read_text())
    provider = config["model_providers"]["local_fixture"]
    if config["model_provider"] != "local_fixture" or provider["base_url"] != "http://127.0.0.1:18767/v1" or provider["requires_openai_auth"] is not False:
        raise ValueError("Lab must use its credential-free loopback fixture")
    # This process owns its environment; the parent user's configuration is untouched.
    isolated_env = environment()
    os.environ.clear()
    os.environ.update(isolated_env)
    requests = []
    class Rejector(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append(self.path)
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error":{"message":"Offline fixture refuses model generation"}}')
        def log_message(self,*args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1",18767),Rejector)
    worker = Thread(target=server.serve_forever,daemon=True)
    worker.start()
    results = []
    try:
        for case in cases:
            (LAB/"control.json").write_text(json.dumps({"mode":case if case in ("crash","timeout") else "normal"}),encoding="utf-8")
            before = len(requests)
            with AppServer(PROJECT,30) as client:
                inventory = client.request("hooks/list",{"cwds":[str(PROJECT)]})
                thread = client.request("thread/start",{"cwd":str(PROJECT),"model":"fixture-no-model","sandbox":"read-only","approvalPolicy":"never","ephemeral":True})
                session = thread["thread"]["id"]
                prompt = "Offline governor grant test: " + case
                ledger = LAB/(case+".sqlite3")
                if case in ("missing", "disabled"):
                    grant = {}
                else:
                    task = "native-"+case+"-"+str(time.time_ns())
                    budget_action({"action":"open","task_id":task,"budget_credits":10},ledger)
                    budget_action({"action":"reserve","task_id":task,"lease_id":"call","model":"gpt-6-astra","estimated_credits":5,"ttl_seconds":1 if case=="expired" else 60},ledger)
                    grant = {"session_id":session,"cwd":str(PROJECT),"prompt_sha256":sha256(prompt.encode()).hexdigest(),"ledger":str(ledger),"task_id":task,"lease_id":"call"}
                    if case == "expired":
                        time.sleep(1.1)
                (LAB/"grant.json").write_text(json.dumps(grant),encoding="utf-8")
                events = []
                try:
                    client.request("turn/start",{"threadId":session,"input":[{"type":"text","text":prompt}]})
                    end = time.monotonic()+15
                    while time.monotonic()<end:
                        message = client.event(end-time.monotonic())
                        method = message.get("method","")
                        if "hook" in method.lower() or method in ("turn/completed","error"):
                            events.append({"method":method,"params":message.get("params")})
                        if method == "turn/completed":
                            break
                except (ValueError,TimeoutError) as exc:
                    events.append({"client_error_type":type(exc).__name__})
                # Native diagnostics stay in ignored build/, never publish raw host context.
                (LAB/(case+"-"+str(time.time_ns())+"-native.json")).write_text(json.dumps({"inventory":inventory,"events":events},indent=2),encoding="utf-8")
            result = {"case":case,"fixture_requests":len(requests)-before,"event_methods":[e.get("method") for e in events],
                      "trust_statuses":[h["trustStatus"] for row in inventory["data"] for h in row["hooks"]],
                      "hook_enabled":[h["enabled"] for row in inventory["data"] for h in row["hooks"]],
                      "hook_statuses":[e["params"]["run"]["status"] for e in events if e.get("method")=="hook/completed"]}
            results.append(result)
            history_path = LAB/"observations.json"
            history = json.loads(history_path.read_text()) if history_path.exists() else []
            history.append(result)
            history_path.write_text(json.dumps(history,indent=2),encoding="utf-8")
            (LAB/"results.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
            print(json.dumps(result),flush=True)
        (LAB/"results.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action",choices=["prepare","review","test","prepare-faults"])
    parser.add_argument("--case", choices=["missing","expired","valid","crash","timeout","disabled"])
    args = parser.parse_args()
    info = prepare()
    if args.action == "prepare-faults":
        hook = json.loads((HOME/"hooks.json").read_text())
        hook["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"] = subprocess.list2cmdline([sys.executable,str(ROOT/"scripts/native_hook_fixture.py"),str(LAB)])
        (HOME/"hooks.json").write_text(json.dumps(hook,indent=2),encoding="utf-8")
        (LAB/"control.json").write_text(json.dumps({"mode":"normal"}),encoding="utf-8")
        print("Changed lab hook needs native review; no trust state modified.")
        return
    if args.action == "prepare":
        print(json.dumps(info,indent=2))
        return
    if args.action == "test":
        native_tests([args.case] if args.case else ["missing","expired","valid"])
        return
    executable = shutil.which("codex.exe") or shutil.which("codex")
    if not executable:
        raise ValueError("Codex is unavailable")
    subprocess.run([executable,"--no-alt-screen","--cd",str(PROJECT)],env=environment(),cwd=PROJECT,check=False)


if __name__ == "__main__":
    main()
