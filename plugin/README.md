# Governor Plugin: Local Development Package

This plugin supplies Astra-first planning guidance and an MCP configuration
example. It does not contain Python, install dependencies, activate hooks or
control unrelated chats. This development package is not the published beta.

## Setup

1. Install a separately qualified Governor wheel with the optional MCP extra using
   the [isolated installer](docs/INSTALLATION.md). The plugin ZIP is not a wheel.
2. Review the [MCP guide](docs/MCP.md). Before enabling the plugin, replace the
   illustrative `python` command in `.mcp.json` with the absolute interpreter from
   the isolated installer's generated client template. Do not copy another user's
   runtime path. Configure only through your host's supported plugin mechanism.
3. Confirm tools are actually available in your client. Skill discovery alone does
   not prove an MCP connection. Shared registration or restart requires approval.

Paths such as `docs/HOST_INTEGRATION.md` and `examples/astra_preferred.json` in
the skill are relative to the extracted plugin root, not the working project.
Resolve them there before using example commands; examples are not spend approval.
Only directly referenced guides and examples are bundled. Secondary documentation
links may require the [complete source repository](https://github.com/sulabhdubey/premium-model-budget-governor).
For development behavior, consult the matching checkout, not an older public tag.

## Artifact Review

From the source checkout, `python scripts/build_plugin.py --output plugin.zip`
creates an allowlisted archive and prints its SHA256 plus per-file hashes. Existing
outputs are refused. Unchanged input bytes produce the same archive bytes, without
bundling arbitrary local files, Python dependencies or native libraries.

Hashes establish byte identity, not authenticity, safety or a digital signature.
Review source, license notices and package contents before distribution. No
installation, publication or shared configuration change is performed by the build.
