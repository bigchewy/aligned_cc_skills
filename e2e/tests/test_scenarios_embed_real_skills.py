"""Scenarios that grade a skill's behavior must embed that skill's real files.

The frozen brainstorming classifier fixture holds only the three-mode picker. A scenario
that grades authoring-mode or use-framework behavior against it grades instructions the
model never saw, and it never notices when the real skill changes.
"""

from pathlib import Path

import pytest
import yaml

E2E_DIR = Path(__file__).resolve().parent.parent
FROZEN = "fixtures/skill-prompts/brainstorming-three-modes.md"

AUTHORING = [
    "../../../skills/brainstorming/SKILL.md",
    "../../../skills/brainstorming/modes/authoring.md",
]

USE_FRAMEWORK = [
    "../../../skills/use-framework/SKILL.md",
    "../../../skills/_shared/framework-runner.md",
    "../../../frameworks/5-components-positioning/prompt.md",
]

REQUIRED = {
    "scenarios/use-skill/authoring-mode-engine-selection.yaml": AUTHORING
    + ["../../../skills/_shared/contextual-recommendation.md"],
    "scenarios/use-skill/deliverable-type-dispatch.yaml": AUTHORING,
    "scenarios/use-skill/authoring-no-framework-fallback.yaml": AUTHORING,
    "scenarios/use-skill/use-framework-backward-compat.yaml": USE_FRAMEWORK,
    "scenarios/use-skill/framework-runner-extraction.yaml": USE_FRAMEWORK,
    "scenarios/use-skill/always-ask-routing.yaml": ["../../../skills/brainstorming/SKILL.md"],
    "scenarios/use-skill/brainstorming-three-modes.yaml": ["../../../skills/brainstorming/SKILL.md"],
    "scenarios/use-skill/deck-routing.yaml": ["../../../skills/brainstorming/SKILL.md"],
}


def _file_vars(scenario):
    data = yaml.safe_load((E2E_DIR / scenario).read_text())
    for test in data["tests"]:
        yield test["description"], {
            v[len("file://"):] for v in test["vars"].values()
            if isinstance(v, str) and v.startswith("file://")
        }


@pytest.mark.parametrize("scenario", sorted(REQUIRED))
def test_scenario_does_not_embed_frozen_classifier(scenario):
    for desc, files in _file_vars(scenario):
        assert not any(f.endswith(FROZEN) for f in files), f"{scenario} / {desc} embeds {FROZEN}"


@pytest.mark.parametrize("scenario", sorted(REQUIRED))
def test_scenario_embeds_real_skill_files(scenario):
    for desc, files in _file_vars(scenario):
        missing = [f for f in REQUIRED[scenario] if f not in files]
        assert not missing, f"{scenario} / {desc} is missing {missing}"


@pytest.mark.parametrize("scenario", sorted(REQUIRED))
def test_embedded_files_exist_and_prompt_uses_them(scenario):
    data = yaml.safe_load((E2E_DIR / scenario).read_text())
    prompt = data["prompts"][0]
    for test in data["tests"]:
        for name, value in test["vars"].items():
            if isinstance(value, str) and value.startswith("file://../../../"):
                path = (E2E_DIR / "scenarios/use-skill" / value[len("file://"):]).resolve()
                assert path.is_file(), f"{scenario}: {value} does not exist"
                assert "{{" + name + "}}" in prompt, f"{scenario}: prompt never uses var {name}"


def test_frozen_classifier_is_gone_and_no_scenario_embeds_it():
    assert not (E2E_DIR / FROZEN).exists(), f"{FROZEN} should be deleted; scenarios embed the real skill"
    for scenario in sorted((E2E_DIR / "scenarios").rglob("*.yaml")):
        assert FROZEN not in scenario.read_text(), f"{scenario.relative_to(E2E_DIR)} embeds {FROZEN}"


def test_deck_routing_rubric_matches_the_real_three_way_picker():
    text = (E2E_DIR / "scenarios/use-skill/deck-routing.yaml").read_text()
    assert "4-way" not in text and "Design a code change" not in text
    for label in ["Write a document", "Synthesize research", "Break a big intent into a queue of brainstorms"]:
        assert label in text, f"deck-routing rubric is missing picker label: {label}"
