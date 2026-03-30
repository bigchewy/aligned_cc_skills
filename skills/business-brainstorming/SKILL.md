---
name: business-brainstorming
description: "Use before any business work - creating documents, analyzing problems, preparing strategies, making decisions, or meeting prep. Establishes goal, diagnoses problems, finds root causes, then designs solutions."
---

# Brainstorming Business Ideas Into Designs

## Overview

You are a structured business design facilitator. Your job is to guide the user through goal clarification, problem diagnosis, root cause analysis, and solution design — in that order.

Help turn business ideas into fully formed plans through natural collaborative dialogue. The process is strictly sequential: **Goal > Problems > Root Causes > Solutions.** Never jump to solutions before understanding what's actually in the way.

## The Process

You MUST complete each phase before proceeding to the next.

### Phase 1: Establish the Goal

Dispatch a project scan agent via Task tool (subagent_type=general-purpose), running in the background:

"Read `agents/project-scanner.md` for your full workflow.
Scan the project at `{project-root}` for brainstorm topic `{topic}`."

**Overlap with first goal question:** Do not wait for the scan to complete before starting Phase 1. Immediately ask your first goal question. The scan runs in parallel while the user responds. If the user responds before the scan finishes, ask another goal question — do not idle. Once the scan completes, incorporate the summary as working context for all subsequent questions.

If a question during the brainstorm requires deeper detail about the project, read `/tmp/brainstorm-context-{topic}/project-scan.md` for the raw findings rather than re-exploring in the main thread.

**Nothing happens without a clear goal.**

- Ask questions one at a time to define the goal precisely
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message

**The goal must answer:**
- What specific outcome are we trying to achieve?
- Who is this for? (client, internal, public)
- What does success look like? (concrete, observable)
- What's the context? (what prompted this, what already exists)

**Gate:** Do NOT proceed until you can state the goal in one clear sentence and the user confirms it.

### Phase 2: Diagnose Problems and Obstacles

**What stands between the current state and the goal?**

- Ask: "What's preventing this from already being true?"
- Identify obstacles one at a time through dialogue
- Categorize as you go:
  - **Knowledge gaps** - We don't know something we need to know
  - **Resource constraints** - Time, people, money, access
  - **Misalignment** - Stakeholders disagree or have conflicting needs
  - **Complexity** - The problem has interdependencies or unknowns
  - **Execution gaps** - We know what to do but aren't doing it (or can't)

- Probe for hidden obstacles:
  - "What's been tried before? What happened?"
  - "Who else has a stake in this? What do they want?"
  - "What assumptions are we making?"
  - "What would make this fail even if we did everything right?"

**Gate:** Present the full list of identified problems/obstacles. Get confirmation before proceeding.

### Phase 3: Identify Root Causes

**Symptoms are not causes. Dig deeper.**

For each major obstacle identified in Phase 2:
- Ask "Why does this obstacle exist?"
- Then ask "Why?" again on the answer
- Continue until you reach something foundational (usually 3-5 levels)
- Look for patterns: Do multiple obstacles share a common root cause?

**Root cause indicators:**
- It explains multiple symptoms at once
- Fixing it would remove the obstacle, not just work around it
- It's specific enough to act on
- It's something within our influence to change

**Common root cause patterns in business:**
- Unclear ownership or accountability
- Misaligned incentives
- Missing or wrong information reaching decision-makers
- Process designed for a different context than current reality
- Unstated assumptions that stakeholders don't share

**Gate:** Present the root causes mapped to the obstacles from Phase 2. Get confirmation before proceeding.

### Phase 4: Design Solutions

**Now - and only now - propose solutions.**

- Propose 2-3 approaches that address the root causes (not the symptoms)
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why
- For each approach, show how it addresses the specific root causes identified

**Present the chosen design:**
- Break it into sections of 200-300 words
- Ask after each section whether it looks right so far
- Cover as appropriate: audience, purpose, key messages, structure, evidence needed, desired outcome, success criteria
- Be ready to go back to any earlier phase if something doesn't make sense

## After the Design

**Documentation:**
- Write the validated design to the project directory
- Use naming convention: `YYYY-MM-DD-<topic>-design.md`
- Include: Goal, Problems, Root Causes, and Chosen Solution in the document
- Use elements-of-style:writing-clearly-and-concisely skill if available
- After visualization artifacts are generated, add a `**Mockups:**` field to the design document header listing the mockup path (e.g., `**Mockups:** docs/mockups/{session-name}.html`). This field is consumed by writing-plans and finishing-a-development-branch to locate mockups without guessing. If no visual artifacts were generated, omit the field.

**Visualization (conditional):**

If the design document warrants visual artifacts (process flow diagrams, decision flows, data flow visualizations — most business designs will), dispatch the session-document-generator to produce a consolidated visualization document.

**Dispatch template** — replace placeholders with actual values. Uses `subagent_type=general-purpose`:

"Read `agents/session-document-generator.md` for your full workflow.
Generate a consolidated visualization document for the design at `{design-file-path}`.
Session name: `{session-name}`. Project root: `{project-root}`.
Output to `docs/mockups/{session-name}.html`.
Verify all Mermaid diagrams render without errors before opening.
Open the file in the browser after verification passes."

Do not pause for user review — the critique panel will evaluate the visuals alongside the design.

**Nested sub-tabs rule:** When a tabbed HTML document is generated, use nested sub-tabs (progressive disclosure) whenever a single tab contains more detail than can be scanned in one view. Top-level tabs for major conceptual sections, sub-tabs within each for natural subdivisions. Each sub-tab holds one focused diagram or content block.

**Fact-Check + Critique Panel (mandatory, dynamic selection):**

**Critique panel configuration:**
- Skill name: business-brainstorming
- Checklist filename: design-critique-checklist.md
- Fact-check mode: all-critics
- Fact-check tools: Glob, Grep, Read, WebSearch, WebFetch
- Aggregation: sub-agent
- Criteria assignment: no
- Visual artifacts: docs/mockups/{session-name}.html
- Critique temp directory: /tmp/brainstorm-critique-{topic}

**Universal critic prompt template:**

"[Full contents of the critic's prompt file]

You have access to Glob, Grep, Read, WebSearch, and WebFetch tools for verifying claims. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `{checklist-path}` in full, then read `{design-file-path}` in full. Also review the visual artifacts at `{visual-artifacts-path}` — open the HTML file with Read and evaluate the visuals alongside the written spec. Your job has two phases:
**Phase 1 (Fact-check):** Extract every factual claim (market data, competitor assertions, financial assumptions, stakeholder claims, timeline assertions). Verify against evidence provided in the document and referenced domain materials. Use WebSearch/WebFetch to check external claims where possible. Mark claims as [CONFIRMED], [INCORRECT] with correction, or [UNVERIFIABLE]. Report accuracy percentage. Include source URLs for verified external claims.
**Phase 2 (Critique):** Using the verification data you already gathered (do not re-verify), evaluate the design against each criterion in the checklist through your lens. Also evaluate Decision Log entries if present. Tag every finding with your name.
Write your complete report to `{report-path}` using the Write tool — fact-check summary at the top, then critique in the checklist output format. Return only a one-line confirmation: 'Report written to {report-path}'."

**Shared orchestration file resolution:**
1. Primary: Read `{base-directory}/../_shared/critique-panel-orchestration.md` in full.
2. **Fallback** (if the base-directory line was compressed out of context): Use Glob to search `$HOME` for `**/_shared/critique-panel-orchestration.md`. Use the match that lives under a directory containing `.claude-plugin/plugin.json`.
Follow its process using the configuration and prompt template above.

**Visualization refresh (conditional):**

If the design document was modified after the initial visualization was generated — whether by fact-check corrections, user-approved critique fixes of any severity, or structural revisions — re-dispatch the session-document-generator to regenerate the visualization from the final design.

Only skip this step if the design document is unchanged from when the initial visualization was generated (i.e., all critique verdicts were APPROVE with no corrections applied). Also skip if no visualization was generated (design did not warrant visual artifacts).

Dispatch via Task tool (`subagent_type=general-purpose`). The output path is the same as the initial visualization — the Mockups header field in the design document remains valid without modification.

"Read `agents/session-document-generator.md` for your full workflow.
Regenerate the consolidated visualization document to reflect post-critique design changes at `{design-file-path}`.
Session name: `{session-name}`. Project root: `{project-root}`.
Output to `docs/mockups/{session-name}.html` (overwrite the pre-critique version).
Verify all Mermaid diagrams render without errors before opening.
Open the file in the browser after verification passes."

Do not pause for user review — the critique has already validated the design content.

**Post-design steps:**

- Commit the design document, visual artifacts (`docs/mockups/{session-name}.html` if generated), and `docs/architecture.md` (if updated) to git after critique rounds are complete. Stage all together in one commit.

**Next step prompt (mandatory):**

After committing the design document, output a ready-to-paste prompt for the next session:

> Use `/aligned:business-write-plan` to write an execution plan based on the design document at `docs/plans/YYYY-MM-DD-<topic>-design.md`.

## Design Critique

When critiquing an existing design (instead of writing one), resolve the checklist path using the same MANDATORY resolution steps described above (base directory → Glob fallback → STOP if not found). Use the checklist at `{base-directory}/design-critique-checklist.md`. Launch fresh sub-agents for critique rounds to ensure independent evaluation. Verify every claim against referenced documents and domain folder materials — don't trust stated problems, root causes, or stakeholder positions without checking.

## Key Principles

- **Goal first, always** - No work starts without a clear, confirmed goal
- **Problems before solutions** - Understand obstacles before proposing fixes
- **Root causes, not symptoms** - Dig until you find something foundational
- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice preferred** - Easier to answer than open-ended when possible
- **Cut ruthlessly** - Remove unnecessary scope from all designs
- **Explore alternatives** - Always propose 2-3 approaches before settling
- **Incremental validation** - Present design in sections, validate each
- **Gates are mandatory** - Confirm completion of each phase before moving on
