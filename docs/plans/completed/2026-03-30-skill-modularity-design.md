# Skill Modularity: Shared Modules for Brainstorming Pair

**Date:** 2026-03-30
**Status:** Design
**Scope:** brainstorming + business-brainstorming skill pair
**Mockups:** docs/mockups/skill-modularity.html

## Goal

Extract shared structural patterns from the brainstorming/business-brainstorming skill pair into reusable shared files and agents, so that orchestration improvements are "edit once, both get it." Additionally, upgrade business-brainstorming with capabilities it currently lacks (project scanning, sub-agent aggregation, visualization) that naturally fall out of the shared modules. Domain-specific content stays in each skill's own SKILL.md.

**Motivation:** The skills have existed for ~2 months and are already 2x diverged in line count. The technical brainstorming skill has received significant improvements (Architect auto-consult, division-of-labor critique panels, sub-agent aggregation, mandatory visualization) that business brainstorming hasn't benefited from. This refactoring is preventive — establishing modularity now before the divergence deepens further.

## Decision Log

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Use `skills/_shared/*.md` "read this file" pattern for shared orchestration | Already established by 6+ skills referencing `kanban-entry-format.md`. No build step, no preprocessing, compatible with direct-edit-and-test workflow. **Note:** The shared critique panel file is fundamentally different from `kanban-entry-format.md` — it is a parameterized orchestration protocol (~60 lines, 7 parameters, conditional branches, 2 consumers) rather than a simple reference document (23 lines, zero parameters, 6 consumers). This is a new category of shared file. A configuration validation preamble mitigates the risk of misconfigured parameters. |
| D2 | Extract project scan to `agents/project-scanner.md` | Self-contained unit of work: receives project root + topic, writes findings to `/tmp/`, returns summary. No user interaction needed. Matches the agent pattern (like session-document-generator). |
| D3 | Inline checklist resolution into critique panel file (not a separate shared file) | Anthropic best practices: keep references one level deep from SKILL.md. A shared file referencing another shared file creates two hops. The kanban-entry-format precedent is always a leaf node. |
| D4 | Keep business brainstorming on "all-critics" fact-check mode | Business fact-checking uses WebSearch/WebFetch where different critics bring different search strategies for the same claim. The 50% token waste argument from technical (where codebase fact-checking is deterministic) does not apply. Additionally, `criteria-assignment: no` is structurally required for business — the business checklist has entirely different criteria (goal precision, root cause depth, stakeholder mapping) that don't map to the same domain buckets as the technical criteria mapping table. This is not a preference toggle; it reflects fundamentally different checklist semantics. |
| D5 | Upgrade business brainstorming to sub-agent aggregation | Inline aggregation consumes main-thread context with raw reports. Sub-agent aggregation keeps reports in `/tmp/` and returns a concise summary. Requires changing critic prompt templates to write-to-file. **Note:** This is a behavioral change, not a pure extraction — acknowledged as a new capability for business-brainstorming. |
| D6 | Add visualization to business brainstorming | session-document-generator has a global fallback for design-principles at `~/.claude/docs/design/design-principles.md`, so it will not hard-fail on business projects lacking a project-local design-principles file. Business brainstorming benefits from process flow diagrams, decision flow visualizations, and data flow diagrams. Visualization dispatch is conditional: only dispatch if the design document warrants visual artifacts (which it will in most cases). **Note:** Business projects using the global fallback will get generic software-oriented styling rather than project-specific design tokens — acceptable for process/decision flow diagrams; a project-local design-principles.md can be added later for better styling. |
| D7 | Selective sync model | Some improvements cross over (orchestration, project scan), others don't (Architect consult is technical-only, 4-phase goal/problems/root-causes/solutions is business-only). |

## File Changes

### New Files

#### 1. `agents/project-scanner.md`

**Type:** Agent (dispatched as sub-agent via Task tool)

**Frontmatter:**
```yaml
---
model: opus
---
```

**Contents:**

The scanner adapts its investigation based on what it finds. It checks for code artifacts (package.json, go.mod, src/) AND domain materials (docs/plans/, meeting notes, deliverables, existing analyses). If the project is primarily documents/plans rather than code, it emphasizes the domain materials rather than trying to find a tech stack.

- Investigation checklist:
  - Project structure (key directories, entry points, config files)
  - Recent git activity (last 10-15 commits via `git log --oneline -15`)
  - Existing docs (README, CLAUDE.md, docs/ directory)
  - Architecture docs (`docs/architecture.md` — read in full if exists; note data flows, module dependencies, system diagrams, staleness)
  - Existing plans and designs (`docs/plans/` — scan for prior design docs and active plans)
  - Domain materials (meeting notes, strategy docs, analyses, deliverables — any non-code context relevant to the brainstorm)
  - Architecture patterns (module organization, key abstractions, data flow conventions) — if applicable
  - Tech stack and dependencies (package.json, go.mod, etc.) — if applicable
- Tools: Bash (for git commands only), Glob, Grep, Read, Write
- Contract:
  - Input: project root path, topic slug
  - Output: writes detailed findings to `/tmp/brainstorm-context-{topic}/project-scan.md`, returns concise summary (under 300 words)

**Note:** Adding this agent to business-brainstorming is a new capability (business-brainstorming previously had no project scan). The scan findings help Claude ask better questions during goal clarification and problem diagnosis.

**Dispatch pattern (same for both skills):**
```
"Read agents/project-scanner.md for your full workflow.
Scan the project at {project-root} for brainstorm topic {topic}."
```

#### 2. `skills/_shared/critique-panel-orchestration.md`

**Type:** Shared instruction file (read into main context)

**Parameters set by calling SKILL.md before reading:**
- `fact-check-mode`: "division-of-labor" or "all-critics"
- `fact-check-tools`: tool list for critic sub-agents
- `aggregation`: "sub-agent" or "inline"
- `criteria-assignment`: "yes" (with mapping table provided) or "no"
- `visual-artifacts`: path to visuals or "none"
- `critique-temp-directory`: `/tmp/brainstorm-critique-{topic}`
- Critic prompt templates: fact-checker + regular (if division-of-labor), or universal (if all-critics)

**Contents:**

1. **Configuration validation preamble** — Before proceeding, verify all required parameters are present in the SKILL.md context above:
   - `fact-check-mode` must be either "division-of-labor" or "all-critics"
   - `fact-check-tools` must be a non-empty tool list
   - `aggregation` must be either "sub-agent" or "inline"
   - `criteria-assignment` must be "yes" (with mapping table) or "no"
   - `visual-artifacts` must be a path or "none"
   - `critique-temp-directory` must be set
   - At least one critic prompt template must be provided
   - `skill-name` and `checklist-filename` must be set
   If any required parameter is missing, STOP and tell the user which parameter is missing from their SKILL.md configuration block.

2. **MANDATORY sub-agent launch rule** — You MUST use the Task tool to launch fresh sub-agents for every critique round. NEVER run the critique in the main context window.

3. **Checklist resolution (inlined):**
   - Find the "Base directory for this skill:" line from skill load context
   - Construct path: `{base-directory}/{checklist-filename}`
   - Fallback: Glob search `$HOME` for `**/{skill-name}/{checklist-filename}`, match under directory containing `.claude-plugin/plugin.json`
   - Verify path exists with Read. STOP if not found.
   - Parameterized by `{skill-name}` and `{checklist-filename}` from the calling SKILL.md

4. **Round 1 orchestration:**
   a. Read `advisors/registry.md`
   b. Select 1-4 critics following registry selection guidelines. Hard-exclude critics whose `not_for` matches the design's primary domain. Prefer diversity of lens.
   c. Read each selected critic's full prompt file

   **If division-of-labor:**
   d. Designate fact-checker (priority: QA Engineer > Architect > first selected critic). Fact-checker does both fact-checking and domain critique.
   e. Assign each checklist criterion (1-N) to one critic using the mapping table from the SKILL.md. Criterion 9 (Decision quality) goes to all critics. Target 2-4 criteria per critic.
   f. State full assignment table before launching.
   g. Create temp directory: `{critique-temp-directory}/round-1/`
   h. Launch all critics in parallel (single message, multiple Task tool calls, `subagent_type=general-purpose`, `model=opus`). Use the fact-checker prompt template for the designated fact-checker, regular critic prompt template for others.

   **If all-critics:**
   d. Create temp directory: `{critique-temp-directory}/round-1/`
   e. Launch all critics in parallel using the universal critic prompt template.

   **Aggregation:**

   **If sub-agent:**
   Dispatch one aggregation agent via Task tool (`subagent_type=general-purpose`, `model=opus`):
   - Read all report files in `{critique-temp-directory}/round-1/`
   - Read design document for context
   - Produce unified report: fact-check summary (total claims, accuracy percentage, every INCORRECT claim with correction), critique findings (merged, de-duplicated, grouped by severity high > medium > low), action items (ordered by severity, noting which critics raised each)
   - Keep under 1500 words

   **If inline:**
   Merge all critic reports in the main thread. De-duplicate, preserve persona tags, group by severity.

   Present unified report to user.

5. **Apply fixes (BEFORE Round 2):**
   - Apply corrections for every INCORRECT fact-check claim immediately
   - Present medium/high critique issues to the user for approval
   - Apply user-approved fixes to the design document
   - These modifications MUST be completed before any Round 2 dispatch — Round 2 critics evaluate the updated document, not the original

6. **Round 2 (conditional):**
   - Only run if Round 1 found medium or high severity issues AND fixes were applied in step 6
   - Same critics and role assignments from Round 1, fresh sub-agents
   - Write to `{critique-temp-directory}/round-2/`
   - Prepare a brief summary of what changed since Round 1 and pass it to each agent
   - Scope to changes only: fact-checker re-verifies only changed claims, other critics re-evaluate only changed sections
   - Aggregate same way as Round 1

7. **Escalation:**
   - If Round 1 revealed concerns in a domain not covered by selected critics, add one specialist for Round 2
   - State escalation reason
   - Maximum one additional critic per round

### Modified Files

#### 3. `skills/brainstorming/SKILL.md`

**Change 1: Project scan dispatch (lines 18-33)**

Replace 16-line inline dispatch template with:
```
First, dispatch a project scan agent via Task tool (subagent_type=general-purpose):

"Read agents/project-scanner.md for your full workflow.
Scan the project at {project-root} for brainstorm topic {topic}."
```

Sequencing rule stays (technical-only, references Architect).

**Change 2: Critique panel (lines 172-251)**

Replace ~80 lines with configuration block + prompt templates + shared file read:

```
**Critique panel configuration:**
- Skill name: brainstorming
- Checklist filename: design-critique-checklist.md
- Fact-check mode: division-of-labor
- Fact-check tools: Glob, Grep, Read, Write
- Aggregation: sub-agent
- Criteria assignment: yes
- Visual artifacts: docs/mockups/{session-name}.html
- Critique temp directory: /tmp/brainstorm-critique-{topic}
```

Followed by:
- Architect independence note (technical-only, ~3 lines)
- Criteria mapping table (technical-only, ~12 lines)
- Fact-checker prompt template (~8 lines)
- Regular critic prompt template (~8 lines)
- `Read {base-directory}/../_shared/critique-panel-orchestration.md in full and follow its process using the configuration and prompt templates above.`

**Estimated:** ~28 lines replacing ~80 lines. Net savings: ~52 lines.

**Untouched sections:**
- Architect auto-consult (lines 67-133)
- Mockup generation (lines 54-65)
- Visualization dispatch + nested sub-tabs (lines 148-170)
- Visualization refresh (lines 253-268)
- Next-step prompt with autopilot (lines 272-296)
- Design critique standalone mode (lines 298-300)
- Key principles (lines 302-309)

#### 4. `skills/business-brainstorming/SKILL.md`

**Change 1: Add project scan dispatch (new, at start of Phase 1)**

Add ~3 lines before goal Q&A:
```
First, dispatch a project scan agent via Task tool (subagent_type=general-purpose):

"Read agents/project-scanner.md for your full workflow.
Scan the project at {project-root} for brainstorm topic {topic}."

Wait for the scan to complete, then proceed with Phase 1 goal questions
using the summary as working context.
```

**Change 2: Add visualization dispatch (new, after design documentation)**

Add visualization dispatch after writing the design document and before the critique panel, matching the pattern from technical brainstorming (~10 lines):
- Dispatch session-document-generator agent to produce process flow diagrams, decision flows, and data flow visualizations
- Include nested sub-tabs rule for progressive disclosure
- Add conditional visualization refresh after critique (if design was modified)
- Add `**Mockups:**` field to design document header

This is a new capability for business-brainstorming. The session-document-generator has a global fallback for design-principles, so it works in projects without a local design-principles.md.

**Change 3: Critique panel (lines 104-139)**

Replace ~36 lines with configuration block + prompt template + shared file read:

```
**Critique panel configuration:**
- Skill name: business-brainstorming
- Checklist filename: design-critique-checklist.md
- Fact-check mode: all-critics
- Fact-check tools: Glob, Grep, Read, WebSearch, WebFetch
- Aggregation: sub-agent
- Criteria assignment: no
- Visual artifacts: docs/mockups/{session-name}.html
- Critique temp directory: /tmp/brainstorm-critique-{topic}
```

Followed by:
- Universal critic prompt template (~10 lines, updated to write reports to `{report-path}` and return one-line confirmation instead of returning inline)
- `Read {base-directory}/../_shared/critique-panel-orchestration.md in full and follow its process using the configuration and prompt template above.`

**Estimated:** ~17 lines replacing ~36 lines. Net savings: ~19 lines.

**Behavioral changes:**
- Critics now write reports to files and the aggregation sub-agent reads from those files. Previously, critics returned reports inline and aggregation happened in the main thread.
- Critics now review visual artifacts alongside the written spec (new, enabled by visualization dispatch above).

**Untouched sections:**
- 4-phase process: goal > problems > root causes > solutions (lines 18-94)
- Documentation conventions (lines 98-103)
- Next-step prompt pointing to business-write-plan (lines 145-149)
- Design critique standalone mode (lines 151-153)
- Key principles (lines 155-166)

## Summary Table

| File | Before | After | Delta |
|------|--------|-------|-------|
| brainstorming/SKILL.md | 309 lines | ~250 lines | -59 |
| business-brainstorming/SKILL.md | 165 lines | ~160 lines | -5, +project scan, +visualization, +sub-agent aggregation |
| _shared/critique-panel-orchestration.md | — | ~70 lines | new (includes config validation preamble) |
| agents/project-scanner.md | — | ~40 lines | new |
| **Total** | **474 lines** | **~520 lines** | +46 lines, but shared orchestration is now single-source |

The total line count increases because the shared files add structure and business-brainstorming gains new capabilities. The value is not line reduction — it is the "edit once" property for orchestration improvements plus feature parity where appropriate.

## Testing Strategy

### Structural Verification

After writing the files, verify:
- Both SKILL.md files reference `_shared/critique-panel-orchestration.md`
- Both SKILL.md files reference `agents/project-scanner.md`
- The shared critique panel file contains checklist resolution logic (inlined)
- No orphaned inline critique panel instructions remain in either SKILL.md
- No two-hop references (shared file does not reference another shared file)
- `agents/project-scanner.md` has frontmatter with `model: opus`

### Manual Smoke Tests

1. `/aligned:brainstorming` against this repo with a small topic:
   - Verify project scan dispatches via agent file (not inline template)
   - Verify critique panel reads shared file and follows division-of-labor mode
   - Verify Architect auto-consult still fires (untouched section)
   - Verify visualization still dispatches session-document-generator (untouched section)

2. `/aligned:business-brainstorming` against this repo with a small topic:
   - Verify project scan dispatches (new capability)
   - Verify critique panel reads shared file with all-critics mode
   - Verify critics write reports to files (new behavior)
   - Verify aggregation sub-agent reads those files and returns summary
   - Verify 4-phase process is unchanged

### Structural Validation

After implementation, run these verification checks:
- Grep both SKILL.md files for `_shared/critique-panel-orchestration.md` — both must reference it
- Grep both SKILL.md files for `agents/project-scanner.md` — both must reference it
- Grep business-brainstorming SKILL.md for `session-document-generator` — must be present (new visualization)
- Verify the shared critique panel file does NOT reference any other `_shared/` file (one-hop rule)
- Verify both SKILL.md configuration blocks contain all required parameters (fact-check-mode, fact-check-tools, aggregation, criteria-assignment, skill-name, checklist-filename)
- Verify no orphaned inline critique panel instructions remain in either SKILL.md

### Regression Checks

- brainstorming: next-step prompt still offers both options (hands-on + autopilot)
- business-brainstorming: next-step prompt still points to `/aligned:business-write-plan`
- Both: design critique standalone mode still works with correct checklist

### Shared File Regression Rule

**Changes to `skills/_shared/critique-panel-orchestration.md` MUST be smoke-tested against both brainstorming and business-brainstorming skills.** The shared file has only 2 consumers, so testing both is feasible and required. A regression in the orchestration file breaks two skills silently.

## Future Work

- **Expand to other pairs** — Apply same pattern to writing-plans/business-write-plan, executing-plans/business-executing, systematic-debugging/business-diagnosis.
- **Business aggregation upgrade for write-plan** — `business-write-plan` also aggregates inline; could adopt sub-agent aggregation once proven in business-brainstorming.
