---
name: autopilot
description: "Nearly automated pipeline from idea to working code. Asks up to 3 clarifying questions in a single message, then autonomously designs, plans, creates a worktree, and executes — all with minimal human involvement. Use when you want to go from idea to implementation with almost no interaction."
---

# Autopilot: Idea to Implementation

## Overview

Full pipeline from idea to working code with one interaction point. Ask up to 3 clarifying questions at the start, then autonomously handle design, planning, worktree setup, and implementation.

Heavy phases (design, planning, execution) run as sub-agents via the Task tool to keep the main context lean. Each sub-agent gets fresh context with only the inputs it needs.

**Announce at start:** "I'm using the autopilot skill. I'll ask a few clarifying questions, then handle everything autonomously — design, planning, and implementation."

## Prerequisites

This skill orchestrates existing skills. The following skills must be available in the aligned plugin namespace: brainstorming, writing-plans, executing-plans, using-git-worktrees.

## When to Use Autopilot

**Good fit:** Small-to-medium features where the implementation plan will have roughly 10 or fewer tasks.

**Poor fit:** Large features (15+ tasks) or deep architectural changes. For these, use the manual multi-session workflow: `/aligned:brainstorming` → `/aligned:writing-plans` → `/aligned:executing-plans` (each in its own session).

**Bailout mechanism:** If the plan produced in Phase 3 exceeds 12 tasks, stop and tell the user: "This plan has N tasks — too large for single-session execution. The plan is committed to main at `{plan-path}`. Start a new session and use `/aligned:executing-plans` to implement it." Then stop.

## Autonomous Overrides

These overrides apply to ALL phases and MUST be included in every sub-agent prompt. They take precedence over any sub-skill instructions that conflict:

- **Never stop for user feedback** unless genuinely blocked (missing credentials, infrastructure not set up, unresolvable ambiguity).
- **Never output "next step" prompts or execution handoff sections.** These sections exist in the sub-skills for multi-session workflows — autopilot replaces that with direct phase continuation.
- **Never ask follow-up questions.** Make decisions independently.
- **When facing a design choice**, pick the simpler option. Prefer existing patterns over new ones.
- **YAGNI aggressively.** Remove unnecessary features from all designs.
- **Skip mockup generation** unless the user's idea is primarily a UI change.

---

## Phase 0: Kickstart Check (main context)

Before Quick Discovery, check if the project has been scaffolded with Aligned conventions:

1. Does `docs/design/design-principles.md` exist?
2. Does `CLAUDE.md` reference Aligned conventions?
3. Does `e2e/` directory exist?

**If all exist:** Skip to Phase 1 (Quick Discovery).

**If missing:** Ask the user: "This project hasn't been set up with Aligned conventions yet. Want me to run `/aligned:kickstart` first?" If yes, run kickstart, then continue the pipeline. If no, proceed without — autopilot still works, it just won't have the scaffolding.

This is a soft check, not a gate. Autopilot works on any project. If the user says yes to kickstart but it fails, report the error and skip to Phase 1 — do not abort the pipeline.

---

## Phase 1: Quick Discovery (main context)

1. Read project context: CLAUDE.md, recent git log (`git log --oneline -10`), and any files referenced in the user's request.
2. Use AskUserQuestion to ask **at most 3 questions in a single message**.
   - Use multiple choice options when possible.
   - Focus on: core intent, key constraints, scope boundaries.
   - Make questions specific enough that answers directly inform design decisions.
3. After receiving answers, proceed autonomously through all remaining phases.

**Decision principle:** When facing an ambiguous choice after Phase 1, pick the simpler option that fits existing codebase patterns. Document the choice in the design doc's decision log rather than asking the user.

**Phase complete when:** Answers received. Proceed immediately.

---

## Phase 2: Design (sub-agent)

Launch a sub-agent (Task tool, `subagent_type=general-purpose`) with this prompt structure:

```
Context: Building a feature for [project description from CLAUDE.md].
User's idea: [original request]
User's answers to clarifying questions: [Phase 1 answers]

Instructions:
1. Read the brainstorming skill's SKILL.md for the full brainstorming workflow.
2. Follow it with these overrides:
   - Skip incremental section validation — write the complete design at once. Autopilot trades validation depth for speed.
   - Skip "Exploring approaches" dialogue — evaluate 2-3 approaches internally, pick the best, document reasoning in a Decision Log.
   - Do run the mandatory critique: launch a fresh sub-agent using the Task tool (subagent_type=general-purpose, model=sonnet) for fact-check + critique against design-critique-checklist.md. NEVER use `claude -p` or Bash to spawn critique — use the Task tool only. Apply corrections.
   - Do commit the design document to git after critique.
   - Do NOT output a "next step prompt" or invoke /aligned:using-git-worktrees.
   - Do NOT ask the user any questions. Make all decisions independently, preferring the simpler option.
   - YAGNI aggressively.
3. When done, report: the design doc file path and a one-paragraph summary of the design.
```

After the sub-agent returns, extract the design doc path and summary. Continue to Phase 3.

**Phase complete when:** Sub-agent returns with committed design doc path.

---

## Phase 3: Plan (sub-agent)

Launch a sub-agent (Task tool, `subagent_type=general-purpose`) with this prompt structure:

```
Context: Writing an implementation plan for [project description].
Design document: [design doc path from Phase 2]

Instructions:
1. Read the writing-plans skill's SKILL.md for the full planning workflow.
2. Read the design document at [path].
3. Follow writing-plans completely with these overrides:
   - Skip the "Execution Handoff" section — do not output next-step prompts.
   - Do run the mandatory critique: launch a fresh sub-agent using the Task tool (subagent_type=general-purpose, model=sonnet) for fact-check + critique against plan-critique-checklist.md. NEVER use `claude -p` or Bash to spawn critique — use the Task tool only. Apply corrections.
   - Do save the plan to the main worktree and commit to main.
   - Do NOT ask the user any questions. Make all decisions independently.
   - YAGNI aggressively.
4. When done, report: the plan file path, total task count, and a one-paragraph summary.
```

After the sub-agent returns, extract the plan path and task count.

**Bailout check:** If task count exceeds 12, tell the user the plan is too large for single-session execution. Report the committed plan path and suggest starting a new session with `/aligned:executing-plans`. Then stop.

Otherwise, continue to Phase 4.

**Phase complete when:** Sub-agent returns with committed plan path and task count is ≤12.

---

## Phase 4: Setup (main context)

Create an isolated worktree for implementation:

1. Invoke the `/aligned:using-git-worktrees` skill to create the worktree. Let it handle branch naming and directory selection.
2. After the worktree is created, verify tests pass in it. Run the project's test command (detect from `package.json`, `Cargo.toml`, `pyproject.toml`, or `CLAUDE.md`).
3. If tests fail, investigate and fix before proceeding. If the failure is environmental (not code-related), stop and explain.

Continue to Phase 5 in the new worktree.

**Phase complete when:** Worktree exists and all tests pass in it.

---

## Phase 5: Execute (sub-agent)

Launch a sub-agent (Task tool, `subagent_type=general-purpose`) with this prompt structure:

```
Context: Executing an implementation plan in a worktree.
Plan file: [plan path from Phase 3, absolute path on main worktree]
Worktree: [worktree path from Phase 4]
Working directory: [worktree path]

Instructions:
1. Read the executing-plans skill's SKILL.md for the full execution workflow.
2. Read the plan file at [path].
3. Follow executing-plans with these overrides:
   - Execute ALL tasks, not just the first 5. The batch size of 5 is for multi-session review workflows. Run to completion in one pass.
   - Skip Step 6 (Report Completion) — do not tell the user to run /aligned:finishing-a-development-branch.
   - Do follow all other steps: verify not on main (Step 0), load plan (Step 1), execute tasks (Step 2), run verifications, archive plan files (Step 5).
   - If evals fail, run the `/aligned:eval-failure-triage` skill to classify and fix.
   - Do NOT ask the user any questions. If blocked, stop and report what's blocking.
4. When done, report: tasks completed, tasks failed (if any), test results, and a summary of what was built.
```

After the sub-agent returns, extract results. Continue to Phase 6.

**Phase complete when:** Sub-agent returns with all tasks executed and verifications passing.

---

## Phase 6: Complete (main context)

1. Run the full test suite from the worktree. Run the project's test command (detect from `package.json`, `Cargo.toml`, `pyproject.toml`, or `CLAUDE.md`).
2. Report to the user:
   - Summary of what was built (from Phase 5 results)
   - Test results
   - Any deviations from the plan and why
3. Tell the user: "Implementation complete. Run `/aligned:finishing-a-development-branch` to merge, create a PR, or clean up."

Do NOT invoke `/aligned:finishing-a-development-branch` directly — the user runs that manually.

---

## Tool Usage

**Include these rules in every sub-agent prompt.**

Never use Bash for file search or content search. Use Glob (not `find`), Grep (not `grep`/`rg`), and Read (not `cat`/`head`/`sed`/`awk`). Keep Bash commands as single operations without pipes or operators. When output needs processing, parse it in context rather than piping to `head`, `awk`, or `grep`.

**For nested sub-agents (critique rounds):** Always use the Task tool (`subagent_type=general-purpose`) to launch critique sub-agents. NEVER shell out to `claude -p` or `claude --print` via Bash. The Task tool runs in-process and respects existing permissions. Bash-spawned `claude` processes trigger permission prompts for every invocation and bypass the sub-agent's tool access.

## Error Recovery

If blocked at any phase:
1. Attempt to resolve independently using codebase exploration.
2. If truly stuck, stop and explain what's blocking progress. Do not guess or skip the blocker.
3. After the user unblocks, resume from where execution stopped — do not restart the pipeline.

**Specific scenarios:**
- **Sub-agent fails or returns an error:** Report the error to the user with full context. Offer to retry the phase or switch to manual mode for that phase.
- **Critique sub-agent fails to launch:** The phase sub-agent should run critique inline as a fallback and note the deviation.
- **Worktree creation fails:** Stop and explain. Worktree issues often require manual cleanup.
- **Tests fail after Phase 5 execution:** Report the failures with full output. Do not mark the pipeline as complete. Let the user decide whether to debug in-session or start a new session.
