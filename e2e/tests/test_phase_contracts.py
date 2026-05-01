"""Static-parse tests for the phase script + shared library decomposition.
Mirrors test_ralph_sentinels.py — no subprocess execution; assertions on
text content of bash files."""

from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RALPH_DIR = REPO_ROOT / "docs" / "ralph_loops"
LIB_DIR = RALPH_DIR / "lib"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_lib_process_exists_with_required_functions():
    proc = LIB_DIR / "process.sh"
    assert proc.is_file(), "lib/process.sh must exist"
    text = _read(proc)
    for fn in (
        "start_heartbeat()",
        "stop_heartbeat()",
        "start_watchdog()",
        "stop_watchdog()",
        "cleanup()",
        "kill_claude()",
        "run_claude_phase()",
    ):
        assert fn in text, f"lib/process.sh must define {fn}"


def test_lib_process_uses_set_u_only():
    text = _read(LIB_DIR / "process.sh")
    assert "set -u" in text, "lib/process.sh must declare 'set -u'"
    assert "set -e" not in text, "lib/process.sh must NOT use 'set -e' (Decision 7)"


def test_run_ralph_does_not_redefine_shared_functions():
    """The 5 functions duplicated between autopilot.sh and run-ralph.sh
    must be defined ONCE — in lib/process.sh — after the refactor. Each
    must have count=0 in run-ralph.sh (the function definition has been
    removed; only the call site remains, and that uses bare names like
    'start_heartbeat ' not 'start_heartbeat()')."""
    text = (RALPH_DIR / "run-ralph.sh").read_text(encoding="utf-8")
    for fn in (
        "start_heartbeat()",
        "stop_heartbeat()",
        "start_watchdog()",
        "stop_watchdog()",
        "cleanup()",
    ):
        # Function-DEFINITION pattern is `name() {` — count must be 0.
        assert f"{fn} {{" not in text and f"{fn}\n{{" not in text, \
            f"run-ralph.sh must not define {fn} — sourced from lib/process.sh"


def test_autopilot_sources_lib_process():
    text = (RALPH_DIR / "autopilot.sh").read_text(encoding="utf-8")
    assert 'source "$SCRIPT_DIR/lib/process.sh"' in text, \
        "autopilot.sh must source lib/process.sh"


def test_autopilot_uses_set_u_only():
    text = (RALPH_DIR / "autopilot.sh").read_text(encoding="utf-8")
    assert "set -u" in text and "set -uo pipefail" not in text, \
        "autopilot.sh must declare 'set -u' (not '-uo pipefail') — Decision 7"


def test_autopilot_does_not_redefine_lib_functions():
    text = (RALPH_DIR / "autopilot.sh").read_text(encoding="utf-8")
    # Definition pattern is `name() {` — count must be 0 for all 7 lib functions.
    for fn in (
        "cleanup()",
        "kill_claude()",
        "start_heartbeat()",
        "stop_heartbeat()",
        "start_watchdog()",
        "stop_watchdog()",
        "run_claude_phase()",
    ):
        assert f"{fn} {{" not in text and f"{fn}\n{{" not in text, \
            f"autopilot.sh must not define {fn} — sourced from lib/process.sh"
