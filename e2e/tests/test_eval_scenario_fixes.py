"""Two evals that failed for reasons in the eval, not the skill.

- authoring-mode-engine-selection, zero-match test: the scenario said only "no matching
  frameworks". The engine searches frameworks and advisors together, so the right answer
  depended on an advisor result the scenario never gave. Answers that assumed no advisor
  passed; answers that covered each advisor case were marked down for hedging.
- brainstorming-positioning: the skill arm embedded a copy of the retired business mode,
  and the rubric scored a finished deliverable. The real skill routes positioning to
  authoring mode, which asks and stops, so a one-shot vanilla answer always won.
"""

from pathlib import Path

import yaml

E2E = Path(__file__).resolve().parent.parent
AUTHORING = [
    "../../../skills/brainstorming/SKILL.md",
    "../../../skills/brainstorming/modes/authoring.md",
]


def load(rel):
    return yaml.safe_load((E2E / rel).read_text(encoding="utf-8"))


def test_zero_match_scenario_says_no_advisor_matched_either():
    data = load("scenarios/use-skill/authoring-mode-engine-selection.yaml")
    test = next(t for t in data["tests"] if "zero matches" in t["description"])
    assert "no matching advisors" in test["vars"]["scenario_description"]


def test_positioning_skill_arm_embeds_the_real_skill():
    data = load("scenarios/use-skill/brainstorming-positioning.yaml")
    arm = next(t for t in data["tests"] if t["metadata"]["arm"] == "full-stack")
    files = {v[len("file://"):] for v in arm["vars"].values() if isinstance(v, str) and v.startswith("file://")}
    for f in AUTHORING:
        assert f in files
    assert not any("brainstorming-business" in f for f in files)


def test_retired_business_mode_fixture_is_gone():
    assert not (E2E / "fixtures/skill-prompts/brainstorming-business.md").exists()


def test_positioning_rubric_scores_the_first_turn():
    text = (E2E / "scenarios/use-skill/brainstorming-positioning.yaml").read_text(encoding="utf-8")
    assert "PHASE DISCIPLINE" in text
    assert "DECISION READINESS" not in text
