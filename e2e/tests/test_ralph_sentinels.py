"""Static-parse tests for run-ralph.sh sentinel handling. Verifies that the
loop checks both .ralph-done and .ralph-human-blocked, in the conservative
order (human-blocked first), and that startup cleanup removes both.
Mirrors the file-reading style of test_manual_deploy_integration.py — no
subprocess execution; behavioral verification is via documented manual
smoke test and the EXECUTE-PLAN.md protocol contract."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUN_RALPH = REPO_ROOT / "docs" / "ralph_loops" / "run-ralph.sh"


def _read() -> str:
    return RUN_RALPH.read_text(encoding="utf-8")


def test_startup_cleanup_removes_both_sentinels():
    text = _read()
    # Startup cleanup runs once, after `cd "$WORKTREE"`. Both sentinels
    # must be removed in case a prior run left one stale.
    assert "rm -f .ralph-done .ralph-human-blocked" in text, (
        "Startup cleanup must remove both .ralph-done and .ralph-human-blocked"
    )


def test_human_blocked_check_precedes_done_check():
    text = _read()
    human_idx = text.find('if [ -f .ralph-human-blocked ]')
    done_idx = text.find('if [ -f .ralph-done ]')
    assert human_idx != -1, "run-ralph.sh must check for .ralph-human-blocked"
    assert done_idx != -1, "run-ralph.sh must check for .ralph-done"
    assert human_idx < done_idx, (
        "Human-blocked sentinel must be checked BEFORE .ralph-done so a "
        "misbehaving agent that touches both halts conservatively rather than "
        "claiming completion."
    )


def test_human_blocked_halt_emits_user_action_message():
    text = _read()
    # The halt block must contain the user-facing identifier and the
    # recovery instruction so the user knows what to do next.
    assert "Ralph Loop Halted — User Action Required" in text
    assert "mark the task ✅ in the plan and re-launch the loop" in text


def test_done_path_unchanged():
    text = _read()
    # Regression guard: the existing complete-path message and handoff
    # recommendation must be preserved.
    assert "=== Ralph Loop Complete ===" in text
    assert "/aligned:finishing-a-development-branch" in text


def test_human_blocked_sentinel_is_removed_after_halt():
    text = _read()
    # Both halt blocks remove their sentinel before exiting so the next
    # invocation starts clean.
    assert "rm .ralph-human-blocked" in text
    assert "rm .ralph-done" in text


def test_run_ralph_sources_lib_process():
    text = _read()
    assert 'source "$SCRIPT_DIR/lib/process.sh"' in text or \
           'source "$(dirname "$0")/lib/process.sh"' in text, \
        "run-ralph.sh must source lib/process.sh"


def test_run_ralph_uses_set_u_only():
    text = _read()
    # Decision 7: standardize on set -u across all callers
    assert "set -u" in text, "run-ralph.sh must declare 'set -u'"
    assert "set -euo pipefail" not in text, \
        "run-ralph.sh must not use 'set -euo pipefail' (Decision 7)"
