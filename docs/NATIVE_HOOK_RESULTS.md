# Native Hook Tests: Codex 0.153.4

## Result

The hook works when trusted and healthy, but **is not fail-closed on host-side
failure**. Use governor-owned admission before `turn/start` as the primary
budget control. Native prompt hooks are supplementary and cannot guarantee a
hard spending limit for arbitrary Desktop activity.

| Condition | Native hook result | Local model endpoint attempts |
| --- | --- | ---: |
| Trusted, missing grant | Blocked | 0 |
| Trusted, expired grant | Blocked | 0 |
| Trusted, valid grant | Completed | 1 |
| Changed definition, not re-trusted | Skipped | 1 |
| Trusted hook exits with failure | Failed, model request proceeded | 1 |
| Trusted hook exceeds timeout | Failed, model request proceeded | 1 |
| Hook disabled through native UI | Skipped | 1 |

All endpoint attempts were refused by an offline loopback fixture. **No paid
model call, account token, or reset credit was used for these native tests.**
The hook was disabled through Codex UI at the end. Nothing was installed into
the user's normal Codex home, and no global trust policy was changed.

## Method

The lab has its own CODEX_HOME and empty Git project under ignored `build/`.
It uses a custom provider pointing only to 127.0.0.1 with no authentication.
The exact production hook command was reviewed and trusted in Codex's native
hook screen. A separate, reviewed fault-injection wrapper was then trusted to
test crashes and timeouts. That wrapper delegates healthy cases to the real gate.
No trust bypass flag or manual trust-hash edit was used.

One App Server initialization failed before the original valid-grant case. That
offline case was rerun. Subsequent observations cover the full matrix above;
the startup failure is recorded as a harness issue, not a hook rejection.
Raw native diagnostics remain private; only status/count metadata is published
in [results.json](../artifacts/native-hook-pilot/results.json).

The lab script requires Python 3.11+ for TOML validation. The package itself still
supports Python 3.10+. Native interactive review is deliberately not automated
or bypassed by the script:

```sh
python scripts/native_hook_lab.py prepare
git init build/native-hook-lab/project
python scripts/native_hook_lab.py review
python scripts/native_hook_lab.py test
```

Review and trust only the displayed lab command. Fault tests require
`prepare-faults`, another native review, then `test --case crash` and
`test --case timeout`. Do not enable the lab fixture in a real account home.
The local endpoint refuses every model attempt and fails if its port is occupied.

## Product Response

`app-run` accepts optional `required_hook_hashes`. If configured, it checks that
each hash is present, enabled and trusted before reserving/dispatching a turn.
It never approves new hashes automatically. Observed hook failures or blocks
stop the client and retain unknown spend. These checks cannot undo an internal
request that the host already sent, nor eliminate a configuration-change race.

The independent reservation and replay checks remain mandatory. A configured
budget is an admission limit, not a provider token cap. Do not globally enable
the optional prompt gate and advertise universal automatic enforcement.

## Next Gate

Native behavior is now measured. The next work is independent real-project
evaluation through the controlled runner, followed by evidence-gated learned
routing. External reviewers and held-out outcomes are still required; this
native compatibility test does not substitute for them.
