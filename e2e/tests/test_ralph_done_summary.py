"""Static-parse test: when run-ralph.sh writes `.ralph-done` after any
task was auto-skipped (⏭️), the summary must include an
`## AUTO-SKIPPED tasks` section.

This is the single user-review surface for skipped items under the
unattended-autopilot contract (no mid-run intervention; user sees
results at end-of-run via verify phase + .ralph-done summary)."""

from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUN_RALPH = REPO_ROOT / "scripts" / "autopilot" / "run-ralph.sh"
SCRIPT_TEXT = RUN_RALPH.read_text(encoding="utf-8")


def test_done_summary_section_emitted():
    # The wrapper writes the literal heading "## AUTO-SKIPPED tasks"
    # into .ralph-done when capping any task.
    assert "AUTO-SKIPPED tasks" in SCRIPT_TEXT, (
        "run-ralph.sh must write an `## AUTO-SKIPPED tasks` section into "
        ".ralph-done when any task was auto-skipped — verify phase reads "
        "this to surface skipped items to the user."
    )


def test_done_sentinel_still_terminal():
    # Regression: the .ralph-done sentinel must still terminate the loop.
    assert "if [ -f .ralph-done ]" in SCRIPT_TEXT, (
        ".ralph-done must still be detected as the loop-complete sentinel."
    )

# Autopilot is parked: non-functional since 0.33.0, retained for possible
# future revival. Its tests are skipped so the suite gates only active
# plugin surface. To revive, delete this block (and its counterparts in
# the other autopilot/ralph test files).
import pytest as _pytest_parked
pytestmark = _pytest_parked.mark.skip(
    reason="autopilot parked (non-functional since 0.33.0; see README changelog)"
)
