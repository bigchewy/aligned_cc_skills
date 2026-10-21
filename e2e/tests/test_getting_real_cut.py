"""Getting Real Cut: Jason Fried cuts a feature list to its epicenter.

Runs on a feature list, a spec, or a design before anyone builds it. Seven
phases, each a Getting Real chapter: the big idea and the enemy, fixed time,
the epicenter, half and then half again, make each survivor earn it (start
with no, hidden costs), strip what doesn't matter yet, race to running
software. What's cut goes to "not now", not a backlog. Fried sets no success
number, so the prompt hands that to Annie Duke and the shaping to Ryan Singer.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = REPO_ROOT / "frameworks" / "getting-real-cut"
PROMPT = FRAMEWORK / "prompt.md"
EXAMPLES = FRAMEWORK / "examples.md"
ANTI = FRAMEWORK / "anti-examples.md"
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "jason-fried.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / "getting-real-cut.yaml"
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
        e = {x["id"]: x for x in yaml.safe_load(f)["frameworks"]}["getting-real-cut"]
    assert e["advisor"] == "jason-fried"
    assert e["name"] == "Getting Real Cut"
    assert e["category"] == "product-design"
    assert e["deliverable_type"] == "plan"
    assert "frame-shape-bet" in e.get("follow_on_frameworks", [])


def test_prompt_opens_in_the_standard_form():
    first = [l for l in _read(PROMPT).split("---", 2)[2].splitlines() if l.strip()][0]
    assert first.startswith("You are Jason Fried, guiding someone through Getting Real Cut - ")


def test_every_phase_waits_for_the_user():
    phases = _phases(_read(PROMPT))
    assert len(phases) == 7
    for n, body in phases.items():
        assert "**WAIT for the user to respond.**" in body, f"PHASE {n} has no WAIT"


def test_prompt_uses_the_getting_real_rules():
    text = _read(PROMPT).lower()
    for rule in ("big idea", "enemy", "epicenter", "cut it in half", "start with no", "hidden costs",
                 "it just doesn't matter", "problem when it's a problem", "preferences", "running software",
                 "not now"):
        assert rule in text, f"prompt should use {rule}"


def test_prompt_keeps_cut_items_out_of_a_backlog():
    assert "backlog" in _read(PROMPT).lower()


def test_prompt_hands_off_what_fried_does_not_do():
    text = _read(PROMPT)
    for handoff in ("Annie Duke", "`launch-bet`", "Ryan Singer", "`frame-shape-bet`"):
        assert handoff in text


def test_anti_examples_cover_the_failure_modes():
    anti = _read(ANTI).lower()
    for failure in ("backlog", "success number", "settings", "scale", "itch"):
        assert failure in anti, f"anti-examples should cover {failure}"


def test_advisor_prompt_lists_the_framework():
    assert "`getting-real-cut`" in _read(ADVISOR)


def test_scenario_exists_and_is_wired():
    assert SCENARIO.is_file()
    flat = yaml.safe_dump(yaml.safe_load(_read(TRIGGER_MAP)))
    for p in ("frameworks/getting-real-cut/prompt.md", "frameworks/getting-real-cut/examples.md",
              "frameworks/getting-real-cut/anti-examples.md"):
        assert p in flat
    assert "scenarios/use-framework/getting-real-cut.yaml" in flat
