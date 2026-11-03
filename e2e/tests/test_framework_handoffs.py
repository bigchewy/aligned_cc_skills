"""Framework handoffs: which framework runs before or after another.

leap-of-faith-assumptions runs first and finds the riskiest assumption.
build-measure-learn takes that assumption and does not look for its own.
working-backwards hands off to getting-real-cut.
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORKS = REPO_ROOT / "frameworks"


def prompt(framework_id):
    return (FRAMEWORKS / framework_id / "prompt.md").read_text()


def registry():
    data = yaml.safe_load((FRAMEWORKS / "registry.yaml").read_text())
    return {entry["id"]: entry for entry in data["frameworks"]}


def test_build_measure_learn_phase_2_takes_assumption_from_leap_of_faith():
    text = prompt("build-measure-learn")
    phase2 = text.split("### PHASE 2")[1].split("### PHASE 3")[0]
    assert "leap-of-faith-assumptions" in phase2
    assert "/aligned:use-framework leap-of-faith-assumptions" in phase2
    assert "What's the riskiest assumption in your initiative right now?" not in text
    assert "WAIT for user response before continuing." in phase2


def test_build_measure_learn_lists_leap_of_faith_output_as_helpful_document():
    assert "leap-of-faith-assumptions results" in registry()["build-measure-learn"]["helpful_documents"]
    frontmatter = prompt("build-measure-learn").split("---")[1]
    assert "leap-of-faith-assumptions results" in yaml.safe_load(frontmatter)["helpful_documents"]


def test_leap_of_faith_hands_off_to_build_measure_learn():
    assert "build-measure-learn" in registry()["leap-of-faith-assumptions"]["follow_on_frameworks"]


def test_working_backwards_hands_off_to_getting_real_cut():
    assert "getting-real-cut" in registry()["working-backwards"]["follow_on_frameworks"]
