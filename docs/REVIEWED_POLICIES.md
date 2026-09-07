# Reviewed Empirical Routing Preferences

Status: implemented mechanism, **no production policy activated**. This is a
scoped empirical preference table, not model-weight training or a proven optimal
router. Proposals do not activate themselves.

## Review Gate

A proposal contains one candidate/baseline comparison, one rubric version and one
measured cost basis. It uses the existing matched calibration validator, including
duplicate-task and calibration/holdout leakage checks. Both splits must have:

- at least 20 declared independent tasks;
- no observed candidate quality regressions against passing baselines;
- at least 90% candidate acceptance;
- lower candidate mean cost than the baseline.

These are conservative product review thresholds, **not** a power calculation,
statistical significance test or guarantee of future savings. Independence,
representativeness, matching and provenance remain caller assertions that a human
reviewer must inspect. Manufacturing task IDs does not manufacture real evidence.

An eligible proposal still needs explicit approval. `approved: true` is the
caller's authorization assertion, not independent proof that a human reviewed it.
Agents must not set it without the user's policy-specific approval.

## Immutable Proposal and Versioned Change

Proposal contents are checksummed, including sanitized pair fields, scope,
calibration output, creation time and 30-day expiry. Activation and rollback append
history events. Updates require `expected_active`, which prevents a stale approval
from silently replacing a newer preference. Rollback can restore a previously
active, still-eligible proposal in the same scope, or `null` for ordinary routing.

Checksums detect accidental changes, not a malicious local user who can rewrite
the database and recompute hashes. The store is not an attestation service.

## Runtime Scope

The workbench supplies an exact scope:

- project identity hashed from its resolved normalized path;
- task type selected by the user, not an invented automatic classification;
- Astra Preferred or Economy mode;
- a fingerprint of declared host catalog, reasoning effort, capabilities,
  context/output allowances and configured rates.

A profile change makes the old preference inactive for that preview. The
fingerprint does not capture every hidden host instruction or provider change;
expiry and periodic reevaluation remain necessary. It is not context attestation.

Application never overrides an existing budget, evidence, project or capability
block. Astra Preferred cannot select a candidate without Astra participation.
Absent, expired, corrupted, out-of-scope or infeasible preferences leave the
ordinary planner in control. No additional model call is needed to consult a policy.

## Advanced CLI

`pm-bg policy --input ACTION.json --store PATH` supports:

```json
{"action":"status","scope":{"project":"PROJECT_FINGERPRINT","family":"review","host_profile":"HOST_FINGERPRINT","mode":"astra_preferred"}}
```

For a proposal, use `action: "propose"` with the preview's `policy_scope` as
`scope` and the measured matched `pairs`. Review the returned report and evidence
before activation. The workbench store is `policies.sqlite3` under its data directory.

```json
{"action":"activate","id":"REVIEWED_PROPOSAL_ID","approved":true,"expected_active":null}
```

To restore ordinary routing, provide the exact scope and current active ID:

```json
{"action":"rollback","scope":{"project":"PROJECT_FINGERPRINT","family":"review","host_profile":"HOST_FINGERPRINT","mode":"astra_preferred"},"target_id":null,"approved":true,"expected_active":"CURRENT_PROPOSAL_ID"}
```

Policy administration is currently an advanced CLI workflow. The everyday task
screen does not require JSON, but a nontechnical policy-review interface is not
claimed. No MCP tool or scheduler automatically promotes a proposal.

## Existing Evidence

`python scripts/audit_policy_evidence.py` evaluates the published v0.3 pilot
without model calls or activation. All three comparisons remain ineligible:
the batch supplies one calibration task and no independent holdout. See the
[audit](../artifacts/reviewed-policy/existing-evidence-audit.json).

Unit fixtures test eligible and rejected proposals, explicit approvals, concurrent
version checks, rollback, expiry, checksum failure, scope changes and runtime
application. Synthetic passing fixtures are not evidence that a real policy is
ready. Representative independent work and reviewer validation remain open.
