"""Structural assertions for the brainstorming three-modes implementation."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text()


def test_research_mini_protocol_has_required_sections():
    text = read("skills/brainstorming/references/research-mini-protocol.md")
    assert "## Phases" in text, "missing ## Phases section"
    assert "## Output contract" in text, "missing ## Output contract section"
    assert "## Recursion forbidden" in text, "missing ## Recursion forbidden section"


def test_spawn_brief_template_has_eight_fields():
    text = read("skills/brainstorming/references/spawn-brief-template.md")
    required_fields = [
        "**Target mode:**",
        "**Status:**",
        "**Rough size:**",
        "**Prerequisites:**",
        "**External dependencies:**",
        "**Why now:**",
        "**Spawn brief (one paragraph, brainstorm-ready):**",
        "**Success criterion:**",
    ]
    missing = [f for f in required_fields if f not in text]
    assert not missing, f"missing fields in spawn-brief template: {missing}"


def test_research_critique_checklist_structure():
    text = read("skills/brainstorming/research-critique-checklist.md")
    assert text.startswith("# Research Critique Checklist"), "missing top heading"
    for section in ["## Critique Criteria", "## Critique Output Format", "## Important"]:
        assert section in text, f"missing {section}"
    for criterion in [
        "Scope clarity", "Corpus coverage", "Source quality",
        "Comparison rigor", "Validation honesty", "Licensing/cost clarity",
        "Recommendation defensibility", "Open-questions completeness",
        "Decision quality",
    ]:
        assert criterion in text, f"missing criterion: {criterion}"
