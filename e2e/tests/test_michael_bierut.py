"""Michael Bierut: the board's first visual identity advisor.

He makes logo marks, decides how a set of sibling brands look next to each other, and judges
whether a mark still works at 16 pixels and on a book spine. He ships with three frameworks:
Boil It Down (find what the product already has and cut it down to a mark), How Much the
Siblings Share (Olins's three types and Aaker's test, then a share list), and The Small-Size and
Print Test (Haviv's three tests, the doodle test, sizes, one-color print, and Albers's rule for
color). Borrowed rules are credited by name. Quotes the research could not confirm stay out of
every prompt.
"""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "michael-bierut.md"
RESEARCH = REPO_ROOT / "docs" / "advisors" / "new_advisors" / "v_michael-bierut.md"
CONSULT = REPO_ROOT / "e2e" / "scenarios" / "use-advisor" / "michael-bierut-consult.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"

FRAMEWORKS = {
    "boil-it-down": ("Boil It Down", "plan"),
    "how-much-siblings-share": ("How Much the Siblings Share", "decision"),
    "small-size-and-print-test": ("The Small-Size and Print Test", "analysis"),
}

UNCONFIRMED = (
    "a way to say, 'This is me.'",
    "world of associations",
    "process of distillation",
    "It doesn't mean much until you get to know the person",
)

HANDOFFS = ("Don Draper", "Steve Jobs", "Adham Dannaway", "Brad Frost", "Steve Krug", "James Gurney")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _phases(text: str) -> dict:
    parts = re.split(r"^### PHASE (\d+):", text, flags=re.MULTILINE)
    return {int(parts[i]): parts[i + 1].split("## Key Rules")[0] for i in range(1, len(parts), 2)}


def _advisor_entry():
    with open(REPO_ROOT / "advisors" / "registry.yaml") as f:
        return {x["id"]: x for x in yaml.safe_load(f)["advisors"]}.get("michael-bierut")


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
    assert e is not None, "michael-bierut missing from advisors/registry.yaml"
    assert e["name"] == "Michael Bierut"
    assert e["prompt"] == "advisors/prompts/michael-bierut.md"
    assert "visual-identity" in e["domains"]
    for word in ("logo", "sibling", "small", "color"):
        assert word in e["best_for"].lower(), f"best_for should mention {word}"
    for name in HANDOFFS:
        assert name in e["not_for"], f"not_for should send work to {name}"
    assert e.get("evaluation_expertise")


def test_advisor_prompt_opens_with_who_he_is():
    first = _read(ADVISOR).splitlines()[0]
    assert first.startswith("You are Michael Bierut")
    assert "Pentagram" in first


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


def test_advisor_commits_to_one_mark():
    lower = _read(ADVISOR).lower()
    assert "pick one" in lower or "commit" in lower
    assert "hedg" in lower


def test_advisor_hands_off_to_neighbors():
    text = _read(ADVISOR)
    for name in HANDOFFS:
        assert name in text, f"advisor prompt should hand off to {name}"


def test_borrowed_rules_are_credited():
    text = _all_prompt_text()
    for name in ("Sagi Haviv", "Wally Olins", "David Aaker", "Josef Albers", "Penguin"):
        assert name in text, f"prompts should credit {name}"


def test_unconfirmed_quotes_stay_out():
    text = _all_prompt_text()
    for quote in UNCONFIRMED:
        assert quote not in text, f"unconfirmed quote in prompts: {quote}"


def test_first_project_stays_out_of_prompts():
    text = _all_prompt_text()
    for name in ("Moments With", "Before You Came Along"):
        assert name not in text, f"{name} belongs in evals, not prompts"


def test_consult_scenario_exists_and_is_wired():
    assert CONSULT.is_file()
    assert "advisors/prompts/michael-bierut.md" in _read(CONSULT)
    flat = yaml.safe_dump(yaml.safe_load(_read(TRIGGER_MAP)))
    assert "advisors/prompts/michael-bierut.md" in flat
    assert "scenarios/use-advisor/michael-bierut-consult.yaml" in flat


def test_advisor_readme_lists_him():
    readme = _read(REPO_ROOT / "advisors" / "README.md")
    assert "| michael-bierut | Michael Bierut |" in readme
    assert "| **Michael Bierut** |" in readme


# --- frameworks ------------------------------------------------------------


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_framework_files_exist(fid):
    for name in ("prompt.md", "examples.md", "anti-examples.md"):
        assert (REPO_ROOT / "frameworks" / fid / name).is_file(), f"missing {fid}/{name}"


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_framework_registry_entry(fid):
    name, deliverable = FRAMEWORKS[fid]
    e = _framework_entries()[fid]
    assert e["advisor"] == "michael-bierut"
    assert e["name"] == name
    assert e["category"] == "visual-identity"
    assert e["deliverable_type"] == deliverable
    assert "michael-bierut" in e.get("default_critic_advisors", [])


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_framework_readme_lists_it(fid):
    name, _ = FRAMEWORKS[fid]
    readme = _read(REPO_ROOT / "frameworks" / "README.md")
    assert f"| {fid} | {name} | michael-bierut | visual-identity |" in readme
    assert f"- **{fid}** — {name} (michael-bierut)" in readme


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_framework_prompt_opens_in_the_standard_form(fid):
    name, _ = FRAMEWORKS[fid]
    text = _read(REPO_ROOT / "frameworks" / fid / "prompt.md")
    first = [l for l in text.split("---", 2)[2].splitlines() if l.strip()][0]
    assert first.startswith(f"You are Michael Bierut, guiding someone through {name} - ")


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


def test_boil_it_down_starts_from_the_product_and_bans_the_category_cliche():
    lower = _read(REPO_ROOT / "frameworks" / "boil-it-down" / "prompt.md").lower()
    assert "already has" in lower
    assert "cliché" in lower or "cliche" in lower
    assert "almost unfinished" in lower
    assert "if you have a great idea but can't make it work, it isn't a great idea" in lower


def test_siblings_uses_olins_types_aaker_test_and_a_share_list():
    lower = _read(REPO_ROOT / "frameworks" / "how-much-siblings-share" / "prompt.md").lower()
    for word in ("monolithic", "endorsed", "branded"):
        assert word in lower
    assert "add anything" in lower and "own name" in lower
    for part in ("name", "mark", "type", "color"):
        assert f"**{part}:**" in lower, f"share list should cover {part}"


def test_small_size_test_covers_sizes_print_and_color():
    lower = _read(REPO_ROOT / "frameworks" / "small-size-and-print-test" / "prompt.md").lower()
    for word in ("appropriate", "distinctive", "simple", "from memory", "16", "home-screen",
                 "spine", "one color", "4.5:1", "3:1", "next to"):
        assert word in lower, f"small-size test should cover {word}"
