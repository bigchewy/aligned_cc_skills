---
name: writing-plans
description: "Produces TDD implementation plans from specs or design docs, with parallel sub-agent critique and architectural review. Use when requirements are defined and the next step is a concrete, task-by-task build plan."
---

# Writing Plans

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/writing-plans/`. See `skills/_shared/resolve-skill-path.md` for rationale.

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

**Plans MUST always be written to the main worktree directory and committed to `main`.** This prevents plan files from being lost if a feature branch is discarded, abandoned, or never merged. All plan writes are centralized in this skill — no other skill mutates the plan file.

**Before writing the plan file, determine the main worktree path:**

```bash
git worktree list
```

Parse the output to extract the path from the first line (text before the first space). Store this as `main_worktree`. Do NOT use piped commands (`| head | awk`) — run the single command and parse the output.

**Cross-repo guard:** Before writing, verify the plan belongs in this repo. Compare `$main_worktree` against the plan's target working directory (from the user's request, spec, or design doc). If the work targets a different repo (e.g., you're in `~/software/project-a` but the plan's tasks modify files in `~/software/project-b`), **STOP.** Tell the user:

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

**If running in a worktree, merge main forward so the plan is available there:**

```bash
git -C "$worktree_path" merge main --no-edit
```

The worktree was typically created before writing-plans ran, so its branch doesn't have the plan commit. This merge brings the plan file into the worktree's working tree, where EXECUTE-PLAN.md needs to read it, mark tasks with ✅, and commit those updates. Skip this step if no worktree exists (plan was written directly on main).

### Chunked Writing for Large Plans

The Write tool has a content size limit (~32K tokens). Plans with >15 tasks and full code snippets will often exceed this. When writing a large plan:

1. **Write the first chunk** via Write tool — header through approximately Task 8-10 (aim for well under the limit)
2. **Append remaining tasks** via successive Edit calls — set `old_string` to the last task heading and its first line (e.g., `### Task 10: Component Name\n\n**Files:**`), and `new_string` to that same text plus the next batch of tasks after it. Use a full task heading as the match target — it will be unique in the document. Do not match on generic lines like `---` or blank lines.
3. **Append the Decision Log last** — it's always the final section

If you hit a Write tool size error, do not retry the same content. Split it in half and use the chunked approach above.

## Before Writing

Explore the codebase before writing any plan:
1. Read the spec/requirements document or design
2. **Read architecture docs:** If the project has `docs/architecture.md` (or equivalent), read it to understand data flows, module dependencies, and existing patterns before exploring code. This orients the plan around the actual system structure. **Caveat:** Architecture docs may be stale — always verify against actual source files in subsequent steps. If you find a discrepancy, file a bug (see the Kanban Entry Format section below).
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

**Enforcement:** The Verifier critic checks for mid-plan autonomy violations during the Fact-Check + Critique Panel. See `plan-critique-checklist.md` Criterion 10's "Autonomy violations" row + the `Autonomy violations — signal list` subsection, and the Round 1 Verifier prompt's Phase 3 in `references/critique-panel-prompts.md`. HIGH severity violations must be resolved (relocate to Prerequisites or Post-Automation) before the plan ships.

## Anti-Pattern: Mid-Flow Human Review (BANNED)

**The autopilot's whole value is unattended completion.** The user reviews ONCE, at the end. Plan tasks that ask for user *judgment* mid-pipeline defeat that proposition — even when framed as "verification," "confirmation," or "review."

This is distinct from the Manual Steps Policy above. That policy governs *execution* the user must perform (Prerequisites, Post-Automation). This ban governs *judgment* the plan author wanted the user to provide between tasks. Different framing — same effect: the loop halts or improvises.

### Banned task body patterns

writing-plans MUST NOT produce plan tasks containing language like:

| Pattern | Why banned |
|---|---|
| "Get user feedback on X before proceeding" | Pipeline doesn't pause for feedback |
| "Have the user verify the UI looks correct" | Mockup fidelity loop is the machine check; user reviews at end |
| "Pause and ask if X is acceptable" | No human present to ask |
| "Review the interface before continuing to Task N+1" | User reviews when autopilot completes |
| "Confirm with user before proceeding" | No conversational surface; loop halts or guesses |
| "Show user the [output/screenshot/result] and wait" | Headless `claude -p` cannot wait for human input |
| "User signs off on the design before implementation" | Sign-off happened during brainstorming; not a plan task |
| "STOP and surface to the user" / "STOP, the cleanup should not proceed" | Mid-task halt sentinel; loop is unattended by contract |
| "Halt the autopilot" / "Halt the loop" / "Halting loop." | Authors the loop's own halt — the very contract violation |
| "Write `.ralph-human-blocked`" / "touch `.ralph-human-blocked`" | Halt sentinel deleted in May 2026; reintroducing it is forbidden |
| "Decision needed from the user" / "User must choose between A/B/C" | Mid-pipeline choice ≡ mid-pipeline halt |

The pattern is "task body asks for *judgment* mid-pipeline." NOT banned: machine checks (mockup fidelity, eval scoring, verify gate are all machine-judged).

### What's allowed

- **Prerequisites (before Task 1)** — execution work the user does to unblock autopilot.
- **Manual Steps (Post-Automation)** — execution work the user does after autopilot completes.
- **Halt-with-reason (`.autopilot-halt`)** — environment failures the *non-LLM phase scripts* (preflight, worktree, verify) cannot resolve. Phase scripts emit halts via `write_halt`; plan task bodies must never instruct the LLM to do this.
- **BLOCKED retry (`🔄`)** — task bodies MAY tell the LLM to mark a task `🔄 BLOCKED` and exit when it can't proceed. The wrapper retries, then auto-skips after `MAX_BLOCKED_ITERATIONS` (default 3) consecutive blocks. This is the correct way to say "this task might not always succeed."
- **End-of-autopilot review** — the user reviews everything at the end.

### Enforcement

The Verifier critic flags any task body containing "human review", "user verifies", "review the [UI/interface/mockup/output]", "wait for user", "confirm with user", "before proceeding ask", "user signs off", "get user approval", "STOP and surface", "halt the autopilot", "halt the loop", "halting loop", ".ralph-human-blocked", "decision needed from the user", or semantically equivalent language as HIGH severity. Suggested fix: relocate to Manual Steps (Post-Automation) if it's real verification work; replace with `🔄 BLOCKED` retry if it's a runtime "might not succeed" case; remove if it's a gratuitous gate.

Exemption: Prerequisites, Manual Steps (Post-Automation), and Decision Log sections — these sections are explicitly user-facing and not part of the autopilot's task flow. Task bodies are not exempt regardless of where in the plan they sit.

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
- Modify: `exact/path/to/existing.py` (the `handle_request` function)
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

## Test Command Rules

When writing test steps in a task body, always specify the exact test file path. Never write a bare test runner invocation without a file path.

**Required pattern:**

```bash
# Jest / Next.js
npm test -- path/to/foo.test.ts
# or: npx jest path/to/foo.test.ts

# Vitest
npx vitest run path/to/foo.test.ts

# pytest
pytest tests/path/test_foo.py::test_name -v
```

**Never write:**

```bash
npm test          # runs the full suite — belongs in Phase 9, not task bodies
npx jest          # same — no file path = full suite
vitest run        # same
pytest            # same
npm run build     # full production build — Phase 9 only; spawns 8–10 webpack workers (catastrophic RAM)
next build        # same
tsc               # whole-project typecheck — Phase 9 only
npm run lint      # whole-codebase lint — Phase 9 only
eslint .          # same
```

A task should be verifiable by running only the test files it creates or modifies. If proving the task correct requires the full suite, the task is too large — split it.

The full suite runs in Phase 9 (verify). Not in task bodies.

**Do not create a "final verification" task.** A task whose entire purpose is running the full test suite, building the project, or linting the codebase is not a plan task — it is Phase 9. Tasks named "Final full-suite verification", "End-to-end verification", "Full build check", or any equivalent are a category error. Phase 9 (the verify phase that runs after the ralph loop) already runs `npm test`, `npm run build`, and lint. Duplicating this inside the plan causes the full build to run twice and crashes the system under memory pressure.

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

  Reference: skills/_shared/testing-anti-patterns.md
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

## Plan Manifest (autonomous authoring)

After the plan body is drafted and verified, generate a YAML front-matter manifest declaring the executor environment requirements. Schema and validation rules: `skills/_shared/plan-manifest-format.md`.

**Procedure:**

1. Scan the plan body for `mcp__*__*` references using a regex that skips fenced code blocks (``` ``` ```) with language tags `text` / `markdown` / `yaml`, blockquotes (`> ...`), and ``inline code`` spans. Collect the unique tool strings.
2. Prepend the manifest as YAML front-matter at the very top of the plan file (before the `# <Title>` heading). Format per `plan-manifest-format.md`.
3. If the MCP list is empty, prepend an empty front-matter block (`---\n---\n`) so preflight detects "manifest present, nothing to check" rather than "no manifest, skip preflight." (This signal is intentional — empty manifest = author confirmed no MCP requirements.)

**Visibility:** The manifest is written autonomously without user confirmation. The user reviews it as part of reading the committed plan. The Verifier critic catches mismatches between manifest and body.

**Idempotency:** Re-running the procedure on a plan with an existing manifest replaces it (do not append). Match the existing front-matter via `^---\n.*?\n---\n` (multiline) and substitute.

This step runs BEFORE the Manual Deploy Artifact Scan so both checks operate on a fully-authored plan.

## Manual Deploy Artifact Scan

**Purpose:** Detect files in the plan that require a manual production step (e.g., Supabase migrations). Auto-populate `## Manual Steps (Post-Automation)` so the user sees the obligation at plan time. The downstream `finishing-a-development-branch` skill re-surfaces this as a non-blocking notice at merge time.

**Run this step BEFORE the Fact-Check + Critique Panel.** In the current SKILL.md file, the `## Fact-Check + Critique Panel` section precedes `## Verification Gate` in document order; insert the new `## Manual Deploy Artifact Scan` section immediately before `## Fact-Check + Critique Panel` (which is the only reliable anchor). If the plan has no catalog match, the step still runs and emits the "no matches" message below.

**Catalog:** Read `skills/_shared/manual-deploy-artifact-catalog.md`. Each entry under `## CRITICAL — ...` is a class carrying a fenced ```` ```yaml ```` block with `detector_glob` / `detector_grep` and `severity`.

**Scan procedure:**

1. Build a file list from the plan body: every path after `Create:` or `Modify:` inside any task's `**Files:**` block.
2. For each path, apply the built-in non-prod exemption patterns (`**/seed/**`, `**/fixtures/**`, `**/__tests__/**`, `**/*.test.*`). Matches are exempt — do NOT produce a Post-Automation entry. Surface a single-line comment in the conversation output below: "Exempt (built-in pattern): <path>".
3. For each non-exempt path, match against every catalog entry's `detector_glob` / `detector_grep`. Bucket matches by artifact class.
4. If there are matches:
   - Ensure the plan has a `## Manual Steps (Post-Automation)` section; create one immediately after the final task if missing.
   - Under that section, for each matched class, inject a subsection `### <class-id> <class-name>` (e.g., `### M1 migrations`) if not already present.
   - Under the subsection, list each matched file as a bullet: `- \`<path>\` — <prod step from the catalog entry>`.

**Visible conversation output:**

After the scan completes, print ONE of the following blocks to the user (never silently inject):

If at least one catalog match was found:

```
Manual-deploy scan: detected N catalog matches.
- Added Post-Automation entries for:
  • M1 migrations (N): <up to 10 file paths, truncate with "+ N more">
- Exempt (built-in pattern match): <list or "none">
```

If no catalog matches were found:

```
Manual-deploy scan: no catalog matches detected.
```

Cap each class list at 10 entries; for overflow append a "+ N more" line.

**Idempotency:** The injection is structural (find-by-heading, append-list-item). Re-running the scan on a plan that already contains the expected entries MUST NOT duplicate them. Match existing entries by file-path string equality on each list item.

## Fact-Check + Critique Panel (mandatory, 2 parallel technical critics)

**MANDATORY: You MUST use the Task tool to launch fresh sub-agents** for every critique round. NEVER run the critique in the main context window. The sub-agents provide independent evaluation — they haven't seen the planning conversation, so they won't anchor on the author's assumptions. Running critique inline defeats the purpose and is a skill violation.

### ⛔ MANDATORY: Parallel dispatch — both critics in ONE assistant message

This applies to Round 1 AND Round 2. When launching the Architect and Verifier:

- **Both Task tool calls MUST appear in the same assistant message** — a single turn containing two `tool_use` blocks side-by-side.
- **Sequential dispatch is a skill violation.** Dispatching the Architect alone, waiting for it to return, then dispatching the Verifier in a follow-up turn — doubles wall-clock time and is the most common cause of plan-writing timeouts. It defeats the purpose of having two independent critics.
- **Self-check before sending:** If your next message contains exactly one Task tool call for a critic, STOP. Re-draft to include both critics' Task calls in the same message before sending.
- **Rationale:** Each critic spends 5–10 minutes reading the plan + design doc + checklist + source files. Running them in parallel costs the wall-clock of the slower one. Running them serially costs the sum.

**Division of labor:** The Verifier owns exhaustive fact-checking. The Architect does NOT duplicate this work — it reads key files to understand patterns, then focuses purely on architectural critique. This prevents the ~80% overlap in verification work that occurs when both agents fact-check independently.

**Before dispatching critics — resolve the checklist (MANDATORY):**
The checklist is at `{base-directory}/plan-critique-checklist.md`. Verify it exists with Read. **If the checklist cannot be found, STOP and tell the user — do not proceed with the critique panel without it.** Use the verified absolute path as `{checklist-path}` in the sub-agent prompts below.

**Round 1:**
1. Create a temporary directory for this critique round: `/tmp/plan-critique-{feature}/round-1/`. Launch the Architect and Verifier sub-agents — **both Task tool calls in the SAME assistant message** (see "Parallel dispatch" contract above; sequential dispatch is a skill violation). Each uses `subagent_type=general-purpose`, `model=sonnet`. Replace `{plan-file-path}` with the absolute path of the plan document, `{checklist-path}` with the resolved checklist path, and `{report-path}` with `/tmp/plan-critique-{feature}/round-1/{critic-slug}-report.md`.

   The prompt templates for both critics and the aggregator live at `{base-directory}/references/critique-panel-prompts.md`. Read that file and substitute `{plan-file-path}`, `{checklist-path}`, and `{report-path}` into each prompt before launching the sub-agent.

   **Critic 1 — The Architect (Codebase Alignment lens):** Use the section "Round 1: Architect prompt" from `references/critique-panel-prompts.md`.

   **Critic 2 — The Verifier (Accuracy & Design Fidelity lens):** Use the section "Round 1: Verifier prompt" from `references/critique-panel-prompts.md`.

2. **Aggregate via sub-agent (do NOT aggregate in the main thread):**

   After both critics finish, dispatch one aggregation agent via Task tool (`subagent_type=general-purpose`, `model=sonnet`) using the section "Round 1: Aggregation prompt" from `references/critique-panel-prompts.md`. Substitute `{plan-file-path}` before launching.

   Present the aggregation agent's unified report to the user.

3. Apply corrections for any INCORRECT fact-check claims. Apply fixes for medium/high critique issues. If you need to review a specific critic's raw findings in detail, read the report file directly — do not ask the user to summarize it.

**Round 2 (conditional):**
Only run if Round 1 found medium or high severity issues. Use fresh sub-agents (do NOT resume Round 1 agents).

Round 2 is **scoped to changes only** — not a full re-review. Before launching agents, prepare a brief summary of what changed since Round 1 (which sections were edited and why). Pass this summary to both agents. Write to `/tmp/plan-critique-{feature}/round-2/`.

Launch the Architect and Verifier sub-agents — **both Task tool calls in the SAME assistant message** (see "Parallel dispatch" contract above; sequential dispatch is a skill violation). Both use `subagent_type=general-purpose`, `model=haiku`. Both critics write their reports to `/tmp/plan-critique-{feature}/round-2/{critic-slug}-report.md` and return only a one-line confirmation. Substitute `{plan-file-path}`, `{report-path}`, and `{summary-of-changes}` into each prompt before launching.

   **Critic 1 — The Architect (Round 2):** Use the section "Round 2: Architect prompt" from `references/critique-panel-prompts.md`.

   **Critic 2 — The Verifier (Round 2):** Use the section "Round 2: Verifier prompt" from `references/critique-panel-prompts.md`.

Aggregate Round 2 the same way — dispatch an aggregation agent, do not aggregate inline.

If the plan changes system architecture (new routes, module restructuring, database schema changes), add a final task to update `docs/architecture.md` with the new state.

## Plan Critique

When critiquing an existing plan (instead of writing one), use the checklist at `{base-directory}/plan-critique-checklist.md`. Launch fresh sub-agents for critique rounds to ensure independent evaluation. Verify every claim against actual source code — don't trust line numbers, file paths, code snippets, or test counts without checking.

## Verification Gate

Before including any file path or code snippet in the plan, verify it exists in the codebase:
- **Glob** to confirm file paths exist (or confirm "Create" targets don't already exist)
- **Read** to verify code snippets are accurate
- **Grep** to confirm counts, imports, and usage patterns

**Use content anchors, not line numbers.** Line numbers go stale between plan writing and execution. Instead of `Modify: src/app/page.tsx:133-154`, write `Modify: src/app/page.tsx (the StageIndicator entries)`. Function names, section headers, component names, and variable names are stable anchors that survive edits to surrounding code.

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

When filing a Kanban entry, read `{base-directory}/../_shared/kanban-entry-format.md` for the template and counter instructions. Use `writing-plans` as the "Discovered during" value.

## Execution Handoff

**Resolve the plugin root path:** The Ralph loop script lives in this plugin's `scripts/autopilot/` directory. Derive the plugin root as two levels up from `{base-directory}`: `{base-directory}/../..` (i.e., strip `skills/writing-plans/`). Verify the resolved path exists by reading `{plugin-root}/scripts/autopilot/run-ralph.sh`. **If it cannot be found, STOP and tell the user.** Store as `{plugin-root}`.

After saving the plan (to the main worktree and committed to main), present execution options.

**Output this to the user:**

```
Plan complete and saved to `docs/plans/<filename>.md` (committed to main).
```

Then output two execution options (with `{plan-file-path}`, `{feature-name}`, and `{worktree-path}` filled in). **Before the options, state your recommendation** of which option fits this plan better and why. Use these heuristics:

- **Option A (Interactive)** when: plan has ≤10 tasks, tasks require judgment calls or creative decisions, the feature touches shared/sensitive code where you'd want human review at checkpoints, or the plan has ambiguities that may need mid-execution clarification.
- **Option B (Ralph loop)** when: plan has >10 well-specified tasks, every task has unambiguous acceptance criteria and verification commands, the work is mechanical (rote file edits, repetitive patterns), or context window bloat would degrade quality in a single session.

State the recommendation as a single sentence, e.g.: "**Recommendation:** Option B (Ralph loop) — this plan has 23 mechanical tasks with clear verification steps; fresh context per task will prevent quality drift."

The user-facing output templates for both options live at `{base-directory}/references/execution-handoff-templates.md`. Read that file and pick the section that matches:

- **Standard handoff (worktree path known):** Use when the worktree was created by a prior brainstorming session or is otherwise available. Substitute `{worktree-path}`, `{plan-file-path}`, `{feature-name}`, and `{plugin-root}`.
- **Worktree-not-created handoff (worktree path unknown):** Use when writing-plans was invoked without a prior worktree. Substitute `{feature-name}` and `{plugin-root}`.

Copy the selected template text into the conversation with the substitutions applied — do not present the unsubstituted placeholders to the user.

**Verification gate (mandatory before presenting the handoff):**

Before outputting the execution options, verify by checking all three conditions. If any fail, fix before presenting.

1. **Plan file exists on main:** Read `$main_worktree/docs/plans/YYYY-MM-DD-<feature-name>.md` — must succeed.
2. **run-ralph.sh exists:** Read `{plugin-root}/scripts/autopilot/run-ralph.sh` — must succeed.
3. **Worktree path exists:** Glob `{worktree-path}/*` — must return results.
