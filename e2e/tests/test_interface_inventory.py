"""Interface Inventory: Brad Frost's audit of an app that already exists.

Follows his five published steps and sixteen categories, adapted for one
builder working with AI coding agents: capture every pattern by category,
present each category, name the patterns, decide what becomes a component,
a recipe, or a snowflake, and send values missing from design-principles.md
to the design principles skill.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = REPO_ROOT / "frameworks" / "interface-inventory"
PROMPT = FRAMEWORK / "prompt.md"
EXAMPLES = FRAMEWORK / "examples.md"
ANTI = FRAMEWORK / "anti-examples.md"
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "brad-frost.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / "interface-inventory.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"

CATEGORIES = [
    "Global", "Navigation", "Image types", "Icons", "Forms", "Buttons", "Headings", "Blocks",
    "Lists", "Interactive Components", "Media", "3rd Party", "Advertising", "Messaging",
    "Colors", "Animation",
]
STEPS = ["Round up the troops", "Prepare for screenshotting", "Screenshot exercise",
         "Present Findings", "Regroup and Establish Next Steps"]


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
        e = {x["id"]: x for x in yaml.safe_load(f)["frameworks"]}["interface-inventory"]
    assert e["advisor"] == "brad-frost"
    assert e["name"] == "Interface Inventory"
    assert e["category"] == "product-design"
    assert e["deliverable_type"] == "analysis"


def test_prompt_opens_in_the_standard_form():
    first = [l for l in _read(PROMPT).split("---", 2)[2].splitlines() if l.strip()][0]
    assert first.startswith("You are Brad Frost, guiding someone through Interface Inventory - ")


def test_every_phase_waits_for_the_user():
    phases = _phases(_read(PROMPT))
    assert len(phases) >= 5
    for n, body in phases.items():
        assert "**WAIT for the user to respond.**" in body, f"PHASE {n} has no WAIT"


def test_prompt_uses_his_published_steps_and_categories():
    text = _read(PROMPT)
    for step in STEPS:
        assert step in text, f"prompt should name his step: {step}"
    for cat in CATEGORIES:
        assert cat in text, f"prompt should list category: {cat}"


def test_prompt_states_the_contract():
    text = _read(PROMPT)
    for term in ("component", "recipe", "snowflake", "design-principles.md",
                 "/aligned:create-design-principles", "data-from"):
        assert term in text, f"prompt should cover {term}"
    # Solo adaptation is named as such, not presented as his.
    assert "one builder" in text.lower() or "solo" in text.lower()
    # Output files.
    assert "docs/design/interface-inventory-{date}.md" in text


def test_anti_examples_cover_the_failure_modes():
    anti = _read(ANTI).lower()
    for failure in ("every instance", "redesign", "invent"):
        assert failure in anti, f"anti-examples should cover {failure}"


def test_advisor_prompt_lists_the_framework():
    assert "`interface-inventory`" in _read(ADVISOR)


def test_scenario_exists_and_is_wired():
    assert SCENARIO.is_file()
    flat = yaml.safe_dump(yaml.safe_load(_read(TRIGGER_MAP)))
    for p in ("frameworks/interface-inventory/prompt.md", "frameworks/interface-inventory/examples.md",
              "frameworks/interface-inventory/anti-examples.md"):
        assert p in flat
    assert "scenarios/use-framework/interface-inventory.yaml" in flat
