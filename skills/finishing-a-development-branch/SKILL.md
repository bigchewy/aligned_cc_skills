---
name: finishing-a-development-branch
description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup
---

# Finishing a Development Branch

## Overview

Guide completion of development work by presenting clear options and handling chosen workflow.

**Core principle:** Deployment audit → Verify tests → Verify build → Present options → Execute choice → Clean up.

**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."

## CRITICAL: Always Run From the Main Repo

**This skill MUST be run from the main repository directory, NOT from inside a worktree.**

Running from inside a worktree causes cascading failures:
- `git add` for KB entries fails (files are in main repo, not worktree)
- Worktree cleanup destroys the session CWD
- `git mv` for plan archival operates on wrong git index
- Test runners may pick up duplicate test files from other worktrees

**Step 0 (before anything else):** Verify CWD is the main repo, not a worktree.

```bash
pwd
git rev-parse --show-toplevel
```

If CWD is inside a worktree, **stop and ask the user to restart from the main repo.** All subsequent steps assume CWD is the main repo. Use the worktree path only for reading files or running tests against the branch — never `cd` into it.

When the user invokes this skill, they should specify which branch/worktree to finish. Example:
```
/finishing-a-development-branch for feature/content-pipeline-phase2 at .worktrees/content-pipeline-phase2
```

## The Process

### Step 0: Deployment Platform Audit

**Before running tests, check for deployment pitfalls that tests cannot catch.**

Read `CLAUDE.md` to determine the deployment platform. If the platform is Vercel (or not specified — Vercel is the default), load the Vercel section of the deployment pitfall catalog. If the platform is not Vercel, skip Vercel-specific checks but still run framework-agnostic checks (file system access, environment variables, dynamic requires).

Load `references/deployment-pitfall-catalog.md` for detection patterns and false-positive rules.

**Run these searches in parallel across `src/` (excluding `__tests__/` directories):**

1. **File System Access (CRITICAL)**
   - Grep for `__dirname` and `__filename`
   - Grep for `readFileSync` and `readFile` — check if paths use `__dirname` or dynamic variables
2. **Environment Variables (CRITICAL)**
   - Grep for `process\.env\[` (bracket access that defeats inlining)
3. **Dynamic Requires (CRITICAL)**
   - Grep for `require(` with template literals or string concatenation
4. **Module-Level Mutable State (HIGH)** — only in files changed on this branch
   - Run `git diff --name-only <base-branch>...HEAD` to get changed files
   - In those files only, check for `new Map()`, `new Set()`, mutable `let` at module level
   - Skip static read-only caches and TTL-bounded caches (see catalog for classification rules)
5. **Native Dependencies (HIGH)**
   - Check `package.json` for `sharp`, `canvas`, `bcrypt`, `better-sqlite3`, `puppeteer`, `playwright`

**For each match:** Read surrounding code and apply the false-positive rules from the catalog. Classify as true positive or false positive.

**Report findings:**

```
## Deployment Platform Audit

### Summary
- CRITICAL: N findings
- HIGH: N findings

### [Severity] Findings
#### [ID] Description
- **File:** path:line
- **Risk:** Why this breaks in production
- **Fix:** What to change

### Clean Categories
- [List categories with no findings]
```

**If CRITICAL findings exist:**
```
CRITICAL deployment issues found. These will fail silently in production.
Must fix before proceeding.
```
Stop. Don't proceed to Step 1.

**If only HIGH or lower:** Show findings as warnings, continue to Step 1.

**If no findings:** Report clean, continue to Step 1.

**Scope:** The default audit runs CRITICAL + HIGH checks. MEDIUM and LOW categories (timeouts, edge runtime, writable filesystem) are documented in the catalog for manual review but not checked automatically.

### Step 1: Verify Tests

**Run the project's test suite:**

```bash
# Run the project's test command
```

**If tests fail:**
```
Tests failing (<N> failures). Must fix before completing:

[Show failures]

Cannot proceed with merge/PR until tests pass.
```

Stop. Don't proceed to Step 2.

**If tests pass:** Continue to Step 1a.

### Step 1a: Verify Build

**Run the production build to catch issues that tests miss.**

Different test runners and bundlers use different module resolution. Imports that work in tests can fail in the build (e.g., default vs named exports, missing type declarations). The only way to catch these is to run the actual build.

```bash
# Run the project's build command
```

**If build fails:**
```
Build failing. Must fix before completing:

[Show error]

Cannot proceed with merge/PR until build passes.
```

Stop. Don't proceed to Step 1b.

**If build passes:** Continue to Step 1b.

### Step 1b: LLM Eval (auto-run if surface changed)

**After tests pass, check if LLM behavior surface files were changed on this branch.**

```bash
git diff --name-only <base-branch>...HEAD
```

Check if any changed files match the LLM behavior surface patterns defined in the project's eval configuration (e.g., `e2e/eval-config.ts`) under `llmSurfacePatterns`. Common patterns: advisor prompts, framework prompts, prompt builders, personalization logic.

**If surface files changed:** Auto-run scoped eval scenarios:

```bash
# Run the project's eval command
```

**Blocking behavior by result level:**
- **fail** (exit code 1) — hard stop, same as a failing test. Show the scorecard. Run the `/aligned:eval-failure-triage` skill to classify failures and apply targeted fixes. Cannot proceed to Step 2 until failures are resolved.
- **warn** (warnings in output but exit 0) — continue to Step 2 with warning shown. Does not block.
- **pass** (clean exit 0) — continue silently.

**If no surface files changed:** Skip silently, continue to Step 2.

### Step 1c: Architecture Doc Update

**After all verification passes, check if the work changed system architecture.**

Compare the branch changes against architecture-relevant patterns:

```bash
git diff --name-only <base-branch>...HEAD
```

If changed files include any of: architecture-relevant paths as defined in the project's `CLAUDE.md` or detected from framework conventions (e.g., `src/app/api/` for Next.js, `src/routes/` for SvelteKit, `app/` for Rails), new pages, new lib modules, database schema changes, new hooks, or new external service integrations — the architecture doc likely needs updating.

**If architecture-relevant changes detected:**

1. Read `docs/architecture.md` (or the project's equivalent)
2. **Verify diagrams affected by this branch** — architecture docs may be stale. For the specific diagrams you're updating, check if they accurately reflect the current code (not just your changes). The actual source files are always the source of truth. If you find discrepancies in the diagrams you're editing, file bugs (see "Bug Board Entry Format" below) with category `architecture-discrepancy`. Do NOT audit unrelated diagrams.
3. Update the affected diagrams to reflect the new state
4. Commit the update (including any bug board entries) to the feature branch before proceeding

**If no architecture-relevant changes:** Skip silently, continue to Step 1d.

### Step 1d: Code Simplification Scan

**After all verification and doc updates, scan branch changes for simplification opportunities.**

This step is **non-blocking** — findings are filed to the Kanban board as improvement opportunities, but never prevent merge/PR.

**Spawn the `code-simplifier` agent** via the Task tool:

```
subagent_type: "code-simplifier"
prompt: "Analyze the branch changes for simplification opportunities.
  Base branch: <base-branch>
  Working directory: <project-root>"
```

**If the agent returns findings** (non-empty JSON array):

1. Read `docs/kanban/.counter` for the next KB number (pad to 3 digits)
2. For each finding:
   a. Derive a kebab-case slug from the title (max 50 chars)
   b. Write `docs/kanban/todo/KB-NNN-slug.md`:

```markdown
# KB-NNN: [finding title]

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `[file]:[line_range]`
- **Observed:** [finding observed]
- **Expected:** [finding suggestion]
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** [finding severity]
- **Created:** [today's date]
```

   c. Increment the KB number
3. Write the final incremented number back to `docs/kanban/.counter`
4. Commit the Kanban entries to the main repo.

**Report to user:**
```
Code simplification scan: N opportunities filed to Kanban board.
```

**If the agent returns no findings:** Report silently:
```
Code simplification scan: clean.
```

Continue to Step 2.

### Step 2: Determine Base Branch

Try `main` first, then fall back to `master`. Run each command separately (do NOT combine with `||`):

```bash
git merge-base HEAD main
```

If that fails:

```bash
git merge-base HEAD master
```

Or ask: "This branch split from main - is that correct?"

### Step 3: Present Options

Present exactly these 4 options:

```
Implementation complete. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work

Which option?
```

**Don't add explanation** - keep options concise.

### Step 4: Execute Choice

#### Option 1: Merge Locally

**If working in a worktree**, use `git -C <main-repo-path>` for all commands since checkout isn't possible from a worktree of the same repo:

Run each command separately (do NOT chain with `&&`):

```bash
git -C <main-repo-path> checkout <base-branch>
```

```bash
git -C <main-repo-path> pull
```

```bash
git -C <main-repo-path> merge <feature-branch>
```

Verify tests on merged result — `cd` first, then run tests as a separate command:

```bash
cd <main-repo-path>
```

```bash
<test command>
```

Cleanup: cd out of worktree first, THEN remove it, THEN delete branch (Step 5 handles this).

**If NOT in a worktree:**

```bash
git checkout <base-branch>
git pull
git merge <feature-branch>
<test command>
git branch -d <feature-branch>
```

Then: Cleanup worktree (Step 5)

#### Option 2: Push and Create PR

```bash
git push -u origin <feature-branch>
```

Then create the PR. Do NOT use heredoc syntax — pass the body as a quoted string:

```bash
gh pr create --title "<title>" --body "## Summary
<2-3 bullets of what changed>

## Test Plan
- [ ] <verification steps>"
```

Then: Cleanup worktree (Step 5)

#### Option 3: Keep As-Is

Report: "Keeping branch <name>. Worktree preserved at <path>."

**Don't cleanup worktree.**

#### Option 4: Discard

**Confirm first:**
```
This will permanently delete:
- Branch <name>
- All commits: <commit-list>
- Worktree at <path>

Type 'discard' to confirm.
```

Wait for exact confirmation.

If confirmed:
```bash
git checkout <base-branch>
git branch -D <feature-branch>
```

Then: Cleanup worktree (Step 5)

### Step 5: Cleanup Worktree

**For Options 1, 2, 4:**

Check if in worktree by running each command separately (do NOT pipe):

```bash
git worktree list
```

```bash
git branch --show-current
```

Compare the outputs to determine if the current branch corresponds to a worktree.

If yes — **CWD safety is critical.** If the shell is inside the worktree, removing it will invalidate the CWD and break ALL subsequent commands irreversibly. `git -C` is NOT a substitute for `cd` — it only changes git's context, not the shell's CWD.

**Step 5a: Verify CWD is safe** (run as its own command):
```bash
cd <main-repo-path> && pwd
```
Confirm `pwd` output shows the main repo path, NOT the worktree path. Do NOT proceed until this succeeds.

**Step 5b: Remove worktree** (separate command):
```bash
git worktree remove <worktree-path> --force
```

**Step 5c: Delete branch** (separate command):
```bash
git branch -d <feature-branch>
```

**The order is non-negotiable:** cd out (5a) → verify pwd (5a) → remove worktree (5b) → delete branch (5c). Skipping 5a or using `git -C` instead causes an unrecoverable cascade of shell failures.

**For Option 3:** Keep worktree.

### Step 6: Archive Plan Documents

**For Options 1 and 2 only.** After merge and cleanup, move completed plan and design documents to `docs/plans/completed/`.

1. **Check if applicable:** If `docs/plans/` does not exist in the project, skip silently.

2. **Identify plan files:** Scan `docs/plans/*.md` (top-level only, not `completed/`) for files associated with this work. Match by:
   - Branch name pattern (e.g., branch `feat/repo-agnostic-skills` matches `*repo-agnostic*`)
   - Files referenced in the conversation when the skill was invoked (the user typically names the plan)
   - If ambiguous, list the candidates and ask the user which to archive

3. **Include companion docs:** For each plan file found, also check for associated design documents with the same date prefix and topic.

4. **Move to completed:**

   **Before each `git mv`, verify the file is tracked** — untracked files (created but never committed) cannot be `git mv`'d. Use `git ls-files <path>` to check. For untracked files, use plain `mv` (or `rm` if they should be discarded).

   ```bash
   mkdir -p docs/plans/completed
   git mv docs/plans/<plan-file>.md docs/plans/completed/
   git mv docs/plans/<design-file>.md docs/plans/completed/  # if exists
   ```

5. **Commit the archival:**
   ```bash
   git commit -m "chore: archive completed plan docs to docs/plans/completed/"
   ```

**If no plan files found:** Report: "No plan documents found to archive." and continue.

## Quick Reference

| Step | Action | Blocks on failure? |
|------|--------|--------------------|
| 0. Deployment audit | Scan for deployment pitfalls | CRITICAL: yes, HIGH: no |
| 1. Verify tests | Run test suite | Yes |
| 1a. Verify build | Run build command | Yes |
| 1b. LLM eval | Run eval command if surface changed | Yes (fail), No (warn/pass) |
| 1c. Architecture doc | Update `docs/architecture.md` if structure changed | No |
| 1d. Simplification scan | Spawn code-simplifier agent, file Kanban entries | No |
| 2. Base branch | Determine merge target | No |
| 3. Present options | Show 4 choices | No |
| 4. Execute | Run chosen workflow | N/A |
| 5. Cleanup | Remove worktree if applicable | N/A |
| 6. Archive plans | Move plan/design docs to completed/ | No |

| Option | Merge | Push | Keep Worktree | Cleanup Branch | Archive Plans |
|--------|-------|------|---------------|----------------|---------------|
| 1. Merge locally | yes | - | - | yes | yes |
| 2. Create PR | - | yes | yes | - | - |
| 3. Keep as-is | - | - | yes | - | - |
| 4. Discard | - | - | - | yes (force) | - |

## Common Mistakes

**Skipping deployment audit**
- **Problem:** Deploy code that breaks silently in production
- **Fix:** Always run Step 0 before tests — tests can't catch deployment pitfalls

**Skipping test verification**
- **Problem:** Merge broken code, create failing PR
- **Fix:** Always verify tests before offering options

**Skipping build verification**
- **Problem:** Tests pass but deploy fails — different module resolution between test runners and bundlers
- **Fix:** Always run the build command after tests pass

**Open-ended questions**
- **Problem:** "What should I do next?" — ambiguous
- **Fix:** Present exactly 4 structured options

**Removing worktree while shell CWD is inside it**
- **Problem:** `git worktree remove` deletes the directory the shell is in, invalidating CWD. Every subsequent command fails with "No such file or directory", causing an unrecoverable cascade. Using `git -C <main-repo>` does NOT help — `-C` only changes git's context, the shell's CWD is still invalid.
- **Fix:** Always run `cd <main-repo-path> && pwd` as a separate command FIRST. Verify `pwd` shows the main repo. Only then run `git worktree remove`.

**Automatic worktree cleanup**
- **Problem:** Remove worktree when might need it (Option 2, 3)
- **Fix:** Only cleanup for Options 1 and 4

**No confirmation for discard**
- **Problem:** Accidentally delete work
- **Fix:** Require typed "discard" confirmation

## Red Flags

**Never:**
- Proceed with CRITICAL deployment findings
- Proceed with failing tests
- Merge without verifying tests on result
- Delete work without confirmation
- Force-push without explicit request

**Always:**
- Run deployment audit before tests
- Verify tests before offering options
- Verify build passes before offering options
- Present exactly 4 options
- Get typed confirmation for Option 4
- Clean up worktree for Options 1 & 4 only

## Lessons-Learned Gate

BEFORE completing this skill's process:
  IF the deployment audit or build caught an issue that tests missed:
    Write a lesson to docs/lessons-learned/YYYY-MM-DD-short-description.md
    using the lesson template (see kickstart scaffold docs).

## Kanban Entry Format

When filing an entry to the Kanban board:

1. Read `docs/kanban/.counter` for the next KB number (pad to 3 digits)
2. Derive a kebab-case slug from the title (max 50 chars)
3. Write `docs/kanban/todo/KB-NNN-slug.md`:

```markdown
# KB-NNN: [Title]

- **Type:** bug
- **Discovered during:** finishing-a-development-branch
- **Location:** `[file path]:[line range]`
- **Observed:** [What exists and why it's a problem]
- **Expected:** [What should change]
- **Why out of scope:** [Why it wasn't fixed when discovered]
- **Severity:** LOW | MEDIUM | HIGH
- **Created:** [today's date]
```

4. Write the incremented number back to `docs/kanban/.counter`

## Integration

**Called by:**
- **executing-plans** (Step 6) - After all tasks complete
- **autopilot** (Phase 6) - After pipeline completes

**Pairs with:**
- **using-git-worktrees** - Cleans up worktree created by that skill
