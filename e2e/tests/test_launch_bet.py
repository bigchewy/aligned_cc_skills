"""Launch Bet: Annie Duke runs a launch with one real customer as one bet.

Phase 1 of a site launch names the bet, runs a premortem whose controlled
reasons become the launch checklist, writes the success line and the quit
line as a state and a date before the build, and picks and recruits the
first customer. Phase 8 reads the result against those lines, separates the
decision from the luck, and decides: keep going, change one thing, stop, or
wait for one named fact. Recruiting is not Duke's published method, so the
prompt says so and names Rob Fitzpatrick's commitment test as the source.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = REPO_ROOT / "frameworks" / "launch-bet"
PROMPT = FRAMEWORK / "prompt.md"
EXAMPLES = FRAMEWORK / "examples.md"
ANTI = FRAMEWORK / "anti-examples.md"
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "annie-duke.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / "launch-bet.yaml"
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
        e = {x["id"]: x for x in yaml.safe_load(f)["frameworks"]}["launch-bet"]
    assert e["advisor"] == "annie-duke"
    assert e["name"] == "Launch Bet"
    assert e["category"] == "startup"
    assert e["deliverable_type"] == "decision"
    assert "pivot-or-persevere" in e.get("follow_on_frameworks", [])


def test_prompt_opens_in_the_standard_form():
    first = [l for l in _read(PROMPT).split("---", 2)[2].splitlines() if l.strip()][0]
    assert first.startswith("You are Annie Duke, guiding someone through Launch Bet - ")


def test_every_phase_waits_for_the_user():
    phases = _phases(_read(PROMPT))
    assert len(phases) == 7
    for n, body in phases.items():
        assert "**WAIT for the user to respond.**" in body, f"PHASE {n} has no WAIT"


def test_prompt_has_both_launch_sittings():
    text = _read(PROMPT)
    assert "Phase 1 of the launch" in text and "Phase 8 of the launch" in text
    assert "decisions.md" in text


def test_prompt_writes_the_lines_before_the_build():
    text = _read(PROMPT).lower()
    for term in ("state and a date", "quit line", "too early to tell", "premortem", "before the build"):
        assert term in text, f"prompt should cover {term}"


def test_prompt_separates_decision_from_luck():
    text = _read(PROMPT).lower()
    for term in ("resulting", "sample of one", "what you controlled"):
        assert term in text, f"prompt should cover {term}"


def test_recruiting_step_is_marked_as_not_hers():
    text = _read(PROMPT)
    assert "Rob Fitzpatrick" in text
    assert "not my method" in text.lower()


def test_hands_off_big_changes_to_ries():
    assert "`pivot-or-persevere`" in _read(PROMPT)


def test_anti_examples_cover_the_failure_modes():
    anti = _read(ANTI).lower()
    for failure in ("moving the line", "bad luck", "gave nothing up", "conversion rate"):
        assert failure in anti, f"anti-examples should cover {failure}"


def test_advisor_prompt_lists_the_framework():
    assert "`launch-bet`" in _read(ADVISOR)


def test_scenario_exists_and_is_wired():
    assert SCENARIO.is_file()
    flat = yaml.safe_dump(yaml.safe_load(_read(TRIGGER_MAP)))
    for p in ("frameworks/launch-bet/prompt.md", "frameworks/launch-bet/examples.md",
              "frameworks/launch-bet/anti-examples.md"):
        assert p in flat
    assert "scenarios/use-framework/launch-bet.yaml" in flat
