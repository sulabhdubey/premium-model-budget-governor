# Local Service Boundary Review

Scope: current local workbench HTTP parsing, browser rendering, selected-file
reads and adjacent resource handling. This is a bounded Codex review, not an
independent penetration test or a full-product security certification.

## Fixed Findings

### 1. Ambiguous JSON Fields (Moderate)

Authenticated requests previously accepted duplicate keys using last-value-wins
semantics. Conflicting task or approval fields could therefore be interpreted
differently by a caller and the server. There was no demonstrated unauthenticated
bypass. The parser now rejects duplicate keys at every object depth before the
application sees the request.

Evidence: `src/premium_model_budget_governor/local_server.py:20` and its
`object_pairs_hook`; duplicate-key HTTP tests in `tests/test_local_server.py`.

### 2. Unbounded Header Integer Conversion (Low)

Content-Length was converted before bounding digit count, and Unicode isdigit
accepted characters that integer conversion rejects. Malformed authenticated
headers could terminate the handler unexpectedly. The service now requires ASCII
decimal digits and bounds the string before conversion. Rejection-body draining
also bounds conversion and never trusts unframed trailing content.

Evidence: `src/premium_model_budget_governor/local_server.py:229`; tests cover
5000 digits, non-ASCII digits, signed and negative values. Header-only cases
receive 400/413. Unframed trailing bytes may cause a Windows reset/abort instead;
tests verify no application handler call and subsequent service availability.

## Confirmed Boundaries

- Authenticated APIs check a random bearer token, exact Host and POST Origin
  (`local_server.py:169`). Existing HTTP tests exercise these checks.
- Selected-file reads are bounded at the read operation, not only by a prior
  size stat (`workbench.py:206`). Aggregate and per-file limits remain enforced.
- Project roots are revalidated before host access (`workbench.py:149`). This is
  not a race-proof filesystem sandbox against the same local OS account.
- Browser output uses textContent and created elements. The reviewed file contains
  no innerHTML, eval, browser persistent storage or postMessage sink. CSP is
  delivered by the server. These observations do not prove absence of all XSS.

## Remaining Risks and Release Gates

- Launch-link files now use restricted creation before writing: Windows protected
  current-user-only DACL or POSIX mode 0600, followed by atomic replacement.
  Windows ACL inspection and replacement-safe cleanup tests pass. POSIX private-file
  tests also pass in Ubuntu/WSL; cross-account access trials remain unverified. Keep launch files out of
  shared directories and never publish tokens or the terminal launch output.
- Inherited host connector permissions are not revoked by a read-only filesystem
  sandbox. Do not claim the model can access only the attached excerpts.
- Regex injection/secret scans and image signature checks are incomplete defenses,
  not malware scanning or proof that content is safe.
- Interrupted image staging and orphaned provider work still need broader crash
  investigation. Missing terminal usage cannot be reconciled as zero.
- Reviewed-policy schema-creation failure now closes its connection; an injected
  failure test retains the handle and verifies it is closed before returning.
- This Python standard-library loopback server is not approved for internet
  exposure. Cross-platform qualification and independent review remain open.

No model-quality, budget-savings, or weekly-limit attribution claims follow from
this review. A subsequent locally rebuilt wheel includes these parser changes;
its qualification hashes are recorded under artifacts/onboarding. It is not a
published release, and an independent security review remains outstanding.
