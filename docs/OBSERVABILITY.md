# Optional Local Observability Preview

```text
pm-bg observability-preview --input examples/long-work.json
```

This opt-in CLI command reconciles supplied receipts and returns a content-excluding
OpenTelemetry OTLP JSON log request under `result.otlp`. The outer CLI/result wrapper
is Governor metadata, not an OTLP request: consumers must select `result.otlp`.
No endpoint, credentials, SDK, cloud account or network delivery is configured.
The default installation gains no dependency. Review the preview before sharing.

The export scope version is `1`. It uses custom `pm_bg.*` attributes rather than
pretending a supplied report is a live model span or GenAI token histogram.
One log describes reconciliation of the supplied receipt set. It includes coverage,
receipt/duplicate/missing counts and explicit missing-cache assumption counts.
Only complete supplied coverage gets token totals. Assumed cache zeros are omitted;
measured cache counts remain input subsets. No price estimate or bill is exported.

Observation time is preview creation time, not execution time. Execution timestamps,
trace/span IDs, models, source/receipt/work IDs, prompts, filenames, hashes and
caller-defined strings are excluded. Numeric patterns and timing can still identify
work; exclusion is not anonymity or a substitute for consent. Invalid receipts fail
before export. Each request is a fresh preview: repeated previews may cover the same
work and must not be summed as independent usage. No cross-export deduplication or
provider attestation is claimed.

## Compatibility And Boundaries

The adapter follows the OTLP JSON encoding and log data model, with decimal strings
for int64 values. Tests cover privacy allowlisting, missing and overlapping work,
duplicate receipts, cache subsets, timestamps and CLI operation. An optional test
parses the actual request with the official `opentelemetry-proto` package and round
trips its binary form. That is a protocol check, not a live Collector/backend test.

Direct HTTP/gRPC delivery, retries, persistent queues, endpoint authentication,
dashboard vendor adapters and background collection are deferred. They need their
own consent, data-retention/security design and end-to-end receiving-system tests.
They are not necessary for local Governor use, and this preview does not control
other hosts or lower model consumption by itself.

Primary references reviewed for this implementation:
- [OTLP specification](https://opentelemetry.io/docs/specs/otlp/)
- [Logs data model](https://opentelemetry.io/docs/specs/otel/logs/data-model/)
- [OTLP file encoding](https://opentelemetry.io/docs/specs/otel/protocol/file-exporter/)

Protocol compatibility does not constitute bundled third-party code. The official
protobuf package is used only in an isolated development check; distribution of a
future SDK adapter requires a separate dependency/license review.
