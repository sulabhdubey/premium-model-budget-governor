# Focused Skill Catalog (Experimental)

The Workbench offers **Skill discovery: Focused catalog** only with **Direct,
Astra Preferred and Low reasoning**. Inherited discovery remains the default.
Change any setting after preview and approval must be renewed. Incompatible
settings are rejected, not silently downgraded to a different model or profile.

This profile sends only `skills.max_context_tokens: 1024` in the App Server's
per-thread configuration. It does not edit global Codex configuration, disable
tools/connectors, change safety rules, reduce reasoning after approval or accept
arbitrary client configuration. The scope is bound to the preview and receipt;
reviewed policies use a distinct profile fingerprint. Older servers that omit
the selected profile cannot silently execute an inherited-profile preview.

Codex documents the catalog-budget setting in its
[official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
Support and behavior can change across host versions. A host accepting a setting
does not independently attest its internal application.

**Tradeoff:** less catalog text can mean less useful skill guidance is discovered.
Keep inherited discovery when that guidance matters or when uncertain. This is
not a claim that every Astra capability is preserved on every task. Tools remain
available under their inherited permissions; a read-only filesystem sandbox does
not revoke connector access.

The [four-call visual experiment](FIELD_TRIAL_2026_09_07.md) measured about 17.3%
lower mean estimated credits with the same correct answers, but only on one task.
The governor deliberately keeps the same conservative admission allowance; it
does not assume cache hits, promised savings or a weekly-limit conversion.
Switch back to Inherited to restore the normal catalog budget for a new preview.
