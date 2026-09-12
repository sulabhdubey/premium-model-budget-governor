"""Build a local, allowlisted plugin archive without installing or publishing it."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile


SOURCES = {
    ".codex-plugin/plugin.json": "plugin/.codex-plugin/plugin.json",
    ".mcp.json": "plugin/.mcp.json",
    "skills/premium-model-budget-governor/SKILL.md":
        "plugin/skills/premium-model-budget-governor/SKILL.md",
    "README.md": "plugin/README.md",
    "LICENSE": "LICENSE",
    "NOTICE": "NOTICE",
}
for name in ("NATIVE_HOOK_RESULTS", "HOST_INTEGRATION", "GOVERNED_EXECUTION",
             "CAPABILITY_CONTROLS", "ASTRA_PREFERRED", "MCP", "INSTALLATION"):
    SOURCES[f"docs/{name}.md"] = f"docs/{name}.md"
for name in ("astra_preferred", "tournament_packet", "telemetry_packet"):
    SOURCES[f"examples/{name}.json"] = f"examples/{name}.json"


def read_source(root: Path, relative: str) -> bytes:
    root = root.resolve()
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("plugin source escapes the checkout")
    if not candidate.is_file() or candidate.stat().st_size > 2_000_000:
        raise ValueError("plugin source missing, not a file or oversized")
    return candidate.read_bytes()


def build(root: Path, output: Path) -> dict:
    contents = {name: read_source(root, source) for name, source in SOURCES.items()}
    manifest = json.loads(contents[".codex-plugin/plugin.json"])
    # Stored entries avoid compressor-version differences; preserve source bytes.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(contents.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    payload = buffer.getvalue()
    with output.open("xb") as stream:
        stream.write(payload)
    return {
        "version": manifest["version"],
        "sha256": hashlib.sha256(payload).hexdigest(),
        "files": {name: hashlib.sha256(data).hexdigest()
                  for name, data in sorted(contents.items())},
        "installed": False,
        "publication_authorized": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = build(Path(__file__).resolve().parents[1], args.output)
    except (OSError, ValueError, KeyError):
        parser.exit(2, "Plugin build failed; check required sources and a new output path.\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
