---
name: finishing-a-development-branch
description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, deploy, or cleanup
---

# Finishing a Development Branch

## Overview

Guide completion of development work by presenting clear options and handling chosen workflow.

**Core principle:** Deployment audit → Verify tests → Verify build → Present options → Execute choice → Clean up → Archive plans → Completion summary.

**Required reference:** Read `skills/_shared/verification-checklist.md` — every success claim requires fresh evidence in the current message.

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

See `references/llm-eval-gate.md` for the full workflow. Resolve `{base-directory}` using the "Base directory for this skill:" line printed when the skill loads, then read the referenced file. Summary:

- Check `ANTHROPIC_API_KEY` and `e2e/eval-surface.yaml` / `e2e/trigger-map.yaml` configs — skip non-blocking if missing
- Match changed files against surface patterns (directory prefix, wildcard-in-path, exact match)
- Run scoped `promptfoo eval` scenarios from the trigger map; any exit 1 is a hard stop
- Record result for the completion summary (Passed / Partial / Skipped / Failed)

### Step 1c: Architecture Doc Update

**After all verification passes, check if the work changed system architecture.**

Compare the branch changes against architecture-relevant patterns:

```bash
git diff --name-only <base-branch>...HEAD
```

If changed files include any of: architecture-relevant paths as defined in the project's `CLAUDE.md` or detected from framework conventions (e.g., `src/app/api/` for Next.js, `src/routes/` for SvelteKit, `app/` for Rails), new pages, new lib modules, database schema changes, new hooks, or new external service integrations — the architecture doc likely needs updating.

**If architecture-relevant changes detected:**

1. Read `docs/architecture.md` (or the project's equivalent)
2. **Verify diagrams affected by this branch** — architecture docs may be stale. For the specific diagrams you're updating, check if they accurately reflect the current code (not just your changes). The actual source files are always the source of truth. If you find discrepancies in the diagrams you're editing, file bugs (see `skills/_shared/kanban-entry-format.md`) with category `architecture-discrepancy`. Do NOT audit unrelated diagrams.
3. Update the affected diagrams to reflect the new state
4. Commit the update (including any bug board entries) to the feature branch before proceeding

**If no architecture-relevant changes:** Skip silently, continue to Step 1d.

### Step 1d: Code Review

See `references/code-review-scan.md` for the full workflow (covers Step 1d and Step 1e). Resolve `{base-directory}` using the "Base directory for this skill:" line printed when the skill loads, then read the referenced file. Summary:

- Dispatch the `aligned:code-reviewer` sub-agent with branch, base, worktree, and plan file
- CRITICAL findings block the merge — fix, re-run tests/build, re-dispatch
- Important findings are filed to the Kanban board (shared entry format); Suggestions are shown as context

### Step 1e: Code Simplification Scan

See `references/code-review-scan.md` for the full workflow. Summary:

- Dispatch the `aligned:code-simplifier` sub-agent in READ-ONLY mode
- File any returned findings to the Kanban board as `simplification` entries
- Non-blocking — always continue to Step 1f

### Step 1f: Mockup Fidelity Check

See `references/mockup-fidelity-check.md` for the full workflow (covers Step 1f and Step 1g). Resolve `{base-directory}` using the "Base directory for this skill:" line printed when the skill loads, then read the referenced file. Summary:

- Locate the plan's `**Mockups:**` directory; skip silently if the branch has no mockups
- Dispatch a general-purpose sub-agent to compare mockup HTML against implementation source files
- Produce a drift report and hand off to Step 1g if unannounced deviations exist

### Step 1g: Fix Mockup Deviations (user-directed)

See `references/mockup-fidelity-check.md` for the full workflow. Summary:

- Present deviations and ask the user: fix all, fix specific, or skip
- For selected deviations, spawn parallel root-cause diagnosis sub-agents (COSMETIC/STRUCTURAL/DATA/LOGIC)
- Apply fixes, commit, re-verify (tests, build, optional eval, re-run fidelity check)
- Cycle up to 5 times; after that, present remaining deviations as informational

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

**If merge fails with "untracked working tree files would be overwritten by merge":**

This happens when the target branch has untracked files that also exist on the feature branch. Recovery is non-interactive — no user prompt needed.

1. Extract the indented file paths from git's error output (they follow the "error: The following untracked working tree files would be overwritten by merge:" line)
2. Commit those specific files to the target branch:
   ```bash
   git add <file1> <file2> ...
   ```
   ```bash
   git commit -m "chore: commit untracked files before merge"
   ```
3. Retry the merge:
   ```bash
   git merge <feature-branch>
   ```
4. The retry will likely produce add/add conflicts on the files extracted in step 1 (same file added on both branches). For those files, resolve by combining both versions — keep content from both sides. If conflicts appear on *other* files not in the step 1 list, those are genuine merge conflicts — run `git merge --abort` then `git reset HEAD~1` to remove the step-2 commit, and ask the user. Then complete the merge:
   ```bash
   git add <resolved-files>
   ```
   ```bash
   git commit -m "Merge <feature-branch> into <base-branch>"
   ```

**If recovery fails:** If step 2 or 3 fails, undo the step-2 commit with `git reset HEAD~1` (mixed reset — files return to untracked, which is their original state), report the error, and ask the user. If step 4 fails during conflict resolution, run `git merge --abort` then `git reset HEAD~1` to also remove the step-2 commit. Report the error and ask the user. Do not leave a phantom commit on the target branch.

Verify tests on merged result:

```bash
<test command>
```

Then: Cleanup worktree (Step 5), then archive plan docs (Step 6).

#### Option 2: Deploy to Production + Smoke Test

See `references/deploy-smoke-test.md` for the full workflow. Resolve `{base-directory}` using the "Base directory for this skill:" line printed when the skill loads, then read the referenced file. Summary:

- Parse scope (QUICK default, FULL on explicit request), then merge + push to remote like Option 1
- Run worktree cleanup (Step 5) before waiting for the deployment
- Wait for deployment via Vercel MCP (Path A, when `.claude/deployment.json` sets `vercelMcpAccess: true`) or timed wait + URL probe (Path B)
- Run Playwright smoke flows from `e2e/smoke-test-flows.md`; auth profiles come from `smokeTestProfiles` in `.claude/deployment.json`
- Report results (smoke failures are non-blocking — code is already deployed), then archive plan docs (Step 6)

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

### Step 7: Completion Summary

**After all steps complete, present a completion summary.**

Analyze the branch's commit history to understand what was built:

```bash
git log --oneline <base-branch>...<feature-branch>
```

Then present:

```
## Completion Summary

<1-3 sentence overview of the features or changes implemented on this branch.>

| Step | Result |
|------|--------|
| Deployment audit | <Clean / N critical, N high findings> |
| Tests | <N/N passing> |
| Build | <Passed / Failed> |
| LLM eval | <Passed / Warned / Skipped — reason> |
| Architecture doc | <Updated / Skipped> |
| Code review | <Clean / N CRITICAL, N Important, N Suggestions> |
| Code simplification | <N findings filed / Clean> |
| Mockup fidelity | <N matches, N deviations / No mockups / Skipped> |
| Deviation fixes | <N fixed (root causes) / Skipped / Accepted as-is> |
| Integration | <Option chosen + outcome, e.g., "Merged feature/x → main"> |
| Worktree | <Removed / Kept> |
| Plan archive | <Archived N files / No plans found / Skipped> |
```

**Populate each row from the actual results of the preceding steps.** Omit rows for steps that were not applicable (e.g., no worktree involved → omit Worktree row).

## Quick Reference

| Step | Action | Blocks on failure? |
|------|--------|--------------------|
| 0. Deployment audit | Scan for deployment pitfalls | CRITICAL: yes, HIGH: no |
| 1. Verify tests | Run test suite | Yes |
| 1a. Verify build | Run build command | Yes |
| 1b. LLM eval | Run eval command if surface changed | Yes (fail), No (warn/pass) |
| 1c. Architecture doc | Update `docs/architecture.md` if structure changed | No |
| 1d. Code review | Spawn code-reviewer agent, fix CRITICAL issues | Yes (CRITICAL) |
| 1e. Simplification scan | Spawn code-simplifier agent, file Kanban entries | No |
| 1f. Mockup fidelity | Compare implementation against brainstorming mockups | No |
| 1g. Fix deviations | Root-cause diagnose and fix unannounced mockup deviations (user-directed) | No |
| 2. Base branch | Determine merge target | No |
| 3. Present options | Show 4 choices | No |
| 4. Execute | Run chosen workflow | N/A |
| 5. Cleanup | Remove worktree if applicable | N/A |
| 6. Archive plans | Move plan/design docs to completed/ | No |
| 7. Completion summary | Present changes overview + results table | No |

| Option | Merge | Push | Smoke Test | Keep Worktree | Cleanup Branch | Archive Plans |
|--------|-------|------|------------|---------------|----------------|---------------|
| 1. Merge locally | yes | - | - | - | yes | yes |
| 2. Deploy + smoke test | yes | yes | yes | - | yes | yes |
| 3. Keep as-is | - | - | - | yes | - | - |
| 4. Discard | - | - | - | - | yes (force) | - |

## Common Mistakes

| Mistake | Why it matters | Fix |
|---------|---------------|-----|
| Running from inside a worktree | Cascading failures: wrong git index, CWD destroyed on cleanup, duplicate tests | Run from main repo (see CRITICAL section) |
| Removing other worktrees during cleanup | Kills active processes, destroys uncommitted work | Only remove the worktree being finished |
| `git mv` on untracked plan files | Write tool files never committed cause `git mv` to fail | Check `git ls-files` first; use plain `mv` for untracked |
| Prompting user on untracked-file merge conflict | Always the same answer: commit untracked files, retry merge, combine both versions | Auto-recover (see Option 1 merge logic) |
| Assuming Vercel MCP access | Wastes time iterating projects without access | Read `.claude/deployment.json` first |
| No confirmation for discard | Accidentally delete work | Require typed "discard" confirmation |

## Red Flags

**Never:** Proceed with CRITICAL deployment findings or failing tests/build. Never merge without verifying tests on result. Never delete work without confirmation or force-push without explicit request.

**Always:** Follow the step order (audit → tests → build → eval → code review → simplification scan → mockup fidelity → fix deviations → options). Present exactly 4 options. Run from main repo. Only remove the specific worktree being finished. Read `.claude/deployment.json` before deploy. Kill stale Chrome before Playwright. Archive plans after merge.

## Lessons-Learned Gate

BEFORE completing this skill's process:
  IF the deployment audit or build caught an issue that tests missed:
    Write a lesson to docs/lessons-learned/YYYY-MM-DD-short-description.md
    using the lesson template (see kickstart scaffold docs).

## Integration

**Called by:**
- **executing-plans** (Step 6) — After all tasks complete
- **run-ralph.sh** (aligned plugin's `docs/ralph_loops/`) — User runs manually after Ralph loop completes
- **autopilot.sh** (aligned plugin's `docs/ralph_loops/`) — User runs manually after autopilot completes (autopilot stops at verification, does not merge)

**Pairs with:**
- **using-git-worktrees** - Cleans up worktree created by that skill
