import pytest

from src.permissions.models import PermissionManager, PermissionMode
from src.permissions.sandbox import SandboxManager


def test_permission_manager_default_mode():
    pm = PermissionManager()
    assert pm.mode == PermissionMode.ASK


def test_permission_manager_deny_rule():
    pm = PermissionManager({
        "mode": "allow",
        "rules": [
            {"pattern": "Bash(rm -rf *)", "action": "deny"}
        ]
    })
    assert pm.check_permission("Bash(rm -rf /)", {}) == False


def test_permission_manager_allow():
    pm = PermissionManager({
        "mode": "allow",
        "rules": []
    })
    assert pm.check_permission("read_file", {}) == True


def test_sandbox_validate_path():
    sm = SandboxManager({
        "enabled": True,
        "allowed_directories": ["workspace/"],
        "denied_patterns": [".env"]
    })
    assert sm.validate_path("workspace/test.txt") == True
    assert sm.validate_path("/etc/passwd") == False


def test_sandbox_validate_command():
    sm = SandboxManager({"enabled": True})
    assert sm.validate_command("echo hello") == True
    assert sm.validate_command("rm -rf /") == False
    assert sm.validate_command("sudo apt update") == False
