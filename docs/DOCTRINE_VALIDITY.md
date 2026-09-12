# Remember When Advice Stops Applying

The doctrine ledger is a local inventory, not model-weight distillation or an
automatically learned router. Repeated principles are not necessarily correct.

An ordinary `pm-bg doctrine --ledger <file>` reports `inventory_only`. It must not
be interpreted as current applicable guidance. To request a filtered view:

```text
pm-bg doctrine --ledger <file> --context <current-context.json>
```

The explicit context contains exactly these fields:

```json
{
  "scope_id": "opaque-project",
  "source_snapshot": "verified-source-version",
  "policy_version": "reviewed-policy-version",
  "permissions": ["read"]
}
```

New entries can include `validity` with those same fields and a timezone-aware
`valid_until` timestamp. Their `outcome` must be `passed` to enter the applicable
summary. Append with the existing `--input` option, not together with `--context`.
Unrecognized binding fields are rejected rather than silently ignored. Changes to
dependencies or requirements must change the bound source or policy version.

All four bindings must match. Permission ordering is immaterial; any change to the
permission set invalidates reuse. Expired, legacy unbound and unsuccessful records
are excluded with counts. Existing files are not migrated or rewritten. Even a
matching record has `validity_verified: false`: the caller supplies bindings and
outcomes, and must verify live sources and authorization before trusting the advice.
Expiry is a deadline, not proof that information remains true until then.

## Privacy And Limits

New entries validate bounded string fields and scan allowed fields before appending.
The explicit raw-prompt field is omitted, but free text can still contain prompts,
private material or undetected secrets. Consequently `prompt_free` is false. Old
entries are validated and scanned before being included in a summary, without
changing the file. Scanner findings are not echoed in the rejection response.
These heuristic checks are not a malware, privacy or prompt-injection guarantee.

Inventory reads are bounded to 4 MiB and records to 64 KiB. Malformed lines are
counted, not silently treated as valid; files beyond the bound require reviewed
maintenance. This JSONL ledger remains a single-writer local facility, not a
transactional multi-user database. It is not encrypted and has no automatic backup,
retention, migration or publication. Do not point it at shared Rta-Smriti storage.

The changed output removes the old blanket prompt-free assertion; consumers should
use the explicit mode, exclusion counts and uncertainty fields. Tests establish
filtering and validation behavior, not the truth or benefit of stored principles.
