---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

## Overview

You are a senior implementation planner. Your job is to produce plans that a fresh sub-agent can execute without any prior context about the codebase.

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** This may be run in a dedicated worktree (created by brainstorming skill) or on main.

**Autonomous execution:** Run to completion without pausing for user feedback.
Pre-approved actions (do not ask):
- Create/edit files in worktrees
- Read any skill files
- Read any project files
- Run the project's test command (e.g., `npm test`, `cargo test`, `pytest`)
- Launch sub-agents for codebase research
- Commit the plan to main

Only stop for: destructive operations on main branch, or unresolvable ambiguity in the design document.

**Save plans to the MAIN worktree:** `docs/plans/YYYY-MM-DD-<feature-name>.md`

### Plan File Location Rule

**Plans MUST always be written to the main worktree directory and committed to `main`.** This prevents plan files from being lost if a feature branch is discarded, abandoned, or never merged.

**Before writing the plan file, determine the main worktree path:**

```bash
git worktree list
```

Parse the output to extract the path from the first line (text before the first space). Store this as `main_worktree`. Do NOT use piped commands (`| head | awk`) — run the single command and parse the output.

**Save the plan to:** `$main_worktree/docs/plans/YYYY-MM-DD-<feature-name>.md`

**After writing the plan file, commit it to main:**

```bash
git -C "$main_worktree" add docs/plans/YYYY-MM-DD-<feature-name>.md
git -C "$main_worktree" commit -m "docs: add implementation plan for <feature-name>"
```

**Why:** Plan files written inside a worktree only exist on the feature branch. If that branch is discarded (Option 4 in finishing-a-development-branch), the plan is permanently lost. Writing to main ensures plans survive regardless of what happens to the feature branch.

## Before Writing

Explore the codebase before writing any plan:
1. Read the spec/requirements document or design
2. **Read architecture docs:** If the project has `docs/architecture.md` (or equivalent), read it to understand data flows, module dependencies, and existing patterns before exploring code. This orients the plan around the actual system structure. **Caveat:** Architecture docs may be stale — always verify against actual source files in subsequent steps. If you find a discrepancy, file a bug (see "Bug Board Entry Format" below).
3. Use Glob/Grep to find files relevant to the feature
4. Read key files to understand current patterns and conventions
5. **Sub-agent research:** When exploring the codebase (reading multiple files, searching for patterns across the project), prefer launching a sub-agent (`subagent_type=Explore`) to keep the main context window lean. Reserve direct Glob/Grep/Read for targeted lookups where you know the exact file or pattern.
6. **Check lessons-learned:** If `docs/lessons-learned/` exists, read all non-completed lesson files. Check if any relate to the feature being planned. Factor prevention guidance into task design to avoid repeating known mistakes.
7. Only then begin writing the plan with verified file paths and code references

## Manual Steps Policy

**Plans MUST NOT include manual steps in the middle of the task sequence.** The Ralph loop (`while :; do claude -p ...`) cannot pause for human intervention — it will skip or incorrectly mark manual tasks as complete.

Manual steps fall into two categories:

1. **Prerequisites (before Task 1):** Steps the user must complete before starting execution. Place these in a `## Prerequisites` section between the header and Task 1. Examples: running SQL in Supabase Dashboard, enabling a feature flag, configuring OAuth credentials.

2. **Post-automation steps (after the last task):** Steps the user must complete after all automatable tasks finish. Place these in a `## Manual Steps (Post-Automation)` section after the final task. Examples: running a migration against production, updating DNS records, manual QA.

**Never bury a manual step inside Task N.** If a task requires manual intervention mid-plan, restructure:
- Move the manual prerequisite to the Prerequisites section
- Split the remaining work into tasks that can run after the prerequisite is done
- If a manual step depends on automated output (e.g., "run this generated SQL"), defer it to Post-Automation with clear instructions on what to run and where

## Standalone Scripts and Environment Variables

When a plan includes a standalone TypeScript/JavaScript script (migration, seed, one-off task) that reads `process.env`, the script **will not** have access to `.env.local` variables unless it loads them explicitly. Next.js loads `.env.local` automatically, but `npx tsx script.ts` does not.

**Rule:** Any standalone script in a plan that uses environment variables MUST include dotenv loading at the top:

```typescript
import 'dotenv/config' // or: import { config } from 'dotenv'; config({ path: '.env.local' })
```

If dotenv is not a project dependency, the plan should either:
- Add it: `npm install -D dotenv`
- Or use the shell prefix: `source .env.local && npx tsx script.ts` (note: only works if `.env.local` uses `export VAR=value` syntax, which Supabase/Next.js `.env.local` files typically do not)

**Prefer the dotenv import approach** — it's reliable regardless of `.env.local` format.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Source Design Doc:** [path relative to repo root, e.g. `docs/plans/2026-01-15-feature-design.md`, or `N/A` if none]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---

## Prerequisites (if any)

> Complete these steps manually before starting Task 1.

- [ ] [Manual step description with exact instructions]

---
```

## Task Structure

```markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
```

## MANDATORY: Error Path Tests for Mocks

**CRITICAL REQUIREMENT:** When a task involves tests that mock external operations, the plan MUST specify BOTH success AND error path tests.

### Operations That ALWAYS Need Error Path Tests

When writing test specs that mock any of these, ALWAYS include error path tests:

| Operation | Can Fail Because | Error Test Required |
|-----------|------------------|---------------------|
| `req.formData()` | Malformed multipart body | `mockRejectedValue(new Error('Parse failed'))` |
| `req.json()` | Invalid JSON | `mockRejectedValue(new SyntaxError())` |
| `file.arrayBuffer()` | Read failure | `mockRejectedValue(new Error('Read failed'))` |
| `fetch()` | Network error | `mockRejectedValue(new Error('Network error'))` |
| `db.query()` | Connection failure | `mockRejectedValue(new Error('Connection lost'))` |
| `fs.readFile()` | File not found | `mockRejectedValue(new Error('ENOENT'))` |
| External API calls | Timeout, 500, rate limit | `mockRejectedValue(new Error('Timeout'))` |

### Example: Correct Test Spec in Plan

```typescript
// Success path test
it('extracts text from uploaded PDF', async () => {
  const formData = new FormData()
  formData.append('file', new File(['content'], 'test.pdf'))

  const req = {
    headers: { get: () => 'multipart/form-data' },
    formData: jest.fn().mockResolvedValue(formData),
  }

  const response = await POST(req)
  expect(response.status).toBe(200)
})

// Error path test (MANDATORY)
it('returns 400 when formData() throws', async () => {
  const req = {
    headers: { get: () => 'multipart/form-data' },
    formData: jest.fn().mockRejectedValue(new Error('Malformed body')),
  }

  const response = await POST(req)

  expect(response.status).toBe(400)
  const body = await response.json()
  expect(body.error).toContain('parse')
})
```

### Gate Function for Plan Writers

```
BEFORE completing any test spec that uses mocks:

  1. List ALL async operations being mocked
  2. For EACH mocked operation, verify:
     - [ ] Success path test exists (mockResolvedValue)
     - [ ] Error path test exists (mockRejectedValue)
     - [ ] Error handling returns appropriate response (400, not 500)

  IF error path test is missing:
    STOP - Add it to the plan before proceeding

  Reference: test-driven-development/testing-anti-patterns.md
             See Anti-Pattern 6: Mocking Away Error Paths
```

## Eval Scenarios Section

If the plan involves changes to advisor prompts, frameworks, prompt construction, or personalization logic, include an "Eval Scenarios" section specifying which scenarios need to be created or updated. If the plan involves LLM behavior changes, include eval scenario specs using the project's eval conventions (see `e2e/` directory if it exists).

## Decision Log (mandatory)

After completing the plan, append a Decision Log section. Include every choice where reasonable alternatives existed. Focus on decisions the user might question or want to revisit.

### Format

```markdown
## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | [topic]  | [choice]   | [alt A], [alt B]       |

### Appendix: Decision Details

#### Decision 1: [topic]
**Chose:** [choice]
**Why:** [2-3 paragraphs — reasoning, trade-offs, evidence from codebase]
**Alternatives rejected:**
- [Alt A]: [why not]
- [Alt B]: [why not]
```

The summary table should fit on one page. Supporting detail goes in the appendix.

## Fact-Check + Critique (mandatory, merged into one agent)

**MANDATORY: You MUST use the Task tool to launch a fresh sub-agent** for every critique round. NEVER run the critique in the main context window. The sub-agent provides independent evaluation — it hasn't seen the planning conversation, so it won't anchor on the author's assumptions. Running critique inline defeats the purpose and is a skill violation.

**Round 1:**
1. Launch a fresh sub-agent (Task tool, `subagent_type=general-purpose`, `model=sonnet`). Replace `{plan-file-path}` below with the absolute path of the plan document you wrote in the previous step. Prompt:
   - "You are a skeptical, evidence-driven plan reviewer. Read `skills/writing-plans/plan-critique-checklist.md` in full, then read `{plan-file-path}` in full. Your job has two phases:
     **Phase 1 (Fact-check):** Extract every factual claim about the codebase (file paths, function names, imports, data flows, config references). Verify each using Glob/Grep/Read. Mark claims as [CONFIRMED], [INCORRECT] with correction, or [UNVERIFIABLE]. Report accuracy percentage.
     **Phase 2 (Critique):** Using the verification data you already gathered (do not re-verify), evaluate the plan against each criterion in the checklist. Also evaluate Decision Log entries if present.
     Output a single combined report: fact-check summary at the top, then critique in the checklist output format."
2. Apply corrections for any INCORRECT claims. Apply fixes for medium/high critique issues.

**Round 2 (conditional):**
Only run if Round 1 found medium or high severity issues.
Same as Round 1 but against the updated document. Use a fresh sub-agent (do NOT resume Round 1).

If the plan changes system architecture (new routes, module restructuring, database schema changes), add a final task to update `docs/architecture.md` with the new state.

## Plan Critique

When critiquing an existing plan (instead of writing one), use the checklist in `plan-critique-checklist.md`. Launch fresh sub-agents for critique rounds to ensure independent evaluation. Verify every claim against actual source code — don't trust line numbers, file paths, code snippets, or test counts without checking.

## Verification Gate

Before including any file path, line number, or code snippet in the plan, verify it exists in the codebase:
- **Glob** to confirm file paths exist (or confirm "Create" targets don't already exist)
- **Read** to verify line numbers and code snippets are accurate
- **Grep** to confirm counts, imports, and usage patterns

If a referenced file cannot be found, flag it as `[NOT FOUND]` in the plan rather than guessing.

## Remember
- Exact file paths always — verified with Glob/Read before writing
- Complete code in plan (not "add validation")
- Exact commands with expected output
- Reference relevant skills with @ syntax
- DRY, YAGNI, TDD, frequent commits
- **Every mock with mockResolvedValue needs a corresponding mockRejectedValue test**
- **No manual steps mid-plan** — prerequisites before Task 1, manual steps after last task
- **Standalone scripts need dotenv** — `import 'dotenv/config'` if reading process.env outside Next.js

## Bug Board Entry Format

When filing a discrepancy to `docs/Kanban-board.md`:

1. Read the board file
2. Find the highest existing `[BUG-NNN]` number and increment by 1 (start with BUG-001 if none exist)
3. Use the Edit tool to insert the entry under "## To Do", before any existing entries (most recent first):

```markdown
### [BUG-NNN] Short description
- **Date:** YYYY-MM-DD
- **Found by:** writing-plans
- **Category:** architecture-discrepancy
- **Severity:** low | medium | high
- **File:** docs/architecture.md:line-range
- **Details:** Diagram says X, but code at path/to/file shows Y
```

## Execution Handoff

After saving the plan (to the main worktree and committed to main), generate ready-to-paste prompts for executing the plan. Since the brainstorming phase already created the worktree, these prompts reference the existing worktree path.

**Output this to the user:**

```
Plan complete and saved to `docs/plans/<filename>.md` (committed to main).
```

Then output two execution options (with `{plan-file-path}`, `{feature-name}`, and `{worktree-path}` filled in):

````
## Next Steps

### Option A: Interactive execution (smaller plans)
Copy into a new Claude Code session:
> `cd {worktree-path}` then use `/aligned:executing-plans` to execute `{plan-file-path}`.

### Option B: Ralph loop execution (larger plans)
Run from the worktree directory:
```bash
cd {worktree-path} && rm -f .ralph-done && while :; do claude -p "$(cat docs/ralph_loops/EXECUTE-PLAN.md)

Plan: {plan-file-path}
Worktree: {worktree-path}" && [ -f .ralph-done ] && rm .ralph-done && break; done
```
````

If the worktree path is not known (e.g., writing-plans was invoked without a prior brainstorming session), fall back to the format that includes worktree creation. **Both options must be shown** — Option B uses the worktree path that Option A creates:

````
### Option A: Interactive execution (smaller plans)
Copy into a new Claude Code session:
> Use the /aligned:using-git-worktrees skill to create a worktree for branch `feature/{feature-name}`. Once the worktree is ready and tests pass, use the /aligned:executing-plans skill to execute the plan at `{plan-file-path}`. Note: the plan file lives on main, not the feature branch — read it using the absolute path from the main worktree.

### Option B: Ralph loop execution (larger plans)
First create the worktree, then run from it:
```bash
cd /path/to/your/project && git worktree add .worktrees/{feature-name} -b feature/{feature-name}
cd .worktrees/{feature-name} && npm install && ln -sf ../../.env.local .env.local
rm -f .ralph-done && while :; do claude -p "$(cat docs/ralph_loops/EXECUTE-PLAN.md)

Plan: {plan-file-path}
Worktree: $(pwd)" && [ -f .ralph-done ] && rm .ralph-done && break; done
```
Note: Replace `/path/to/your/project` with the actual project root. The `$(pwd)` resolves the worktree path automatically after `cd`.
````
