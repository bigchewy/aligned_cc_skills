"""FEW HICCUPPS Review: Michael Bolton runs a design doc through his oracles.

Runs on a design doc, a feature, or an existing screen before (or instead of)
building more. One person, 20-40 minutes. The phases walk the eleven FEW
HICCUPPS consistency oracles in groups, with Claims and History used to check
what the doc says about the codebase against the code itself. Each finding
names the oracle it rests on, because an inconsistency points to a possible
problem, not a proven one. Passing checks (Eric's TDD tests) are welcome; the
review looks for what they miss. The original HICCUPPS list is James Bach's;
the prompt credits him.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = REPO_ROOT / "frameworks" / "few-hiccupps-review"
PROMPT = FRAMEWORK / "prompt.md"
EXAMPLES = FRAMEWORK / "examples.md"
ANTI = FRAMEWORK / "anti-examples.md"
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "michael-bolton.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / "few-hiccupps-review.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"

ORACLES = ("familiarity", "explainability", "world", "history", "image", "comparable products",
           "claims", "user desires", "product", "purpose", "statutes and standards")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _phases(text: str) -> dict:
    parts = re.split(r"^### PHASE (\d+):", text, flags=re.MULTILINE)
    return {int(parts[i]): parts[i + 1].split("## Key Rules")[0] for i in range(1, len(parts), 2)}


def test_framework_files_exist():
    for p in (PROMPT, EXAMPLES, ANTI):
        assert p.is_file(), f"missing {p.relative_to(REPO_ROOT)}"


def test_registry_entry():
    with open(REPO_ROOT / "frameworks" / "registry.yaml") as f:
        e = {x["id"]: x for x in yaml.safe_load(f)["frameworks"]}["few-hiccupps-review"]
    assert e["advisor"] == "michael-bolton"
    assert e["name"] == "FEW HICCUPPS Review"
    assert e["category"] == "product-design"
    assert e["deliverable_type"] == "analysis"
    assert "michael-bolton" in e.get("default_critic_advisors", [])


def test_readme_lists_the_framework():
    readme = _read(REPO_ROOT / "frameworks" / "README.md")
    assert "| few-hiccupps-review | FEW HICCUPPS Review | michael-bolton |" in readme
    assert "- **few-hiccupps-review** — FEW HICCUPPS Review (michael-bolton)" in readme


def test_prompt_opens_in_the_standard_form():
    first = [l for l in _read(PROMPT).split("---", 2)[2].splitlines() if l.strip()][0]
    assert first.startswith("You are Michael Bolton, guiding someone through FEW HICCUPPS Review - ")


def test_every_phase_waits_for_the_user():
    phases = _phases(_read(PROMPT))
    assert len(phases) >= 5
    for n, body in phases.items():
        assert "**WAIT for the user to respond.**" in body, f"PHASE {n} has no WAIT"


def test_prompt_has_scripts_breaks_and_key_rules():
    text = _read(PROMPT)
    assert text.count("Say something like:") >= len(_phases(text))
    assert text.count("\n---\n") >= len(_phases(text))
    assert "## Key Rules" in text


def test_prompt_names_all_eleven_oracles():
    text = _read(PROMPT).lower()
    for oracle in ORACLES:
        assert oracle in text, f"prompt should name the {oracle} oracle"


def test_prompt_checks_the_docs_claims_against_the_code():
    text = _read(PROMPT).lower()
    assert "claims" in text and "codebase" in text
    assert "read the code" in text or "open the file" in text


def test_prompt_treats_oracles_as_fallible_and_credits_bach():
    text = _read(PROMPT)
    lower = text.lower()
    assert "heuristic" in lower
    assert "doesn't guarantee that there's a problem" in lower or "not proof" in lower
    assert "James Bach" in text


def test_prompt_welcomes_checks_and_hands_off():
    text = _read(PROMPT)
    lower = text.lower()
    assert "checks" in lower and "tdd" in lower
    for handoff in ("The Architect", "The Security Reviewer", "Steve Krug"):
        assert handoff in text, f"prompt should hand off to {handoff}"


def test_examples_cover_golden_struggle_and_edge():
    text = _read(EXAMPLES).lower()
    assert "golden path" in text and "struggle" in text and "edge case" in text
    assert text.count("why it works") >= 6


def test_anti_examples_cover_the_failure_modes():
    anti = _read(ANTI)
    lower = anti.lower()
    sections = re.findall(r"^## \d+\.", anti, flags=re.MULTILINE)
    assert 3 <= len(sections) <= 5
    for part in ("**User:**", "**Wrong:**", "**Right:**", "**What to do instead:**"):
        assert anti.count(part) == len(sections), f"every anti-example needs {part}"
    for failure in ("stop writing", "proof", "codebase", "pass", "every oracle"):
        assert failure in lower, f"anti-examples should cover {failure}"


def test_advisor_prompt_lists_the_framework():
    assert "`few-hiccupps-review`" in _read(ADVISOR)


def test_scenario_exists_and_is_wired():
    assert SCENARIO.is_file()
    assert "frameworks/few-hiccupps-review/prompt.md" in _read(SCENARIO)
    flat = yaml.safe_dump(yaml.safe_load(_read(TRIGGER_MAP)))
    for p in ("frameworks/few-hiccupps-review/prompt.md", "frameworks/few-hiccupps-review/examples.md",
              "frameworks/few-hiccupps-review/anti-examples.md"):
        assert p in flat
    assert "scenarios/use-framework/few-hiccupps-review.yaml" in flat
