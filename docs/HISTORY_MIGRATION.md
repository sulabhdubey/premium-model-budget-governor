# Privacy History Migration

The owner approved rewriting two branches and eight tags to anonymize unnecessary
private-project references. Source-level checks pass in the sanitized history.
The affected rc.4 wheel and checksum manifest were withdrawn. Use the separately
versioned rc.5 candidate; it is not a stable release.

## Existing Clones

Do not merge an old clone back into the repository: that can reintroduce removed
history. Preserve your local changes privately, then clone into a new directory
and reapply only reviewed changes. Do not publish old recovery bundles or raw
history inventories. Collaborators must coordinate before pushing old branches.

Existing installed runtimes and external usage ledgers are not automatically
migrated or deleted by a Git history rewrite. Follow INSTALLATION.md to install
the new candidate into a new owned runtime; preserve your data and configuration.

## Limits

The old draft PR was closed, not erased. GitHub-managed cached commits and PR refs,
forks and third-party clones may retain old copies. GitHub Support decides whether
a removal request qualifies; rewriting public refs is not proof of total erasure.
See [GitHub's guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

No credential exposure was established by the audit: generic-token findings were
reviewed as token-generation source code. The privacy correction concerns project
attribution and internal context, not a claim of stolen account credentials.
