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

REQUIRED = {
    "scenarios/use-skill/authoring-mode-engine-selection.yaml": AUTHORING
    + ["../../../skills/_shared/contextual-recommendation.md"],
    "scenarios/use-skill/deliverable-type-dispatch.yaml": AUTHORING,
    "scenarios/use-skill/authoring-no-framework-fallback.yaml": AUTHORING,
    "scenarios/use-skill/use-framework-backward-compat.yaml": [
        "../../../skills/use-framework/SKILL.md",
        "../../../skills/_shared/framework-runner.md",
        "../../../frameworks/5-components-positioning/prompt.md",
    ],
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
