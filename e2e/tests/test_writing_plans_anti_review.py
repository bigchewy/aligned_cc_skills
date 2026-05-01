"""Static-parse tests for the Mid-Flow Human Review anti-pattern enforcement."""

from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL = REPO_ROOT / "skills" / "writing-plans" / "SKILL.md"
CHECKLIST = REPO_ROOT / "skills" / "writing-plans" / "plan-critique-checklist.md"
PROMPTS = REPO_ROOT / "skills" / "writing-plans" / "references" / "critique-panel-prompts.md"

BANNED_PHRASES = [
    "human review",
    "user verifies",
    "review the UI",
    "wait for user",
    "confirm with user",
    "before proceeding ask",
    "user signs off",
    "get user approval",
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_skill_has_anti_pattern_section():
    text = _read(SKILL)
    assert "Mid-Flow Human Review" in text, \
        "writing-plans/SKILL.md must contain a 'Mid-Flow Human Review' section"


def test_skill_lists_banned_phrases():
    text = _read(SKILL).lower()
    # At minimum, three of the banned phrases must appear in the policy text
    hits = sum(1 for p in BANNED_PHRASES if p.lower() in text)
    assert hits >= 3, f"writing-plans must list banned phrasings; found {hits}"


def test_checklist_criterion_10_has_mid_flow_row():
    text = _read(CHECKLIST)
    # New row in the gap-analysis table OR a dedicated subsection
    assert "Mid-flow human review" in text or "human review" in text.lower(), \
        "Criterion 10 must reference mid-flow human review"


def test_verifier_prompt_has_mid_flow_review_check():
    text = _read(PROMPTS)
    assert "human review" in text.lower() or "user verifies" in text.lower(), \
        "Verifier prompt must include the mid-flow review check"
