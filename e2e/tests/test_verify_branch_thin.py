"""Verifies VERIFY-BRANCH.md was collapsed to a thin wrapper after the
verify-gate triplication was eliminated."""

from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VERIFY = REPO_ROOT / "scripts" / "autopilot" / "VERIFY-BRANCH.md"


def _read() -> str:
    return VERIFY.read_text(encoding="utf-8")


def test_verify_branch_is_thin():
    text = _read()
    # After collapse, the file is a wrapper — should be much shorter than
    # the pre-collapse 123 lines.
    assert len(text.splitlines()) < 60, \
        "VERIFY-BRANCH.md should be a thin wrapper (<60 lines) after Decision 8 collapse"


def test_verify_branch_delegates_to_finishing_skill():
    text = _read()
    assert "skills/finishing-a-development-branch/SKILL.md" in text, \
        "VERIFY-BRANCH.md must point at the canonical finishing skill"


def test_verify_branch_preserves_verify_only_scope():
    text = _read()
    # Must still forbid merge/cleanup/archive
    for forbid in ("Do NOT merge", "Do NOT clean up worktrees", "Do NOT archive"):
        assert forbid in text, f"VERIFY-BRANCH.md must still state: {forbid}"


def test_verify_branch_writes_finish_status():
    text = _read()
    assert ".finish-status" in text, \
        "VERIFY-BRANCH.md must still write .finish-status (autopilot reads it)"
