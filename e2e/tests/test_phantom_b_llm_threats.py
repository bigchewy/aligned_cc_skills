"""PHANTOM-B LLM Threats: Adam Shostack's STRIDE analog for the LLM parts.

PHANTOM-B (Shostack + Associates White Paper #6, July 2026) structures how you
answer "What can go wrong with the LLM parts of the system?" Eight threats:
Prompt injection, Hallucination, Anthropomorphization, Non-explainability,
Training issues, Over-reliance, Missing security engineering, Biases. It is a
fixed lens for LLM callers, it holds no defenses by design, and STRIDE still
covers the rest of the system.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = REPO_ROOT / "frameworks" / "phantom-b-llm-threats"
PROMPT = FRAMEWORK / "prompt.md"
EXAMPLES = FRAMEWORK / "examples.md"
ANTI = FRAMEWORK / "anti-examples.md"
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "adam-shostack.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / "phantom-b-llm-threats.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"

LETTERS = ("Prompt injection", "Hallucination", "Anthropomorphization", "Non-explainability",
           "Training issues", "Over-reliance", "Missing security engineering", "Biases")


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
        e = {x["id"]: x for x in yaml.safe_load(f)["frameworks"]}["phantom-b-llm-threats"]
    assert e["advisor"] == "adam-shostack"
    assert e["name"] == "PHANTOM-B LLM Threats"
    assert e["category"] == "security"
    assert e["deliverable_type"] == "analysis"
    assert "four-question-threat-model" in e.get("follow_on_frameworks", [])


def test_prompt_opens_in_the_standard_form():
    first = [l for l in _read(PROMPT).split("---", 2)[2].splitlines() if l.strip()][0]
    assert first.startswith("You are Adam Shostack, guiding someone through PHANTOM-B LLM Threats - ")


def test_every_phase_waits_and_has_a_script():
    phases = _phases(_read(PROMPT))
    assert len(phases) == 5
    for n, body in phases.items():
        assert "**WAIT for the user to respond.**" in body, f"PHASE {n} has no WAIT"
        assert "Say something like:" in body, f"PHASE {n} needs a script"


def test_prompt_uses_all_eight_threats():
    text = _read(PROMPT)
    for letter in LETTERS:
        assert letter in text, f"prompt should name {letter}"


def test_prompt_marks_the_llm_parts_and_keeps_stride_for_the_rest():
    phase1 = _phases(_read(PROMPT))[1]
    assert "LLM parts" in phase1
    assert "STRIDE" in phase1


def test_prompt_says_phantom_b_holds_no_defenses():
    text = _read(PROMPT).lower()
    assert "no defenses" in text
    assert "unsolvable" in text
    assert "agentic" in text


def test_prompt_hands_back_to_the_four_questions():
    assert "`four-question-threat-model`" in _read(PROMPT)
    assert "## Key Rules" in _read(PROMPT)


def test_anti_examples_cover_the_failure_modes():
    anti = _read(ANTI).lower()
    for failure in ("whole system", "do not", "unsolvable", "defenses", "review"):
        assert failure in anti, f"anti-examples should cover {failure}"
    assert anti.count("**wrong:**") >= 3


def test_examples_cover_golden_path_struggle_and_edge_case():
    ex = _read(EXAMPLES)
    for kind in ("Golden path", "Struggle", "Edge case", "**Why it works:**"):
        assert kind in ex


def test_advisor_prompt_lists_the_framework():
    assert "`phantom-b-llm-threats`" in _read(ADVISOR)


def test_scenario_exists_and_is_wired():
    assert SCENARIO.is_file()
    flat = yaml.safe_dump(yaml.safe_load(_read(TRIGGER_MAP)))
    for p in ("frameworks/phantom-b-llm-threats/prompt.md", "frameworks/phantom-b-llm-threats/examples.md",
              "frameworks/phantom-b-llm-threats/anti-examples.md"):
        assert p in flat
    assert "scenarios/use-framework/phantom-b-llm-threats.yaml" in flat
