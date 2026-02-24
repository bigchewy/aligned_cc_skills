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

   "Survey the project at `{project-root}` to build context for a brainstorming session. You have access to Bash, Glob, Grep, Read, and Write tools.

   Investigate:
   - Project structure (key directories, entry points, config files)
   - Recent git activity (last 10-15 commits — run `git log --oneline -15` via Bash)
   - Existing docs (README, CLAUDE.md, any docs/ directory)
   - Architecture patterns (how modules are organized, key abstractions, data flow conventions)
   - Tech stack and dependencies (package.json, requirements.txt, go.mod, etc.)

   Write your full detailed findings to `/tmp/brainstorm-context-{topic}/project-scan.md` using the Write tool. Include file paths, code patterns, and specific details you discovered.

   Then return ONLY a concise summary (under 300 words) covering: what this project is, tech stack, key architectural patterns, and anything notable about recent activity. Do not return the full scan — just the summary."

Wait for the scan to complete, then proceed with the Q&A using the summary as your working context. If a question during the brainstorm requires deeper detail about the project (e.g., how a specific module works, what pattern an existing feature follows), read `/tmp/brainstorm-context-{topic}/project-scan.md` for the raw findings rather than re-exploring the codebase in the main thread.

**Sequencing rule:** Do not dispatch an Architect auto-consult (see below) until the project scan has completed and you've reviewed the summary. For early technical questions, check whether the scan findings already answer the question before dispatching a separate sub-agent.

Then:
- Ask questions one at a time to refine the idea
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message - if a topic needs more exploration, break it into multiple questions
- Focus on understanding: purpose, constraints, success criteria

**Exploring approaches:**
- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why

**Architect auto-consult (technical questions only):**

When you're about to present a question with options that is technical in nature, consult The Architect before presenting it to the user. This applies during both "Understanding the idea" and "Exploring approaches" — any phase where you're about to ask the user to choose between options.

**What counts as technical:** Data model choices, type structures, where to put state, which layer handles something, API shape, streaming behavior, tool design, module boundaries, persistence strategies, integration approach — anything where the answer depends on the existing codebase rather than user preference.

**What stays user-facing without consult:** Product direction, UX preferences, feature scope, naming/branding, "do you want X or Y feature", interaction style choices.

**Workflow:**
1. Formulate the question and options as you normally would
2. Before presenting to the user, dispatch a sub-agent via Task tool (`subagent_type=general-purpose`, `model=opus`) with The Architect's persona to evaluate the options against the actual codebase. Use this dispatch template — replace placeholders with actual values:

   "[Full contents of `advisors/.claude/the-architect.md`]

   Note: Your usual role is to critique, not propose. In this context, you are evaluating pre-formulated options against the codebase — you are not proposing new architectures. Recommend the option that best fits the existing codebase.

   You have access to Glob, Grep, and Read tools. For project context, first read `/tmp/brainstorm-context-{topic}/project-scan.md` — it contains a prior scan of the project structure, patterns, and conventions. Use this as a starting point rather than re-exploring from scratch.

   Evaluate these technical options for the project at `{project-root}`:

   Context: {1-2 sentences on what the user is building and key constraints/decisions established so far}
   Question: {the question you were about to ask}
   Options:
   {numbered list of options with brief descriptions}

   Investigate the existing codebase to determine which option best aligns with current patterns, module boundaries, and architecture. Consider blast radius, integration risk, and consistency with established conventions.

   Output format:
   - **Recommended option:** Which one and why, grounded in specific codebase evidence (file paths, patterns found, existing conventions)
   - **Key findings:** Specific files, patterns, or conventions that informed the recommendation
   - **Risks of alternatives:** Brief note on why the other options are weaker fits for this codebase"

3. Incorporate The Architect's recommendation into your presentation to the user:
   - Lead with the architect-recommended option
   - Include their codebase-grounded reasoning (e.g., "The Architect recommends Option B — the codebase uses X pattern in 8 modules, and this option follows it")
   - Still present all options with trade-offs — The Architect advises, the user decides

**Presenting the design:**
- Once you believe you understand what you're building, present the design
- Break it into sections of 200-300 words
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify if something doesn't make sense

## After the Design

**Documentation:**
- Write the validated design to `docs/plans/YYYY-MM-DD-<topic>-design.md`

**Mockup generation (conditional):**

If the design involves frontend/UI changes, generate mockups AFTER writing the design document and BEFORE the critique round. Dispatch the mockup generator via the Task tool (`subagent_type=general-purpose`). Use this dispatch template — replace placeholders with actual values:

   "Read `agents/mockup-generator.md` for your full workflow. Generate mockups for the design at `{design-file-path}`. Project root: `{project-root}`. Focus on these UI elements: {list specific views, pages, or components from the design that need visualization}."

Do not pause for user review — the critique panel will evaluate the mockups alongside the design.

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
5. Create a temporary directory for this critique round: `/tmp/brainstorm-critique-{topic}/round-1/`. Launch all selected critics **in parallel** (single message, multiple Task tool calls). Each uses `subagent_type=general-purpose`, `model=opus`. Replace `{design-file-path}` with the absolute path of the design document, `{criteria-list}` with the assigned criteria numbers, and `{report-path}` with `/tmp/brainstorm-critique-{topic}/round-1/{critic-slug}-report.md`.

   **For the designated fact-checker, use this prompt:**

   "[Full contents of the critic's prompt file]

   You have access to Glob, Grep, Read, and Write tools. Read `skills/brainstorming/design-critique-checklist.md` in full, then read `{design-file-path}` in full. {If mockups were generated, add: Also review the mockups at `docs/mockups/{session-name}/` — open each HTML file with Read and evaluate the visual design alongside the written spec.} Your job has two phases:
   **Phase 1 (Fact-check):** You are the SOLE fact-checker — no other critic is verifying claims. Be thorough. Extract every factual claim about the codebase (file paths, function names, imports, data flows, config references). Verify each using Glob/Grep/Read. Mark claims as [CONFIRMED], [INCORRECT] with correction, or [UNVERIFIABLE]. Report accuracy percentage.
   **Phase 2 (Critique):** Using the verification data you already gathered (do not re-verify), evaluate the design against criteria {criteria-list} and 9 in the checklist through your lens. Also evaluate Decision Log entries if present. Tag every finding with your name.
   Write your complete report to `{report-path}` using the Write tool — fact-check summary at the top, then critique in the checklist output format. Return only a one-line confirmation: 'Report written to {report-path}'."

   **For all other critics, use this prompt:**

   "[Full contents of the critic's prompt file]

   You have access to Glob, Grep, Read, and Write tools. Read `skills/brainstorming/design-critique-checklist.md` in full, then read `{design-file-path}` in full. {If mockups were generated, add: Also review the mockups at `docs/mockups/{session-name}/` — open each HTML file with Read and evaluate the visual design alongside the written spec.}
   **IMPORTANT: You do NOT fact-check.** Another critic handles exhaustive verification of file paths, line numbers, and code claims in parallel. Do not extract and verify every claim — that work is covered.
   Read key codebase files relevant to your domain expertise (enough to understand existing patterns and context), then evaluate the design against criteria {criteria-list} and 9 in the checklist through your lens. Also evaluate Decision Log entries if present. Tag every finding with your name.
   Write your complete report to `{report-path}` using the Write tool — use the checklist output format. No fact-check summary section needed. Return only a one-line confirmation: 'Report written to {report-path}'."

6. **Aggregate via sub-agent (do NOT aggregate in the main thread):**

   After all critics finish, dispatch one aggregation agent via Task tool (`subagent_type=general-purpose`, `model=opus`):

   "You are a critique aggregator. You have access to Glob and Read tools. Read all report files in `/tmp/brainstorm-critique-{topic}/round-1/`. Also read the design document at `{design-file-path}` for context.

   Produce a unified report:
   - **Fact-checks:** The report from {fact-checker-slug} is the authoritative fact-check source. Summarize: total claims checked, accuracy percentage, list every INCORRECT claim with the correction. If another critic flagged a factual issue incidentally, include it.
   - **Critique findings:** Merge all critic findings, preserving persona tags. De-duplicate — when two or more critics flag the same issue, keep the highest-severity version and note all sources. Group by severity (high → medium → low).
   - **Action items:** List concrete changes needed, ordered by severity. For each, note which critic(s) raised it.

   Be concise — the goal is to give the design author a clear, actionable summary without needing to read the raw reports. Keep the unified report under 1500 words."

   Present the aggregation agent's unified report to the user.

7. Apply corrections for any INCORRECT fact-check claims. Apply fixes for medium/high critique issues the user approves. If you need to review a specific critic's raw findings in detail, read the report file directly — do not ask the user to summarize it.

**Round 2 (conditional):**
Only run if Round 1 found medium or high severity issues. Use the same critics and role assignments from Round 1 with fresh sub-agents (do NOT resume Round 1 agents). Write to `/tmp/brainstorm-critique-{topic}/round-2/`. Scope Round 2 to changes only — prepare a brief summary of what changed since Round 1 and pass it to each agent. The fact-checker re-verifies only changed claims. Other critics re-evaluate only changed sections against their assigned criteria. Aggregate Round 2 the same way — dispatch an aggregation agent, do not aggregate inline.

**Escalation:** If Round 1 revealed concerns in a domain not covered by the selected critics, add one specialist critic for Round 2. For example, if The Architect flagged a security concern but The Security Reviewer was not in Round 1, add them for Round 2. State the escalation reason. Maximum one additional critic per round.

Apply any remaining fixes. Present final results to the user.

- Commit the design document to git after critique rounds are complete

**Create worktree + next step prompt (mandatory):**

After committing the design document, invoke `/aligned:using-git-worktrees` to create the worktree for the upcoming implementation work. Then output a ready-to-paste prompt for the next session with the worktree path filled in:

> `cd [worktree-path]` then use `/aligned:writing-plans` to write an implementation plan based on the design document at `docs/plans/YYYY-MM-DD-<topic>-design.md`.

## Design Critique

When critiquing an existing design (instead of writing one), use the checklist in `design-critique-checklist.md`. Launch fresh sub-agents for critique rounds to ensure independent evaluation. Verify every claim against the actual codebase — don't trust file paths, architecture claims, or integration assumptions without checking.

## Key Principles

- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice preferred** - Easier to answer than open-ended when possible
- **YAGNI ruthlessly** - Remove unnecessary features from all designs
- **Explore alternatives** - Always propose 2-3 approaches before settling
- **Incremental validation** - Present design in sections, validate each
- **Be flexible** - Go back and clarify when something doesn't make sense
