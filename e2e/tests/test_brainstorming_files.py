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


def test_skill_md_description_names_five_modes():
    text = read("skills/brainstorming/SKILL.md")
    # Find the frontmatter description line
    lines = text.splitlines()
    desc_line = next((l for l in lines[:10] if l.startswith("description:")), None)
    assert desc_line is not None, "frontmatter description line not found"
    # Must reference all five modes
    for mode in ["software", "business", "research", "authoring", "planning"]:
        assert mode.lower() in desc_line.lower(), f"description missing mode: {mode}"


def test_skill_md_overview_describes_five_modes():
    text = read("skills/brainstorming/SKILL.md")
    overview_start = text.index("## Overview")
    overview_end = text.index("## Step 1")
    overview = text[overview_start:overview_end]
    for mode in ["Software", "Business", "Research", "Authoring", "Planning"]:
        assert mode in overview, f"Overview missing mode: {mode}"


def test_skill_md_step1_has_five_signal_sets():
    text = read("skills/brainstorming/SKILL.md")
    step1_start = text.index("## Step 1")
    step2_start = text.index("## Step 2")
    step1 = text[step1_start:step2_start]
    # All 5 mode names appear as bolded headers
    for header in [
        "**Software mode**",
        "**Business mode**",
        "**Research mode**",
        "**Authoring mode**",
        "**Planning mode**",
    ]:
        assert header in step1, f"Step 1 missing signal set header: {header}"
    # 'planning' must NOT appear in Business signal set
    business_idx = step1.index("**Business mode**")
    research_idx = step1.index("**Research mode**")
    business_block = step1[business_idx:research_idx]
    assert "planning" not in business_block.lower(), \
        "'planning' should be in Planning mode signals, not Business"
    # 'planning' MUST appear in Planning signal set
    planning_idx = step1.index("**Planning mode**")
    planning_block = step1[planning_idx:]
    assert "planning" in planning_block.lower() or "roadmap" in planning_block.lower(), \
        "Planning signal set missing planning/roadmap keywords"


def test_planning_mode_file_structure():
    text = read("skills/brainstorming/modes/planning.md")
    assert text.splitlines()[0] == "<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->"
    assert "Within this mode file, `{base-directory}` resolves to" in text
    # 5 process phases
    for phase in [
        "Opportunity space",
        "Candidate inventory",
        "Sizing & dependencies",
        "Sequencing & rationale",
        "Spawn briefs per item",
    ]:
        assert phase in text, f"missing process phase: {phase}"
    # Two-artifact output
    assert "-roadmap.md" in text
    assert "-portfolio.md" in text
    # Critique panel
    assert "Fact-check mode: division-of-labor" in text
    assert "Criteria assignment: yes" in text
    assert "planning-critique-checklist.md" in text
    # Default panel + Cagan-conditional
    assert "Christensen" in text and "Rumelt" in text and "Eric Ries" in text, \
        "missing default launch panel"
    # Cagan absence-handling must reference the actual prompt-file path, not just the name
    assert "advisors/prompts/marty-cagan.md" in text, \
        "Cagan absence-handling must check the actual prompt-file path"
    # Spawn-brief reference
    assert "spawn-brief-template.md" in text


def test_skill_md_mode_explanation_block_grouped():
    text = read("skills/brainstorming/SKILL.md")
    # New grouped headers must appear
    for group in ["Build & ship", "Diagnose & decide", "Sequence work"]:
        assert group in text, f"missing group label: {group}"
    # Each mode must have a description line in SKILL.md
    for mode in [
        "Software mode description",
        "Business mode description",
        "Research mode description",
        "Authoring mode description",
        "Planning mode description",
    ]:
        assert mode in text, f"missing mode description: {mode}"


def test_skill_md_has_disambiguation_rules():
    text = read("skills/brainstorming/SKILL.md")
    assert "### Disambiguation Rules" in text, "missing Disambiguation Rules subsection"
    # All three rule pairs must appear
    for pair in [
        "Software vs Authoring",
        "Authoring vs Research",
        "Business vs Planning",
    ]:
        assert pair in text, f"missing rule: {pair}"
    # 5-way disambiguation question must appear
    assert ("Software design" in text and "Business strategy" in text
            and "Research synthesis" in text and "Content authoring" in text
            and "Multi-feature planning" in text), \
        "5-way disambiguation question must list all five modes"


def test_skill_md_step2_has_per_mode_emphasis():
    text = read("skills/brainstorming/SKILL.md")
    step2_start = text.index("## Step 2")
    step3_start = text.index("## Step 3")
    step2 = text[step2_start:step3_start]
    # Each mode's emphasis tag should be present in the dispatch prompt template
    for hint in [
        "code artifacts",
        "domain materials",
        "literature/KB/registries",
        "content registries",
        "prior roadmaps",
    ]:
        assert hint in step2, f"missing per-mode emphasis hint: {hint}"


def test_skill_md_step3_has_five_handoff_branches():
    text = read("skills/brainstorming/SKILL.md")
    step3_start = text.index("## Step 3")
    step3 = text[step3_start:]
    # Each mode must have a handoff branch
    for branch in [
        "**If software mode:**",
        "**If business mode:**",
        "**If research mode:**",
        "**If authoring mode:**",
        "**If planning mode:**",
    ]:
        assert branch in step3, f"missing handoff branch: {branch}"
    # Each mode points to its checklist file
    for checklist in [
        "design-critique-checklist.md",
        "business-critique-checklist.md",
        "research-critique-checklist.md",
        "authoring-critique-checklist.md",
        "planning-critique-checklist.md",
    ]:
        assert checklist in step3, f"missing checklist reference: {checklist}"


def test_kickstart_marketing_copy_mentions_five_modes():
    text = read("skills/kickstart/SKILL.md")
    # The "Run a brainstorm" line must reference five modes (or simply not say "software or business" any more)
    assert "software or business" not in text, "kickstart still uses two-mode marketing copy"
    # The new copy must explicitly reference five modes
    assert "five modes" in text or "5 modes" in text, "kickstart marketing copy should call out 5-mode router"


def test_orchestration_supports_portfolio_file_path():
    text = read("skills/_shared/critique-panel-orchestration.md")
    # The hardcoded "(e.g., software.md or business.md)" example list should be gone
    # (replaced with mode-agnostic phrasing per design §What changes)
    assert "(e.g., `software.md` or `business.md`)" not in text, \
        "hardcoded mode example list still present"
    # The optional portfolio-file-path field must be documented
    assert "portfolio-file-path" in text, "missing optional portfolio-file-path config field"
    # Must clarify it's optional (Planning-mode only)
    assert "optional" in text.lower(), "portfolio-file-path must be marked optional"


def test_software_mode_critique_config_unchanged():
    text = read("skills/brainstorming/modes/software.md")
    # Contract: division-of-labor + criteria-assignment yes + design-critique-checklist
    assert "Fact-check mode: division-of-labor" in text
    assert "Criteria assignment: yes" in text
    assert "Checklist filename: design-critique-checklist.md" in text
    # Output path convention preserved
    assert "docs/plans/YYYY-MM-DD-<topic>-design.md" in text
    # Temp dir pattern preserved
    assert "/tmp/brainstorm-context-{topic}" in text
    assert "/tmp/brainstorm-critique-{topic}" in text
    # Post-critique checklist still has 3 mandatory steps
    assert "POST-CRITIQUE CHECKLIST — 3 mandatory steps" in text


def test_business_mode_critique_config_unchanged():
    text = read("skills/brainstorming/modes/business.md")
    assert "Fact-check mode: all-critics" in text
    assert "Criteria assignment: no" in text
    assert "Checklist filename: business-critique-checklist.md" in text
    assert "docs/plans/YYYY-MM-DD-<topic>-design.md" in text
    assert "/tmp/brainstorm-context-{topic}" in text
    assert "/tmp/brainstorm-critique-{topic}" in text
    assert "POST-CRITIQUE CHECKLIST — 3 mandatory steps" in text


def test_five_modes_eval_fixture_lists_15_briefs():
    text = read("e2e/scenarios/use-skill/brainstorming-five-modes.yaml")
    # Smoke check: 5 modes × 3 briefs each = 15 test entries
    test_count = text.count("- description:")
    assert test_count >= 15, f"expected ≥15 test briefs in fixture; found {test_count}"
    # Each mode appears as a label
    for mode_label in ["software", "business", "research", "authoring", "planning"]:
        assert mode_label in text.lower(), f"missing mode label: {mode_label}"
