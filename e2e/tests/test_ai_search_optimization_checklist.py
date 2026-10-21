"""AI Search Optimization Checklist: Aleyda Solis's twelve steps, for a small site.

Quoted from her page "The AI Search Optimization Framework & Checklist - With
Worksheet [Updated Sep 2026]". Steps 1-2 measure AI presence, 3-10 diagnose
and fix readiness, 11-12 report impact and rerun. One phase per step. This
version is for one person on a small site: fewer prompts, free checks, and it
says which steps rarely apply (commercial feeds, separate country markets).
It measures before it fixes, and it refuses manipulation (prompt injection,
fabricated reviews, citation gaming).
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = REPO_ROOT / "frameworks" / "ai-search-optimization-checklist"
PROMPT = FRAMEWORK / "prompt.md"
EXAMPLES = FRAMEWORK / "examples.md"
ANTI = FRAMEWORK / "anti-examples.md"
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "aleyda-solis.md"
RESEARCH = REPO_ROOT / "docs" / "advisors" / "new_advisors" / "v_aleyda-solis.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / "ai-search-optimization-checklist.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"

STEP_TITLES = [
    "Establish the prompts and journeys you actually want to influence in AI systems",
    "Measure your initial AI presence in popular AI systems before implementation",
    "Diagnose your brand AI search presence gap before taking action",
    "Make priority pages retrievable and extractable for AI systems",
    "Align your brand entity, naming and positioning signals",
    "Create decision support content and prioritize what still has a role after the AI answer",
    "Grow your brand’s third-party AI source ecosystem",
    "Make commercial and transactional information machine-readable",
    "Localize your presence by market, not only by language",
    "Classify and measure what earns citations and what attracts clicks separately",
    "Report AI search optimization efforts and outcomes without overclaiming",
    "Run a recurring AI validation and optimization loop",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _phases(text: str) -> dict:
    parts = re.split(r"^### PHASE (\d+):", text, flags=re.MULTILINE)
    return {int(parts[i]): parts[i + 1].split("## Key Rules")[0] for i in range(1, len(parts), 2)}


def test_framework_files_exist():
    for p in (PROMPT, EXAMPLES, ANTI):
        assert p.is_file(), f"missing {p.relative_to(REPO_ROOT)}"


def test_primary_source_was_read():
    text = _read(RESEARCH)
    assert "aleydasolis.com/en/ai-search/ai-search-optimization-checklist" in text
    for title in STEP_TITLES:
        assert title in text, f"research file should quote step: {title}"


def test_registry_entry():
    with open(REPO_ROOT / "frameworks" / "registry.yaml") as f:
        e = {x["id"]: x for x in yaml.safe_load(f)["frameworks"]}["ai-search-optimization-checklist"]
    assert e["advisor"] == "aleyda-solis"
    assert e["name"] == "AI Search Optimization Checklist"
    assert e["category"] == "marketing"
    assert e["deliverable_type"] == "plan"


def test_prompt_opens_in_the_standard_form():
    first = [l for l in _read(PROMPT).split("---", 2)[2].splitlines() if l.strip()][0]
    assert first.startswith("You are Aleyda Solis, guiding someone through the AI Search Optimization Checklist - ")


def test_one_phase_per_step_and_every_phase_waits():
    phases = _phases(_read(PROMPT))
    assert len(phases) == 12
    for n, body in phases.items():
        assert "**WAIT for the user to respond.**" in body, f"PHASE {n} has no WAIT"
        assert STEP_TITLES[n - 1] in body, f"PHASE {n} should carry her step title"


def test_prompt_measures_before_it_fixes():
    text = _read(PROMPT)
    assert text.index("Measure your initial AI presence") < text.index("Make priority pages retrievable")
    low = text.lower()
    for term in ("prompt", "three to five times", "raw html", "fact sheet", "third-party",
                 "without overclaiming", "keep, expand, revise or stop"):
        assert term in low, f"prompt should use {term}"


def test_prompt_adapts_for_a_small_site():
    low = _read(PROMPT).lower()
    assert "small site" in low
    assert "rarely applies" in low or "rarely apply" in low
    assert "good seo is good geo" in low


def test_prompt_refuses_manipulation():
    low = _read(PROMPT).lower()
    for term in ("prompt injection", "fabricated reviews", "citation gaming"):
        assert term in low


def test_prompt_hands_back_to_the_page_diagnostic():
    assert "`why-my-page-doesnt-rank`" in _read(PROMPT)


def test_anti_examples_cover_the_failure_modes():
    anti = _read(ANTI).lower()
    for failure in ("llms.txt", "fake reviews", "before measuring", "javascript", "traffic"):
        assert failure in anti, f"anti-examples should cover {failure}"


def test_examples_explain_why_they_work():
    ex = _read(EXAMPLES)
    assert ex.count("**Why it works:**") >= 6
    for kind in ("Golden path", "Struggle", "Edge case"):
        assert kind in ex


def test_advisor_prompt_lists_the_framework():
    assert "`ai-search-optimization-checklist`" in _read(ADVISOR)


def test_scenario_exists_and_is_wired():
    assert SCENARIO.is_file()
    flat = yaml.safe_dump(yaml.safe_load(_read(TRIGGER_MAP)))
    for p in ("frameworks/ai-search-optimization-checklist/prompt.md",
              "frameworks/ai-search-optimization-checklist/examples.md",
              "frameworks/ai-search-optimization-checklist/anti-examples.md"):
        assert p in flat
    assert "scenarios/use-framework/ai-search-optimization-checklist.yaml" in flat
