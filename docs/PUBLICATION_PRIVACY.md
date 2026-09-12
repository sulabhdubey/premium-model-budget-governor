# Publication Privacy

Public proof needs aggregate outcomes, not private-project names, source,
architecture, operational state, participant records or account information.
An owner-approved product release is not permission to expose unrelated projects.

## Preflight

Use an installed development checkout to inspect explicit text files or packages:

```sh
python scripts/check_publication.py README.md docs/FIELD_TRIAL_2026_09_07.md --terms-file /private/location/terms.json --report /private/location/report.json
python scripts/check_publication.py /path/to/candidate.whl --terms-file /private/location/terms.json
python scripts/check_publication.py README.md --docs-root docs
```

The private terms file is a JSON list of phrases chosen by the owner. Keep it
outside Git. Do not commit the identities as a public denylist. Reports contain
opaque input/entry positions and rule names, not matched text, terms or paths.
Input hashes bind the inspected bytes; a changed artifact must be checked again.
The optional docs-root includes Markdown descendants, sorted for deterministic
report positions. CI uses this to cover new guides without maintaining a fixed
document list. This does not include images, HTML, Git history or ignored private
outputs; those remain separate review inputs. The existing inspection bounds apply.

The checker inspects bounded UTF-8 text, decoded JSON strings and ZIP/wheel entry
contents without extracting or executing them. It checks known secret patterns,
personal home paths and supplied private terms. Binary, unreadable, encrypted,
nested or oversized material requires manual review; no silent passing skip.
Human reviewers must also inspect screenshots, PDFs, video, sensitive facts,
package README metadata, release notes, PR text and the deployed site.

`no_pattern_findings` is not privacy certification or publication authorization.
The checker is not an antivirus, a semantic confidentiality detector or a remote
history scanner. A reviewed source-code false positive remains recorded, not a
reason to weaken scanning globally.

## Historical Exposure

Current documentation anonymization does not erase old tagged files, package
metadata, downloaded copies, Git history, PR references or cached pages. Preserve
a private backup and inventory the affected references before any rewrite.
Obtain explicit approval for the exact destructive changes. Use a separate clone,
verify sanitized results and coordinate ref changes and artifact replacements.
Do not silently overwrite a published binary under an unchanged version/hash.

Follow [GitHub's removal guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
Changed commit IDs and collaborator coordination are expected. GitHub Support
decides whether cached-data removal qualifies; copies in third-party clones
cannot be recalled. Never claim total erasure merely because a force push passed.

## Current Boundary

Current reporting has been anonymized. Following explicit owner approval, two
branches and eight tags were rewritten from a verified private backup. Rewritten
snapshots passed the supplied private-term check. The affected rc.4 wheel and
its checksum manifest were withdrawn; rc.5 is the separately versioned successor.
The old PR was closed, not erased. GitHub-managed cached/PR references and copies
in other people's clones remain outside this local cleanup's verified scope.
No total erasure or secret compromise is inferred from a pattern match. Stable
promotion and broad outreach remain gated by the acceptance register.
