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
- Check out the current project state first (files, docs, recent commits)
- Ask questions one at a time to refine the idea
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message - if a topic needs more exploration, break it into multiple questions
- Focus on understanding: purpose, constraints, success criteria

**Exploring approaches:**
- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why

**Check lessons-learned (conditional):**
If `docs/lessons-learned/` exists, read all non-completed lesson files. Check if any relate to the design area being brainstormed. If relevant lessons exist, factor their prevention guidance into the design.

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

**Fact-Check + Critique Panel (mandatory, dynamic selection):**

**MANDATORY: You MUST use the Task tool to launch fresh sub-agents** for every critique round. NEVER run the critique in the main context window. The sub-agents provide independent evaluation — they haven't seen the brainstorming conversation, so they won't anchor on the author's assumptions. Running critique inline defeats the purpose and is a skill violation.

**Round 1:**
1. Read `advisors/registry.md`.
2. Based on the design document's content, select 1-4 critics following the registry's selection guidelines. Hard-exclude any critic whose `not_for` matches the design's primary domain. Prefer diversity of lens — avoid selecting critics with overlapping domains. State which critics you selected and why (one sentence each).
3. Read each selected critic's full prompt file (the path listed in the registry entry).
4. Launch all selected critics **in parallel** (single message, multiple Task tool calls). Each uses `subagent_type=general-purpose`, `model=opus`. Replace `{design-file-path}` below with the absolute path of the design document you wrote in the previous step.

   Each critic's prompt:

   "[Full contents of the critic's prompt file]

   You have access to Glob, Grep, and Read tools for verifying claims. Read `skills/brainstorming/design-critique-checklist.md` in full, then read `{design-file-path}` in full. {If mockups were generated, add: Also review the mockups at `docs/mockups/{session-name}/` — open each HTML file with Read and evaluate the visual design alongside the written spec.} Your job has two phases:
   **Phase 1 (Fact-check):** Extract every factual claim about the codebase (file paths, function names, imports, data flows, config references). Verify each using Glob/Grep/Read. Mark claims as [CONFIRMED], [INCORRECT] with correction, or [UNVERIFIABLE]. Report accuracy percentage.
   **Phase 2 (Critique):** Using the verification data you already gathered (do not re-verify), evaluate the design against each criterion in the checklist through your lens. Also evaluate Decision Log entries if present. Tag every finding with your name (e.g., [Jobs], [The Architect]).
   Output a single combined report: fact-check summary at the top, then critique in the checklist output format."

5. **Aggregate the reports:**
   - **Fact-checks:** Merge all. De-duplicate — if multiple critics verified the same claim, report it once with all confirming sources (e.g., `[The Architect, The QA Engineer]`). If critics disagree on a claim, note both findings.
   - **Critique findings:** Merge all, preserving persona tags. De-duplicate — when two or more critics flag the same issue, keep the highest-severity version and note all sources.
   - Present the unified report to the user.

6. Apply corrections for any INCORRECT fact-check claims. Apply fixes for medium/high critique issues the user approves.

**Round 2 (conditional):**
Only run if Round 1 found medium or high severity issues. Use the same critics from Round 1 with fresh sub-agents (do NOT resume Round 1 agents), against the updated document.

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
