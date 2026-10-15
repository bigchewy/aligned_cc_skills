"""Adham Dannaway joins the board to run create-design-principles.

His published method (Practical UI and his design system guide) sets tokens
with numbers and a reason for each: colour by role, a type scale from a base
and a ratio, two weights, t-shirt spacing, three radii, two shadows, one
primary button. He publishes nothing on finding a product's feeling, motion,
or loading, error, and empty states, so the prompt must not claim those.
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPT = REPO_ROOT / "advisors" / "prompts" / "adham-dannaway.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-advisor" / "adham-dannaway-consult.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"


def _entry():
    with open(REPO_ROOT / "advisors" / "registry.yaml") as f:
        return {a["id"]: a for a in yaml.safe_load(f)["advisors"]}["adham-dannaway"]


def test_registered_with_a_prompt():
    e = _entry()
    assert e["name"] == "Adham Dannaway"
    assert e["prompt"] == "advisors/prompts/adham-dannaway.md"
    assert PROMPT.is_file()
    for field in ("best_for", "not_for", "evaluation_expertise", "summary"):
        assert e.get(field, "").strip(), f"adham-dannaway needs {field}"
    assert "design-tokens" in e["domains"]


def test_prompt_carries_his_numbers():
    text = PROMPT.read_text(encoding="utf-8")
    for rule in ("4.5:1", "3:1", "1.2", "48", "Text strong", "Stroke weak", "regular and bold"):
        assert rule in text, f"prompt should state {rule}"


def test_prompt_does_not_claim_what_he_never_published():
    text = PROMPT.read_text(encoding="utf-8").lower()
    assert "what he does not publish" in text or "you never published" in text
    for gap in ("feeling", "motion", "empty"):
        assert gap in text


def test_prompt_hands_off_to_the_neighbors():
    text = PROMPT.read_text(encoding="utf-8")
    for neighbor in ("Steve Jobs", "Brad Frost", "Steve Krug", "create-design-principles"):
        assert neighbor in text


def test_consult_scenario_is_wired():
    assert SCENARIO.is_file()
    assert "advisors/prompts/adham-dannaway.md" in SCENARIO.read_text(encoding="utf-8")
    flat = yaml.safe_dump(yaml.safe_load(TRIGGER_MAP.read_text(encoding="utf-8")))
    assert "scenarios/use-advisor/adham-dannaway-consult.yaml" in flat
