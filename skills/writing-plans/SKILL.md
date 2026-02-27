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

**Cross-repo guard:** Before writing, verify the plan belongs in this repo. Compare `$main_worktree` against the plan's target working directory (from the user's request, spec, or design doc). If the work targets a different repo (e.g., you're in `~/software/epch-projects` but the plan's tasks modify files in `~/software/aligned_cc_skills`), **STOP.** Tell the user:

```
This plan targets [target repo], but the current repo is [current repo].
Plans must live in the repo where the work happens.
Please start a session in [target repo] and re-run writing-plans there.
```

Never write a plan for repo B into repo A's `docs/plans/`. The plan, its archival, and its execution all assume they share a repo.

**Save the plan to:** `$main_worktree/docs/plans/YYYY-MM-DD-<feature-name>.md`

**After writing the plan file, commit it to main:**

```bash
git -C "$main_worktree" add docs/plans/YYYY-MM-DD-<feature-name>.md
git -C "$main_worktree" commit -m "docs: add implementation plan for <feature-name>"
```

**Why:** Plan files written inside a worktree only exist on the feature branch. If that branch is discarded (Option 4 in finishing-a-development-branch), the plan is permanently lost. Writing to main ensures plans survive regardless of what happens to the feature branch.

### Chunked Writing for Large Plans

The Write tool has a content size limit (~32K tokens). Plans with >15 tasks and full code snippets will often exceed this. When writing a large plan:

1. **Write the first chunk** via Write tool — header through approximately Task 8-10 (aim for well under the limit)
2. **Append remaining tasks** via successive Edit calls — set `old_string` to the last task heading and its first line (e.g., `### Task 10: Component Name\n\n**Files:**`), and `new_string` to that same text plus the next batch of tasks after it. Use a full task heading as the match target — it will be unique in the document. Do not match on generic lines like `---` or blank lines.
3. **Append the Decision Log last** — it's always the final section

If you hit a Write tool size error, do not retry the same content. Split it in half and use the chunked approach above.

## Before Writing

Explore the codebase before writing any plan:
1. Read the spec/requirements document or design
2. **Read architecture docs:** If the project has `docs/architecture.md` (or equivalent), read it to understand data flows, module dependencies, and existing patterns before exploring code. This orients the plan around the actual system structure. **Caveat:** Architecture docs may be stale — always verify against actual source files in subsequent steps. If you find a discrepancy, file a bug (see "Bug Board Entry Format" below).
3. Use Glob/Grep to find files relevant to the feature
4. Read key files to understand current patterns and conventions
5. **Sub-agent research:** When exploring the codebase (reading multiple files, searching for patterns across the project), prefer launching a sub-agent (`subagent_type=Explore`) to keep the main context window lean. Reserve direct Glob/Grep/Read for targeted lookups where you know the exact file or pattern.
6. Only then begin writing the plan with verified file paths and code references

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

**Mockups:** [path to mockups directory, e.g. `docs/mockups/feature-name/`, or omit if none — read from design doc's `**Mockups:**` field]

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

## Mockup Verification in UI Tasks

When the source design doc references mockups (in `docs/mockups/{session}/`) and a task involves UI changes (creating or modifying pages, components, or layouts), add a **mockup verification step** to that task — between "verify tests pass" and "commit."

**Only add this step to tasks that change UI.** Non-UI tasks (API routes, data models, config, scripts) skip it.

### Template for the mockup verification step

```markdown
**Step N: Verify mockup fidelity**

Read the mockup at `docs/mockups/{session}/{file}.html`. Compare your implementation:
- Layout structure matches (sections, columns, ordering)
- Components present and positioned correctly
- Data displayed matches mockup examples (labels, columns, field names)
- Interactive elements present (tabs, accordions, hover states, modals)

If you intentionally deviate from the mockup (e.g., discovered a better approach during implementation), add a note below the task heading:
> MOCKUP DEVIATION: [what changed and why]
```

**Relationship to The Verifier:** The Verifier critic (see Fact-Check + Critique Panel) verifies at plan-writing time that the plan's tasks cover all mockup elements. This per-task step ensures the executor actually matches the mockup at implementation time — plan coverage and execution fidelity are complementary checks.

**How this works with Ralph loops:** Each Ralph loop invocation reads the task spec. If the task includes a mockup verification step, the loop checks fidelity for that task before marking it complete. Drift is caught per-task, not just at the end.

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

  Reference: skills/test-driven-development/testing-anti-patterns.md
             See Anti-Pattern 6: Mocking Away Error Paths
```

### Test Value Gate (Anti-Inflation)

When specifying tests in a plan, every test must pass this check:

```
BEFORE adding a test to the plan:

  1. Does the function under test contain LOGIC?
     Logic = conditionals, loops, transformations, error handling,
     sorting, filtering, mapping, calculations, state machines

  2. If NO logic (pure delegation, one-line wrapper):
     SKIP — Don't add a test for this function.
     The function's callee should have tests instead.

  3. If YES logic, what KIND of test?
     - Behavioral (input → output)? ✅ Always write
     - Error handling (try/catch behavior)? ✅ Write if handling exists
     - Error propagation (no try/catch)? ❌ Skip — Anti-Pattern 7
     - Type shape (assign + assert)? ❌ Skip — TypeScript handles this
     - Interaction only (toHaveBeenCalledWith)? ⚠️ Only if the CALL is the logic

  4. Does the test use realistic data?
     - ❌ Single-word strings ('Fast', 'test')
     - ✅ Realistic content that exercises edge cases
```

**Why this matters:** TDD discipline can produce test inflation when applied mechanically. A codebase with 1,000 thin-wrapper tests and 400 logic tests has worse coverage than one with just the 400 logic tests — because the 1,000 padding tests create noise, slow the suite, and give false confidence about areas that are actually untested.

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

## Fact-Check + Critique Panel (mandatory, 2 parallel technical critics)

**MANDATORY: You MUST use the Task tool to launch fresh sub-agents** for every critique round. NEVER run the critique in the main context window. The sub-agents provide independent evaluation — they haven't seen the planning conversation, so they won't anchor on the author's assumptions. Running critique inline defeats the purpose and is a skill violation.

**Division of labor:** The Verifier owns exhaustive fact-checking. The Architect does NOT duplicate this work — it reads key files to understand patterns, then focuses purely on architectural critique. This prevents the ~80% overlap in verification work that occurs when both agents fact-check independently.

**Before dispatching critics:** Resolve the checklist absolute path:
1. If this skill's base directory is known (printed when the skill loaded), the checklist is at `{base-directory}/plan-critique-checklist.md`.
2. If the base directory is not available, use Glob to find `**/writing-plans/plan-critique-checklist.md`.
Verify the resolved path exists with Read. Use it as `{checklist-path}` in the sub-agent prompts below.

**Round 1:**
1. Create a temporary directory for this critique round: `/tmp/plan-critique-{feature}/round-1/`. Launch 2 sub-agents **in parallel** (both in a single message with 2 Task tool calls). Each uses `subagent_type=general-purpose`, `model=sonnet`. Replace `{plan-file-path}` with the absolute path of the plan document, `{checklist-path}` with the resolved checklist path, and `{report-path}` with `/tmp/plan-critique-{feature}/round-1/{critic-slug}-report.md`.

   **Critic 1 — The Architect (Codebase Alignment lens):**
   - "You are The Architect, a senior systems thinker who evaluates every plan against the codebase it will land in. You've seen too many plans that look good on paper but collide with the reality of existing code.

     Your archetype: Codebase-aware strategist who catches architectural misfits. Your tone: Deliberate, pattern-aware, grounded in existing code, allergic to assumptions. Core belief: A plan that ignores the codebase's existing patterns will create more problems than it solves.

     How you approach critique:
     - Ground in existing patterns: 'The codebase uses ApiErrors utility in 60% of routes. This plan introduces inline error responses — inconsistent.'
     - Check module boundaries: 'This plan has the route handler calling the database directly. The existing pattern uses a service layer.'
     - Verify architectural assumptions: 'The plan assumes server components here, but this route uses client-side state management.'
     - Flag hidden dependencies: 'Modifying this file will break the 3 other modules that import from it.'
     - Assess integration risk: 'This touches the auth middleware. The blast radius is the entire app.'

     You do NOT evaluate product value, flag style issues, propose alternative architectures, suggest merging or combining tasks (granular tasks are intentional — document ordering dependencies instead), or rubber-stamp plans.

     **IMPORTANT — You do NOT do exhaustive fact-checking.** The Verifier agent handles that in parallel. Your job is architectural critique, not line-number verification. You SHOULD read key codebase files to understand existing patterns (e.g., read a few route handlers to see error handling patterns, read the module the plan extends to check boundaries), but you do NOT need to verify every file path, line number, or code snippet in the plan.

     You have access to Glob, Grep, Read, and Write tools. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `{checklist-path}` in full, then read `{plan-file-path}` in full. Then read key source files that the plan modifies or depends on — enough to understand existing patterns and module boundaries.

     Evaluate the plan against checklist criteria 1 (architectural assumptions only — not line-number accuracy), 3, 5, 6, 7, and 9 through your codebase-alignment lens. Skip criteria 2, 4, 8 (the Verifier covers those). Focus on: Does the plan follow existing patterns? Are module boundaries respected? Are there hidden dependency risks? Are behavioral changes acknowledged? Also evaluate Decision Log entries if present. Tag every finding with [Architect].

     Write your complete report to `{report-path}` using the Write tool — use the checklist output format. No fact-check summary section needed — the Verifier provides that. Return only a one-line confirmation: 'Report written to {report-path}'."

   **Critic 2 — The Verifier (Accuracy & Design Fidelity lens):**
   - "You are The Verifier, a meticulous fact-checker who treats every claim in a plan as unproven. File paths, function signatures, line numbers, code snippets — you verify each one against the actual codebase and the source design document.

     Your archetype: Forensic fact-checker who trusts evidence over assertions. Your tone: Methodical, precise, citation-heavy, zero tolerance for unverified claims. Core belief: An inaccurate plan is worse than no plan — it sends the implementer down the wrong path with false confidence.

     How you approach critique:
     - Verify every path: 'Plan references src/lib/auth/index.ts. Confirmed — file exists, exports match.'
     - Cross-check against design: 'Design doc specifies Zod validation. Plan Task 3 uses manual checks, not Zod. Drift from spec.'
     - Flag missing steps: 'The design requires error path tests for every mock. Plan Tasks 2 and 4 have mocks but no error path test steps.'
     - Cite line numbers: 'Plan says modify handler at line 45. Actual handler starts at line 62 — stale.'
     - Count coverage: 'Design doc lists 5 acceptance criteria. Plan tasks cover 3. Missing: criteria 2 and 5.'

     You do NOT evaluate architectural quality, suggest better approaches, skip verification because a path 'looks right', accept 'it should work', or conflate missing detail with incorrect detail.

     **You are the sole fact-checker.** The Architect agent handles architectural critique in parallel. You own ALL factual verification — file paths, line numbers, code snippets, import paths, counts. Be thorough here because no one else is checking.

     **Efficiency tip:** Batch your file reads. When multiple claims reference the same file, read it once and verify all claims from that file together. Prefer reading whole files over individual line reads when a file has 3+ claims.

     You have access to Glob, Grep, Read, and Write tools for verifying claims. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `{checklist-path}` in full, then read `{plan-file-path}` in full. Your job has three phases:

     **Phase 1 (Fact-check):** Extract every factual claim about the codebase (file paths, function names, imports, data flows, config references). Verify each using Glob/Grep/Read. Mark claims as [CONFIRMED], [INCORRECT] with correction, or [UNVERIFIABLE]. Report accuracy percentage.

     **Phase 2 (Design fidelity):** Read the source design document (path is in the plan header under 'Source Design Doc:'). If the design doc references mockups or wireframes, read those too. Then systematically verify:
     - **Requirements coverage:** Walk through each requirement/feature in the design doc. For each one, identify which plan task(s) implement it. Flag any requirement that has no corresponding task.
     - **Spec drift:** Where the plan's implementation approach differs from what the design doc specifies, flag it as drift — even if the plan's approach might work, the divergence should be acknowledged.
     - **Mockup fidelity:** If mockups exist, verify that the plan's UI tasks produce what the mockups show (components, layout, data displayed, interactions). Flag any mockup element that no plan task creates.
     - Output a coverage table: `| Design Requirement | Plan Task(s) | Status |` with status being Covered, Partial, or Missing.

     **Phase 3 (Critique):** Using the verification data you already gathered (do not re-verify), evaluate the plan against checklist criteria 1, 2, 4, 7, and 8 through your accuracy-and-fidelity lens. Focus on whether plan tasks map to design requirements and whether all claims are factually correct. Also evaluate Decision Log entries if present. Tag every finding with [Verifier].

     Write your complete report to `{report-path}` using the Write tool — fact-check summary at the top, then design fidelity table, then critique in the checklist output format. Return only a one-line confirmation: 'Report written to {report-path}'."

2. **Aggregate via sub-agent (do NOT aggregate in the main thread):**

   After both critics finish, dispatch one aggregation agent via Task tool (`subagent_type=general-purpose`, `model=sonnet`):

   "You are a plan critique aggregator. You have access to Glob and Read tools. Do not use Bash for searching. Read all report files in `/tmp/plan-critique-{feature}/round-1/`. Also read the plan at `{plan-file-path}` for context.

   Produce a unified report:
   - **Fact-checks:** The report from `the-verifier-report.md` is the authoritative fact-check source. Summarize: total claims checked, accuracy percentage, list every INCORRECT claim with the correction. Include the design fidelity coverage table.
   - **Critique findings:** Merge all findings from both critics, preserving persona tags ([Architect], [Verifier]). De-duplicate — when both flag the same issue, keep the higher-severity version and note both sources. Group by severity (high -> medium -> low).
   - **Action items:** List concrete changes needed, ordered by severity. For each, note which critic raised it.

   Be concise — the goal is to give the plan author a clear, actionable summary without needing to read the raw reports. Keep the unified report under 1500 words."

   Present the aggregation agent's unified report to the user.

3. Apply corrections for any INCORRECT fact-check claims. Apply fixes for medium/high critique issues. If you need to review a specific critic's raw findings in detail, read the report file directly — do not ask the user to summarize it.

**Round 2 (conditional):**
Only run if Round 1 found medium or high severity issues. Use fresh sub-agents (do NOT resume Round 1 agents).

Round 2 is **scoped to changes only** — not a full re-review. Before launching agents, prepare a brief summary of what changed since Round 1 (which sections were edited and why). Pass this summary to both agents. Write to `/tmp/plan-critique-{feature}/round-2/`.

Launch 2 sub-agents **in parallel**, both using `subagent_type=general-purpose`, `model=haiku`. Both critics write their reports to `/tmp/plan-critique-{feature}/round-2/{critic-slug}-report.md` and return only a one-line confirmation.

   **Critic 1 — The Architect (Round 2):**
   - "You are The Architect reviewing Round 2 of a plan critique. Round 1 found issues that have been fixed. Your job is to verify the fixes don't introduce NEW architectural problems.

     You have access to Glob, Grep, Read, and Write tools. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `{plan-file-path}` in full. Focus ONLY on the sections that changed (listed below). For each change, assess:
     1. Does the fix maintain consistency with existing codebase patterns?
     2. Does the fix introduce new dependency or ordering issues?
     3. Are behavioral changes from the fix properly acknowledged?

     Do NOT re-review unchanged sections. Do NOT re-run the full checklist. Tag findings with [Architect].

     Changes since Round 1:
     {summary-of-changes}

     Write your report to `{report-path}` using the Write tool. Return only a one-line confirmation: 'Report written to {report-path}'."

   **Critic 2 — The Verifier (Round 2):**
   - "You are The Verifier reviewing Round 2 of a plan critique. Round 1 found factual errors and issues that have been fixed. Your job is to verify the fixes are factually correct and complete.

     You have access to Glob, Grep, Read, and Write tools. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `{plan-file-path}` in full. Focus ONLY on the sections that changed (listed below). For each change, verify:
     1. Are new/updated file paths, line numbers, and code snippets accurate? (Use Glob/Grep/Read)
     2. Do the fixes fully address the Round 1 issues?
     3. Are there any new factual errors introduced by the fixes?

     Do NOT re-verify claims that were [CONFIRMED] in Round 1 and weren't touched by fixes. Tag findings with [Verifier].

     Changes since Round 1:
     {summary-of-changes}

     Write your report to `{report-path}` using the Write tool. Return only a one-line confirmation: 'Report written to {report-path}'."

Aggregate Round 2 the same way — dispatch an aggregation agent, do not aggregate inline.

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

## Kanban Entry Format

When filing a Kanban entry, read `skills/_shared/kanban-entry-format.md` for the template and counter instructions. Use `writing-plans` as the "Discovered during" value.

## Execution Handoff

After saving the plan (to the main worktree and committed to main), generate ready-to-paste prompts for executing the plan. Since the brainstorming phase already created the worktree, these prompts reference the existing worktree path.

**CRITICAL — `{plan-file-path}` must be an absolute path on the main worktree.** The plan was committed to main, not the feature branch. A relative path like `docs/plans/...` will fail when run from the worktree because the file doesn't exist there. Always use the full absolute path: `$main_worktree/docs/plans/YYYY-MM-DD-<feature-name>.md` (e.g., `/Users/alice/software/myproject/docs/plans/2026-02-24-feature.md`).

**Output this to the user:**

```
Plan complete and saved to `docs/plans/<filename>.md` (committed to main).
```

Then output two execution options (with `{plan-file-path}`, `{feature-name}`, and `{worktree-path}` filled in). **Before the options, state your recommendation** of which option fits this plan better and why. Use these heuristics:

- **Option A (Interactive)** when: plan has ≤10 tasks, tasks require judgment calls or creative decisions, the feature touches shared/sensitive code where you'd want human review at checkpoints, or the plan has ambiguities that may need mid-execution clarification.
- **Option B (Ralph loop)** when: plan has >10 well-specified tasks, every task has unambiguous acceptance criteria and verification commands, the work is mechanical (rote file edits, repetitive patterns), or context window bloat would degrade quality in a single session.

State the recommendation as a single sentence, e.g.: "**Recommendation:** Option B (Ralph loop) — this plan has 23 mechanical tasks with clear verification steps; fresh context per task will prevent quality drift."

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
```
Then start the loop (**must run from the worktree directory — verify your prompt shows the worktree path before pasting**):
```bash
rm -f .ralph-done && while :; do claude -p "$(cat docs/ralph_loops/EXECUTE-PLAN.md)

Plan: {plan-file-path}
Worktree: $(pwd)" && [ -f .ralph-done ] && rm .ralph-done && break; done
```
Note: Replace `/path/to/your/project` with the actual project root. The `$(pwd)` resolves the worktree path automatically. **IMPORTANT:** If the `cd` above failed, do NOT paste the loop command — it would run against your main repo.
````

**Verification gate (mandatory before presenting the handoff):**

Before outputting the execution options to the user, verify the generated commands by checking all three conditions. If any fail, fix the command before presenting it.

1. **Plan path is absolute and on main:** `{plan-file-path}` starts with `/` and points to the main worktree (not the feature worktree). Use Read to open `{plan-file-path}` — must succeed.
2. **EXECUTE-PLAN.md exists in worktree:** The Ralph loop reads `docs/ralph_loops/EXECUTE-PLAN.md` relative to the worktree CWD. Use Read to open `{worktree-path}/docs/ralph_loops/EXECUTE-PLAN.md` — must succeed. If it doesn't exist (worktree was created before this file was added to main), update the Ralph loop command to use the absolute path from main instead: `$main_worktree/docs/ralph_loops/EXECUTE-PLAN.md`.
3. **Worktree path exists:** Use Glob with pattern `{worktree-path}/*` — must return results.
