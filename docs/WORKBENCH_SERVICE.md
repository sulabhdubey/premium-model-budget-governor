# Local Workbench Service

Status: implemented service layer, now connected to the local HTTP/UI preview.
See WORKBENCH.md for the current transport and rendered workflow; not a finished product.
No additional model calls were used to test this layer. Unit tests use injected
host probes/executors; they are not new real-task Astra experiments.

## Contract

`Workbench(projects, data)` requires an explicit map of project IDs to existing
local directories. It does not search the disk, change Codex configuration, or
automatically register private projects. The upcoming authenticated local server
will own registration, browser sessions and execution progress.

- `preview(request)` accepts a task, project ID, mode, budget, optional evidence
  and images, reasoning effort and required capabilities. It probes the host catalog
  without a model turn. It builds direct candidates with the existing Python planner.
- `execute(preview_id, approved=True)` executes the stored preview, not client-supplied
  model/cost/prompt overrides. Preview expiry is ten minutes. Replays are rejected.
- `history()` reads the most recent 100 prompt-free receipts and recorded states.
  Answers are returned to the caller but not persisted in the receipt database.

Astra Preferred requires Astra. Economy compares Sol and Astra direct candidates.
Candidate quality is explicitly unmeasured. Prepared/review strategies and learned
policy approval remain separate unfinished work, not hidden behind this direct path.
Unknown weekly capacity requires approval; a conditionally feasible preview is
never authorization to execute.

## Evidence and Privacy

Text evidence must be UTF-8, within the selected project, at most eight files,
80 KB each and 240 KB combined. Private credential/configuration paths are excluded.
Pattern failures return generic messages without excerpts. Images must have a
supported PNG/JPEG/WebP signature, at most four files, 20 MB each and 24 MB total.
These bounds are explicit rejection conditions, not silent truncation.

Paths and hashes are rechecked before admission. Approved image bytes are copied
to a temporary local staging directory for dispatch and removed after the executor
returns. Text excerpts are bound in the in-memory prompt. This does not freeze
the entire repository; tools may read subsequent project changes.

Up to eight previews remain in memory until expiry or execution. Prompts, evidence
and answers are not written into the usage ledger or history database. Temporary
image staging contains actual selected content; abrupt process termination may
leave staging files for later cleanup. Do not claim forensic erasure or encrypted
storage. The future server must protect access and implement crash cleanup.

Image signatures are not full decoding or malware scanning. Pattern checks cannot
guarantee injection safety. Read-only applies to the filesystem sandbox, not an
automatic revocation of inherited connector permissions. Write/Desktop-only tasks
are rejected as unsupported, not downgraded to equivalent read-only work.

## Accounting

The initial default uses a provisional 32,000-token host allowance, a rough text
estimate, a 4,000-token allowance per image and 2,000 output tokens. These are
visible assumptions, not observations, provider bounds or tokenizer counts. No
cache savings are assumed. Ten percent of the entered task budget is contingency.
The service must not label these defaults as calibrated.

An atomic SQLite admission prevents simultaneous dispatch across service instances
sharing the same data directory. The existing runner reserves before model calls.
Completed results must contain valid counters agreeing with the ledger. Exceptions,
invalid receipts and incomplete turns produce unknown usage; reservations are never
refunded automatically. Further runs stop pending reconciliation.

## Remaining Integration Work

- HTTP transport, origin/Host checks, request/connection limits and CSP are implemented/tested.
- Task entry, file browsing, preview/consent, progress, stop/reconnect and receipt
  display are implemented/tested with the scopes documented in WORKBENCH.md.
- Native project registration and diagnostic export without private content remain.
- OS-backed crash ownership/recovery is implemented. A persisted `running` row is
  an admission record, not proof that a process remains alive. Recovery retains
  unknown usage; it neither retries nor claims provider execution stopped.
- Reconciliation controls using real receipts; a blocked unknown run currently
  requires operator investigation. Do not offer a blind reset button.
- Real host end-to-end and browser validation, followed by human onboarding trials.
