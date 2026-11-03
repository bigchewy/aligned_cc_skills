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
    assert phase2.count("WAIT for user response before continuing.") == 1
    assert "/aligned:use-framework build-measure-learn" in phase2
    assert "Right?" not in phase2


def test_build_measure_learn_lists_leap_of_faith_output_as_helpful_document():
    helpful = registry()["build-measure-learn"]["helpful_documents"]
    assert {"doc": "leap-of-faith-assumptions results", "from": "leap-of-faith-assumptions"} in helpful
    frontmatter = prompt("build-measure-learn").split("---")[1]
    assert "leap-of-faith-assumptions results" in yaml.safe_load(frontmatter)["helpful_documents"]


def writers_of(framework_id):
    """Every framework id named in a `from` of this framework's documents."""
    entry = registry()[framework_id]
    return [
        w
        for key in ("required_documents", "helpful_documents")
        for d in entry.get(key) or []
        for w in ([d["from"]] if isinstance(d["from"], str) else d["from"])
    ]


def test_leap_of_faith_hands_off_to_build_measure_learn():
    assert "leap-of-faith-assumptions" in writers_of("build-measure-learn")


def test_working_backwards_hands_off_to_getting_real_cut():
    assert "working-backwards" in writers_of("getting-real-cut")


# Handoffs that follow_on_frameworks used to carry. Each is now a document the
# first framework writes and the second one uses (writer, framework that takes it).
RETIRED_FOLLOW_ONS = [
    ("80-20-audit", "zone-of-genius"),
    ("build-measure-learn", "pivot-or-persevere"),
    ("finding-the-crux", "kernel-of-good-strategy"),
    ("four-market-types", "earlyvangelists"),
    ("four-market-types", "leap-of-faith-assumptions"),
    ("ice-prioritization", "growth-hacking-process"),
    ("mobilizer-taxonomy", "teach-tailor-take-control"),
    ("origin-story-interview", "5-components-positioning"),
    ("origin-story-interview", "strategic-narrative"),
    ("product-market-fit-test", "pivot-or-persevere"),
    ("buyer-persona", "teach-tailor-take-control"),
    ("messaging-distillation", "sales-pitch-structure"),
    ("blue-ocean-value-props", "5-components-positioning"),
    ("blue-ocean-value-props", "value-metric"),
    ("launch-bet", "pivot-or-persevere"),
    ("phantom-b-llm-threats", "four-question-threat-model"),
    ("how-much-siblings-share", "boil-it-down"),
    ("how-much-siblings-share", "small-size-and-print-test"),
    ("choose-an-effective-visual", "declutter-and-focus"),
    ("why-my-page-doesnt-rank", "ai-search-optimization-checklist"),
]


def test_retired_follow_ons_became_document_links():
    missing = [(a, b) for a, b in RETIRED_FOLLOW_ONS if a not in writers_of(b)]
    assert not missing, missing
