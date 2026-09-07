# v0.4.0-rc.2: Native Hook Evidence

Seven native conditions tested on Codex CLI 0.153.4 using a credential-free,
loopback-only fixture. No paid model calls or reset credits were used.

- Trusted missing and expired grants blocked before model dispatch.
- A valid grant reached the refusing local model endpoint.
- Modified and disabled hooks were skipped.
- Hook crashes and timeouts allowed model dispatch: hooks alone are not fail-closed.
- Optional `required_hook_hashes` now verifies presence, enabled state and trust
  before controlled dispatch. Unknown spend is still retained.
- The isolated hook was reviewed/trusted through native UI and disabled after testing.

See the [full results](https://github.com/sulabhdubey/premium-model-budget-governor/blob/main/docs/NATIVE_HOOK_RESULTS.md).
Keep governor-owned admission primary. This remains a prerelease: independent
real-project validation and learned routing are still open. Idea and product
direction: Sulabh Dubey; engineering and testing: Codex under that direction.
