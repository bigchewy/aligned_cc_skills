"""Four Question Threat Model: Adam Shostack's Four Question Framework, solo.

One person, one design doc, under an hour. The phases are his four questions,
word for word: What are we working on? What can go wrong? What are we going
to do about it? Did we do a good job? STRIDE is the checklist for the second
question. Threats get a decision (mitigate, eliminate, accept, transfer, or
don't build it), not only a fix. LLM parts hand to PHANTOM-B.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = REPO_ROOT / "frameworks" / "four-question-threat-model"
PROMPT = FRAMEWORK / "prompt.md"
EXAMPLES = FRAMEWORK / "examples.md"
ANTI = FRAMEWORK / "anti-examples.md"
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "adam-shostack.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / "four-question-threat-model.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"

QUESTIONS = ("What are we working on?", "What can go wrong?", "What are we going to do about it?",
             "Did we do a good job?")


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
        e = {x["id"]: x for x in yaml.safe_load(f)["frameworks"]}["four-question-threat-model"]
    assert e["advisor"] == "adam-shostack"
    assert e["name"] == "Four Question Threat Model"
    assert e["category"] == "security"
    assert e["deliverable_type"] == "analysis"
    assert "phantom-b-llm-threats" in e.get("follow_on_frameworks", [])


def test_prompt_opens_in_the_standard_form():
    first = [l for l in _read(PROMPT).split("---", 2)[2].splitlines() if l.strip()][0]
    assert first.startswith("You are Adam Shostack, guiding someone through Four Question Threat Model - ")


def test_phases_are_the_four_questions_and_each_waits():
    phases = _phases(_read(PROMPT))
    assert len(phases) == 4
    for n, body in phases.items():
        assert "**WAIT for the user to respond.**" in body, f"PHASE {n} has no WAIT"
        assert QUESTIONS[n - 1] in body, f"PHASE {n} should ask {QUESTIONS[n - 1]}"


def test_every_phase_has_a_script_and_a_struggle_branch():
    for n, body in _phases(_read(PROMPT)).items():
        assert "Say something like:" in body, f"PHASE {n} needs a script"
        assert re.search(r"^If (they|the user)", body, flags=re.MULTILINE), f"PHASE {n} needs a branch"


def test_stride_is_the_checklist_for_what_can_go_wrong():
    q2 = _phases(_read(PROMPT))[2]
    for letter in ("Spoofing", "Tampering", "Repudiation", "Information Disclosure", "Denial of Service",
                   "Elevation of Privilege"):
        assert letter in q2, f"PHASE 2 should run {letter}"
    assert "boundary" in q2.lower()


def test_what_to_do_is_more_than_fix_it():
    q3 = _phases(_read(PROMPT))[3].lower()
    for move in ("mitigate", "eliminate", "accept", "transfer"):
        assert move in q3


def test_prompt_hands_off_what_the_framework_does_not_cover():
    text = _read(PROMPT)
    for handoff in ("`phantom-b-llm-threats`", "Kim Wuyts", "Boris Cherny"):
        assert handoff in text
    assert "## Key Rules" in text


def test_anti_examples_cover_the_failure_modes():
    anti = _read(ANTI).lower()
    for failure in ("think like an attacker", "whole", "list", "accept", "score"):
        assert failure in anti, f"anti-examples should cover {failure}"
    assert anti.count("**wrong:**") >= 3
    assert anti.count("**what to do instead:**") >= 3


def test_examples_cover_golden_path_struggle_and_edge_case():
    ex = _read(EXAMPLES)
    for kind in ("Golden path", "Struggle", "Edge case", "**Why it works:**"):
        assert kind in ex


def test_advisor_prompt_lists_the_framework():
    assert "`four-question-threat-model`" in _read(ADVISOR)


def test_scenario_exists_and_is_wired():
    assert SCENARIO.is_file()
    flat = yaml.safe_dump(yaml.safe_load(_read(TRIGGER_MAP)))
    for p in ("frameworks/four-question-threat-model/prompt.md",
              "frameworks/four-question-threat-model/examples.md",
              "frameworks/four-question-threat-model/anti-examples.md"):
        assert p in flat
    assert "scenarios/use-framework/four-question-threat-model.yaml" in flat
