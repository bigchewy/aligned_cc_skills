---
name: finishing-a-development-branch
description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, deploy, or cleanup
---

# Finishing a Development Branch

## Overview

Guide completion of development work by presenting clear options and handling chosen workflow.

**Core principle:** Deployment audit → Verify tests → Verify build → Present options → Execute choice → Clean up → Archive plans.

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
4. Commit the Kanban entries. **If CWD is a worktree**, KB files are written to the main repo's `docs/kanban/` via absolute paths — use `git -C <main-repo-path> add` and `git -C <main-repo-path> commit` (not bare `git add` from the worktree). If CWD is the main repo, use bare `git add/commit` as normal.

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
2. Deploy to production + smoke test
3. Keep the branch as-is (I'll handle it later)
4. Discard this work

Which option?
```

**Don't add explanation** - keep options concise.

### Step 4: Execute Choice

#### Option 1: Merge Locally

Since we are always running from the main repo (see "CRITICAL" section above), merge commands run directly:

Run each command separately (do NOT chain with `&&`):

```bash
git checkout <base-branch>
```

```bash
git pull
```

```bash
git merge <feature-branch>
```

Verify tests on merged result:

```bash
<test command>
```

Then: Cleanup worktree (Step 5), then archive plan docs (Step 6).

#### Option 2: Deploy to Production + Smoke Test

**Parse scope:** If the user said "full smoke tests" or similar, set scope to FULL. Otherwise default to QUICK.

**Step 4a: Merge to main**

Same as Option 1's merge logic. Since CWD is the main repo:

```bash
git checkout <base-branch>
```

```bash
git pull
```

```bash
git merge <feature-branch>
```

**Step 4b: Push to remote**

```bash
git push origin <base-branch>
```

Record the push timestamp for deployment matching.

**Step 4c: Worktree cleanup**

Run Step 5 (Cleanup Worktree) now — since CWD is always the main repo, cleanup is safe.

**Step 4d: Wait for deployment**

First, read `.claude/deployment.json` from the project root. This file configures per-project deployment behavior:

```json
{
  "productionUrl": "https://example.vercel.app",
  "vercelMcpAccess": true,
  "deployWaitSeconds": 120,
  "smokeTestProfiles": ["playwright-full", "playwright-summaries"]
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `productionUrl` | (none) | URL to smoke test against |
| `vercelMcpAccess` | `true` | Whether Vercel MCP tools can access this project's deployments |
| `deployWaitSeconds` | `120` | Seconds to wait before smoke testing (Path B only) |
| `smokeTestProfiles` | `[]` | Playwright MCP profile names. Empty array = no auth, use headless |

**If `.claude/deployment.json` doesn't exist:** Create it interactively. Ask the user:
1. What is the production URL? (e.g., `https://myapp.vercel.app`)
2. Do you have Vercel MCP access to this project's deployments? (yes/no, default: no)
3. Do you use named Playwright auth profiles for smoke tests? (if yes, list them; default: none)

Write the answers to `.claude/deployment.json`, commit it, and continue. This ensures the config exists for all future runs.

**Path A: `vercelMcpAccess` is true (or config missing)**

Read `.vercel/project.json` from the main repo path to get `projectId` and `orgId`:

```bash
cat <main-repo-path>/.vercel/project.json
```

If `.vercel/project.json` doesn't exist, fall through to Path B.

Use the Vercel MCP tool `list_deployments` with the `projectId` and `teamId` (which is the `orgId` value). Poll every 30 seconds (initial estimate — tune based on observed behavior). Look for a deployment in the response array where:
- `target` is `"production"`
- `meta.githubCommitRef` is `"main"`
- `created` (ms timestamp) is after the push timestamp
- `state` is `"READY"`

Verified API response fields: `created` (number, ms), `state` ("READY"/"ERROR"), `target` ("production"), `meta.githubCommitRef`, `meta.githubCommitSha`, `inspectorUrl`.

**Note:** This assumes only one Claude Code instance uses Playwright MCP at a time.

**If state is `ERROR`:** Report the build failure and stop. Skip smoke tests.

```
Vercel build failed. Check the deployment logs:
[deployment URL]
Smoke tests skipped.
```

**If Vercel API call fails:** Report the error and stop.

```
Vercel API error: [error message]
Could not verify deployment status. Run smoke tests manually later.
```

**Timeout after 10 minutes:**

```
Deployment not ready after 10 minutes. Check Vercel dashboard.
Smoke tests skipped.
```

**Path B: `vercelMcpAccess` is false (or `.vercel/project.json` missing)**

No Vercel API available. Wait for the configured deploy time, then proceed directly to smoke tests.

```
Vercel MCP access not available for this project.
Waiting <deploy_wait>s for Vercel auto-deploy from GitHub push...
```

Wait `deployWaitSeconds` (default 120s). Then check if the production URL responds:

1. Use Playwright to navigate to the production URL
2. If the page loads (any 2xx response), proceed to smoke tests
3. If the page returns an error or doesn't load, report and skip smoke tests:

```
Production URL <url> not responding after deploy wait. Smoke tests skipped.
Check deployment status manually.
```

**If no `productionUrl` is configured:** Report and skip.

```
No productionUrl in .claude/deployment.json. Smoke tests skipped.
Add a .claude/deployment.json with productionUrl to enable post-deploy testing.
```

**Step 4e: Run smoke tests**

Read `e2e/smoke-test-flows.md` for the flow definitions. The production URL comes from `productionUrl` in `.claude/deployment.json` (Path B) or the Vercel deployment URL (Path A).

Before each Playwright session, kill stale Chrome processes:

```bash
pgrep -f "mcp-chrome" | xargs kill 2>/dev/null || true
```

Wait 2 seconds, then verify no processes remain:

```bash
pgrep -f "mcp-chrome" || echo "Clean"
```

**Branch on `smokeTestProfiles` from `.claude/deployment.json`:**

**If `smokeTestProfiles` is empty `[]` (or config missing and no `e2e/auth/` directory exists):**

No auth profiles needed. Run smoke tests directly against the production URL using the default Playwright MCP connection:

1. Navigate to `<production_url>` using `playwright-headless`
2. Execute flows from `e2e/smoke-test-flows.md` based on scope:
   - QUICK: flows tagged `[QUICK]`
   - FULL: all flows
3. Close the browser

**If `smokeTestProfiles` has entries (e.g., `["playwright-full", "playwright-summaries"]`):**

For each profile:

1. Navigate to the production URL using the profile's Playwright MCP connection
2. Check if redirected to `/login` — if so, auth is expired:
   ```
   Auth expired for <profile>. Re-authenticate before next deploy.
   Skipping <profile> smoke tests.
   ```
3. If authenticated, run flows from `e2e/smoke-test-flows.md` based on scope
4. Close the browser
5. Kill stale Chrome processes before starting the next profile

**Step 4f: Report results**

```
## Post-Deploy Smoke Test Results

### Deployment
- Commit: <sha> (pushed to <base-branch>)
- Deploy URL: <production_url>
- Deploy verification: <Vercel API | timed wait (Ns)>

### Results
[For each flow executed, report PASS/FAIL with details on failure]

[Summary: All passed / N failures found]
```

Smoke test failures are non-blocking — the code is already deployed. Report what to fix.

Then: Archive plan docs (Step 6).

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

Since CWD is always the main repo (see "CRITICAL" section), worktree cleanup is straightforward.

**IMPORTANT: Only remove the worktree being finished.** Do NOT touch other worktrees — they may have active Ralph loops or other work in progress. Check `git worktree list` and only operate on the specific worktree for this branch.

**Step 5a: Remove worktree:**
```bash
git worktree remove <worktree-path> --force
```

**Step 5b: Delete branch:**
```bash
git branch -d <feature-branch>
```

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

| Option | Merge | Push | Smoke Test | Keep Worktree | Cleanup Branch | Archive Plans |
|--------|-------|------|------------|---------------|----------------|---------------|
| 1. Merge locally | yes | - | - | - | yes | yes |
| 2. Deploy + smoke test | yes | yes | yes | - | yes | yes |
| 3. Keep as-is | - | - | - | yes | - | - |
| 4. Discard | - | - | - | - | yes (force) | - |

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

**Running from inside a worktree**
- **Problem:** Causes cascading failures: `git add` for KB entries fails (wrong git index), worktree cleanup destroys CWD, `git mv` for plan archival operates on wrong context, test runners pick up duplicate tests from other worktrees.
- **Fix:** Always run this skill from the main repo directory. See "CRITICAL" section at top.

**Removing other worktrees during cleanup**
- **Problem:** Other worktrees may have active Ralph loops or in-progress work. Removing them kills running processes and destroys uncommitted changes.
- **Fix:** Only remove the specific worktree for the branch being finished. Never touch other worktrees.

**`git mv` on untracked plan files**
- **Problem:** Plan files created with the Write tool but never committed cause `git mv` to fail with "not under version control".
- **Fix:** Check `git ls-files <path>` before `git mv`. Use plain `mv` or `rm` for untracked files.

**Assuming Vercel MCP access without checking**
- **Problem:** Iterating through all Vercel projects searching for a match wastes time and tokens when the project doesn't have MCP access
- **Fix:** Read `.claude/deployment.json` first. If `vercelMcpAccess: false`, skip Vercel API entirely — use timed wait + production URL

**Wrong smoke test scope**
- **Problem:** Running quick scope when changes affect critical user flows
- **Fix:** If branch changed files in critical flow paths (e.g., advisor selection, board flows, checkout), suggest full scope

**Skipping plan archival**
- **Problem:** Plan and design docs left in `docs/plans/` after work is merged, cluttering active plans
- **Fix:** Always run Step 6 after merge (Options 1, 2) to move completed docs to `docs/plans/completed/`

**Worktree cleanup when CWD is safe**
- **Problem:** Skip cleanup when CWD is outside the worktree (unnecessary deferral)
- **Fix:** Since CWD should always be the main repo (per CRITICAL section), worktree cleanup should always proceed immediately — never defer unnecessarily.

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
- Always run from the main repo, never from inside a worktree
- Only remove the worktree being finished — never touch other worktrees
- Read `.claude/deployment.json` before Step 4d — respect per-project deployment config
- Kill stale Chrome processes before each Playwright session
- Report smoke test auth expiry as a non-blocking failure
- Archive plan/design docs to `docs/plans/completed/` after merge (Options 1, 2)

## Lessons-Learned Gate

BEFORE completing this skill's process:
  IF the deployment audit or build caught an issue that tests missed:
    Write a lesson to docs/lessons-learned/YYYY-MM-DD-short-description.md
    using the lesson template (see kickstart scaffold docs).

## Kanban Entry Format

When filing a Kanban entry, read `skills/_shared/kanban-entry-format.md` for the template and counter instructions. Use `finishing-a-development-branch` as the "Discovered during" value.

## Integration

**Called by:**
- **executing-plans** (Step 6) - After all tasks complete
- **autopilot** (Phase 6) - After pipeline completes

**Pairs with:**
- **using-git-worktrees** - Cleans up worktree created by that skill
