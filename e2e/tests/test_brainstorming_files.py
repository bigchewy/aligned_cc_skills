"""Structural assertions for the brainstorming three-modes implementation."""
import json
import yaml
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text()


def test_research_mini_protocol_has_required_sections():
    text = read("skills/brainstorming/references/research-mini-protocol.md")
    assert "## Phases" in text, "missing ## Phases section"
    assert "## Output contract" in text, "missing ## Output contract section"
    assert "## Recursion forbidden" in text, "missing ## Recursion forbidden section"


def test_spawn_brief_template_has_five_fields():
    """Roadmap-mode redesign (May 2026): the spawn-brief schema collapsed from
    8 fields to 5, dropping Status/External dependencies/Why now/Rough size as
    portfolio-management bookkeeping that decomposition scaffolding doesn't need."""
    text = read("skills/brainstorming/references/spawn-brief-template.md")
    required_fields = [
        "**Target mode:**",
        "**Prerequisites:**",
        "**Spawn brief (paste-ready):**",
        "**Success criterion:**",
    ]
    missing = [f for f in required_fields if f not in text]
    assert not missing, f"missing fields in spawn-brief template: {missing}"
    # Component title is the `##` heading line, not a bolded field — assert the
    # schema documents it as the heading.
    assert "## {Component title}" in text, "schema must document the ## heading as the title field"
    # The fields removed in the v1 redesign must not return silently.
    for retired in [
        "**Status:**",
        "**External dependencies:**",
        "**Why now:**",
        "**Rough size:**",
    ]:
        assert retired not in text, f"retired field came back: {retired}"


@pytest.mark.parametrize("path,heading,criteria", [
    (
        "skills/brainstorming/research-critique-checklist.md",
        "# Research Critique Checklist",
        ["Scope clarity", "Corpus coverage", "Source quality",
         "Comparison rigor", "Validation honesty", "Licensing/cost clarity",
         "Recommendation defensibility", "Open-questions completeness",
         "Decision quality"],
    ),
    (
        "skills/brainstorming/authoring-critique-checklist.md",
        "# Authoring Critique Checklist",
        ["Population fit", "Constraint preservation", "Sequencing rigor",
         "Library coverage", "Voice consistency", "Goal-metric alignment",
         "v1/v2 scoping", "Code/schema seam", "Decision quality"],
    ),
    (
        "skills/brainstorming/roadmap-critique-checklist.md",
        "# Roadmap Spawn-List Critique Checklist",
        ["Spawn-brief paste-readiness", "Decomposition fit"],
    ),
])
def test_critique_checklist_structure(path, heading, criteria):
    text = read(path)
    assert text.startswith(heading), f"{path} missing top heading {heading!r}"
    for section in ("## Critique Criteria", "## Critique Output Format", "## Important"):
        assert section in text, f"{path} missing {section}"
    for criterion in criteria:
        assert criterion in text, f"{path} missing criterion: {criterion}"


def test_research_mode_file_structure():
    text = read("skills/brainstorming/modes/research.md")
    # First line must be the canonical mode-file HTML comment (matches modes/software.md:1)
    assert text.splitlines()[0] == "<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->"
    # Anti-regression: the {base-directory} resolution note was extracted to
    # references/shared-rules.md; mode files must not re-duplicate it.
    assert "Within this mode file, `{base-directory}` resolves to" not in text, \
        "base-directory note should live only in references/shared-rules.md, not be duplicated in mode files"
    # Required process phases per design §Research/Process
    for phase in ["Question scoping", "Corpus scan", "Comparative synthesis", "Skeptic pass", "Ranking"]:
        assert phase in text, f"missing process phase: {phase}"
    # Critique panel config must match design §Research/Critique-panel config
    assert "Fact-check mode: all-critics" in text
    assert "Criteria assignment: no" in text
    assert "research-critique-checklist.md" in text
    assert "POST-CRITIQUE CHECKLIST" in text, "missing post-critique checklist anchor"


def test_authoring_mode_file_structure():
    """New authoring.md dispatches via shared runners with no-framework Q&A fallback."""
    text = read("skills/brainstorming/modes/authoring.md")
    assert text.splitlines()[0] == "<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->"
    # 3-phase dispatch shape
    assert "Phase 1: Engine selection" in text
    assert "Phase 2: Engine execution" in text
    assert "Phase 3:" in text and "deliverable_type" in text
    # Engine selection invokes contextual-recommendation
    assert "_shared/contextual-recommendation.md" in text
    assert "framework-or-advisor" in text
    # Shared runners — only framework-runner is invoked from authoring mode.
    # Advisor execution in Phase 2b/2c/2d uses the inline software-mode-style
    # Q&A pattern (Architect-as-proxy), not _shared/advisor-runner.md. See the
    # PARITY MARKER in authoring.md and Decision 5 in the design doc.
    assert "_shared/framework-runner.md" in text
    assert "intake_gate_mode" in text and "strict" in text
    # Fallback ladder
    assert "Wise Eric" in text, "missing last-resort default advisor"
    assert "structured Q&A" in text or "Architect" in text and "proxy" in text
    # Duplication marker
    assert "PARITY MARKER" in text or "DUPLICATED FROM" in text
    assert "modes/software.md" in text
    # Critique panel config
    assert "authoring-critique-checklist.md" in text
    assert "deliverable_type" in text  # post-engine dispatch
    # default_critic_advisors must be consumed by Phase 3 (the field added in Task 10
    # is load-bearing here, not just metadata).
    assert "default_critic_advisors" in text, (
        "Phase 3 must consume default_critic_advisors from the registry"
    )
    # Path 4 handoff must be documented so contextual-recommendation does not
    # double-prompt the user.
    assert "Path 4" in text, (
        "authoring mode must document how it interacts with contextual-recommendation's Path 4"
    )


def test_authoring_mode_is_in_eval_surface():
    text = read("e2e/eval-surface.yaml")
    assert "skills/brainstorming/modes/authoring.md" in text


def test_skill_md_description_names_four_modes():
    text = read("skills/brainstorming/SKILL.md")
    lines = text.splitlines()
    desc_line = next((l for l in lines[:10] if l.startswith("description:")), None)
    assert desc_line is not None
    for mode in ["software", "authoring", "research", "roadmap"]:
        assert mode.lower() in desc_line.lower(), f"description missing mode: {mode}"
    for gone in ["business", "planning"]:
        assert gone.lower() not in desc_line.lower(), f"description still mentions retired mode: {gone}"


def test_skill_md_overview_describes_four_modes():
    text = read("skills/brainstorming/SKILL.md")
    overview = text[text.index("## Overview"):text.index("## Step 1")]
    for mode in ["Software", "Authoring", "Research", "Roadmap"]:
        assert mode in overview, f"overview missing: {mode}"
    assert "Business" not in overview, "overview still mentions retired Business mode"
    assert "Planning" not in overview, "overview still mentions retired Planning mode"


def test_skill_md_step1_has_four_signal_sets_and_always_ask():
    text = read("skills/brainstorming/SKILL.md")
    step1 = text[text.index("## Step 1"):text.index("## Step 2")]
    for h in ["**Software mode**", "**Authoring mode**", "**Research mode**", "**Roadmap mode**"]:
        assert h in step1, f"missing signal-set header: {h}"
    for gone in ["**Business mode**", "**Planning mode**"]:
        assert gone not in step1, f"retired signal-set still present: {gone}"
    # Always-ask discipline
    assert "always" in step1.lower() and ("ask" in step1.lower() or "present the question" in step1.lower())
    # Picker label format (task vocabulary, not mode IDs).
    # The Roadmap picker label changed from "Break a big initiative into smaller
    # pieces" to "Break a big intent into a queue of brainstorms" in the
    # decomposition-scaffolding redesign.
    for label_fragment in ["Write a document", "Design a code change", "Synthesize research", "Break a big intent"]:
        assert label_fragment in step1, f"missing picker label: {label_fragment}"


def test_skill_md_keyword_expansion_includes_deck_and_breakdown_signals():
    text = read("skills/brainstorming/SKILL.md")
    # Authoring keyword expansion (May 17 amendment)
    for kw in ["deck", "presentation", "pitch deck", "memo", "battle card"]:
        assert kw in text.lower(), f"authoring missing keyword: {kw}"
    # Roadmap keyword expansion (May 2026 decomposition-scaffolding redesign).
    # "big idea" was retired alongside the long-horizon-planning framing; the
    # replacements emphasize decomposition shape.
    for kw in ["break", "decompose", "smaller pieces", "spawn list", "multi-step", "brainstorm queue"]:
        assert kw in text.lower(), f"roadmap missing keyword: {kw}"


def test_skill_md_im_not_sure_routes_to_authoring():
    text = read("skills/brainstorming/SKILL.md")
    # The post-collapse refusal-handling rule
    assert "I'm not sure" in text or "not sure" in text.lower()
    # Find context around "I'm not sure" and assert routes to Authoring
    idx = text.lower().find("not sure")
    nearby = text[idx:idx+300].lower()
    assert "authoring" in nearby, "'I'm not sure' must route to Authoring post-collapse"
    assert "business" not in nearby, "stale Business reference"


def test_skill_md_explicit_mode_arg_skips_question():
    text = read("skills/brainstorming/SKILL.md")
    assert "--mode" in text, "missing explicit --mode arg skip condition"
    assert "session" in text.lower(), "missing session-scoped skip rule"


def test_roadmap_mode_file_structure():
    """Roadmap mode was redesigned in May 2026 from a portfolio-sequencing process
    (5 phases, 2 artifacts, strategy-advisor panel, full critique pipeline) into
    pure decomposition scaffolding (4 phases, 1 artifact, no advisor panel, inline
    self-review). This test pins the new shape."""
    text = read("skills/brainstorming/modes/roadmap.md")
    assert text.splitlines()[0] == "<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->"
    # Anti-regression: extracted to references/shared-rules.md by the
    # visualization-protocol / shared-rules refactor.
    assert "Within this mode file, `{base-directory}` resolves to" not in text, \
        "base-directory note should live only in references/shared-rules.md, not be duplicated in mode files"
    # 4 process phases (down from 5)
    for phase in [
        "Outcome and why it needs decomposition",
        "Decompose into 3",  # "Decompose into 3–6 components" — match prefix to tolerate en-dash
        "Dependencies and run order",
        "Spawn briefs",
    ]:
        assert phase in text, f"missing process phase: {phase}"
    # Single-artifact output (spawn-list.md only — roadmap.md/portfolio.md were retired)
    assert "-spawn-list.md" in text
    assert "-roadmap.md" not in text, "old two-artifact roadmap.md output must be retired"
    assert "-portfolio.md" not in text, "old two-artifact portfolio.md output must be retired"
    # The critique panel was replaced with inline self-review.
    assert "Fact-check mode:" not in text, "critique-panel config block must be removed"
    assert "Criteria assignment:" not in text, "critique-panel config block must be removed"
    # The checklist reference survives (now used for inline self-review)
    assert "roadmap-critique-checklist.md" in text
    # The strategy-advisor panel was removed wholesale
    for advisor in ["Christensen", "Rumelt", "Eric Ries", "Marty Cagan", "marty-cagan"]:
        assert advisor not in text, f"strategy-advisor panel must be removed; still references: {advisor}"
    # Spawn-brief reference still present
    assert "spawn-brief-template.md" in text
    # Pure-orchestration framing must be explicit so the redesign intent is preserved
    assert "orchestration scaffolding" in text.lower(), \
        "the 'pure orchestration scaffolding' framing must remain explicit"



def test_skill_md_has_disambiguation_rules():
    text = read("skills/brainstorming/SKILL.md")
    assert "### Disambiguation Rules" in text, "missing Disambiguation Rules subsection"
    # Rule pairs present after 4-mode collapse (Business mode removed)
    for pair in [
        "Software vs Authoring",
        "Authoring vs Research",
    ]:
        assert pair in text, f"missing rule: {pair}"
    # 4-mode picker labels must appear in Step 1
    for label in [
        "Write a document",
        "Design a code change",
        "Synthesize research",
        "Break a big intent into a queue of brainstorms",
    ]:
        assert label in text, f"missing 4-mode picker label: {label}"


def test_skill_md_step2_has_per_mode_emphasis():
    text = read("skills/brainstorming/SKILL.md")
    step2_start = text.index("## Step 2")
    step3_start = text.index("## Step 3")
    step2 = text[step2_start:step3_start]
    # Each of the 4 modes' emphasis tags must be present in the dispatch prompt template.
    # Roadmap's emphasis shifted from "prior roadmaps + open kanban + customer asks" to
    # "prior spawn-lists + related design docs" in the decomposition-scaffolding redesign.
    for hint in [
        "code artifacts",
        "literature/KB/registries",
        "document corpus",
        "prior spawn-lists",
    ]:
        assert hint in step2, f"missing per-mode emphasis hint: {hint}"
    # Business mode must be dropped from the 4-mode shape
    assert "domain materials" not in step2, \
        "Business 'domain materials' hint must be removed for 4-mode shape"
    assert "|business|" not in step2, \
        "Business must be removed from mode enum in Step 2"


def test_skill_md_step3_uses_table_driven_handoff():
    """Step 3 was refactored from five literal '**If <mode> mode:**' branches into a
    single shared-rules read plus a four-row mode/checklist lookup table. Assert the
    new structure: shared-rules.md is read once, all four modes appear as rows, and
    each mode's checklist is referenced."""
    text = read("skills/brainstorming/SKILL.md")
    step3_start = text.index("## Step 3")
    step3 = text[step3_start:]

    # Shared-rules.md must be read once (extracted from per-mode duplication)
    assert "references/shared-rules.md" in step3, \
        "Step 3 must instruct reading references/shared-rules.md once"

    # Anti-regression: the old per-mode '**If <mode> mode:**' branches must be gone
    for old_branch in [
        "**If software mode:**",
        "**If business mode:**",
        "**If research mode:**",
        "**If authoring mode:**",
        "**If planning mode:**",
    ]:
        assert old_branch not in step3, \
            f"Step 3 should be table-driven; stale branch still present: {old_branch}"

    # Each of the 4 modes appears as a labeled row in the lookup table
    for mode_label in ["Software", "Research", "Authoring", "Roadmap"]:
        assert mode_label in step3, f"Step 3 table missing mode row: {mode_label}"

    # Business mode must be absent from 4-mode shape
    assert "Business" not in step3, \
        "Business mode must be removed from Step 3 for 4-mode shape"

    # Each mode's mode file is referenced in the table
    for mode_file in [
        "modes/software.md",
        "modes/research.md",
        "modes/authoring.md",
        "modes/roadmap.md",
    ]:
        assert mode_file in step3, f"Step 3 table missing mode file: {mode_file}"

    assert "modes/business.md" not in step3, \
        "modes/business.md must be removed from Step 3 for 4-mode shape"

    # Each mode's critique checklist is referenced in the table
    for checklist in [
        "design-critique-checklist.md",
        "research-critique-checklist.md",
        "authoring-critique-checklist.md",
        "roadmap-critique-checklist.md",
    ]:
        assert checklist in step3, f"missing checklist reference: {checklist}"

    assert "business-critique-checklist.md" not in step3, \
        "business-critique-checklist.md must be removed from Step 3 for 4-mode shape"


def test_shared_rules_owns_base_directory_resolution():
    """The {base-directory} resolution note was extracted from each mode file into
    references/shared-rules.md. Assert the canonical home contains the note."""
    text = read("skills/brainstorming/references/shared-rules.md")
    assert "{base-directory}" in text, "shared-rules.md must document {base-directory} resolution"
    assert "brainstorming skill directory" in text or "router" in text, \
        "shared-rules.md must explain that {base-directory} resolves to the router, not modes/"


def test_kickstart_marketing_copy_mentions_four_modes():
    text = read("skills/kickstart/SKILL.md")
    assert "four modes" in text.lower(), "kickstart must declare four modes"
    # Must not still claim five modes outside of CHANGELOG context
    assert "five modes" not in text.lower(), "kickstart still claims five modes"


def test_readme_does_not_claim_two_mode_brainstorm():
    text = read("README.md")
    # L80's stale "Auto-detects software vs business mode" must be retired
    assert "software vs business" not in text.lower()


def test_orchestration_does_not_reference_portfolio_file_path():
    """The portfolio-file-path config field was the only Roadmap-mode-specific
    hook in critique-panel-orchestration. The May 2026 redesign retired the
    Roadmap critique panel entirely (replaced with inline self-review), so the
    hook should be removed to keep the shared orchestration mode-agnostic."""
    text = read("skills/_shared/critique-panel-orchestration.md")
    # The hardcoded "(e.g., software.md or business.md)" example list should remain gone
    assert "(e.g., `software.md` or `business.md`)" not in text, \
        "hardcoded mode example list still present"
    # The portfolio-file-path field must be fully removed
    assert "portfolio-file-path" not in text, \
        "portfolio-file-path should be removed; no mode uses it after the Roadmap redesign"


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



def test_business_files_removed_after_collapse():
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[2]
    for rel in [
        "skills/brainstorming/modes/business.md",
        "skills/brainstorming/business-critique-checklist.md",
        "skills/brainstorming/references/templates/business-template.html",
    ]:
        assert not (REPO / rel).exists(), f"{rel} must be deleted in mode-collapse cutover"


def test_trigger_map_does_not_reference_business():
    text = read("e2e/trigger-map.yaml")
    assert "modes/business.md" not in text, "trigger-map still references deleted file"


def test_eval_surface_does_not_reference_business():
    text = read("e2e/eval-surface.yaml")
    assert "modes/business.md" not in text, "eval-surface still references deleted file"


def test_four_modes_fixture_exists_and_lists_four_modes():
    REPO = Path(__file__).resolve().parents[2]
    assert not (REPO / "e2e/fixtures/skill-prompts/brainstorming-five-modes.md").exists()
    assert (REPO / "e2e/fixtures/skill-prompts/brainstorming-four-modes.md").exists()
    text = (REPO / "e2e/fixtures/skill-prompts/brainstorming-four-modes.md").read_text()
    for label in ["Software", "Authoring", "Research", "Roadmap"]:
        assert label in text, f"missing mode label: {label}"
    for retired in ["Business mode", "Planning mode"]:
        assert retired not in text, f"retired mode still present: {retired}"


def test_four_modes_eval_fixture_lists_briefs():
    text = read("e2e/scenarios/use-skill/brainstorming-four-modes.yaml")
    test_count = text.count("- description:")
    assert test_count >= 4, f"expected ≥4 test briefs in four-modes fixture; found {test_count}"
    for mode_label in ["software", "research", "authoring", "roadmap"]:
        assert mode_label in text.lower(), f"missing mode label: {mode_label}"
    for retired in ["business", "planning"]:
        assert retired not in text.lower(), f"retired mode still in four-modes fixture: {retired}"


def test_new_eval_scenario_files_exist_and_parse():
    REPO = Path(__file__).resolve().parents[2]
    base = REPO / "e2e/scenarios/use-skill"
    scenarios = [
        "always-ask-routing.yaml",
        "deck-routing.yaml",
        "authoring-no-framework-fallback.yaml",
        "brainstorming-four-modes.yaml",
        "framework-runner-extraction.yaml",
        "deliverable-type-dispatch.yaml",
        "use-framework-backward-compat.yaml",
        "authoring-mode-engine-selection.yaml",
    ]
    for name in scenarios:
        path = base / name
        assert path.exists(), f"missing scenario file: {name}"
        with path.open() as f:
            parsed = yaml.safe_load(f)
        assert parsed is not None, f"failed to parse {name}"
        assert "description" in parsed, f"{name} missing top-level description field"


def test_roadmap_mode_does_not_reference_strategy_advisor_panel():
    """The Roadmap-mode strategy-advisor panel (Christensen / Rumelt / Eric Ries /
    Cagan / Bezos / Graham / Tan / Hogan) was removed in the May 2026 decomposition-
    scaffolding redesign. Advisor consultation is intentionally out of scope —
    if a component needs strategic framing, that surfaces inside its own
    downstream brainstorm, not in the decomposition pass."""
    text = read("skills/brainstorming/modes/roadmap.md")
    for advisor in [
        "Christensen", "Rumelt", "Eric Ries", "Marty Cagan",
        "marty-cagan", "Jeff Bezos", "Paul Graham", "Garry Tan", "Lara Hogan",
    ]:
        assert advisor not in text, \
            f"strategy-advisor panel must remain removed; still references: {advisor}"


def test_planning_mode_file_removed_after_rename():
    """Planning → Roadmap rename must be complete; no planning mode file remains."""
    assert not (REPO_ROOT / "skills/brainstorming/modes/planning.md").exists(), \
        "modes/planning.md must be renamed to modes/roadmap.md"
    assert not (REPO_ROOT / "skills/brainstorming/planning-critique-checklist.md").exists()
    assert not (REPO_ROOT / "skills/brainstorming/references/templates/planning-template.html").exists()
    assert (REPO_ROOT / "skills/brainstorming/modes/roadmap.md").exists()


def test_planning_string_references_purged_from_brainstorming_skill():
    """Post-rename grep gate: `planning` should appear ≤2 times in skills/brainstorming/
    (only intentional references to /aligned:writing-plans or historical CHANGELOG context)."""
    hits = 0
    for p in (REPO_ROOT / "skills/brainstorming").rglob("*"):
        if not p.is_file() or p.suffix not in {".md", ".html", ".yaml"}:
            continue
        for line in p.read_text().splitlines():
            if "planning" in line.lower() and "writing-plans" not in line:
                hits += 1
    assert hits <= 2, f"too many residual 'planning' references: {hits} (expected ≤2)"



def test_critique_interactive_html_agent_exists():
    """The interactive critique HTML agent must exist and declare the inputs
    and behavior the orchestration depends on."""
    text = read("agents/critique-interactive-html-generator.md")
    # Frontmatter
    assert text.startswith("---\nmodel: sonnet\n---"), "missing sonnet model frontmatter"
    # Required input placeholders
    for placeholder in [
        "{aggregated-json-path}",
        "{design-file-path}",
        "{session-name}",
        "{mode}",
    ]:
        assert placeholder in text, f"agent must document input: {placeholder}"
    # Output path convention
    assert "docs/mockups/{session-name}-critique.html" in text, \
        "agent must write to the standard critique HTML output path"
    # Default toggle states match orchestration's Apply Fixes bias
    assert "high" in text.lower() and "medium" in text.lower() and "low" in text.lower(), \
        "agent must address all three severity buckets"
    # Fact-checks are read-only per the orchestration's auto-apply rule
    assert "not toggleable" in text.lower() or "read-only" in text.lower(), \
        "fact-checks must be documented as non-toggleable"
    # Clipboard-only round-trip (no auto-send)
    assert "clipboard" in text.lower() or "navigator.clipboard" in text, \
        "agent must describe clipboard-based copy-as-prompt"
    # Don't commit — brainstorming commits artifacts together
    assert "Do NOT commit" in text or "do not commit" in text.lower(), \
        "agent must warn against committing"


def test_orchestration_dispatches_interactive_html():
    """The shared critique panel orchestration must dispatch the interactive
    decision HTML generator after aggregation and document the JSON schema
    both aggregation paths produce."""
    text = read("skills/_shared/critique-panel-orchestration.md")
    # New section header
    assert "## Interactive Decision HTML" in text, \
        "orchestration must add an Interactive Decision HTML section"
    # New agent reference
    assert "critique-interactive-html-generator" in text, \
        "orchestration must reference the new agent"
    # Both aggregation paths write the same two files
    assert "aggregated.md" in text and "aggregated.json" in text, \
        "orchestration must require aggregated.md + aggregated.json from aggregation step"
    # JSON schema documented (fact_checks + findings)
    assert "fact_checks" in text and "findings" in text, \
        "orchestration must document the structured aggregator output schema"
    # Sub-agent aggregator must now have Write tool
    assert "Glob, Read, and Write tools" in text, \
        "sub-agent aggregator must have Write tool to produce both files"
    # User-facing instructions for the round-trip
    assert "Copy follow-up prompt" in text, \
        "orchestration must surface the copy-follow-up-prompt affordance to the user"
    # Chat path remains as fallback
    assert "both paths work" in text.lower() or "chat path" in text.lower(), \
        "orchestration must preserve chat path as a fallback"


def test_plugin_version_bumped():
    plugin_json = json.loads(read(".claude-plugin/plugin.json"))
    marketplace_json = json.loads(read(".claude-plugin/marketplace.json"))
    # Both manifests must agree on version (per CLAUDE.md §Version)
    plugin_version = plugin_json["version"]
    marketplace_version = marketplace_json["plugins"][0]["version"]
    assert plugin_version == marketplace_version, \
        f"plugin.json ({plugin_version}) and marketplace.json ({marketplace_version}) disagree"
    # Must be > 0.26.0 (the version on main when this plan was authored)
    def parse(v):
        return tuple(int(x) for x in v.split("."))
    assert parse(plugin_version) > parse("0.26.0"), \
        f"version {plugin_version} not bumped above pre-plan baseline 0.26.0"


def test_authoring_mode_documents_missing_deliverable_type_fallback():
    """Phase 3 must define behavior when registry drift loses deliverable_type."""
    text = read("skills/brainstorming/modes/authoring.md")
    assert "missing" in text.lower() and "deliverable_type" in text
    assert "content" in text.lower(), "fallback to content template must be documented"
    assert "sync_framework_frontmatter" in text or "re-sync" in text.lower(), (
        "drift remediation hint must point at the sync script"
    )


def test_authoring_mode_documents_project_scan_failure():
    """Design L211: authoring mode with project scan failure."""
    text = read("skills/brainstorming/modes/authoring.md")
    assert "scan" in text.lower()
    # Acceptable phrasings: "scan fails", "scan failure", "scan unavailable", "without scan"
    assert any(s in text.lower() for s in [
        "scan fail", "scan returns empty", "without scan", "scan unavailable",
    ]), "missing project-scan-failure handling"


def test_authoring_critique_checklist_has_conditional_sections():
    text = read("skills/brainstorming/authoring-critique-checklist.md")
    for tag in ["content", "decision", "plan", "analysis"]:
        assert tag in text.lower(), f"checklist missing conditional section for {tag}"
    # Section anchors so the orchestrator can find them
    assert "## Conditional sections" in text or "### deliverable_type:" in text


def test_authoring_has_one_template_per_deliverable_type():
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[2]
    base = REPO / "skills/brainstorming/references/templates"
    assert (base / "authoring-template.html").is_file(), "default content template missing"
    for kind in ["decision", "plan", "analysis"]:
        assert (base / f"authoring-{kind}-template.html").is_file(), (
            f"missing per-deliverable-type template: authoring-{kind}-template.html"
        )


def test_references_describe_four_modes_post_collapse():
    for rel in [
        "skills/brainstorming/references/shared-rules.md",
        "skills/brainstorming/references/visualization-protocol.md",
        "skills/brainstorming/references/brainstorm-components.md",
        "skills/_shared/critique-panel-orchestration.md",
    ]:
        text = read(rel)
        # Must not enumerate business or planning anymore (writing-plans excepted)
        for retired in [" business,", " planning,", "business |", "planning |"]:
            assert retired not in text.lower(), f"{rel} still enumerates retired mode: {retired!r}"
        # Must enumerate Authoring as part of the 4-mode set
        assert "authoring" in text.lower(), f"{rel} missing authoring"
        # roadmap or research must be present in any mode enumeration
        assert "roadmap" in text.lower() or "research" in text.lower()


def test_authoring_templates_share_common_scaffolding():
    # All four templates must share the live-refresh script and the design-doc header anchor
    # so visualization-protocol's strip step works uniformly.
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[2]
    base = REPO / "skills/brainstorming/references/templates"
    files = [
        "authoring-template.html",
        "authoring-decision-template.html",
        "authoring-plan-template.html",
        "authoring-analysis-template.html",
    ]
    for name in files:
        text = (base / name).read_text()
        # Anchor: every template carries the live-refresh script marker that
        # visualization-protocol.md's strip rule looks for.
        assert "<script" in text, f"{name} missing live-refresh script anchor"


def test_spawn_brief_target_mode_excludes_roadmap():
    """The May 2026 redesign dropped Roadmap as a target_mode for spawn-list entries.
    Recursive decomposition is intentionally out of scope: if a component is itself
    too big for a single brainstorm, Phase 2 decomposes it further at authoring time,
    rather than punting to a nested Roadmap brainstorm later."""
    text = read("skills/brainstorming/references/spawn-brief-template.md")
    # target_mode enum must be exactly the three terminal brainstorming modes
    assert "{Software | Authoring | Research}" in text, \
        "target_mode enum must list exactly Software, Authoring, Research"
    # The enum line must not include Roadmap
    enum_line = next(
        (l for l in text.splitlines() if l.strip().startswith("**Target mode:**")),
        None,
    )
    assert enum_line is not None, "schema must declare Target mode field"
    assert "Roadmap" not in enum_line, \
        "Roadmap must not appear in target_mode enum — recursive decomposition was retired"


def test_visualization_protocol_delegates_to_runner():
    text = read("skills/brainstorming/references/visualization-protocol.md")
    # Still readable at its e2e-pinned path, still no YAML frontmatter
    assert not text.lstrip().startswith("---")
    # Delegates the engine to the shared runner
    assert "skills/_shared/visualization-runner.md" in text, "wrapper must delegate to the runner"
    # Brainstorming-specific lifecycle stays in the wrapper
    assert "docs/mockups/" in text, "pre-critique snapshot path must stay in the wrapper"
    assert "**Mockups:**" in text, "Mockups header field is brainstorming-specific"
    # Delegation appears early — within the first ~40 lines, not buried in prose
    head = "\n".join(text.splitlines()[:40])
    assert "skills/_shared/visualization-runner.md" in head, "delegation must be the first actionable line, not buried"
