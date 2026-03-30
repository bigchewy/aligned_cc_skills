# Skill Modularity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Extract shared orchestration patterns from the brainstorming/business-brainstorming skill pair into reusable shared files and agents, and upgrade business-brainstorming with project scanning, visualization, and sub-agent aggregation.

**Source Design Doc:** `docs/plans/2026-03-30-skill-modularity-design.md`

**Mockups:** `docs/mockups/skill-modularity.html`

**Architecture:** The refactoring extracts two new shared resources: `agents/project-scanner.md` (self-contained sub-agent for project scanning) and `skills/_shared/critique-panel-orchestration.md` (parameterized orchestration protocol consumed by both brainstorming skills). Each SKILL.md sets configuration parameters before reading the shared file. Domain-specific content stays in each skill's own SKILL.md.

**Tech Stack:** Claude Code skills (Markdown instruction files), Claude Code agents (Markdown with YAML frontmatter), Task tool sub-agent dispatch pattern.

**Task ordering dependencies:**
- Tasks 1-2 (new files) must complete before Tasks 3-8 (SKILL.md modifications)
- Tasks 3→4 must be sequential (both modify `skills/brainstorming/SKILL.md`)
- Tasks 5→6→7→8 must be sequential (all modify `skills/business-brainstorming/SKILL.md`)
- Task 9 (verification) must run after all prior tasks
- Task 10 (version bump) can run after Task 9

---

### ✅ Task 1: Create the project-scanner agent

**Files:**
- Create: `agents/project-scanner.md`

**Step 1: Write the agent file**

Create `agents/project-scanner.md` with the following content:

```markdown
---
model: opus
---

# Project Scanner

## Overview

Self-contained sub-agent that surveys a project to build context for a brainstorming session. Investigates both code artifacts (package.json, go.mod, src/) AND domain materials (docs/plans/, meeting notes, deliverables, existing analyses). Adapts investigation based on what it finds — if the project is primarily documents/plans rather than code, it emphasizes domain materials rather than trying to find a tech stack.

## Inputs

The dispatch prompt must provide:
- `{project-root}` — path to the project root
- `{topic}` — short kebab-case slug for the brainstorm topic

## Investigation Checklist

Use Bash only for system commands (e.g., git). Use the Grep tool for searching file contents. Never use Bash for content search.

1. **Project structure** — key directories, entry points, config files (use Glob)
2. **Recent git activity** — last 10-15 commits (run `git -C {project-root} log --oneline -15` via Bash)
3. **Existing docs** — README, CLAUDE.md, any docs/ directory (use Glob, Read)
4. **Architecture docs** — `docs/architecture.md` if it exists — read in full; note data flows, module dependencies, system diagrams, and anything that looks stale (use Read)
5. **Existing plans and designs** — `docs/plans/` — scan for prior design docs and active plans (use Glob, Read)
6. **Domain materials** — meeting notes, strategy docs, analyses, deliverables — any non-code context relevant to the brainstorm (use Glob, Read)
7. **Architecture patterns** — module organization, key abstractions, data flow conventions — if applicable (use Grep, Read)
8. **Tech stack and dependencies** — package.json, go.mod, requirements.txt, etc. — if applicable (use Read)

## Output

1. Write full detailed findings to `/tmp/brainstorm-context-{topic}/project-scan.md` using the Write tool. Include file paths, code patterns, and specific details you discovered.
2. Return ONLY a concise summary (under 300 words) covering: what this project is, tech stack (if applicable), key architectural patterns (if applicable), domain context, and anything notable about recent activity. Do not return the full scan — just the summary.
```

**Step 2: Verify the file was created correctly**

Run: `ls -la agents/project-scanner.md` via Bash
Expected: File exists

Read `agents/project-scanner.md` and verify:
- Frontmatter has `model: opus`
- Investigation checklist has 8 items
- Output contract specifies `/tmp/brainstorm-context-{topic}/project-scan.md`
- Summary constraint is under 300 words

**Step 3: Commit**

```bash
git add agents/project-scanner.md
git commit -m "feat: add project-scanner agent for brainstorming context gathering"
```

---

### Task 2: Create the shared critique-panel-orchestration file

**Files:**
- Create: `skills/_shared/critique-panel-orchestration.md`

**Step 1: Write the shared orchestration file**

Create `skills/_shared/critique-panel-orchestration.md` with the following content:

```markdown
# Critique Panel Orchestration

Shared orchestration protocol for brainstorming critique panels. Read this file after setting configuration parameters in your SKILL.md.

## Configuration Validation

Before proceeding, verify all required parameters are present in the SKILL.md context above:

- `skill-name` must be set (e.g., "brainstorming", "business-brainstorming")
- `checklist-filename` must be set (e.g., "design-critique-checklist.md")
- `fact-check-mode` must be either "division-of-labor" or "all-critics"
- `fact-check-tools` must be a non-empty tool list
- `aggregation` must be either "sub-agent" or "inline"
- `criteria-assignment` must be "yes" (with mapping table provided) or "no"
- `visual-artifacts` must be a path or "none"
- `critique-temp-directory` must be set
- At least one critic prompt template must be provided

If any required parameter is missing, STOP and tell the user which parameter is missing from their SKILL.md configuration block.

## Mandatory Sub-Agent Rule

You MUST use the Task tool to launch fresh sub-agents for every critique round. NEVER run the critique in the main context window. The sub-agents provide independent evaluation — they haven't seen the brainstorming conversation, so they won't anchor on the author's assumptions. Running critique inline defeats the purpose and is a skill violation.

## Checklist Resolution

Resolve the checklist's absolute path:
1. Find the "Base directory for this skill:" line printed when this skill loaded (near the top of the conversation). The checklist is at `{base-directory}/{checklist-filename}`.
2. **Fallback** (if the base-directory line was compressed out of context): Use Glob to search `$HOME` for `**/{skill-name}/{checklist-filename}`. Use the match that lives under a directory containing `.claude-plugin/plugin.json`.
Verify the resolved path exists with Read. **If the checklist cannot be found after both strategies, STOP and tell the user — do not proceed with the critique panel without it.** Use the verified absolute path as `{checklist-path}` in the sub-agent prompts below.

## Round 1

1. Read `advisors/registry.md`.
2. Based on the design document's content, select 1-4 critics following the registry's selection guidelines. Hard-exclude any critic whose `not_for` matches the design's primary domain. Prefer diversity of lens — avoid selecting critics with overlapping domains. State which critics you selected and why (one sentence each).
3. Read each selected critic's full prompt file (the path listed in the registry entry).

**If `fact-check-mode` is "division-of-labor":**

4. **Assign roles before launching agents:**

   **Fact-checker designation:** Exactly one critic owns Phase 1 (exhaustive fact-checking). Priority: The QA Engineer > The Architect > first selected critic. The fact-checker also gets domain critique work (Phase 2) — they do both jobs.

   **Criteria assignment (only if `criteria-assignment` is "yes"):** Assign each checklist criterion to the one critic whose domain best matches it, using the mapping table provided in the SKILL.md configuration. Criterion 9 (Decision quality) goes to all critics. Each other criterion goes to exactly one critic. If no selected critic's domain matches a criterion, assign it to the fact-checker as catch-all. Target 2-4 criteria per critic.

   State the full assignment table before launching agents.

5. Create temp directory: `{critique-temp-directory}/round-1/`. Launch all critics in parallel (single message, multiple Task tool calls, `subagent_type=general-purpose`, `model=opus`). Use the fact-checker prompt template for the designated fact-checker, regular critic prompt template for others. Each critic writes their report to `{critique-temp-directory}/round-1/{critic-slug}-report.md` and returns only a one-line confirmation.

**If `fact-check-mode` is "all-critics":**

4. Create temp directory: `{critique-temp-directory}/round-1/`. Launch all critics in parallel using the universal critic prompt template. Each critic writes their report to `{critique-temp-directory}/round-1/{critic-slug}-report.md` and returns only a one-line confirmation.

**Aggregation:**

**If `aggregation` is "sub-agent":**

After all critics finish, dispatch one aggregation agent via Task tool (`subagent_type=general-purpose`, `model=opus`):

"You are a critique aggregator. You have access to Glob and Read tools. Do not use Bash for searching. Read all report files in `{critique-temp-directory}/round-1/`. Also read the design document at `{design-file-path}` for context.

Produce a unified report:
- **Fact-checks:** The fact-check report (from the designated fact-checker if division-of-labor, or merged from all critics if all-critics) is the authoritative source. Summarize: total claims checked, accuracy percentage, list every INCORRECT claim with the correction. If another critic flagged a factual issue incidentally, include it.
- **Critique findings:** Merge all critic findings, preserving persona tags. De-duplicate — when two or more critics flag the same issue, keep the highest-severity version and note all sources. Group by severity (high → medium → low).
- **Action items:** List concrete changes needed, ordered by severity. For each, note which critic(s) raised it.

Be concise — the goal is to give the design author a clear, actionable summary without needing to read the raw reports. Keep the unified report under 1500 words."

Present the aggregation agent's unified report to the user.

**If `aggregation` is "inline":**

Merge all critic reports in the main thread. De-duplicate, preserve persona tags, group by severity (high → medium → low). Present the unified report to the user.

## Apply Fixes

Apply corrections for any INCORRECT fact-check claims. Apply fixes for medium/high critique issues the user approves. If you need to review a specific critic's raw findings in detail, read the report file directly — do not ask the user to summarize it.

## Round 2 (conditional)

Only run if Round 1 found medium or high severity issues AND fixes were applied (at least one correction applied to the design document). Use the same critics and role assignments from Round 1 with fresh sub-agents (do NOT resume Round 1 agents). Write to `{critique-temp-directory}/round-2/`.

Prepare a brief summary of what changed since Round 1 and pass it to each agent. Scope to changes only:
- If division-of-labor: the fact-checker re-verifies only changed claims. Other critics re-evaluate only changed sections against their assigned criteria.
- If all-critics: all critics re-evaluate only changed sections.

Aggregate Round 2 the same way as Round 1 (sub-agent or inline, per configuration).

## Escalation

If Round 1 revealed concerns in a domain not covered by the selected critics, add one specialist critic for Round 2. State the escalation reason. Maximum one additional critic per round.

Apply any remaining fixes. Present final results to the user.
```

**Step 2: Verify the file**

Read `skills/_shared/critique-panel-orchestration.md` and verify:
- Configuration validation section lists all 9 required parameters
- Both `fact-check-mode` branches are present (division-of-labor and all-critics)
- Both `aggregation` branches are present (sub-agent and inline)
- Checklist resolution logic is inlined (no reference to another `_shared/` file)
- Round 2 is conditional on medium/high severity issues AND fixes were applied
- Escalation section is present

**Step 3: Commit**

```bash
git add skills/_shared/critique-panel-orchestration.md
git commit -m "feat: add shared critique-panel-orchestration for brainstorming skills"
```

---

### Task 3: Refactor brainstorming/SKILL.md — replace project scan dispatch

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (the inline project scan template starting at `First, dispatch a project scan sub-agent`)

**Step 1: Read the current file**

Read `skills/brainstorming/SKILL.md` from `**Understanding the idea:**` through `**Sequencing rule:**` to confirm the exact text of the inline dispatch template.

**Step 2: Replace the inline dispatch with agent reference**

Replace the inline dispatch template (starting at `First, dispatch a project scan sub-agent via Task tool...` through `Do not return the full scan — just the summary."`) with:

```markdown
First, dispatch a project scan agent via Task tool (subagent_type=general-purpose):

"Read `agents/project-scanner.md` for your full workflow.
Scan the project at `{project-root}` for brainstorm topic `{topic}`."
```

Keep the existing paragraph at line 34 (`Wait for the scan to complete...`) and line 36 (`**Sequencing rule:**...`) unchanged.

**Step 3: Verify the edit**

Read `skills/brainstorming/SKILL.md` lines 16-40. Verify:
- The dispatch now references `agents/project-scanner.md`
- The "Wait for the scan to complete" paragraph is preserved
- The "Sequencing rule" paragraph is preserved
- No leftover inline scan template text remains

**Step 4: Commit**

```bash
git add skills/brainstorming/SKILL.md
git commit -m "refactor: brainstorming uses project-scanner agent instead of inline template"
```

---

### Task 4: Refactor brainstorming/SKILL.md — replace critique panel with shared orchestration

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (the critique panel section starting at the `**Fact-Check + Critique Panel**` heading)

**Step 1: Read the current critique panel section**

Read `skills/brainstorming/SKILL.md` from the `**Fact-Check + Critique Panel**` heading through `Apply any remaining fixes. Present final results to the user.` (the line just before `**Visualization refresh**`). This is the ~80-line section to replace.

**Step 2: Replace with configuration block + prompt templates + shared file reference**

Replace the entire critique panel section (from `**Fact-Check + Critique Panel (mandatory, dynamic selection with division of labor):**` through `Apply any remaining fixes. Present final results to the user.`) with:

```markdown
**Fact-Check + Critique Panel (mandatory, dynamic selection with division of labor):**

**Critique panel configuration:**
- Skill name: brainstorming
- Checklist filename: design-critique-checklist.md
- Fact-check mode: division-of-labor
- Fact-check tools: Glob, Grep, Read, Write
- Aggregation: sub-agent
- Criteria assignment: yes
- Visual artifacts: docs/mockups/{session-name}.html
- Critique temp directory: /tmp/brainstorm-critique-{topic}

**Architect independence note:** If The Architect was consulted during the auto-consult phase and is also selected as a critique panel critic, add this to The Architect's critique prompt: "This design followed an earlier Architect recommendation during brainstorming. Challenge the design with fresh eyes — do not assume the earlier recommendation was correct. Look for integration risks or pattern violations that a quick options evaluation might have missed."

**Criteria mapping table:**

| Criterion | Best-fit domains |
|-----------|-----------------|
| 1. Requirements completeness | product, prioritization, scope control, user problems |
| 2. Architecture feasibility | codebase alignment, patterns, module boundaries |
| 3. YAGNI violations | simplicity, focus, first principles, scope control |
| 4. Edge cases / error handling | edge cases, failure modes, testing, reliability |
| 5. Data flow clarity | codebase alignment, patterns, integration risk |
| 6. Integration points | integration risk, security, authentication, blast radius |
| 7. Testing strategy | testing, reliability, edge cases, failure modes |
| 8. Scope creep | focus, simplicity, scope control, prioritization |

Criterion 9 (Decision quality) goes to **all** critics. Each criterion 1-8 goes to exactly one critic. If no selected critic's domain matches a criterion, assign it to the fact-checker as catch-all. Target 2-4 criteria per critic.

**Fact-checker prompt template:**

"[Full contents of the critic's prompt file]

You have access to Glob, Grep, Read, and Write tools. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `{checklist-path}` in full, then read `{design-file-path}` in full. Also review the visual artifacts at `{visual-artifacts-path}` — open the HTML file with Read and evaluate the visuals (mockups, flowcharts, architecture diagrams) alongside the written spec. Your job has two phases:
**Phase 1 (Fact-check):** You are the SOLE fact-checker — no other critic is verifying claims. Be thorough. Extract every factual claim about the codebase (file paths, function names, imports, data flows, config references). Verify each using Glob/Grep/Read. Mark claims as [CONFIRMED], [INCORRECT] with correction, or [UNVERIFIABLE]. Report accuracy percentage.
**Phase 2 (Critique):** Using the verification data you already gathered (do not re-verify), evaluate the design against criteria {criteria-list} and 9 in the checklist through your lens. Also evaluate Decision Log entries if present. Tag every finding with your name.
Write your complete report to `{report-path}` using the Write tool — fact-check summary at the top, then critique in the checklist output format. Return only a one-line confirmation: 'Report written to {report-path}'."

**Regular critic prompt template:**

"[Full contents of the critic's prompt file]

You have access to Glob, Grep, Read, and Write tools. Do not use Bash for searching — use the Grep tool instead. Bash grep triggers security prompts that halt execution. Read `{checklist-path}` in full, then read `{design-file-path}` in full. Also review the visual artifacts at `{visual-artifacts-path}` — open the HTML file with Read and evaluate the visuals (mockups, flowcharts, architecture diagrams) alongside the written spec.
**IMPORTANT: You do NOT fact-check.** Another critic handles exhaustive verification of file paths, line numbers, and code claims in parallel. Do not extract and verify every claim — that work is covered.
Read key codebase files relevant to your domain expertise (enough to understand existing patterns and context), then evaluate the design against criteria {criteria-list} and 9 in the checklist through your lens. Also evaluate Decision Log entries if present. Tag every finding with your name.
Write your complete report to `{report-path}` using the Write tool — use the checklist output format. No fact-check summary section needed. Return only a one-line confirmation: 'Report written to {report-path}'."

**Shared orchestration file resolution:**
1. Primary: Read `{base-directory}/../_shared/critique-panel-orchestration.md` in full.
2. **Fallback** (if the base-directory line was compressed out of context): Use Glob to search `$HOME` for `**/_shared/critique-panel-orchestration.md`. Use the match that lives under a directory containing `.claude-plugin/plugin.json`.
Follow its process using the configuration and prompt templates above.
```

**Step 3: Verify the edit**

Read the modified section in `skills/brainstorming/SKILL.md`. Verify:
- Configuration block has 8 explicit parameters; both prompt templates follow separately
- Architect independence note is preserved
- Criteria mapping table is present with 8 rows
- Both prompt templates are present (fact-checker and regular)
- Final line reads the shared orchestration file
- The **Visualization refresh** section immediately follows (unchanged)
- No orphaned inline orchestration instructions remain (no "Launch all selected critics", no "Aggregate via sub-agent" outside the shared file reference)

**Step 4: Count lines**

Run: `wc -l skills/brainstorming/SKILL.md`
Expected: Approximately 250 lines (down from ~310)

**Step 5: Commit**

```bash
git add skills/brainstorming/SKILL.md
git commit -m "refactor: brainstorming critique panel uses shared orchestration"
```

---

### Task 5: Refactor business-brainstorming/SKILL.md — add project scan dispatch

**Files:**
- Modify: `skills/business-brainstorming/SKILL.md` (add project scan at start of Phase 1)

**Step 1: Read Phase 1 opening**

Read `skills/business-brainstorming/SKILL.md` lines 18-26 to confirm the exact text at the start of Phase 1.

**Step 2: Add project scan dispatch before the existing Phase 1 content**

Insert the following after `### Phase 1: Establish the Goal` (line 18) and before `**Nothing happens without a clear goal.**` (line 20), replacing the existing domain materials check at line 22 (`- Check the project directory for relevant domain materials...`):

```markdown

First, dispatch a project scan agent via Task tool (subagent_type=general-purpose):

"Read `agents/project-scanner.md` for your full workflow.
Scan the project at `{project-root}` for brainstorm topic `{topic}`."

Wait for the scan to complete, then proceed with Phase 1 goal questions using the summary as working context. If a question during the brainstorm requires deeper detail about the project, read `/tmp/brainstorm-context-{topic}/project-scan.md` for the raw findings rather than re-exploring in the main thread.

**Nothing happens without a clear goal.**
```

Remove the now-redundant line: `- Check the project directory for relevant domain materials. If relevant folders exist, read existing documents, meeting notes, and related materials. If not found, proceed with information from the user dialogue.`

The project scanner's investigation checklist already covers domain materials (meeting notes, strategy docs, analyses, deliverables), making this inline check redundant.

**Step 3: Verify the edit**

Read `skills/business-brainstorming/SKILL.md` lines 18-35. Verify:
- Project scan dispatch references `agents/project-scanner.md`
- "Wait for the scan" paragraph is present
- "Nothing happens without a clear goal" is preserved
- The old "Check the project directory" bullet is removed
- The rest of the Phase 1 questions are unchanged

**Step 4: Commit**

```bash
git add skills/business-brainstorming/SKILL.md
git commit -m "feat: business-brainstorming adds project scan via shared agent"
```

---

### Task 6: Refactor business-brainstorming/SKILL.md — add visualization dispatch

**Files:**
- Modify: `skills/business-brainstorming/SKILL.md` (add visualization after documentation, before critique panel)

**Step 1: Read the After the Design section**

Read `skills/business-brainstorming/SKILL.md` from `## After the Design` through the start of the critique panel section to confirm exact text and line numbers.

**Step 2: Add visualization dispatch and Mockups field instruction**

First, add a Mockups field instruction to the **Documentation** section (after `- Use elements-of-style:writing-clearly-and-concisely skill if available`), keeping it consistent with brainstorming/SKILL.md which places it under Documentation:

```markdown
- After visualization artifacts are generated, add a `**Mockups:**` field to the design document header listing the mockup path (e.g., `**Mockups:** docs/mockups/{session-name}.html`). This field is consumed by writing-plans and finishing-a-development-branch to locate mockups without guessing. If no visual artifacts were generated, omit the field.
```

Then insert the following visualization section after the Documentation section and before the `**Fact-Check + Critique Panel**` heading:

```markdown

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
```

**Step 3: Verify the edit**

Read the modified section. Verify:
- Mockups field instruction references `writing-plans` and `finishing-a-development-branch`
- Visualization section is conditional ("If the design document warrants")
- Dispatch template references `agents/session-document-generator.md`
- Nested sub-tabs rule is present
- The critique panel section follows immediately after

**Step 4: Commit**

```bash
git add skills/business-brainstorming/SKILL.md
git commit -m "feat: business-brainstorming adds conditional visualization dispatch"
```

---

### Task 7: Refactor business-brainstorming/SKILL.md — replace critique panel with shared orchestration

**Files:**
- Modify: `skills/business-brainstorming/SKILL.md` (the critique panel section)

**Step 1: Read the current critique panel section**

Read the critique panel section in `skills/business-brainstorming/SKILL.md` — from `**Fact-Check + Critique Panel**` through `Apply any remaining fixes. Present final results to the user.`

**Step 2: Replace with configuration block + prompt template + shared file reference**

Replace the entire critique panel section with:

```markdown
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
```

**Step 3: Verify the edit**

Read the modified section. Verify:
- Configuration block has 8 explicit parameters; both prompt templates follow separately
- `fact-check-mode` is "all-critics" (not "division-of-labor")
- `fact-check-tools` includes WebSearch and WebFetch
- `criteria-assignment` is "no"
- `aggregation` is "sub-agent" (upgraded from inline)
- Universal prompt template includes WebSearch/WebFetch
- Universal prompt template writes report to `{report-path}` and returns one-line confirmation
- Final line reads the shared orchestration file (with Glob fallback)
- No orphaned inline orchestration instructions remain — confirm these specific phrases are gone: "Aggregate the reports:", "Merge all critic reports in the main thread", "Each critic's prompt:" (this is an intentional behavioral upgrade from inline to sub-agent aggregation, design doc D5)

**Step 4: Commit**

```bash
git add skills/business-brainstorming/SKILL.md
git commit -m "refactor: business-brainstorming critique panel uses shared orchestration"
```

---

### Task 8: Add visualization refresh to business-brainstorming/SKILL.md

**Files:**
- Modify: `skills/business-brainstorming/SKILL.md` (add visualization refresh after critique panel, before post-design steps)

**Step 1: Read the area after the critique panel**

Read the section after the shared orchestration file reference through the post-design steps.

**Step 2: Add visualization refresh section**

Insert the following after the critique panel's shared orchestration read line and before `**Post-design steps:**`:

```markdown

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
```

**Step 3: Update the post-design commit step**

Modify the post-design commit step to include visual artifacts:

Replace:
```
- Commit the design document to git after critique rounds are complete
```

With:
```
- Commit the design document, visual artifacts (`docs/mockups/{session-name}.html` if generated), and `docs/architecture.md` (if updated) to git after critique rounds are complete. Stage all together in one commit.
```

**Step 4: Verify the edits**

Read the visualization refresh and post-design sections. Verify:
- Visualization refresh is conditional
- Dispatch template references `agents/session-document-generator.md`
- Post-design commit step includes visual artifacts

**Step 5: Commit**

```bash
git add skills/business-brainstorming/SKILL.md
git commit -m "feat: business-brainstorming adds visualization refresh and updated commit step"
```

---

### Task 9: Structural verification

**Files:**
- Read: `skills/brainstorming/SKILL.md`
- Read: `skills/business-brainstorming/SKILL.md`
- Read: `skills/_shared/critique-panel-orchestration.md`
- Read: `agents/project-scanner.md`

**Step 1: Verify cross-references**

Run Grep for `_shared/critique-panel-orchestration.md` in `skills/` — must match exactly 2 files (brainstorming/SKILL.md and business-brainstorming/SKILL.md).

Run Grep for `agents/project-scanner.md` in `skills/` — must match exactly 2 files.

Run Grep for `session-document-generator` in `skills/business-brainstorming/SKILL.md` — must have at least 1 match.

**Step 2: Verify one-hop rule**

Run Grep for `_shared/` in `skills/_shared/critique-panel-orchestration.md` — must have 0 matches. The shared file must not reference another shared file.

**Step 3: Verify no orphaned inline orchestration**

Run Grep for `"Launch all selected critics"` in both SKILL.md files — must have 0 matches (this phrase should only appear in the shared file now).

Run Grep for `"Aggregate via sub-agent"` in both SKILL.md files — must have 0 matches.

Run Grep for `"Aggregate the reports"` in `skills/business-brainstorming/SKILL.md` — must have 0 matches.

**Step 4: Verify configuration completeness**

Read both SKILL.md configuration blocks. Each must contain:
- skill-name (or "Skill name")
- checklist-filename (or "Checklist filename")
- fact-check-mode (or "Fact-check mode")
- fact-check-tools (or "Fact-check tools")
- aggregation (or "Aggregation")
- criteria-assignment (or "Criteria assignment")
- visual-artifacts (or "Visual artifacts")
- critique-temp-directory (or "Critique temp directory")

**Step 5: Verify agent frontmatter**

Read `agents/project-scanner.md` lines 1-3. Verify frontmatter has `model: opus`.

**Step 6: Line counts**

Run: `wc -l skills/brainstorming/SKILL.md skills/business-brainstorming/SKILL.md skills/_shared/critique-panel-orchestration.md agents/project-scanner.md`

Expected approximate counts:
- brainstorming/SKILL.md: ~250 lines (down from ~310)
- business-brainstorming/SKILL.md: ~160 lines (similar to 165, gained features but lost inline critique)
- _shared/critique-panel-orchestration.md: ~70 lines
- agents/project-scanner.md: ~40 lines

**Step 7: Regression checks**

Verify that untouched sections survived the edits:

1. Run Grep for `Option A: Hands-on` in `skills/brainstorming/SKILL.md` — must match (next-step prompt still offers both options).
2. Run Grep for `Option B: Autopilot` in `skills/brainstorming/SKILL.md` — must match.
3. Run Grep for `/aligned:business-write-plan` in `skills/business-brainstorming/SKILL.md` — must match (next-step prompt still points to business-write-plan).
4. Run Grep for `## Design Critique` in both SKILL.md files — must match in each (standalone critique mode intact).
5. Run Grep for `## Key Principles` in both SKILL.md files — must match in each.

**Step 8: Commit verification results**

No commit needed — this is a verification-only task. If any check fails, fix the issue and commit the fix before proceeding.

---

### Task 10: Bump plugin version

**Files:**
- Modify: `.claude-plugin/plugin.json` (the `version` field)

**Step 1: Bump version**

Read `.claude-plugin/plugin.json`. Change the version from `"0.11.0"` to `"0.12.0"` (minor version bump for new shared module pattern + business-brainstorming capabilities).

**Step 2: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: bump version to 0.12.0 for skill modularity refactoring"
```

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Task ordering for SKILL.md edits | New files first, then modify each SKILL.md separately | Interleave new files with modifications |
| 2 | Separate tasks for each business-brainstorming addition | One task per new capability (scan, viz, critique, refresh) | Single large task for all business-brainstorming changes |
| 3 | Preserve prompt templates in SKILL.md rather than shared file | Templates stay in each SKILL.md, only orchestration is shared | Move templates into the shared file with conditional branches |
| 4 | Version bump size | Minor (0.11.0 → 0.12.0) | Patch (0.11.1) |

### Appendix: Decision Details

#### Decision 1: Task ordering for SKILL.md edits
**Chose:** Create `agents/project-scanner.md` and `skills/_shared/critique-panel-orchestration.md` first (Tasks 1-2), then modify each SKILL.md (Tasks 3-8).
**Why:** The new files are self-contained and don't depend on SKILL.md changes. Creating them first means the SKILL.md edits can reference them immediately, and each SKILL.md edit can be verified against the actual shared file. This also means if any task fails, the new files are already committed and available.
**Alternatives rejected:**
- Interleaving (create agent, modify brainstorming, create shared, modify both): Creates unnecessary dependency complexity where a shared file might not exist when a SKILL.md tries to reference it.

#### Decision 2: Separate tasks for each business-brainstorming addition
**Chose:** Four separate tasks (5: scan, 6: viz, 7: critique, 8: refresh) for business-brainstorming changes.
**Why:** Each addition is a distinct capability with its own verification criteria. The design doc explicitly calls out these as separate behavioral changes. Separating them produces cleaner commits and makes it easier to identify which change caused a regression. The executing agent can verify each independently.
**Alternatives rejected:**
- Single task for all business-brainstorming changes: Would produce a large, hard-to-review commit and make it harder to bisect regressions.

#### Decision 3: Preserve prompt templates in SKILL.md
**Chose:** Prompt templates remain in each SKILL.md; only the orchestration protocol (critic selection, launching, aggregation, rounds) moves to the shared file.
**Why:** The design doc specifies this structure explicitly — the shared file is parameterized by configuration + templates set in the calling SKILL.md. The templates differ meaningfully between skills (technical has division-of-labor with two templates; business has all-critics with one universal template, plus WebSearch/WebFetch tools). Moving templates into the shared file would require complex conditional logic and make the shared file harder to maintain.
**Alternatives rejected:**
- Templates in shared file with conditionals: Would violate the design doc's stated structure and create a brittle shared file that's harder to reason about.

#### Decision 4: Version bump size
**Chose:** Minor version bump (0.11.0 → 0.12.0).
**Why:** This change introduces new capabilities (project scan and visualization for business-brainstorming) and a new shared module pattern (`_shared/critique-panel-orchestration.md`). It's not a patch (bug fix) — it's a feature addition with structural changes.
**Alternatives rejected:**
- Patch (0.11.1): Undersells the scope. This introduces a new architectural pattern (parameterized shared orchestration files) and new capabilities for business-brainstorming.
