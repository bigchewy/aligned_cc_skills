---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
---

# Executing Plans

## Overview

Load plan, review critically, execute tasks in batches, report for review between batches.

**Core principle:** Batch execution with checkpoint prior to testing and commit

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Autonomous mode:** Execute all tasks without pausing for review between batches. Only stop if a task fails verification or hits a blocker. When all tasks pass, stop. Do NOT invoke `/aligned:finishing-a-development-branch` — the user will run that manually.

## The Process

### Step 0: Verify Working Branch
Before starting implementation, confirm you're NOT on main:
```bash
git branch --show-current
```
Check the output. If it shows `main` or `master`, STOP. Tell the user and offer to run `/aligned:using-git-worktrees`. Do not proceed with code changes on main.

### Step 1: Load and Review Plan
1. Read plan file. **Note:** Plan files are committed to `main` and saved in the main worktree's `docs/plans/` directory. If working in a worktree, use the absolute path to the main worktree to read the plan:
   ```bash
   git worktree list
   ```
   Parse the output to extract the path from the first line (text before the first space). Store this as `main_worktree`. Do NOT use piped commands. Read plan from: `$main_worktree/docs/plans/<plan-file>.md`
2. **Verify plan against architecture:** If the project has `docs/architecture.md`, read it and cross-check the plan's assumptions (module dependencies, data flows, file paths). Plans may have been written days or weeks ago and the codebase may have changed. Architecture docs may also be stale — trust actual source files over both the plan and the diagrams. If you find discrepancies between the architecture doc and actual code, file them (see "Bug Board Entry Format" below).
3. Review critically - identify any questions or concerns about the plan
4. If concerns: Raise them with your human partner before starting
5. If no concerns: Create a task list with TaskCreate and proceed

### Step 2: Execute Build Tasks
**Default: First 5 tasks**

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

**TDD discipline:** Every task follows RED-GREEN-REFACTOR. Write the failing test first, verify it fails, write minimal implementation, verify it passes. Reference: `test-driven-development` skill. If a task skips TDD steps, STOP and follow the TDD process before continuing.

**LLM surface check:** If the task involved changes to advisor prompts, framework prompts, prompt builders, or personalization logic, run the project's eval command (as defined in `CLAUDE.md` or `e2e/eval-config.ts`) to verify quality. Don't wait until all tasks are done — catching regressions early is cheaper than debugging across multiple steps. If evals fail, run the `/aligned:eval-failure-triage` skill to classify and fix before continuing.

### Step 3: Report
When Build Tasks are complete:
- Show what was implemented
- Show verification output
- Say: "Build is complete. Ready for testing".  give the user instructions on what to test and how to test it.  Include the bash command that the user should run to go to the worktree and start the dev server

### Step 4: Continue
Based on feedback:
- Apply changes if needed
- Execute next tasks

### Step 5: Archive Plan Files

When all tasks are complete and verified, move the plan and its source design doc to `docs/plans/completed/` on the main worktree.

1. Determine the main worktree path (if not already known from Step 1):
   ```bash
   git worktree list
   ```
   Parse the first line to get `main_worktree`.

2. Parse the plan's `**Source Design Doc:**` field to get the design doc path (relative to repo root).

3. Move the plan file:
   ```bash
   git -C "$main_worktree" mv docs/plans/<plan-file>.md docs/plans/completed/
   ```

4. If the source design doc is not `N/A`, move it too:
   ```bash
   git -C "$main_worktree" mv docs/plans/<design-doc>.md docs/plans/completed/
   ```

5. Commit the moves:
   ```bash
   git -C "$main_worktree" commit -m "docs: archive completed plan files for <feature-name>"
   ```

If either move fails (file already moved or doesn't exist), skip it and continue.

### Step 6: Report Completion

Report what was implemented and instruct the user to run `/aligned:finishing-a-development-branch` in a new session. Do NOT invoke it directly.

> **For large plans:** Consider using the Ralph loop instead. Each task runs in a fresh context, avoiding quality degradation from context window bloat. The writing-plans skill generates the correct `run-ralph.sh` command with resolved paths. After the loop completes, run `/aligned:finishing-a-development-branch` manually.

**Required sub-skills:**
- **test-driven-development** — RED-GREEN-REFACTOR cycle for every task
- **verification-before-completion** — verify claims with fresh evidence before marking tasks complete

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker mid-batch (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly
- Before you hit the testing or commit phase

**Ask for clarification rather than guessing.**

## Bug Discovery During Execution

When you encounter a problem that is **outside the current task's scope** during execution:

1. **Don't fix it** — stay focused on the current task
2. **Don't stop** — this isn't a blocker for the current work
3. **Log it** to the Kanban board:

Read `docs/kanban/.counter` for the next KB number (pad to 3 digits). Derive a kebab-case slug from the description (max 50 chars). Write `docs/kanban/todo/KB-NNN-slug.md`:

```markdown
# KB-NNN: [Short description]

- **Type:** bug
- **Discovered during:** [plan filename / Task N]
- **Location:** `src/path/to/file.ts:NN`
- **Observed:** [What you saw — be specific enough for a fresh session to reproduce]
- **Expected:** [What should happen instead]
- **Why out of scope:** [Why this isn't part of the current task]
- **Severity:** CRITICAL | HIGH | MEDIUM | LOW
- **Created:** [today's date]
```

Write the incremented number back to `docs/kanban/.counter`.

4. **Continue** with the current task

**At the end of execution (Step 6),** if any bugs were logged during this session, add to the completion report:

```
N bug(s) were discovered and logged to `docs/kanban/todo/`. Review them and pick up in a fresh session with `/aligned:systematic-debugging`.
```

**What qualifies as a bug to log:**
- Existing broken behavior you notice while working (not caused by your changes)
- Test failures in unrelated files
- Code smells that could cause production issues
- Missing error handling in code you're reading but not modifying

**What does NOT qualify:**
- Issues caused by your current changes (fix them now)
- Things that are part of a later task in the current plan (the plan handles it)
- Style preferences or refactoring wishes (not bugs)

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Tool Usage
**Never use Bash for file search or content search.** Use Glob (not `find`), Grep (not `grep`/`rg`), and Read (not `cat`/`head`/`sed`/`awk`) — even when searching across many files. Complex Bash pipelines with `|`, `&&`, or subshells trigger interactive approval prompts that break autonomous execution. If you need to process multiple files, use Glob to find them, Read to inspect them, and analyze the content in context.

## Kanban Entry Format

When filing a Kanban entry, read `{base-directory}/../_shared/kanban-entry-format.md` for the template and counter instructions (resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load). Use `[plan filename / Task N]` as the "Discovered during" value (more specific than just the skill name).

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Between batches: just report and wait
- Stop when blocked, don't guess
