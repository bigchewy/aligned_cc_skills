"""Bash-function-level tests for lib/manifest.sh — parse + validate. Subprocess
testing is allowed at function boundary (per design Decision 5)."""

from __future__ import annotations
import json
import os
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LIB = REPO_ROOT / "scripts" / "autopilot" / "lib" / "manifest.sh"
FIX = REPO_ROOT / "e2e" / "fixtures" / "manifest"


def _bash(cmd: str, env: dict | None = None) -> subprocess.CompletedProcess:
    full = f'set -u; source "{LIB}"; {cmd}'
    return subprocess.run(["bash", "-c", full], capture_output=True, text=True, env=env)


def test_parse_manifest_present():
    r = _bash(f'parse_manifest "{FIX/"plan_with_manifest.md"}"')
    assert r.returncode == 0, r.stderr
    assert "mcp__playwright__browser_navigate" in r.stdout


def test_parse_manifest_absent_returns_skip():
    r = _bash(f'parse_manifest "{FIX/"plan_no_manifest.md"}"; echo "exit=$?"')
    # Convention: parse_manifest exits 3 (skip) when no front-matter
    assert "exit=3" in r.stdout, r.stdout + r.stderr


def test_parse_manifest_malformed_returns_error():
    r = _bash(f'parse_manifest "{FIX/"plan_partial.md"}"; echo "exit=$?"')
    # Partial/unparseable YAML must NOT silently skip — must error to trigger
    # halt-with-reason: manifest_malformed
    assert "exit=1" in r.stdout, r.stdout + r.stderr


def _run_check_mcp_tool(home: str, cwd: str, tool: str) -> subprocess.CompletedProcess:
    # HOME override prevents the function from finding the host's real
    # ~/.claude/.mcp.json or ~/.claude/settings.local.json, which would leak
    # into the test result.
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": home}
    full = f'set -u; source "{LIB}"; check_mcp_tool {tool} "{cwd}"'
    return subprocess.run(["bash", "-c", full], capture_output=True, text=True, env=env)


def test_check_mcp_tool_unreachable():
    """No .mcp.json defines the requested server → exit 2, 'mcp_unreachable'."""
    with tempfile.TemporaryDirectory() as d:
        sub = Path(d) / "sub"
        sub.mkdir()
        # Use a pseudo-unique server name to make a stray real-filesystem
        # .mcp.json hit astronomically unlikely.
        r = _run_check_mcp_tool(d, str(sub), "mcp__nonexistent_xyz_abc__some_tool")
        assert r.returncode == 2, f"stdout={r.stdout} stderr={r.stderr}"
        assert "mcp_unreachable" in r.stdout, r.stdout


def test_check_mcp_tool_not_allowlisted():
    """Server defined in .mcp.json but tool absent from settings.local.json
    allowlist → exit 2, 'mcp_tool_not_allowlisted'."""
    with tempfile.TemporaryDirectory() as d:
        Path(d, ".mcp.json").write_text(json.dumps({
            "mcpServers": {"playwright": {"command": "npx"}}
        }))
        Path(d, ".claude").mkdir()
        Path(d, ".claude", "settings.local.json").write_text(json.dumps({
            "permissions": {"allow": []}
        }))
        sub = Path(d) / "sub"
        sub.mkdir()
        r = _run_check_mcp_tool(d, str(sub), "mcp__playwright__browser_navigate")
        assert r.returncode == 2, f"stdout={r.stdout} stderr={r.stderr}"
        assert "mcp_tool_not_allowlisted" in r.stdout, r.stdout


def test_check_mcp_tool_ok():
    """Server defined and tool allowlisted → exit 0, 'ok'."""
    with tempfile.TemporaryDirectory() as d:
        Path(d, ".mcp.json").write_text(json.dumps({
            "mcpServers": {"playwright": {"command": "npx"}}
        }))
        Path(d, ".claude").mkdir()
        Path(d, ".claude", "settings.local.json").write_text(json.dumps({
            "permissions": {"allow": ["mcp__playwright__browser_navigate"]}
        }))
        sub = Path(d) / "sub"
        sub.mkdir()
        r = _run_check_mcp_tool(d, str(sub), "mcp__playwright__browser_navigate")
        assert r.returncode == 0, f"stdout={r.stdout} stderr={r.stderr}"
        assert "ok" in r.stdout, r.stdout


def test_preflight_passes_when_env_vars_required_unset():
    """End-to-end: invoke preflight against a fixture plan; verify env-var requirements no longer halt preflight."""
    PREFLIGHT = REPO_ROOT / "scripts" / "autopilot" / "phases" / "preflight.sh"
    fixture = FIX / "plan_with_manifest.md"
    with tempfile.TemporaryDirectory() as d:
        # Set up MCP config in HOME so check_mcp_tool finds playwright and treats it as allowlisted.
        # This isolates the test from the host's real ~/.claude and the fixture's mcp-tools-required entry.
        Path(d, ".mcp.json").write_text(json.dumps({
            "mcpServers": {"playwright": {"command": "npx"}}
        }))
        Path(d, ".claude").mkdir()
        Path(d, ".claude", "settings.local.json").write_text(json.dumps({
            "permissions": {"allow": ["mcp__playwright__browser_navigate"]}
        }))
        # Inherit PATH so parse_manifest can locate a python3 with PyYAML;
        # omit FAKE_TEST_VAR — preflight no longer probes env vars, so this is informational.
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
               "HOME": d,
               "PROJECT": d, "PLAN_FILE": str(fixture),
               "HALT_PATH": f"{d}/.autopilot-halt", "LOG": f"{d}/.log"}
        env.pop("FAKE_TEST_VAR", None)
        r = subprocess.run(
            ["bash", str(PREFLIGHT)], capture_output=True, text=True,
            env=env, cwd=d,
        )
        # Preflight no longer validates env vars → returncode 0, no halt sentinel written.
        assert r.returncode == 0, f"preflight should pass (exit 0), got {r.returncode}: {r.stderr}"
        sentinel = Path(d) / ".autopilot-halt"
        assert not sentinel.exists(), "preflight must NOT write .autopilot-halt when env vars are unset"
