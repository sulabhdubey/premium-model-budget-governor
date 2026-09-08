# Isolated Installation

The guided script creates a dedicated Python environment. It does not change
PATH, Codex settings, hook trust, login, or existing Python installations.
It never starts a model turn. Python 3.10 or newer must already be installed.
This is a terminal-based setup step, not yet a graphical installer.

The current local qualification script also verifies packaged workbench assets,
module imports, loopback serving and unauthenticated API rejection from outside
the source tree. With `--mcp`, it connects a real stdio client and calls a
non-model tool. These are installation checks, not model-quality experiments.
Published and development reports are identified separately below; a passing
report applies to its recorded wheel hash, not every later checkout edit.

## Preview, Then Install

For the **rc.5 testing prerelease**, download both
[install_governor.py](https://github.com/sulabhdubey/premium-model-budget-governor/releases/download/v0.4.0-rc.6/install_governor.py)
and the [rc.5 wheel](https://github.com/sulabhdubey/premium-model-budget-governor/releases/download/v0.4.0-rc.6/premium_model_budget_governor-0.4.0rc6-py3-none-any.whl).
Open a terminal in their folder:

```sh
python install_governor.py install --wheel premium_model_budget_governor-0.4.0rc6-py3-none-any.whl
python install_governor.py install --wheel premium_model_budget_governor-0.4.0rc6-py3-none-any.whl --yes
```

This candidate includes direct and explicit multi-stage workflows plus an
experimental native folder chooser. It is not a completed stable product.

For an explicitly selected development source checkout instead:

```sh
python scripts/install_governor.py install
python scripts/install_governor.py install --yes
```

Source installation installs that checkout's code. Do not assume the default
GitHub branch contains unpublished features described in a development README.

The default location is `~/.pm-bg/runtime`. Use `--directory` to choose a new
dedicated folder. Existing folders are never overwritten. Keep projects, usage
ledgers and personal documents outside the runtime because uninstall removes it.
Installation from source may download build tools from your configured package index.

The script prints the installed executable location. On Windows PowerShell:

```powershell
& "$HOME/.pm-bg/runtime/Scripts/pm-bg.exe" doctor
```

On Linux or macOS:

```sh
"$HOME/.pm-bg/runtime/bin/pm-bg" doctor
```

No virtual environment activation is necessary. `doctor` checks the Codex version
and `codex login status`, discarding their raw output. It reports only categories,
versions and recovery instructions. It does not inspect credential files or verify
model access/capacity. `doctor --offline` skips host commands completely.

For a downloaded, trusted governor wheel, pass `--wheel PATH`. Without `--mcp`,
this path uses `--no-index --no-deps` and performs no package-index download.
Do not install wheels from untrusted sources: packages execute local code.

## Optional MCP

Add `--mcp` to the installation command to install optional MCP dependencies.
They may require network access and have additional runtime requirements.
This does not connect the server automatically. Review [MCP setup](MCP.md),
using the isolated environment's Python executable rather than another Python.
Removing a client connection remains an explicit client action; the installer
neither writes nor removes third-party configuration.

## Recovery and Removal

| Symptom | Next action |
| --- | --- |
| Python missing/too old | Install a supported Python, then rerun the preview |
| Codex missing | Install/update the official CLI and verify `codex --version` in your terminal |
| Authentication unavailable | Run `codex login` yourself; never paste credentials into bug reports |
| Authentication unknown | Check whether the CLI is blocked or timed out; retry `doctor` after resolving it |
| Dependency/network failure | Review local pip output, preview removal of the failed runtime, remove it, then retry |
| Destination exists | Choose a new folder or uninstall that owned runtime first |
| Abrupt interruption left `installing` | Verify installer/pip processes have stopped before inspecting the folder; automatic deletion is refused |

Preview and approve removal:

```sh
python install_governor.py uninstall
python install_governor.py uninstall --yes
```

For a source checkout, use `scripts/install_governor.py` instead. Keep the
standalone installer for removal. Use the same `--directory` for a custom installation. Removal requires an
installer ownership receipt bound to the resolved absolute directory and refuses
root/home/repository ancestors, symlink/junction targets, and relocated receipts.
It removes **all contents of that runtime only**, preserving external governor
ledgers and Codex configuration. The receipt is an accidental-deletion guard,
not a security boundary against someone who can edit local files.

## Diagnostic Contract

`pm-bg doctor --json` returns the CLI `{ok, result}` envelope. `ok` means the
diagnostic completed, not that execution is ready. Inspect `model_execution`:
`preflight_ready`, `needs_attention`, or `not_checked`. A successful login check
does not prove a particular model can run.

Exit codes: 0 for a passing requested check, 1 for setup needing attention,
2 for invalid invocation or diagnostic failure. MCP remains optional and its
presence alone is not a successful MCP runtime test. Reports contain no project
paths, raw host logs, prompts, account identifiers, or credentials.

## Verification Status

The published rc.3 wheel passed isolated installation, optional MCP stdio calls,
installed-package regression and clean uninstall on
[Windows](../artifacts/onboarding/windows-rc3-regression.json) and
[Ubuntu/WSL](../artifacts/onboarding/linux-wsl-rc3-regression.json): 268 passed,
one skipped on each. Its hash is recorded in both reports and in the
[release notes](RELEASE_CANDIDATE_RC3.md), which also distinguish remote CI evidence.

A later, **unpublished 0.4.0rc4.dev1** wheel passed the same checks on
[Windows](../artifacts/onboarding/windows-rc4-dev1-regression.json) and
[Ubuntu/WSL](../artifacts/onboarding/linux-wsl-rc4-dev1-regression.json): 294 passed,
one skipped on each. Receipt-display and folder-chooser changes made after that
build are not covered by those wheel reports. They need a new package qualification.
WSL installation does not prove native desktop interaction, and the development
build has not been qualified on macOS. These tests are not model-benefit evidence.

`scripts/check_installation.py --regression` installs pytest only into its disposable
runtime, clears checkout import paths, runs the suite against the installed wheel,
and then uninstalls it. Raw JUnit traces stay under ignored `build/qualification`;
public JSON reports contain check names, hashes and aggregate results.
Human onboarding is still unvalidated; see [the trial protocol](ONBOARDING_TRIAL.md).
