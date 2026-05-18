"""Structural assertions for the brainstorming three-modes implementation."""
import json
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
        "# Roadmap Critique Checklist",
        ["Opportunity-space clarity", "Inventory completeness", "Sizing realism",
         "Dependency rigor", "Sequencing logic", "Capacity vs scope",
         "Spawn-brief quality", "Strategic coherence", "Decision quality"],
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
    # Shared runners
    assert "_shared/framework-runner.md" in text
    assert "intake_gate_mode" in text and "strict" in text
    assert "_shared/advisor-runner.md" in text
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
    # Picker label format (task vocabulary, not mode IDs)
    for label_fragment in ["Write a document", "Design a code change", "Synthesize research", "Break a big initiative"]:
        assert label_fragment in step1, f"missing picker label: {label_fragment}"


def test_skill_md_keyword_expansion_includes_deck_and_breakdown_signals():
    text = read("skills/brainstorming/SKILL.md")
    # Authoring keyword expansion (May 17 amendment)
    for kw in ["deck", "presentation", "pitch deck", "memo", "battle card"]:
        assert kw in text.lower(), f"authoring missing keyword: {kw}"
    # Roadmap keyword expansion (May 17 amendment)
    for kw in ["break", "decompose", "big idea", "smaller pieces", "spawn list"]:
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
    text = read("skills/brainstorming/modes/roadmap.md")
    assert text.splitlines()[0] == "<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->"
    # Anti-regression: extracted to references/shared-rules.md by the
    # visualization-protocol / shared-rules refactor.
    assert "Within this mode file, `{base-directory}` resolves to" not in text, \
        "base-directory note should live only in references/shared-rules.md, not be duplicated in mode files"
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
    assert "roadmap-critique-checklist.md" in text
    # Default panel + Cagan-conditional
    assert "Christensen" in text and "Rumelt" in text and "Eric Ries" in text, \
        "missing default launch panel"
    # Cagan absence-handling must reference the actual prompt-file path, not just the name
    assert "advisors/prompts/marty-cagan.md" in text, \
        "Cagan absence-handling must check the actual prompt-file path"
    # Spawn-brief reference
    assert "spawn-brief-template.md" in text



def test_skill_md_has_disambiguation_rules():
    text = read("skills/brainstorming/SKILL.md")
    assert "### Disambiguation Rules" in text, "missing Disambiguation Rules subsection"
    # All three rule pairs must appear
    for pair in [
        "Software vs Authoring",
        "Authoring vs Research",
        "Business vs Roadmap",
    ]:
        assert pair in text, f"missing rule: {pair}"
    # 5-way disambiguation question must appear
    assert ("Software design" in text and "Business strategy" in text
            and "Research synthesis" in text and "Content authoring" in text
            and "Multi-feature roadmap" in text), \
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
        "document corpus",
        "prior roadmaps",
    ]:
        assert hint in step2, f"missing per-mode emphasis hint: {hint}"


def test_skill_md_step3_uses_table_driven_handoff():
    """Step 3 was refactored from five literal '**If <mode> mode:**' branches into a
    single shared-rules read plus a five-row mode/checklist lookup table. Assert the
    new structure: shared-rules.md is read once, all five modes appear as rows, and
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

    # Each mode appears as a labeled row in the lookup table
    for mode_label in ["Software", "Business", "Research", "Authoring", "Roadmap"]:
        assert mode_label in step3, f"Step 3 table missing mode row: {mode_label}"

    # Each mode's mode file is referenced in the table
    for mode_file in [
        "modes/software.md",
        "modes/business.md",
        "modes/research.md",
        "modes/authoring.md",
        "modes/roadmap.md",
    ]:
        assert mode_file in step3, f"Step 3 table missing mode file: {mode_file}"

    # Each mode's critique checklist is referenced in the table
    for checklist in [
        "design-critique-checklist.md",
        "business-critique-checklist.md",
        "research-critique-checklist.md",
        "authoring-critique-checklist.md",
        "roadmap-critique-checklist.md",
    ]:
        assert checklist in step3, f"missing checklist reference: {checklist}"


def test_shared_rules_owns_base_directory_resolution():
    """The {base-directory} resolution note was extracted from each mode file into
    references/shared-rules.md. Assert the canonical home contains the note."""
    text = read("skills/brainstorming/references/shared-rules.md")
    assert "{base-directory}" in text, "shared-rules.md must document {base-directory} resolution"
    assert "brainstorming skill directory" in text or "router" in text, \
        "shared-rules.md must explain that {base-directory} resolves to the router, not modes/"


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


def test_roadmap_mode_handles_cagan_absence():
    text = read("skills/brainstorming/modes/roadmap.md")
    # The mode file must do a file-existence check on the Cagan prompt path
    assert "advisors/prompts/marty-cagan.md" in text, \
        "missing Cagan prompt-file existence check"
    # Default panel without Cagan must be explicitly named
    for advisor in ["Christensen", "Rumelt", "Eric Ries"]:
        assert advisor in text, f"default-panel advisor missing: {advisor}"
    # The mode must say absence is handled silently (no surfaced warning)
    # per design §Error paths #5
    assert "silently" in text.lower() or "without surfacing" in text.lower(), \
        "Cagan-absence handling must be silent (no user-facing warning)"


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
