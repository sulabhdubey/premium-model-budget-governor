# Local Observation Management

Local development feature. Usage can preview a receipt packet of up to 60 KB,
then save it after explicit approval. The server recomputes the normalized report
and checks its fingerprint against the preview before saving. A changed packet
needs a new preview. Repeated saves with the same identity/content are idempotent.

The Workbench uses only `observations.sqlite3` in its configured data directory.
Browser requests cannot choose a database path. Up to the newest 100 observation
summaries are shown, with truncation disclosed. Snapshots can overlap and are not
summed into a fictitious total. No automatic collection starts from opening Usage.

## Preview And Cleanup

Settings accepts a local cutoff date. Preview selects observations recorded before
local midnight on that date, and lists their identifiers without deleting them.
Approval applies only to that exact journal state and selection. Changed data or
a modified plan requires another preview. CLI equivalents are:

```text
pm-bg observation-retention --journal <observations.sqlite3> --before <timezone-aware-ISO-time>
pm-bg observation-retention --journal <observations.sqlite3> --plan <preview-result.json> --approve
```

For CLI application, the plan file contains the preview's result object, not the
CLI's outer `ok/result` wrapper. No deletion occurs merely by creating a preview.

The operation creates a unique SQLite backup beside the journal, checks its
integrity and observation contents, obtains a write transaction, and confirms
the live rows still equal the verified backup before deleting selected rows.
A race or failed check stops deletion; a backup already created is retained.
No backup is needed for an empty selection. Foreign databases and unknown schema
versions are rejected. More than 10,000 observations requires a future bounded
maintenance path; the tool does not silently delete a partial selection.

Backup recovery was tested by reading the original observations from the backup.
Restoring over a live journal is deliberately not automatic: stop its writers,
verify the selected backup and preserve the current file before replacement.

## Boundaries

This affects only the dedicated observation journal, not budget leases, task
history, project files, downloaded exports or project-memory banks. It is manual
retention, not a scheduled cleanup. The retained backup still contains deleted
records, and SQLite pages may retain bytes. This is not secure erasure. Backups
inherit local filesystem permissions and are not encrypted or uploaded.

Tests include stale plans, explicit boolean approval, concurrent writes between
backup and deletion, foreign schema protection, backup read-back and the rendered
disposable-journal flow. They do not establish privacy against a compromised local
account or independent human usability.
