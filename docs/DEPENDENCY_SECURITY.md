# Dependency Advisory Checks

Core has no runtime dependencies; MCP and document parsing remain optional. Those
extras still need vulnerability and licensing review, including native libraries
bundled into dependency wheels. Fewer packages do not prove a safer product.

CI installs the optional runtime and pinned pip-audit tooling in a separate Ubuntu
job, then checks known advisories. The editable Governor checkout is excluded from
registry lookup; its source security requires separate review. CI also audits the
audit tool's installed dependencies and environment packages, so its scope differs
from a runtime-only inventory. No automatic fixes or vulnerability suppressions are
enabled. Inspect failed or skipped lookups instead of treating them as clean.

The job runs on the existing push/pull-request triggers, not a new background
schedule. A successful past run can become stale. Rerun before release and whenever
dependency resolution changes. CI configuration is not evidence that a remote run
has completed.

For a bounded runtime-only check, first resolve the optional extras for the target
platform with pip's dry-run JSON report. Audit every transitive package at its exact
resolved version using a reviewed requirements list and `--no-deps --disable-pip`.
Compare the lists and preserve report hashes. This checks versions, not package
archive authenticity; include artifact hashes and installed inventory in the final
release qualification. Different Python versions and operating systems can resolve
different dependencies and must not inherit another environment's clean result.

The advisory service receives package names and versions. Do not point it at private
project inventories, credentials or raw source. Keep local resolution reports
private because they can contain filesystem locations and download URLs. Public
evidence should contain only reviewed metadata and an explicit scope/date.

No-known-advisories means no known matches reported by the selected service at that
time. It is not malware detection, an exhaustive security audit, a license opinion
or permission to publish. Scanner availability, skipped packages and unresolved
findings remain release-review inputs.

Reference: [PyPA pip-audit documentation](https://github.com/pypa/pip-audit).

## Installed Qualification Inventory

The isolated installation checker records installed distribution names/versions,
license expressions and classifiers, declared license-file counts and counts of
recorded files ending in `.pyd`, `.so`, `.dll` or `.dylib`. It takes this inventory
before adding regression-test dependencies. Environment bootstrap packages may be
included; this is not solely the application's dependency graph.

Missing license metadata is unknown, not permission to distribute. A file suffix
count does not identify every bundled native component or its provenance. The
inventory does not replace reviewing actual license texts, bundled notices,
artifact hashes, advisory coverage and distribution obligations. Keep raw reports
private until their metadata and other qualification fields have been reviewed.

## Native Distribution Review

A Windows wheel notice review of the tested dependency versions found scope that
top-level metadata alone does not describe. pywin32 312 contains an LGPL-2.1 license
for adodbapi. lxml 6.1.3's LICENSES.txt identifies additional resources and bundled
libraries, including iconv under LGPL-2.1. Do not describe the entire optional
runtime as covered only by Governor's Apache license or by a single package label.
Upstream references: [pywin32 adodbapi license](https://github.com/mhammond/pywin32/blob/main/adodbapi/license.txt)
and [lxml component notices](https://github.com/lxml/lxml/blob/master/LICENSES.txt).

The inspected Governor wheel contains its own package and distribution metadata,
not those dependency wheels or recorded native-library files. Downloading optional
dependencies during installation and distributing a prebundled runtime are distinct
release configurations. Before offering a bundled runtime, review each included
component's actual license, notices, source and redistribution requirements for
that artifact. This engineering inventory is not a legal clearance or a claim that
Governor must change its own license.

The Windows review does not qualify Linux/macOS binaries, all Rust dependencies,
or every embedded library. Archive versions matched the installed inventory, but
the earlier install report did not record dependency archive hashes; it cannot
attest byte-for-byte identity with the separately reviewed downloads. Final bundled
distribution approval remains open. Preserve upstream notices instead of deleting
them to make a scanner report appear simpler.

## Optional Archive Provenance

The isolated installer accepts `--provenance` to retain pip's install report inside
the owned runtime. This requires that runtime's pip to support `--report`; the
installer does not silently upgrade pip or modify another environment to enable it.
The raw report can contain filesystem paths and download URLs. Keep it private;
owned uninstall removes it along with the runtime.

Qualification enables this option and records only distribution name, version and
reported archive SHA256. It verifies that pip's Governor wheel hash matches the
explicit wheel being qualified. Missing dependency hashes remain unknown, not a
match. Bootstrap packages are present in the separate installed inventory but may
not appear in pip's application-install report. Comparing reported hashes to
separately inspected wheels supplies identity evidence, not a signature, trust
decision, malware result or proof that native code behaved safely.

A subsequent Windows qualification captured all 33 application-install archive
hashes without missing values. The six native dependency wheels from the notice
review matched that new report exactly. This closes archive-identity coverage for
that Windows run, not retroactively for earlier installations or other platforms.
