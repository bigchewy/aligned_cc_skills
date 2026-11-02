"""Hamilton Helmer: the board's moat and durable-advantage advisor.

Author of 7 Powers. He tests whether an advantage is Power: a benefit (lower cost or higher
price) plus a barrier that stops competitors copying it, big enough to matter. He ships with
three frameworks: The Benefit and Barrier Test (castle or shack), the Power Progression Check
(which powers are even available at your stage), and The Counter-Positioning Test (why the
incumbent won't copy you). His research rests on one full interview transcript; book-only
ideas are marked from memory and never quoted as his words.
"""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "hamilton-helmer.md"
RESEARCH = REPO_ROOT / "docs" / "advisors" / "new_advisors" / "v_hamilton-helmer.md"
CONSULT = REPO_ROOT / "e2e" / "scenarios" / "use-advisor" / "hamilton-helmer-consult.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"

FRAMEWORKS = {
    "benefit-and-barrier-test": "The Benefit and Barrier Test",
    "power-progression-check": "Power Progression Check",
    "counter-positioning-test": "The Counter-Positioning Test",
}

# Not found on any page read, or not tied to him by any source.
UNCONFIRMED = ("power intensity", "BASF", "Hitachi", "De Beers")

HANDOFFS = ("Richard Rumelt", "April Dunford", "Clayton Christensen")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _phases(text: str) -> dict:
    parts = re.split(r"^### PHASE (\d+):", text, flags=re.MULTILINE)
    return {int(parts[i]): parts[i + 1].split("## Key Rules")[0] for i in range(1, len(parts), 2)}


def _advisor_entry():
    with open(REPO_ROOT / "advisors" / "registry.yaml") as f:
        return {x["id"]: x for x in yaml.safe_load(f)["advisors"]}.get("hamilton-helmer")


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
    text = _read(RESEARCH)
    for section in ("## Sources", "## Voice", "## Framework candidates", "## From memory, not checked"):
        assert section in text


def test_advisor_registry_entry():
    e = _advisor_entry()
    assert e is not None
    assert e["name"] == "Hamilton Helmer"
    assert e["prompt"] == "advisors/prompts/hamilton-helmer.md"
    for field in ("best_for", "not_for", "evaluation_expertise", "summary"):
        assert e.get(field, "").strip(), f"hamilton-helmer needs {field}"
    assert "competitive-advantage" in e["domains"]


def test_advisor_prompt_opens_with_who_he_is():
    first = _read(ADVISOR).splitlines()[0]
    assert first.startswith("You are Hamilton Helmer, ")


def test_advisor_prompt_has_standard_sections():
    text = _read(ADVISOR)
    for section in (
        "## The Voice",
        "## How You Speak",
        "## What You Do NOT Sound Like",
        "## Signature Questions",
        "## Core Frameworks",
        "## Blind Spots You Surface",
        "## Failure Modes",
    ):
        assert section in text, f"missing {section}"


def test_advisor_prompt_carries_his_tools():
    lower = _read(ADVISOR).lower()
    for tool in ("benefit", "barrier", "material", "castle", "treadmill", "counter-positioning", "origination"):
        assert tool in lower, f"prompt should name {tool}"


def test_advisor_prompt_lists_all_three_frameworks():
    text = _read(ADVISOR)
    for fid in FRAMEWORKS:
        assert f"`{fid}`" in text


def test_advisor_prompt_lists_unbuilt_candidates_as_conversation_only():
    lower = _read(ADVISOR).lower()
    assert "also available in conversation" in lower
    assert "treadmill-or-power" in lower
    assert "seven-powers-audit" in lower


def test_advisor_hands_off_to_neighbors():
    text = _read(ADVISOR)
    for name in HANDOFFS:
        assert name in text, f"advisor prompt should hand off to {name}"


def test_quoted_voice_lines_are_in_the_research_file():
    research = " ".join(_read(RESEARCH).split())  # the research file wraps long quotes
    section = _read(ADVISOR).split("## How You Speak")[1].split("## What You Do NOT")[0]
    for quote in re.findall(r'"([^"]{12,})"', section):
        assert " ".join(quote.split()) in research, f"quoted line not in research: {quote}"


def test_unconfirmed_lines_stay_out():
    text = _all_prompt_text()
    for line in UNCONFIRMED:
        assert line.lower() not in text.lower(), f"unconfirmed line in prompts: {line}"


def test_first_project_stays_out_of_prompts():
    lower = _all_prompt_text().lower()
    for word in ("moments with", "illustrated", "recipient"):
        assert word not in lower, f"{word} belongs in evals, not prompts"


def test_consult_scenario_exists_and_is_wired():
    assert CONSULT.is_file()
    assert "advisors/prompts/hamilton-helmer.md" in _read(CONSULT)
    flat = yaml.safe_dump(yaml.safe_load(_read(TRIGGER_MAP)))
    assert "advisors/prompts/hamilton-helmer.md" in flat
    assert "scenarios/use-advisor/hamilton-helmer-consult.yaml" in flat


def test_advisor_readme_lists_him():
    readme = _read(REPO_ROOT / "advisors" / "README.md")
    assert "| hamilton-helmer | Hamilton Helmer |" in readme


# --- frameworks ------------------------------------------------------------


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_framework_files_exist(fid):
    for name in ("prompt.md", "examples.md", "anti-examples.md", "sources.md"):
        assert (REPO_ROOT / "frameworks" / fid / name).is_file(), f"missing {fid}/{name}"


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_framework_registry_entry(fid):
    e = _framework_entries()[fid]
    assert e["advisor"] == "hamilton-helmer"
    assert e["name"] == FRAMEWORKS[fid]
    assert e["category"] == "strategy"


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_framework_readme_lists_it(fid):
    readme = _read(REPO_ROOT / "frameworks" / "README.md")
    assert fid in readme


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_framework_prompt_opens_in_the_standard_form(fid):
    text = _read(REPO_ROOT / "frameworks" / fid / "prompt.md")
    first = [l for l in text.split("---", 2)[2].splitlines() if l.strip()][0]
    assert first.startswith(f"You are Hamilton Helmer, guiding someone through {FRAMEWORKS[fid]} - ")


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_every_phase_waits_for_the_user(fid):
    phases = _phases(_read(REPO_ROOT / "frameworks" / fid / "prompt.md"))
    assert len(phases) >= 4
    for n, body in phases.items():
        if n == max(phases):
            continue  # the closing phase hands over the result
        assert "**WAIT for the user to respond.**" in body, f"{fid} PHASE {n} has no WAIT"


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_prompt_has_artifact_and_key_rules(fid):
    text = _read(REPO_ROOT / "frameworks" / fid / "prompt.md")
    assert "## Artifact" in text
    assert "## Key Rules" in text


@pytest.mark.parametrize("fid", FRAMEWORKS)
def test_anti_examples_count(fid):
    anti = _read(REPO_ROOT / "frameworks" / fid / "anti-examples.md")
    assert 3 <= len(re.findall(r"^## ", anti, flags=re.MULTILINE)) <= 6


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


def test_benefit_and_barrier_asks_materiality_and_castle_or_shack():
    lower = _read(REPO_ROOT / "frameworks" / "benefit-and-barrier-test" / "prompt.md").lower()
    for word in ("benefit", "barrier", "material", "castle", "shack"):
        assert word in lower


def test_power_progression_strikes_the_late_powers_early():
    lower = _read(REPO_ROOT / "frameworks" / "power-progression-check" / "prompt.md").lower()
    for word in ("origination", "takeoff", "stability", "branding", "process power"):
        assert word in lower


def test_counter_positioning_asks_why_the_incumbent_wont_copy():
    lower = _read(REPO_ROOT / "frameworks" / "counter-positioning-test" / "prompt.md").lower()
    assert "incumbent" in lower
    assert "copy" in lower or "mimic" in lower
