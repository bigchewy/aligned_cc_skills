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

**Mockup generation (conditional):**
If the design involves frontend/UI changes, generate HTML mockups using the `mockup-generator` skill before presenting the design document. Create a session subfolder under `docs/mockups/` with a descriptive kebab-case name. Include flow diagrams as Mermaid blocks that render in the HTML. Run `open` on each file so the user can preview in their browser.

## After the Design

**Documentation:**
- Write the validated design to `docs/plans/YYYY-MM-DD-<topic>-design.md`
- Use elements-of-style:writing-clearly-and-concisely skill if available

**Design Review (Steve Jobs persona, conditional):**
If `docs/design/design-principles.md` exists in the project, load `agents/steve-jobs.md` and adopt the Steve Jobs persona for evaluating the design against the Four Questions from design-principles.md. Deliver the evaluation in Jobs's voice. This applies only to the design-review portion, not the entire session. If design-principles.md does not exist, skip the persona and evaluate without it.

**Fact-Check + Critique (mandatory, merged into one agent):**

**MANDATORY: You MUST use the Task tool to launch a fresh sub-agent** for every critique round. NEVER run the critique in the main context window. The sub-agent provides independent evaluation — it hasn't seen the brainstorming conversation, so it won't anchor on the author's assumptions. Running critique inline defeats the purpose and is a skill violation.

**Round 1:**
1. Launch a fresh sub-agent (Task tool, `subagent_type=general-purpose`, `model=sonnet`). Replace `{design-file-path}` below with the absolute path of the design document you wrote in the previous step. Prompt:
   - "You are a skeptical, evidence-driven design reviewer. Read `skills/brainstorming/design-critique-checklist.md` in full, then read `{design-file-path}` in full. Your job has two phases:
     **Phase 1 (Fact-check):** Extract every factual claim about the codebase (file paths, function names, imports, data flows, config references). Verify each using Glob/Grep/Read. Mark claims as [CONFIRMED], [INCORRECT] with correction, or [UNVERIFIABLE]. Report accuracy percentage.
     **Phase 2 (Critique):** Using the verification data you already gathered (do not re-verify), evaluate the design against each criterion in the checklist. Also evaluate Decision Log entries if present.
     Output a single combined report: fact-check summary at the top, then critique in the checklist output format."
2. Apply corrections for any INCORRECT claims. Apply fixes for medium/high critique issues.

**Round 2 (conditional):**
Only run if Round 1 found medium or high severity issues.
Same as Round 1 but against the updated document. Use a fresh sub-agent (do NOT resume Round 1).

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
