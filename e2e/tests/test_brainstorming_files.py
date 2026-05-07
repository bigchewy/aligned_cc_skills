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


def test_authoring_critique_checklist_structure():
    text = read("skills/brainstorming/authoring-critique-checklist.md")
    assert text.startswith("# Authoring Critique Checklist"), "missing top heading"
    for section in ["## Critique Criteria", "## Critique Output Format", "## Important"]:
        assert section in text, f"missing {section}"
    for criterion in [
        "Population fit", "Constraint preservation", "Sequencing rigor",
        "Library coverage", "Voice consistency", "Goal-metric alignment",
        "v1/v2 scoping", "Code/schema seam", "Decision quality",
    ]:
        assert criterion in text, f"missing criterion: {criterion}"


def test_planning_critique_checklist_structure():
    text = read("skills/brainstorming/planning-critique-checklist.md")
    assert text.startswith("# Planning Critique Checklist"), "missing top heading"
    for section in ["## Critique Criteria", "## Critique Output Format", "## Important"]:
        assert section in text, f"missing {section}"
    for criterion in [
        "Opportunity-space clarity", "Inventory completeness", "Sizing realism",
        "Dependency rigor", "Sequencing logic", "Capacity vs scope",
        "Spawn-brief quality", "Strategic coherence", "Decision quality",
    ]:
        assert criterion in text, f"missing criterion: {criterion}"


def test_research_mode_file_structure():
    text = read("skills/brainstorming/modes/research.md")
    # First line must be the canonical mode-file HTML comment (matches modes/software.md:1)
    assert text.splitlines()[0] == "<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->"
    assert "Within this mode file, `{base-directory}` resolves to" in text, "missing base-directory note"
    # Required process phases per design §Research/Process
    for phase in ["Question scoping", "Corpus scan", "Comparative synthesis", "Skeptic pass", "Ranking"]:
        assert phase in text, f"missing process phase: {phase}"
    # Critique panel config must match design §Research/Critique-panel config
    assert "Fact-check mode: all-critics" in text
    assert "Criteria assignment: no" in text
    assert "research-critique-checklist.md" in text
    assert "POST-CRITIQUE CHECKLIST" in text, "missing post-critique checklist anchor"


def test_authoring_mode_file_structure():
    text = read("skills/brainstorming/modes/authoring.md")
    assert text.splitlines()[0] == "<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->"
    assert "Within this mode file, `{base-directory}` resolves to" in text
    # Process phases
    for phase in [
        "Population & constraints",
        "Corpus scan",
        "Optional Research sub-phase",
        "Arrangement",
        "Orphan / residual catalog",
        "Architect audit",
    ]:
        assert phase in text, f"missing process phase: {phase}"
    # Critique panel config (division-of-labor)
    assert "Fact-check mode: division-of-labor" in text
    assert "Criteria assignment: yes" in text
    assert "authoring-critique-checklist.md" in text
    # Sub-flow contract pointers
    assert "research-mini-protocol.md" in text
    assert "/tmp/brainstorm-context-" in text
    assert "research-{question-slug}-question.md" in text
    assert "research-{question-slug}-synthesis.md" in text
    # Error paths for sub-flow
    assert "5 minutes" in text or "five minutes" in text, "missing sub-agent timeout"
    assert "## Synthesis" in text and "## Open Questions" in text and "## Confidence" in text, \
        "missing required synthesis-file headings in validation step"
