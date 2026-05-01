"""Bash-function-level tests for lib/manifest.sh — parse + validate. Subprocess
testing is allowed at function boundary (per design Decision 5)."""

from __future__ import annotations
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LIB = REPO_ROOT / "docs" / "ralph_loops" / "lib" / "manifest.sh"
FIX = REPO_ROOT / "e2e" / "fixtures" / "manifest"


def _bash(cmd: str, env: dict | None = None) -> subprocess.CompletedProcess:
    full = f'set -u; source "{LIB}"; {cmd}'
    return subprocess.run(["bash", "-c", full], capture_output=True, text=True, env=env)


def test_parse_manifest_present():
    r = _bash(f'parse_manifest "{FIX/"plan_with_manifest.md"}"')
    assert r.returncode == 0, r.stderr
    assert "mcp__playwright__browser_navigate" in r.stdout
    assert "FAKE_TEST_VAR" in r.stdout


def test_parse_manifest_absent_returns_skip():
    r = _bash(f'parse_manifest "{FIX/"plan_no_manifest.md"}"; echo "exit=$?"')
    # Convention: parse_manifest exits 3 (skip) when no front-matter
    assert "exit=3" in r.stdout, r.stdout + r.stderr


def test_parse_manifest_malformed_returns_error():
    r = _bash(f'parse_manifest "{FIX/"plan_partial.md"}"; echo "exit=$?"')
    # Partial/unparseable YAML must NOT silently skip — must error to trigger
    # halt-with-reason: manifest_malformed
    assert "exit=1" in r.stdout, r.stdout + r.stderr


def test_validate_env_var_missing():
    # FAKE_TEST_VAR is not set in the env passed
    r = _bash(
        f'parse_manifest "{FIX/"plan_with_manifest.md"}" >/dev/null; '
        f'check_env_var FAKE_TEST_VAR; echo "exit=$?"',
        env={"PATH": "/usr/bin:/bin"},
    )
    assert "exit=2" in r.stdout, r.stdout + r.stderr


def test_validate_env_var_present():
    r = _bash(
        'check_env_var FAKE_TEST_VAR; echo "exit=$?"',
        env={"PATH": "/usr/bin:/bin", "FAKE_TEST_VAR": "x"},
    )
    assert "exit=0" in r.stdout, r.stdout + r.stderr


def test_preflight_halts_on_missing_env_var():
    """End-to-end: invoke preflight against a fixture plan with an env var
    requirement that the test env does not satisfy."""
    PREFLIGHT = REPO_ROOT / "docs" / "ralph_loops" / "phases" / "preflight.sh"
    fixture = FIX / "plan_with_manifest.md"
    import os, tempfile
    with tempfile.TemporaryDirectory() as d:
        # Inherit PATH so parse_manifest can locate a python3 with PyYAML;
        # explicitly omit FAKE_TEST_VAR so env_var_missing is what trips.
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
               "PROJECT": d, "PLAN_FILE": str(fixture),
               "HALT_PATH": f"{d}/.autopilot-halt", "LOG": f"{d}/.log"}
        env.pop("FAKE_TEST_VAR", None)
        r = subprocess.run(
            ["bash", str(PREFLIGHT)], capture_output=True, text=True,
            env=env, cwd=d,
        )
        # FAKE_TEST_VAR is not set → halt with env_var_missing → exit 2
        assert r.returncode == 2, f"preflight should halt (exit 2), got {r.returncode}: {r.stderr}"
        sentinel = Path(d) / ".autopilot-halt"
        assert sentinel.is_file(), "preflight must write .autopilot-halt"
        assert "env_var_missing" in sentinel.read_text()
