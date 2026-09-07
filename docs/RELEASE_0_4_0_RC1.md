# v0.4.0-rc.1: Experimental Host Integration

This is a prerelease, not a claim that the independent-validation and learned-routing
roadmap is complete. Idea and product direction: Sulabh Dubey. Engineering and
testing: Codex under that direction.

- Live App Server model, reasoning and image-modality discovery, with no model turn.
- Explicitly approved read-only filesystem execution, atomic reservations and replay protection.
- Standard service tier, cumulative token reconciliation and unknown-spend retention.
- Optional prompt admission gate bound to exact prompt/session/turn and a reserved lease.
- Shared dispatch exclusion between the hook and execution clients.
- No global hook installation, trust bypass, credential copying or auto-learning.

The new Astra image turn completed with 24,471 input and 19 output tokens, costing
6.14150 projected credits. It read the image value correctly but lowercased the
units, failing the strict original output assertion. That result remains published.

Native trusted-hook execution is not verified yet. Broader independent real-task
evaluation and learned policy promotion remain open. Read the
[integration scope](https://github.com/sulabhdubey/premium-model-budget-governor/blob/main/docs/HOST_INTEGRATION.md)
before enabling the optional template. The gate is not a provider token cap or
served-model attestation.
