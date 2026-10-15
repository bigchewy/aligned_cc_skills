"""Logic Check: Adham Dannaway names the rule behind every value.

Runs on a design-principles.md or an existing screen. Every value gets a rule
or a fix, using his published guidelines: colour by role and contrast, two
weights, no pure black, one primary button, never colour alone, brand colour
only on what you can click, one icon style, no disabled buttons, and the
Squint Test. Token fixes go to the design principles skill.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = REPO_ROOT / "frameworks" / "logic-check"
PROMPT = FRAMEWORK / "prompt.md"
EXAMPLES = FRAMEWORK / "examples.md"
ANTI = FRAMEWORK / "anti-examples.md"
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "adham-dannaway.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / "logic-check.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"


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
        e = {x["id"]: x for x in yaml.safe_load(f)["frameworks"]}["logic-check"]
    assert e["advisor"] == "adham-dannaway"
    assert e["name"] == "Logic Check"
    assert e["category"] == "product-design"
    assert e["deliverable_type"] == "analysis"


def test_prompt_opens_in_the_standard_form():
    first = [l for l in _read(PROMPT).split("---", 2)[2].splitlines() if l.strip()][0]
    assert first.startswith("You are Adham Dannaway, guiding someone through Logic Check - ")


def test_every_phase_waits_for_the_user():
    phases = _phases(_read(PROMPT))
    assert len(phases) >= 4
    for n, body in phases.items():
        assert "**WAIT for the user to respond.**" in body, f"PHASE {n} has no WAIT"


def test_prompt_checks_each_published_rule():
    text = _read(PROMPT)
    for rule in ("4.5:1", "3:1", "pure black", "regular and bold", "primary button", "colour alone",
                 "interactive", "Squint", "disabled", "Text strong", "/aligned:create-design-principles"):
        assert rule in text, f"prompt should check {rule}"


def test_principles_file_choices_win_over_his_defaults():
    assert "on purpose" in _read(PROMPT)


def test_anti_examples_cover_the_failure_modes():
    anti = _read(ANTI).lower()
    for failure in ("gut feeling", "overrul", "minimal doesn't mean simple"):
        assert failure in anti, f"anti-examples should cover {failure}"


def test_advisor_prompt_lists_the_framework():
    assert "`logic-check`" in _read(ADVISOR)


def test_scenario_exists_and_is_wired():
    assert SCENARIO.is_file()
    flat = yaml.safe_dump(yaml.safe_load(_read(TRIGGER_MAP)))
    for p in ("frameworks/logic-check/prompt.md", "frameworks/logic-check/examples.md",
              "frameworks/logic-check/anti-examples.md"):
        assert p in flat
    assert "scenarios/use-framework/logic-check.yaml" in flat
