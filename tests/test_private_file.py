import os
import stat
import json
import subprocess
from pathlib import Path

import pytest


def test_private_file_roundtrip_and_replacement_safe_cleanup(tmp_path):
    from premium_model_budget_governor.private_file import write_private, remove_if_unchanged
    path = tmp_path / "session.json"
    write_private(path, b"private fixture")
    assert path.read_bytes() == b"private fixture"
    if os.name != "nt":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    path.write_bytes(b"user replacement")
    remove_if_unchanged(path, b"private fixture")
    assert path.read_bytes() == b"user replacement"
    write_private(path, b"second fixture")
    remove_if_unchanged(path, b"second fixture")
    assert not path.exists()


def test_private_write_failure_leaves_previous_file_untouched(tmp_path, monkeypatch):
    from premium_model_budget_governor.private_file import write_private
    path = tmp_path / "session.json"
    path.write_bytes(b"keep")
    def fail(*args):
        raise OSError("replace failed")
    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError):
        write_private(path, b"new")
    assert path.read_bytes() == b"keep"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["session.json"]


@pytest.mark.skipif(os.name != "nt", reason="Windows DACL verification")
def test_windows_file_has_protected_current_user_only_acl(tmp_path):
    from premium_model_budget_governor.private_file import write_private
    path = tmp_path / "session.json"
    write_private(path, b"ACL fixture, not a credential")
    shell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    script = """
$ErrorActionPreference = 'Stop'
$acl = [System.IO.File]::GetAccessControl($env:PM_BG_ACL_TEST_FILE)
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$rules = @($acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]))
$only = $true
foreach ($rule in $rules) { if ($rule.IdentityReference.Value -ne $user -or $rule.AccessControlType -ne 'Allow' -or $rule.IsInherited) { $only = $false } }
[Console]::WriteLine('{"protected":' + $acl.AreAccessRulesProtected.ToString().ToLowerInvariant() + ',"count":' + $rules.Count + ',"userOnly":' + $only.ToString().ToLowerInvariant() + '}')
"""
    result = subprocess.run([str(shell), "-NoProfile", "-NonInteractive", "-Command", script],
                            env={**os.environ, "PM_BG_ACL_TEST_FILE": str(path)}, capture_output=True,
                            text=True, timeout=15, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
    permissions = json.loads(result.stdout)
    assert permissions == {"protected": True, "count": 1, "userOnly": True}
