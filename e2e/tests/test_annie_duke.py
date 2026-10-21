"""Annie Duke joins the board as the launch advisor.

Her published tools cover three of the four launch questions: a premortem for
what has to be true before launch, kill criteria as a state and a date for the
success number, and resulting for judging one customer's result apart from
luck. She publishes nothing on finding or recruiting customers, so the prompt
must say so and not claim it.
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPT = REPO_ROOT / "advisors" / "prompts" / "annie-duke.md"
RESEARCH = REPO_ROOT / "docs" / "advisors" / "new_advisors" / "v_annie-duke.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-advisor" / "annie-duke-consult.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"


def _entry():
    with open(REPO_ROOT / "advisors" / "registry.yaml") as f:
        return {a["id"]: a for a in yaml.safe_load(f)["advisors"]}["annie-duke"]


def test_registered_with_a_prompt():
    e = _entry()
    assert e["name"] == "Annie Duke"
    assert e["prompt"] == "advisors/prompts/annie-duke.md"
    assert PROMPT.is_file()
    for field in ("best_for", "not_for", "evaluation_expertise", "summary"):
        assert e.get(field, "").strip(), f"annie-duke needs {field}"
    assert "launch" in e["domains"]


def test_research_file_exists():
    assert RESEARCH.is_file()


def test_prompt_carries_her_tools():
    text = PROMPT.read_text(encoding="utf-8").lower()
    for tool in ("resulting", "kill criteria", "state and a date", "premortem"):
        assert tool in text, f"prompt should name {tool}"


def test_prompt_does_not_claim_what_she_never_published():
    text = PROMPT.read_text(encoding="utf-8").lower()
    assert "what you never published" in text
    assert "recruit" in text


def test_prompt_hands_off_to_the_neighbors():
    text = PROMPT.read_text(encoding="utf-8")
    for neighbor in ("Eric Ries", "pivot-or-persevere", "Paul Graham", "launch-bet"):
        assert neighbor in text


def test_consult_scenario_is_wired():
    assert SCENARIO.is_file()
    assert "advisors/prompts/annie-duke.md" in SCENARIO.read_text(encoding="utf-8")
    flat = yaml.safe_dump(yaml.safe_load(TRIGGER_MAP.read_text(encoding="utf-8")))
    assert "scenarios/use-advisor/annie-duke-consult.yaml" in flat
