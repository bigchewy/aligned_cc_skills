"""Cole Nussbaumer Knaflic: the board's first data visualization advisor.

She decides what chart to draw, what to cut from it, where the eye should land, and what its
title should say. She ships with three frameworks: Declutter and Focus (gray first, cut the
clutter, one accent color, a takeaway title, then the where-are-your-eyes-drawn test), Choose
an Effective Visual (name the comparison, then pick bar, line, slopegraph or dot plot, or pie),
and The Big Idea and Takeaway Title (who and what, the 3-minute story, one sentence, then each
chart title rewritten as the so-what). Practices from her storytelling with data team are
taught as SWD practice and credited to the team member who wrote them. Only her own words are
quoted as hers.
"""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "cole-nussbaumer-knaflic.md"
RESEARCH = REPO_ROOT / "docs" / "advisors" / "new_advisors" / "v_cole-nussbaumer-knaflic.md"
CONSULT = REPO_ROOT / "e2e" / "scenarios" / "use-advisor" / "cole-nussbaumer-knaflic-consult.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"

FRAMEWORKS = {
    "declutter-and-focus": ("Declutter and Focus", "plan"),
    "choose-an-effective-visual": ("Choose an Effective Visual", "decision"),
    "big-idea-and-takeaway-title": ("The Big Idea and Takeaway Title", "content"),
}

# Seen only in promo text or search snippets, never on a page in her own voice.
UNCONFIRMED = (
    "one exploding 3D pie chart at a time",
    "People Analytics",
    "pie charts are evil",
)

HANDOFFS = ("Adham Dannaway", "Brad Frost", "Steve Krug")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _phases(text: str) -> dict:
    parts = re.split(r"^### PHASE (\d+):", text, flags=re.MULTILINE)
    return {int(parts[i]): parts[i + 1].split("## Key Rules")[0] for i in range(1, len(parts), 2)}


def _advisor_entry():
    with open(REPO_ROOT / "advisors" / "registry.yaml") as f:
        return {x["id"]: x for x in yaml.safe_load(f)["advisors"]}.get("cole-nussbaumer-knaflic")


def _framework_entries():
    with open(REPO_ROOT / "frameworks" / "registry.yaml") as f:
        return {x["id"]: x for x in yaml.safe_load(f)["frameworks"]}


def _all_prompt_text() -> str:
    texts = [_read(ADVISOR)]
    for fid in FRAMEWORKS:
        for name in ("prompt.md", "examples.md", "anti-examples.md"):
            texts.append(_read(REPO_ROOT / "frameworks" / fid / name))
    return "\n".join(texts)


# --- advisor ---------------------------------------------------------------


def test_research_file_exists():
    assert RESEARCH.is_file()


def test_advisor_registry_entry():
    e = _advisor_entry()
    assert e is not None, "cole-nussbaumer-knaflic missing from advisors/registry.yaml"
    assert e["name"] == "Cole Nussbaumer Knaflic"
    assert e["prompt"] == "advisors/prompts/cole-nussbaumer-knaflic.md"
    assert "data-visualization" in e["domains"]
    for word in ("chart", "title", "color", "clutter"):
        assert word in e["best_for"].lower(), f"best_for should mention {word}"
    for name in HANDOFFS:
        assert name in e["not_for"], f"not_for should send work to {name}"
    assert e.get("evaluation_expertise")


def test_advisor_prompt_opens_with_who_she_is():
    first = _read(ADVISOR).splitlines()[0]
    assert first.startswith("You are Cole Nussbaumer Knaflic")
    assert "storytelling with data" in first


def test_advisor_prompt_has_standard_sections():
    text = _read(ADVISOR)
    for section in ("## The Voice", "## How You Speak", "## What You Do NOT Sound Like",
                    "## Signature Questions", "## Core Frameworks", "## Blind Spots You Surface",
                    "## Failure Modes"):
        assert section in text, f"advisor prompt missing {section}"


def test_advisor_prompt_lists_all_three_frameworks():
    text = _read(ADVISOR)
    for fid in FRAMEWORKS:
        assert f"`{fid}`" in text


def test_advisor_prompt_lists_unbuilt_candidates_as_conversation_only():
    lower = _read(ADVISOR).lower()
    assert "also available in conversation" in lower
    assert "storyboard" in lower
    assert "dashboard" in lower


def test_advisor_hands_off_to_neighbors():
    text = _read(ADVISOR)
    for name in HANDOFFS:
        assert name in text, f"advisor prompt should hand off to {name}"


def test_team_practices_are_credited_to_their_authors():
    text = _all_prompt_text()
    assert "storytelling with data" in text
    for name in ("Elizabeth Ricks", "Alex Velez", "Amy Esselman", "Mike Cisneros"):
        assert name in text, f"prompts should credit {name}"
    assert "Nancy Duarte" in text, "the Big Idea comes from Duarte's Resonate"


def test_unconfirmed_lines_stay_out():
    text = _all_prompt_text()
    for line in UNCONFIRMED:
        assert line not in text, f"unconfirmed line in prompts: {line}"


def test_first_project_stays_out_of_prompts():
    lower = _all_prompt_text().lower()
    for word in ("symptom", "histamine"):
        assert word not in lower, f"{word} belongs in evals, not prompts"


def test_consult_scenario_exists_and_is_wired():
    assert CONSULT.is_file()
    assert "advisors/prompts/cole-nussbaumer-knaflic.md" in _read(CONSULT)
    flat = yaml.safe_dump(yaml.safe_load(_read(TRIGGER_MAP)))
    assert "advisors/prompts/cole-nussbaumer-knaflic.md" in flat
    assert "scenarios/use-advisor/cole-nussbaumer-knaflic-consult.yaml" in flat


def test_advisor_readme_lists_her():
    readme = _read(REPO_ROOT / "advisors" / "README.md")
    assert "| cole-nussbaumer-knaflic | Cole Nussbaumer Knaflic |" in readme
    assert "| **Cole Nussbaumer Knaflic** |" in readme


# --- frameworks ------------------------------------------------------------


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_framework_files_exist(fid):
    for name in ("prompt.md", "examples.md", "anti-examples.md", "sources.md"):
        assert (REPO_ROOT / "frameworks" / fid / name).is_file(), f"missing {fid}/{name}"


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_framework_registry_entry(fid):
    name, deliverable = FRAMEWORKS[fid]
    e = _framework_entries()[fid]
    assert e["advisor"] == "cole-nussbaumer-knaflic"
    assert e["name"] == name
    assert e["category"] == "data-visualization"
    assert e["deliverable_type"] == deliverable
    assert "cole-nussbaumer-knaflic" in e.get("default_critic_advisors", [])


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_framework_readme_lists_it(fid):
    name, _ = FRAMEWORKS[fid]
    readme = _read(REPO_ROOT / "frameworks" / "README.md")
    assert f"| {fid} | {name} | cole-nussbaumer-knaflic | data-visualization |" in readme
    assert f"- **{fid}** — {name} (cole-nussbaumer-knaflic)" in readme


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_framework_prompt_opens_in_the_standard_form(fid):
    name, _ = FRAMEWORKS[fid]
    text = _read(REPO_ROOT / "frameworks" / fid / "prompt.md")
    first = [l for l in text.split("---", 2)[2].splitlines() if l.strip()][0]
    assert first.startswith(f"You are Cole Nussbaumer Knaflic, guiding someone through {name} - ")


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_every_phase_waits_for_the_user(fid):
    text = _read(REPO_ROOT / "frameworks" / fid / "prompt.md")
    phases = _phases(text)
    assert len(phases) >= 5
    for n, body in phases.items():
        if n == max(phases):
            continue  # the closing phase hands over the result
        assert "**WAIT for the user to respond.**" in body, f"{fid} PHASE {n} has no WAIT"


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_prompt_has_scripts_breaks_and_key_rules(fid):
    text = _read(REPO_ROOT / "frameworks" / fid / "prompt.md")
    assert text.count("Say something like:") >= len(_phases(text))
    assert text.count("\n---\n") >= len(_phases(text))
    assert "## Key Rules" in text


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_examples_cover_golden_struggle_and_edge(fid):
    text = _read(REPO_ROOT / "frameworks" / fid / "examples.md").lower()
    assert "golden path" in text and "struggle" in text and "edge case" in text
    assert text.count("why it works") >= 6


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_anti_examples_have_the_standard_parts(fid):
    anti = _read(REPO_ROOT / "frameworks" / fid / "anti-examples.md")
    sections = re.findall(r"^## \d+\.", anti, flags=re.MULTILINE)
    assert 3 <= len(sections) <= 5
    for part in ("**User:**", "**Wrong:**", "**Right:**", "**What to do instead:**"):
        assert anti.count(part) == len(sections), f"{fid}: every anti-example needs {part}"


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_framework_scenario_exists_and_is_wired(fid):
    scenario = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / f"{fid}.yaml"
    assert scenario.is_file()
    assert f"frameworks/{fid}/prompt.md" in _read(scenario)
    flat = yaml.safe_dump(yaml.safe_load(_read(TRIGGER_MAP)))
    for name in ("prompt.md", "examples.md", "anti-examples.md"):
        assert f"frameworks/{fid}/{name}" in flat
    assert f"scenarios/use-framework/{fid}.yaml" in flat


def test_frameworks_hand_off_to_each_other():
    for fid in FRAMEWORKS:
        text = _read(REPO_ROOT / "frameworks" / fid / "prompt.md")
        others = [o for o in FRAMEWORKS if o != fid]
        assert any(f"`{o}`" in text for o in others), f"{fid} should name a sibling framework"


def test_declutter_and_focus_does_both_and_ends_with_the_eyes_test():
    lower = _read(REPO_ROOT / "frameworks" / "declutter-and-focus" / "prompt.md").lower()
    for word in ("gray", "gridlines", "legend", "one accent color", "title",
                 "where are your eyes drawn"):
        assert word in lower, f"declutter-and-focus should cover {word}"
    assert "2.5" in lower, "should cite the 2021 study: decluttering alone isn't enough"


def test_choose_an_effective_visual_names_the_comparison_first():
    lower = _read(REPO_ROOT / "frameworks" / "choose-an-effective-visual" / "prompt.md").lower()
    for word in ("categories", "over time", "two points", "part-to-whole", "bar", "line",
                 "slopegraph", "dot plot", "pie", "zero", "spaghetti"):
        assert word in lower, f"choose-an-effective-visual should cover {word}"


def test_big_idea_covers_audience_story_sentence_and_titles():
    lower = _read(REPO_ROOT / "frameworks" / "big-idea-and-takeaway-title" / "prompt.md").lower()
    for word in ("exploratory", "explanatory", "who", "3-minute story", "one sentence",
                 "so what"):
        assert word in lower, f"big-idea-and-takeaway-title should cover {word}"
