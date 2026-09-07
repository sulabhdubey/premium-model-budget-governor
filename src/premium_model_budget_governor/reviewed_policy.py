"""Evidence-gated workflow preferences. Every activation and rollback is explicit."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import time

from .calibration import calibrate

PAIR_KEYS = ("task_id", "family", "snapshot", "rubric", "candidate", "baseline", "split", "cost_basis",
             "matched", "complete", "candidate_pass", "baseline_pass", "candidate_credits", "baseline_credits")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def validate_scope(scope):
    if not isinstance(scope, dict) or set(scope) != {"project", "family", "host_profile", "mode"}:
        raise ValueError("scope requires project, family, host_profile and mode")
    if any(not isinstance(v, str) or not v.strip() or len(v) > 128 for v in scope.values()):
        raise ValueError("scope labels must be non-empty strings of at most 128 characters")
    if scope["mode"] not in {"astra_preferred", "economy", "adaptive"}:
        raise ValueError("unsupported scope mode")
    return deepcopy(scope)


class PolicyStore:
    def __init__(self, path: Path):
        self.path = path

    def _write(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=15)
        try:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS proposals (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS changes (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL, policy_id TEXT,
                    previous_id TEXT, action TEXT NOT NULL, changed_at REAL NOT NULL);
            """)
        except Exception:
            db.close()
            raise
        return db

    @staticmethod
    def _active(db, key):
        row = db.execute("SELECT policy_id FROM changes WHERE scope=? ORDER BY seq DESC LIMIT 1", (key,)).fetchone()
        return row[0] if row else None

    @staticmethod
    def _proposal(db, identifier):
        if not isinstance(identifier, str):
            raise ValueError("proposal ID required")
        row = db.execute("SELECT payload FROM proposals WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise ValueError("proposal not found")
        payload = json.loads(row[0])
        if fingerprint(payload) != identifier:
            raise ValueError("proposal integrity check failed")
        return {"id": identifier, **payload}

    def propose(self, scope, pairs):
        scope = validate_scope(scope)
        if not isinstance(pairs, list) or len(pairs) > 5000 or any(not isinstance(row, dict) for row in pairs):
            raise ValueError("pairs must contain at most 5000 matched task objects")
        rows = [{key: row.get(key) for key in PAIR_KEYS} for row in pairs]
        report = calibrate({"pairs": rows})
        if any(row["family"] != scope["family"] for row in rows):
            raise ValueError("evidence family differs from policy scope")
        labels = {(row["candidate"], row["baseline"], row["cost_basis"], row["rubric"]) for row in rows}
        if len(labels) > 1:
            raise ValueError("one candidate/baseline, cost basis and rubric per policy proposal")
        groups = report["groups"]
        eligible = len(groups) == 2 and {g["split"] for g in groups} == {"calibration", "holdout"}
        eligible = eligible and all(g["independent_tasks"] >= 20 and g["quality_regressions"] == 0
                                   and g["candidate_passes"] / g["independent_tasks"] >= .9
                                   and g["candidate_mean_credits"] < g["baseline_mean_credits"] for g in groups)
        now = time.time()
        payload = {"schema_version": 1, "scope": scope, "pairs": rows, "report": report,
                   "candidate": rows[0]["candidate"] if rows else None,
                   "evidence_fingerprint": fingerprint(rows), "created_at": now,
                   "expires_at": now + 30 * 86400, "eligible_for_review": bool(eligible),
                   "automatic_promotion": False,
                   "gate": "20 tasks per split, no observed quality regression, >=90% candidate pass, lower mean cost",
                   "limitations": "Review thresholds are not a statistical power guarantee. Matching, provenance and scope are caller assertions."}
        identifier = fingerprint(payload)
        db = self._write()
        try:
            with db:
                db.execute("INSERT INTO proposals VALUES (?,?)", (identifier, canonical(payload)))
        finally:
            db.close()
        return {"id": identifier, **payload}

    def status(self, scope):
        scope = validate_scope(scope)
        result = {"scope": scope, "active_id": None, "usable": False, "proposal": None, "events": []}
        if not self.path.exists():
            return result
        db = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            key = fingerprint(scope)
            identifier = self._active(db, key)
            result["active_id"] = identifier
            if identifier:
                proposal = self._proposal(db, identifier)
                result["proposal"] = proposal
                result["usable"] = proposal["eligible_for_review"] and proposal["expires_at"] > time.time()
            result["events"] = [dict(zip(("version", "policy_id", "previous_id", "action", "changed_at"), row))
                                for row in db.execute("SELECT seq,policy_id,previous_id,action,changed_at FROM changes WHERE scope=? ORDER BY seq", (key,))]
            return result
        finally:
            db.close()

    def activate(self, identifier, *, approved, expected_active):
        if approved is not True:
            raise ValueError("explicit policy approval required")
        db = self._write()
        try:
            proposal = self._proposal(db, identifier)
        finally:
            db.close()
        return self._change(proposal["scope"], identifier, "activate", expected_active)

    def rollback(self, scope, *, target_id, approved, expected_active):
        if approved is not True:
            raise ValueError("explicit rollback approval required")
        return self._change(validate_scope(scope), target_id, "rollback", expected_active)

    def _change(self, scope, identifier, action, expected):
        db = self._write()
        try:
            with db:
                db.execute("BEGIN IMMEDIATE")
                key = fingerprint(scope)
                current = self._active(db, key)
                if current != expected:
                    raise ValueError("active policy changed; review the current version first")
                if identifier is not None:
                    proposal = self._proposal(db, identifier)
                    if proposal["scope"] != scope or not proposal["eligible_for_review"] or proposal["expires_at"] <= time.time():
                        raise ValueError("proposal is out of scope, expired or ineligible")
                    if action == "rollback" and not db.execute("SELECT 1 FROM changes WHERE scope=? AND policy_id=?", (key, identifier)).fetchone():
                        raise ValueError("rollback target was never active in this scope")
                db.execute("INSERT INTO changes(scope,policy_id,previous_id,action,changed_at) VALUES (?,?,?,?,?)",
                           (key, identifier, current, action, time.time()))
        finally:
            db.close()
        return self.status(scope)

    def apply(self, plan, scope):
        result = deepcopy(plan)
        try:
            status = self.status(scope)
        except (ValueError, sqlite3.Error):
            result["policy_application"] = {"status": "integrity_or_store_error; default preserved"}
            return result
        result["policy_application"] = {"status": "inactive"}
        if not status["usable"] or scope["mode"] != plan["mode"]:
            return result
        identifier = status["proposal"]["candidate"]
        candidate = next((c for c in plan["candidates"] if c["id"] == identifier and not c["blocks"]), None)
        if candidate is None or (plan["mode"] == "astra_preferred" and not candidate["astra_roles"]):
            result["policy_application"] = {"status": "candidate_not_feasible", "policy_id": status["active_id"]}
            return result
        result["selected"] = deepcopy(candidate)
        result["decision"] = "planned"
        result["astra_participation"] = "planned" if candidate["astra_roles"] else "not_requested"
        result["policy_application"] = {"status": "applied", "policy_id": status["active_id"],
                                        "basis": "manually_approved_empirical_preference; not a quality guarantee"}
        return result
