"""Static-parse tests for EXECUTE-PLAN.md under the unattended-autopilot
contract.

The iteration prompt must NOT mention `.ralph-human-blocked` (removed),
must NOT instruct the agent to halt for human action, and MUST include
an explicit unattended preamble forbidding halt-sentinel writes."""

from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXECUTE_PLAN = REPO_ROOT / "scripts" / "autopilot" / "EXECUTE-PLAN.md"
DOC_TEXT = EXECUTE_PLAN.read_text(encoding="utf-8")


def test_no_human_blocked_sentinel_reference():
    assert ".ralph-human-blocked" not in DOC_TEXT, (
        "EXECUTE-PLAN.md must not reference .ralph-human-blocked — the "
        "halt sentinel was removed; needs-human cases route through the "
        "🔄 BLOCKED retry path with wrapper-side auto-skip."
    )


def test_no_halting_loop_instruction():
    assert "Halting loop" not in DOC_TEXT, (
        "EXECUTE-PLAN.md must not include the 'Halting loop' instruction."
    )


def test_unattended_preamble_present():
    # The iteration prompt must explicitly state the autopilot context.
    lower = DOC_TEXT.lower()
    assert "unattended" in lower, (
        "EXECUTE-PLAN.md must include an 'unattended' preamble per the "
        "no-human-intervention autopilot policy."
    )
    assert (
        "never request human action" in lower
        or "never write halt sentinels" in lower
        or "do not request human action" in lower
    ), (
        "EXECUTE-PLAN.md preamble must explicitly forbid requesting "
        "human action or writing halt sentinels."
    )


def test_blocked_retry_path_remains_documented():
    # The 🔄 BLOCKED retry path is the canonical response to "agent
    # can't proceed right now."
    assert "🔄" in DOC_TEXT, (
        "EXECUTE-PLAN.md must keep the 🔄 BLOCKED retry path."
    )
    assert "BLOCKED" in DOC_TEXT, (
        "EXECUTE-PLAN.md must document the `> BLOCKED:` marker."
    )


def test_done_sentinel_still_documented():
    # Regression: .ralph-done is the sole sentinel under the new contract.
    assert ".ralph-done" in DOC_TEXT, (
        "EXECUTE-PLAN.md must document the .ralph-done sentinel."
    )

# Autopilot is parked: non-functional since 0.33.0, retained for possible
# future revival. Its tests are skipped so the suite gates only active
# plugin surface. To revive, delete this block (and its counterparts in
# the other autopilot/ralph test files).
import pytest as _pytest_parked
pytestmark = _pytest_parked.mark.skip(
    reason="autopilot parked (non-functional since 0.33.0; see README changelog)"
)
