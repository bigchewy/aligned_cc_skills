"""Static-parse tests for run-ralph.sh sentinel handling under the
unattended-autopilot contract.

Policy: once autopilot starts, it never halts for human intervention.
The loop honors a single sentinel — `.ralph-done`. The previous
`.ralph-human-blocked` halt path has been removed; tasks the agent
cannot complete route through the existing 🔄 BLOCKED retry protocol,
and the wrapper auto-skips after MAX_BLOCKED_ITERATIONS consecutive
blocks on the same task.

Mirrors the file-reading style of test_manual_deploy_integration.py — no
subprocess execution; behavioral verification is via documented manual
smoke test and the EXECUTE-PLAN.md protocol contract."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUN_RALPH = REPO_ROOT / "scripts" / "autopilot" / "run-ralph.sh"
SCRIPT_TEXT = RUN_RALPH.read_text(encoding="utf-8")


def test_startup_cleanup_removes_only_done_sentinel():
    # The unattended autopilot has no human-blocked sentinel. Startup
    # cleanup removes only .ralph-done.
    assert "rm -f .ralph-done" in SCRIPT_TEXT, (
        "Startup cleanup must remove .ralph-done"
    )


def test_human_blocked_sentinel_fully_removed():
    # Policy enforcement: .ralph-human-blocked must not appear anywhere
    # in run-ralph.sh — not in cleanup, not in detection, not in messages.
    assert ".ralph-human-blocked" not in SCRIPT_TEXT, (
        "run-ralph.sh must not reference .ralph-human-blocked — the "
        "autopilot contract is that the loop never halts for human input. "
        "Needs-human cases route through the 🔄 BLOCKED retry path."
    )


def test_no_user_action_required_banner():
    # The banner that signaled the broken halt path is gone.
    assert "User Action Required" not in SCRIPT_TEXT, (
        "run-ralph.sh must not print 'User Action Required' — autopilot is "
        "unattended; tasks needing human action auto-skip after the cap."
    )


def test_max_blocked_iterations_constant_present():
    # The wrapper-side retry cap that replaces the halt mechanism.
    assert "MAX_BLOCKED_ITERATIONS" in SCRIPT_TEXT, (
        "run-ralph.sh must define MAX_BLOCKED_ITERATIONS (default 3); "
        "this is the auto-skip threshold replacing the halt mechanism."
    )


def test_auto_skip_marker_present():
    # After N consecutive 🔄 marks on a task, the wrapper rewrites the
    # heading to ⏭️ and continues. Static-parse for the marker.
    assert "⏭️" in SCRIPT_TEXT, (
        "run-ralph.sh must use ⏭️ as the auto-skip heading marker."
    )
    assert "AUTO-SKIPPED" in SCRIPT_TEXT, (
        "run-ralph.sh must record `AUTO-SKIPPED` reason in the task body."
    )


def test_worktree_drift_breadcrumb_present():
    # Per the root-cause investigation: worktree drift gets misdiagnosed
    # as "main is broken." A git-log breadcrumb at iteration start makes
    # the drift visible so future misdiagnoses are debuggable.
    assert "main..HEAD" in SCRIPT_TEXT or "HEAD..origin/main" in SCRIPT_TEXT, (
        "run-ralph.sh must print a worktree-drift breadcrumb (commits in "
        "worktree relative to main) at iteration start."
    )


def test_done_path_unchanged():
    # Regression guard: the complete-path message and handoff
    # recommendation must be preserved.
    assert "=== Ralph Loop Complete ===" in SCRIPT_TEXT
    assert "/aligned:finishing-a-development-branch" in SCRIPT_TEXT


def test_run_ralph_sources_lib_process():
    assert 'source "$SCRIPT_DIR/lib/process.sh"' in SCRIPT_TEXT or \
           'source "$(dirname "$0")/lib/process.sh"' in SCRIPT_TEXT, \
        "run-ralph.sh must source lib/process.sh"


def test_run_ralph_uses_set_u_only():
    # Decision 7: standardize on set -u across all callers
    assert "set -u" in SCRIPT_TEXT, "run-ralph.sh must declare 'set -u'"
    assert "set -euo pipefail" not in SCRIPT_TEXT, \
        "run-ralph.sh must not use 'set -euo pipefail' (Decision 7)"

# Autopilot is parked: non-functional since 0.33.0, retained for possible
# future revival. Its tests are skipped so the suite gates only active
# plugin surface. To revive, delete this block (and its counterparts in
# the other autopilot/ralph test files).
import pytest as _pytest_parked
pytestmark = _pytest_parked.mark.skip(
    reason="autopilot parked (non-functional since 0.33.0; see README changelog)"
)
