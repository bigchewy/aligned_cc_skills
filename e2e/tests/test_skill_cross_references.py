"""Guards the bidirectional authorship-exception link between writing-plans
and finishing-a-development-branch SKILL.md files. A silent rename of either
side breaks the contract; this test catches it in CI."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WRITING_PLANS = REPO_ROOT / "skills" / "writing-plans" / "SKILL.md"
FINISHING = REPO_ROOT / "skills" / "finishing-a-development-branch" / "SKILL.md"


WRITING_PLANS_REQUIRED = (
    "Step 0.5 of ",
    "finishing-a-development-branch",
    "out-of-skill plan mutation",
)

FINISHING_REQUIRED = (
    "writing-plans/SKILL.md",
    "out-of-skill plan mutation",
    "Step 0.5: Manual Deploy Artifact Gate",
)


@pytest.mark.parametrize("needle", WRITING_PLANS_REQUIRED)
def test_writing_plans_mentions_exception(needle):
    text = WRITING_PLANS.read_text(encoding="utf-8")
    assert needle in text, (
        f"writing-plans/SKILL.md is missing required string: {needle!r}. "
        f"This guards the bidirectional authorship-exception link with "
        f"finishing-a-development-branch/SKILL.md."
    )


@pytest.mark.parametrize("needle", FINISHING_REQUIRED)
def test_finishing_mentions_exception(needle):
    text = FINISHING.read_text(encoding="utf-8")
    assert needle in text, (
        f"finishing-a-development-branch/SKILL.md is missing required string: "
        f"{needle!r}. This guards the bidirectional authorship-exception link "
        f"with writing-plans/SKILL.md."
    )
