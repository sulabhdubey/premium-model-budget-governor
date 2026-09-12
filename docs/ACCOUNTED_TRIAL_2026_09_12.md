# Accounted Astra Pilot: Fewer Tokens Did Not Always Cost Less

This four-call internal pilot completed on September 12, 2026. All four fixed
answer checks passed. The matched pair used the same prompt, requested Astra
model and low reasoning. Each call ran in a fresh ephemeral App Server thread.

| Phase | Context | Input | Cached subset | Output | Estimated credits |
| --- | --- | ---: | ---: | ---: | ---: |
| Calibration | Inherited | 23,701 | 0 | 17 | 5.94650 |
| Calibration | Focused catalog | 19,404 | 0 | 17 | 4.87225 |
| Matched audit | Focused catalog | 19,443 | 0 | 31 | 4.89950 |
| Matched audit | Inherited | 23,767 | 6,656 | 31 | 4.48290 |

**Matched result:** focused discovery used **18.19% fewer input tokens**, but
**9.29% more estimated credits**. The inherited run received cache hits. This
does not establish that either context strategy is generally cheaper.

## Complete Declared Pipeline

- Admission: 48 estimated credits for four calls, plus a 12-credit reserve.
- Receipt-derived total: **20.20115 estimated credits**; no unresolved reservation.
- Observed totals: **86,315 input**, **6,656 cached** (already included in input),
  **96 output** tokens. No retry or failed answer was omitted.
- External runner time: approximately **40.94 seconds**.
- Preparation and exact-answer verification used local deterministic code, not
  extra models. Their time is inside the pipeline. The local reporting phase
  used no model; later analysis and this document are outside the measured scope.
- Parent-chat research, engineering and fixture design are excluded. This is not
  a receipt for the entire development project or a weekly allowance measurement.

The matched task audits a savings claim: baseline 10 credits versus candidate
execution 7, preparation 2 and failed attempt 3. The expected complete candidate
cost is 12, so the savings claim is false. The calibration task checks whether
cached input is correctly treated as a subset. These are authored fixtures, not
independent real-project quality assessments.

## Identity and Limitations

All four receipts reported stable host configuration hashes, distinct source
identities, and the same requested reasoning level. Prompt hashes match within
each pair. The focused override submitted was `skills.max_context_tokens=1024`.
Host configuration and submitted overrides are not independent provider
attestation of model identity or effective context contents.

Estimates use the recorded `legacy-configured-v1` rate contract, not provider
bills. Its effective date is unknown. Do not translate these units into dollars
or weekly percentages. The gap between admission and observed usage is forecast
error/headroom, not savings.

One calibration sample per context is **insufficient support** for automatic
forecast promotion. The bounded bootstrap intentionally did not claim to be
calibrated. Do not combine its counter task with the audit task as if they were
independent observations of the same task family.

## Reproduce

From a source checkout with the optional host prerequisites installed:

```powershell
python scripts/run_accounted_trial.py --output <new-private-directory>
```

This previews admission without a model call. Add `--execute` only after approving
the 60-estimated-credit ceiling and ensuring no other run shares the budget. The
script reserves each call, saves every raw receipt privately, stops on unknown
usage or a 12-credit estimate overrun, and never uses a reset. Admission is not a
provider hard cap. Results can differ with cache state, host changes and latency.

The local development Workbench now preserves its original preview estimate next
to receipt-derived estimates and labels quality and savings as unknown where no
validated comparison is linked. It does not automatically apply this pilot's
result to unrelated tasks. Independent newcomer trials remain pending.
