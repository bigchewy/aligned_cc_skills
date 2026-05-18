"""Guards cross-skill references between writing-plans and
finishing-a-development-branch SKILL.md files. Previously enforced a
bidirectional 'Step 0.5 evidence write' authorship-exception link; that
exception was removed in 0.27.3 when Step 0.5 was downgraded from a
gate to a non-blocking notice. The test now guards the inverse: neither
file should resurrect the evidence-mutation language, since plan writes
are once again centralized in writing-plans."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WRITING_PLANS = REPO_ROOT / "skills" / "writing-plans" / "SKILL.md"
FINISHING = REPO_ROOT / "skills" / "finishing-a-development-branch" / "SKILL.md"


FORBIDDEN_IN_BOTH = (
    "out-of-skill plan mutation",
    "Manual Deploy Artifact Gate",
    "manual-deploy-ledger",
    "[evidence pending]",
)


@pytest.mark.parametrize("needle", FORBIDDEN_IN_BOTH)
def test_writing_plans_does_not_reintroduce_gate_language(needle):
    text = WRITING_PLANS.read_text(encoding="utf-8")
    assert needle not in text, (
        f"writing-plans/SKILL.md must not contain {needle!r}. The Step 0.5 "
        f"evidence gate was removed in 0.27.3; this guard prevents accidental "
        f"reintroduction."
    )


@pytest.mark.parametrize("needle", FORBIDDEN_IN_BOTH)
def test_finishing_does_not_reintroduce_gate_language(needle):
    text = FINISHING.read_text(encoding="utf-8")
    assert needle not in text, (
        f"finishing-a-development-branch/SKILL.md must not contain {needle!r}. "
        f"The Step 0.5 evidence gate was removed in 0.27.3; this guard prevents "
        f"accidental reintroduction."
    )


# Required cross-references — if either file is renamed, the linking prose
# rots silently. Each tuple is (source-file, expected-target-substring).
REQUIRED_CROSS_REFS = [
    (
        REPO_ROOT / "skills" / "finishing-a-development-branch" / "references" / "deployment-pitfall-catalog.md",
        "skills/_shared/manual-deploy-artifact-catalog.md",
    ),
    # Shared runners introduced in the framework-runner-refactor — three callers
    # depend on these paths resolving. Renaming either runner without updating
    # the callers would silently break invocation at runtime.
    (
        REPO_ROOT / "skills" / "use-framework" / "SKILL.md",
        "skills/_shared/framework-runner.md",
    ),
    (
        REPO_ROOT / "skills" / "use-advisor" / "SKILL.md",
        "skills/_shared/advisor-runner.md",
    ),
    (
        REPO_ROOT / "skills" / "brainstorming" / "modes" / "authoring.md",
        "skills/_shared/framework-runner.md",
    ),
]


@pytest.mark.parametrize("source,target_rel", REQUIRED_CROSS_REFS)
def test_cross_reference_link_resolves(source, target_rel):
    assert source.is_file(), f"source file missing: {source}"
    text = source.read_text(encoding="utf-8")
    assert target_rel in text, (
        f"{source.relative_to(REPO_ROOT)} must reference {target_rel!r}"
    )
    target = REPO_ROOT / target_rel
    assert target.is_file(), f"cross-reference target does not resolve: {target_rel}"
