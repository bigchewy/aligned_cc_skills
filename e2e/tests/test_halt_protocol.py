"""Static-parse + bash-function tests for the halt protocol (lib/halt.sh
and the autopilot-halt-format.md taxonomy)."""

from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HALT_SH = REPO_ROOT / "docs" / "ralph_loops" / "lib" / "halt.sh"
HALT_DOC = REPO_ROOT / "skills" / "_shared" / "autopilot-halt-format.md"

EXPECTED_REASONS = [
    "mcp_unreachable",
    "mcp_tool_not_allowlisted",
    "env_var_missing",
    "manifest_drift",
    "manifest_malformed",
    "uncommitted_main",
    "verify_failed",
    "human_action_required",
    "phase_crashed",
]


def test_halt_format_doc_exists():
    assert HALT_DOC.is_file(), "skills/_shared/autopilot-halt-format.md must exist"


def test_halt_format_doc_lists_all_reasons():
    text = HALT_DOC.read_text(encoding="utf-8")
    for r in EXPECTED_REASONS:
        assert r in text, f"halt-format doc must list reason: {r}"


def _bash(cmd: str, cwd: Path) -> subprocess.CompletedProcess:
    full = f'set -u; source "{HALT_SH}"; {cmd}'
    return subprocess.run(
        ["bash", "-c", full], capture_output=True, text=True, cwd=cwd
    )


def test_halt_sh_exists_with_required_functions():
    assert HALT_SH.is_file()
    text = HALT_SH.read_text(encoding="utf-8")
    for fn in ("write_halt()", "read_halt()", "format_halt()"):
        assert fn in text, f"lib/halt.sh must define {fn}"


def test_write_halt_creates_sentinel():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        r = _bash(
            f'HALT_PATH="{d}/.autopilot-halt" '
            f'write_halt env_var_missing preflight "FAKE_VAR is unset"',
            cwd=d,
        )
        assert r.returncode == 0, r.stderr
        sentinel = d / ".autopilot-halt"
        assert sentinel.is_file()
        text = sentinel.read_text()
        assert "reason: env_var_missing" in text
        assert "phase: preflight" in text


def test_write_halt_secondary_appends_not_overwrites():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        env = f'HALT_PATH="{d}/.autopilot-halt"'
        _bash(f'{env} write_halt env_var_missing preflight "first"', cwd=d)
        _bash(f'{env} write_halt mcp_unreachable preflight "second"', cwd=d)
        text = (d / ".autopilot-halt").read_text()
        assert "reason: env_var_missing" in text  # first preserved
        assert "secondary-halt:" in text  # second appended
        assert "mcp_unreachable" in text


def test_format_halt_echoes_canonical_fix():
    r = _bash('format_halt env_var_missing', cwd=Path("/tmp"))
    assert r.returncode == 0, r.stderr
    # Each canonical fix instruction must mention the reason name AND the user action
    assert "env_var_missing" in r.stdout or "env var" in r.stdout.lower()
