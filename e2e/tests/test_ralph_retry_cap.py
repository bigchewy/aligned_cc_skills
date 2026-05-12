"""Static-parse tests for the wrapper-side retry cap that replaces the
.ralph-human-blocked halt path.

Contract: after MAX_BLOCKED_ITERATIONS (default 3) consecutive 🔄 marks
on the same task, run-ralph.sh rewrites the heading to ⏭️ AUTO-SKIPPED
and continues. This honors the unattended-autopilot policy (no mid-run
human intervention) while preventing infinite loops on genuinely-stuck
tasks (OAuth, dead API).

State persistence: the consecutive-block counter is tracked per task via
the `> BLOCKED:` marker in the task body, so it survives across
iterations and worktree state without a separate state file."""

from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUN_RALPH = REPO_ROOT / "docs" / "ralph_loops" / "run-ralph.sh"
SCRIPT_TEXT = RUN_RALPH.read_text(encoding="utf-8")


def test_max_blocked_iterations_default_is_three():
    # Default 3 covers transient blockers without burning cycles on
    # genuinely-stuck tasks.
    assert 'MAX_BLOCKED_ITERATIONS="${MAX_BLOCKED_ITERATIONS:-3}"' in SCRIPT_TEXT, (
        "MAX_BLOCKED_ITERATIONS must be declared with default 3 via "
        '`MAX_BLOCKED_ITERATIONS="${MAX_BLOCKED_ITERATIONS:-3}"`.'
    )


def test_auto_skip_marker_used():
    assert "⏭️" in SCRIPT_TEXT, (
        "run-ralph.sh must use ⏭️ as the auto-skip heading marker "
        "(distinct from ✅ success and 🔄 retry)."
    )


def test_auto_skip_records_reason():
    # The auto-skip rewrite appends `> AUTO-SKIPPED: <reason>` to the
    # task body so the verify phase can surface the reason to the user.
    assert "AUTO-SKIPPED" in SCRIPT_TEXT, (
        "run-ralph.sh must emit `> AUTO-SKIPPED:` when capping a task."
    )


def test_blocked_marker_referenced():
    # The cap parses `> BLOCKED:` markers (the existing 🔄 retry path's
    # body line) to count consecutive blocks per task.
    assert "BLOCKED" in SCRIPT_TEXT, (
        "run-ralph.sh must read `> BLOCKED:` markers to enforce the "
        "consecutive-block cap."
    )


def test_blocked_path_does_not_halt():
    # Sanity: the retry-cap implementation must not reintroduce a halt
    # sentinel or 'User Action Required' message by accident.
    assert ".ralph-human-blocked" not in SCRIPT_TEXT
    assert "User Action Required" not in SCRIPT_TEXT
