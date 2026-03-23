---
name: brainstorming
description: "You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation."
---

# Brainstorming Ideas Into Designs

## Overview

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design in small sections (200-300 words), checking after each section whether it looks right so far.

## The Process

**Understanding the idea:**

First, dispatch a project scan sub-agent via Task tool (`subagent_type=general-purpose`, `model=opus`) to survey the project and build context. Use this dispatch template — replace `{topic}` with a short slug for the brainstorm topic and `{project-root}` with the project root:

   "Survey the project at `{project-root}` to build context for a brainstorming session. You have access to Bash, Glob, Grep, Read, and Write tools. Use Bash only for system commands (e.g., npm, git) — never for content search. Use the Grep tool for searching file contents.

   Investigate:
   - Project structure (key directories, entry points, config files)
   - Recent git activity (last 10-15 commits — run `git log --oneline -15` via Bash)
   - Existing docs (README, CLAUDE.md, any docs/ directory)
   - Architecture docs (`docs/architecture.md` if it exists — read in full; note data flows, module dependencies, system diagrams, and anything that looks stale)
   - Architecture patterns (how modules are organized, key abstractions, data flow conventions)
   - Tech stack and dependencies (package.json, requirements.txt, go.mod, etc.)

   Write your full detailed findings to `/tmp/brainstorm-context-{topic}/project-scan.md` using the Write tool. Include file paths, code patterns, and specific details you discovered.

   Then return ONLY a concise summary (under 300 words) covering: what this project is, tech stack, key architectural patterns, and anything notable about recent activity. Do not return the full scan — just the summary."

Wait for the scan to complete, then proceed with the Q&A using the summary as your working context. If a question during the brainstorm requires deeper detail about the project (e.g., how a specific module works, what pattern an existing feature follows), read `/tmp/brainstorm-context-{topic}/project-scan.md` for the raw findings rather than re-exploring the codebase in the main thread.

**Sequencing rule:** Do not dispatch an Architect auto-consult (see below) until the project scan has completed and you've reviewed the summary. For early technical questions, check whether the scan findings already answer the question before dispatching a separate sub-agent.

Then ask questions one at a time to refine the idea. Before asking each question, classify it:

- **Business questions** (ask the user): See "What stays user-facing" under Architect auto-consult below.
- **Technical questions** (auto-resolve via Architect): See "What counts as technical" under Architect auto-consult below.

**For business questions:** Ask the user directly. Prefer multiple choice when possible. One question per message.

**For technical questions:** Do NOT ask the user. Instead, dispatch The Architect as the user's proxy to answer the question (see "Architect as proxy" under Architect auto-consult below). Each technical question gets its own fresh sub-agent dispatch — the answer comes back to the main thread, you incorporate it, and it shapes what questions come next (which may be business or technical). Briefly note each decision to the user: what was decided and why (one sentence), plus any constraints flagged — so they have visibility without needing to weigh in.

**Gray area:** If a question has both business and technical dimensions (e.g., "should we support offline mode?" is business scope + technical feasibility), ask the user the business dimension **first** ("Is offline support important for your users?"). Only after the user answers, and only if their answer warrants it, dispatch The Architect as proxy for the technical dimension (e.g., if the user says offline matters, send The Architect the question "what's the best offline architecture approach given the current codebase?").

**Exploring approaches:**
- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why

**When options involve UI or layout:** Never use ASCII art in AskUserQuestion markdown previews for UI comparisons — they are too low-fidelity for the user to evaluate. Instead:

1. Draft the approach options as normal.
2. Classify the options and consult the right advisor:
   - **Technical UI decisions** (component patterns, state management, module boundaries, where logic lives) → run the Architect auto-consult (below).
   - **UX/usability decisions** (layout clarity, navigation, scanning, labeling, user flow, conventions) → consult Steve Krug (`advisors/prompts/steve-krug.md`) using the same auto-consult dispatch pattern, substituting Krug's prompt for The Architect's.
   - **Both apply?** Consult both in parallel.
3. Dispatch the mockup-generator agent with the advisor-refined options to create a comparison mockup with all options as switchable tabs. Use this dispatch template — replace placeholders with actual values. Uses `subagent_type=general-purpose`.

   "Read `agents/mockup-generator.md` for your full workflow. Generate a comparison mockup showing {number} approach options for: {brief description of what's being compared}. Project root: `{project-root}`. Brainstorming session topic: `{topic}`. Create a single HTML file at `docs/mockups/{session-name}/approach-comparison.html` with tabbed navigation to switch between options. Each tab should be labeled with the approach name and include a short description of the trade-offs. Open the file in the browser after generating."

4. After the user has reviewed the HTML mockup in the browser, proceed with the approach selection question.

**Architect auto-consult:**

Before presenting technical content to the user — whether it's a question with options or a design section — consult The Architect first. This applies in every phase: understanding, exploring approaches, and presenting the design.

**Trigger:** Any of these situations:
- **Q&A phase (proxy mode):** You need to answer a technical question to continue the brainstorm (routed here instead of asking the user — see question classification above). Use the "Architect as proxy" dispatch below.
- **Presenting options (review mode):** You are about to show the user options that contain technical alternatives. Use the standard review dispatch below.
- **Presenting design sections (review mode):** You are about to present a design section that embeds technical choices as assertions (e.g., "here's the state machine with states X, Y, Z"). This case is easy to miss — presenting a design section *is* presenting a technical decision, even though it looks like a statement rather than a question. Use the standard review dispatch below.

**Mode difference:** In proxy mode, The Architect makes decisions (its "do not propose alternatives" constraint is lifted). In review mode, The Architect critiques only — it recommends which option fits best but does not override the user's choice. These are different behavioral contracts for the same persona.

**What counts as technical:** Data model choices, type structures, where to put state, which layer handles something, API shape, streaming behavior, tool design, module boundaries, persistence strategies, integration approach, state machines, lifecycle flows, component patterns — anything where the answer depends on the existing codebase rather than user preference.

**What stays user-facing without consult:** Product direction, feature scope, success criteria, priorities, UX preferences, target audience, naming/branding, "do you want X or Y feature", what problem to solve, what outcome matters, deadlines, trade-off preferences between scope/quality/speed, interaction style choices.

**Architect as proxy** (Q&A-phase technical questions):

The user has delegated technical decision authority to The Architect. The brainstorm's iterative back-and-forth rhythm stays the same — but technical turns go to The Architect (via fresh sub-agent each time) instead of to the user. Each Architect answer feeds back into the main thread and shapes what comes next, just like a human technical advisor sitting in the session.

1. Dispatch a sub-agent via Task tool (`subagent_type=general-purpose`, `model=opus`) with this template:

   "[Full contents of `advisors/prompts/the-architect.md`]

   **Role override for this dispatch:** You are acting as the user's proxy for technical decisions during a brainstorming session. Your normal constraint of 'do not propose alternatives' is suspended — the user has explicitly delegated technical decision-making to you. Investigate the codebase and make a recommendation.

   You have access to Glob, Grep, and Read tools. Do not use Bash for searching — use the Grep tool instead. For project context, first read `/tmp/brainstorm-context-{topic}/project-scan.md` — it contains a prior scan of the project structure, patterns, and conventions. Use this as a starting point rather than re-exploring from scratch.

   Technical question to resolve for the project at `{project-root}`:

   Context: {1-2 sentences on what the user is building and key constraints/decisions established so far}
   Question: {the technical question that needs answering}

   Investigate the existing codebase. Make a decision grounded in existing patterns, conventions, and architecture. If you identify multiple viable approaches, pick the one that best fits the codebase and explain why.

   Output format:
   - **Decision:** What to do (one clear answer)
   - **Reasoning:** Why this fits the existing codebase, citing specific files, patterns, or conventions
   - **Constraints:** Any preconditions, caveats, or risks that affect the design (e.g., 'requires migrating X first', 'incompatible with planned move to Y')"

2. Incorporate the decision into the brainstorm's working context. The Architect's answer will often shape what the next question is — that's the point. Continue the Q&A flow: if the next question is business, ask the user; if technical, dispatch a fresh Architect agent. Each new dispatch includes accumulated context from prior decisions (e.g., "Prior decisions: {list}. New question: {question}").
3. Briefly note each Architect decision to the user: what was decided and why (one sentence), plus any constraints flagged — do not drop caveats that affect the design.

**Standard review workflow** (presenting options or design sections):

1. Draft the content you're about to present (options, design section, or both)
2. Before presenting to the user, dispatch a sub-agent via Task tool (`subagent_type=general-purpose`, `model=opus`) with The Architect's persona to review it against the codebase. Use this dispatch template — replace placeholders with actual values:

   "[Full contents of `advisors/prompts/the-architect.md`]

   You have access to Glob, Grep, and Read tools. Do not use Bash for searching — use the Grep tool instead. For project context, first read `/tmp/brainstorm-context-{topic}/project-scan.md` — it contains a prior scan of the project structure, patterns, and conventions. Use this as a starting point rather than re-exploring from scratch.

   Review this technical content before it is presented to the user for the project at `{project-root}`:

   Context: {1-2 sentences on what the user is building and key constraints/decisions established so far}
   Content to review:
   {the draft question with options OR design section text}

   Investigate the existing codebase. If the content presents options, recommend which best fits current patterns. If the content presents a design, validate it — check for missing states, broken flows, wrong assumptions, integration risks. In either case, ground your analysis in specific codebase evidence.

   Output format:
   - **Verdict:** APPROVE or REVISE
   - **Recommendation:** What to change and why, citing specific files, patterns, or conventions
   - **Key findings:** Codebase evidence that informed the review"

3. Incorporate The Architect's findings:
   - If REVISE: fix the issues before presenting. Note the input briefly (e.g., "The Architect caught a missing 'deploying' state — added.")
   - If presenting options: lead with the architect-recommended option and include their codebase-grounded reasoning. Still present all options — The Architect advises, the user decides.

**Presenting the design:**
- Once you believe you understand what you're building, present the design
- Break it into sections of 200-300 words
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify if something doesn't make sense

## After the Design

**Documentation:**
- Write the validated design to `docs/plans/YYYY-MM-DD-<topic>-design.md`
- After visualization artifacts are generated, add a `**Mockups:**` field to the design document header listing the mockup directory path (e.g., `**Mockups:** docs/mockups/{session-name}.html`). This field is consumed by writing-plans and finishing-a-development-branch to locate mockups without guessing. If no visual artifacts were generated, omit the field.

**Visualization (mandatory):**

Every brainstorm produces at least one visual artifact. After writing the design document and BEFORE the critique round, dispatch the session-document-generator to produce a consolidated visualization document.

**Dispatch template** — replace placeholders with actual values. Uses `subagent_type=general-purpose`:

"Read `agents/session-document-generator.md` for your full workflow.
Generate a consolidated visualization document for the design at `{design-file-path}`.
Session name: `{session-name}`. Project root: `{project-root}`.
Output to `docs/mockups/{session-name}.html`.
Verify all Mermaid diagrams render without errors before opening.
Open the file in the browser after verification passes."

Do not pause for user review — the critique panel will evaluate the visuals alongside the design.

**Nested sub-tabs rule (applies to session-document-generator AND mockup-generator dispatches):**

When a tabbed HTML document is generated, use nested sub-tabs (progressive disclosure) whenever a single tab contains more detail than can be scanned in one view. Do not flatten into many top-level tabs or cram everything into one scrollable panel. The pattern is:
- **Top-level tabs** for major conceptual sections
- **Sub-tabs within each** for natural subdivisions (phases, layers, concerns)
- Each sub-tab holds **one focused diagram or content block**

The check: if a tab contains multiple diagrams, subgraphs, or sections that each deserve their own view, break them into nested sub-tabs rather than stacking vertically.

**Fact-Check + Critique Panel (mandatory, dynamic selection with division of labor):**

**MANDATORY: You MUST use the Task tool to launch fresh sub-agents** for every critique round. NEVER run the critique in the main context window. The sub-agents provide independent evaluation — they haven't seen the brainstorming conversation, so they won't anchor on the author's assumptions. Running critique inline defeats the purpose and is a skill violation.

**Division of labor:** One critic owns exhaustive fact-checking. The others do NOT duplicate this work — they read key files to understand context, then focus purely on their domain-specific checklist criteria. This prevents the ~50% token waste that occurs when every critic independently fact-checks the same claims and evaluates the same criteria.

**Architect independence note:** If The Architect was consulted during the auto-consult phase and is also selected as a critique panel critic, add this to The Architect's critique prompt: "This design followed an earlier Architect recommendation during brainstorming. Challenge the design with fresh eyes — do not assume the earlier recommendation was correct. Look for integration risks or pattern violations that a quick options evaluation might have missed."

**Round 1:**
1. Read `advisors/registry.md`.
2. Based on the design document's content, select 1-4 critics following the registry's selection guidelines. Hard-exclude any critic whose `not_for` matches the design's primary domain. Prefer diversity of lens — avoid selecting critics with overlapping domains. State which critics you selected and why (one sentence each).
3. **Assign roles before launching agents:**

   **Fact-checker designation:** Exactly one critic owns Phase 1 (exhaustive fact-checking). Priority: The QA Engineer > The Architect > first selected critic. The fact-checker also gets domain critique work (Phase 2) — they do both jobs.

   **Criteria assignment:** Assign each checklist criterion (1-8) to the one critic whose domain best matches it. Use this mapping:

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

   Criterion 9 (Decision quality) goes to **all** critics — it's lightweight and each lens adds value. Each criterion 1-8 goes to exactly one critic. If no selected critic's domain matches a criterion, assign it to the fact-checker as catch-all. Target 2-4 criteria per critic.

   State the full assignment table before launching agents (e.g., "Steve Jobs: criteria 1, 3, 8. The QA Engineer [fact-checker]: criteria 4, 5, 7 + fact-checking.").

4. Read each selected critic's full prompt file (the path listed in the registry entry).
5. **Resolve the checklist (MANDATORY):** The checklist is a sibling file in this skill's directory. Resolve its absolute path:
   - Find the "Base directory for this skill:" line printed when this skill loaded (near the top of the conversation). The checklist is at `{base-directory}/design-critique-checklist.md`.
   - **Fallback** (if the base-directory line was compressed out of context): Use Glob to search `$HOME` for `**/brainstorming/design-critique-checklist.md`. Use the match that lives under a directory containing `.claude-plugin/plugin.json`.
   Verify the resolved path exists with Read. **If the checklist cannot be found after both strategies, STOP and tell the user — do not proceed with the critique panel without it.** Use the verified absolute path as `{checklist-path}` in the sub-agent prompts below.
6. Create a temporary directory for this critique round: `/tmp/brainstorm-critique-{topic}/round-1/`. Launch all selected critics **in parallel** (single message, multiple Task tool calls). Each uses `subagent_type=general-purpose`, `model=opus`. Replace `{design-file-path}` with the absolute path of the design document, `{criteria-list}` with the assigned criteria numbers, and `{report-path}` with `/tmp/brainstorm-critique-{topic}/round-1/{critic-slug}-report.md`.

   **For the designated fact-checker, use this prompt:**

   "[Full contents of the critic's prompt file]

   You have access to Glob, Grep, Read, and Write tools. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `{checklist-path}` in full, then read `{design-file-path}` in full. Also review the visual artifacts at `docs/mockups/{session-name}.html` — open the HTML file with Read and evaluate the visuals (mockups, flowcharts, architecture diagrams) alongside the written spec. Your job has two phases:
   **Phase 1 (Fact-check):** You are the SOLE fact-checker — no other critic is verifying claims. Be thorough. Extract every factual claim about the codebase (file paths, function names, imports, data flows, config references). Verify each using Glob/Grep/Read. Mark claims as [CONFIRMED], [INCORRECT] with correction, or [UNVERIFIABLE]. Report accuracy percentage.
   **Phase 2 (Critique):** Using the verification data you already gathered (do not re-verify), evaluate the design against criteria {criteria-list} and 9 in the checklist through your lens. Also evaluate Decision Log entries if present. Tag every finding with your name.
   Write your complete report to `{report-path}` using the Write tool — fact-check summary at the top, then critique in the checklist output format. Return only a one-line confirmation: 'Report written to {report-path}'."

   **For all other critics, use this prompt:**

   "[Full contents of the critic's prompt file]

   You have access to Glob, Grep, Read, and Write tools. Do not use Bash for searching — use the Grep tool instead. Bash grep triggers security prompts that halt execution. Read `{checklist-path}` in full, then read `{design-file-path}` in full. Also review the visual artifacts at `docs/mockups/{session-name}.html` — open the HTML file with Read and evaluate the visuals (mockups, flowcharts, architecture diagrams) alongside the written spec.
   **IMPORTANT: You do NOT fact-check.** Another critic handles exhaustive verification of file paths, line numbers, and code claims in parallel. Do not extract and verify every claim — that work is covered.
   Read key codebase files relevant to your domain expertise (enough to understand existing patterns and context), then evaluate the design against criteria {criteria-list} and 9 in the checklist through your lens. Also evaluate Decision Log entries if present. Tag every finding with your name.
   Write your complete report to `{report-path}` using the Write tool — use the checklist output format. No fact-check summary section needed. Return only a one-line confirmation: 'Report written to {report-path}'."

7. **Aggregate via sub-agent (do NOT aggregate in the main thread):**

   After all critics finish, dispatch one aggregation agent via Task tool (`subagent_type=general-purpose`, `model=opus`):

   "You are a critique aggregator. You have access to Glob and Read tools. Do not use Bash for searching. Read all report files in `/tmp/brainstorm-critique-{topic}/round-1/`. Also read the design document at `{design-file-path}` for context.

   Produce a unified report:
   - **Fact-checks:** The report from {fact-checker-slug} is the authoritative fact-check source. Summarize: total claims checked, accuracy percentage, list every INCORRECT claim with the correction. If another critic flagged a factual issue incidentally, include it.
   - **Critique findings:** Merge all critic findings, preserving persona tags. De-duplicate — when two or more critics flag the same issue, keep the highest-severity version and note all sources. Group by severity (high → medium → low).
   - **Action items:** List concrete changes needed, ordered by severity. For each, note which critic(s) raised it.

   Be concise — the goal is to give the design author a clear, actionable summary without needing to read the raw reports. Keep the unified report under 1500 words."

   Present the aggregation agent's unified report to the user.

8. Apply corrections for any INCORRECT fact-check claims. Apply fixes for medium/high critique issues the user approves. If you need to review a specific critic's raw findings in detail, read the report file directly — do not ask the user to summarize it.

**Round 2 (conditional):**
Only run if Round 1 found medium or high severity issues. Use the same critics and role assignments from Round 1 with fresh sub-agents (do NOT resume Round 1 agents). Write to `/tmp/brainstorm-critique-{topic}/round-2/`. Scope Round 2 to changes only — prepare a brief summary of what changed since Round 1 and pass it to each agent. The fact-checker re-verifies only changed claims. Other critics re-evaluate only changed sections against their assigned criteria. Aggregate Round 2 the same way — dispatch an aggregation agent, do not aggregate inline.

**Escalation:** If Round 1 revealed concerns in a domain not covered by the selected critics, add one specialist critic for Round 2. For example, if The Architect flagged a security concern but The Security Reviewer was not in Round 1, add them for Round 2. State the escalation reason. Maximum one additional critic per round.

Apply any remaining fixes. Present final results to the user.

**Visualization refresh (conditional):**

If the design document was modified after the initial visualization was generated — whether by fact-check corrections, user-approved critique fixes of any severity, or structural revisions — re-dispatch the session-document-generator to regenerate the visualization from the final design. This ensures the committed HTML matches the post-critique design exactly.

Only skip this step if the design document is unchanged from when the initial visualization was generated (i.e., all critique verdicts were APPROVE with no corrections applied).

Dispatch via Task tool (`subagent_type=general-purpose`). The output path is the same as the initial visualization — the Mockups header field in the design document remains valid without modification.

"Read `agents/session-document-generator.md` for your full workflow.
Regenerate the consolidated visualization document to reflect post-critique design changes at `{design-file-path}`.
Session name: `{session-name}`. Project root: `{project-root}`.
Output to `docs/mockups/{session-name}.html` (overwrite the pre-critique version).
Verify all Mermaid diagrams render without errors before opening.
Open the file in the browser after verification passes."

Do not pause for user review — the critique has already validated the design content. The refresh ensures visual fidelity only.

- Commit the design document, visual artifacts (`docs/mockups/{session-name}.html`), and `docs/architecture.md` (if updated) to git after critique rounds are complete. Stage all together in one commit.

**Next step prompt (mandatory):**

After committing the design document, present two options. **Resolve the plugin root path first:** the plugin root is two levels up from the base directory for this skill (`{base-directory}/../..`). If the base-directory line was compressed out of context, use Glob to search `$HOME` for `**/docs/ralph_loops/autopilot.sh` and use the match whose parent directory contains `.claude-plugin/plugin.json`. Store as `{plugin-root}`.

````
## Next Steps

### Option A: Hands-on (write plan interactively, then choose execution method)
I'll create a worktree and write the implementation plan now. You'll review the plan and choose how to execute it.

> Ready to proceed? I'll invoke `/aligned:using-git-worktrees` to create the worktree, then `/aligned:writing-plans` to write the plan.

### Option B: Autopilot (fully unattended — plan through verification)
Run from any terminal. Writes the plan, creates a worktree, executes all tasks via Ralph loop, checks mockup fidelity, and verifies the branch — but does NOT merge:
```bash
bash {plugin-root}/docs/ralph_loops/autopilot.sh "{project-root}" "{design-doc-path}"
```
Review the work when it finishes, then merge manually or run `/aligned:finishing-a-development-branch`.
````

If the user chooses Option A, invoke `/aligned:using-git-worktrees` to create the worktree, then output:

> `cd [worktree-path]` then use `/aligned:writing-plans` to write an implementation plan based on the design document at `docs/plans/YYYY-MM-DD-<topic>-design.md`.

If the user chooses Option B, no further action is needed — the terminal command handles everything.

## Design Critique

When critiquing an existing design (instead of writing one), resolve the checklist path using the same MANDATORY resolution steps described above (base directory → Glob fallback → STOP if not found). Use the checklist at `{base-directory}/design-critique-checklist.md`. Launch fresh sub-agents for critique rounds to ensure independent evaluation. Verify every claim against the actual codebase — don't trust file paths, architecture claims, or integration assumptions without checking.

## Key Principles

- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice preferred** - Easier to answer than open-ended when possible
- **YAGNI ruthlessly** - Remove unnecessary features from all designs
- **Explore alternatives** - Always propose 2-3 approaches before settling
- **Incremental validation** - Present design in sections, validate each
- **Be flexible** - Go back and clarify when something doesn't make sense
