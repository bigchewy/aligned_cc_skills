---
name: finishing-a-development-branch
description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, deploy, or cleanup
---

# Finishing a Development Branch

## Overview

Guide completion of development work by presenting clear options and handling chosen workflow.

**Core principle:** Deployment audit → Manual deploy notice → Verify tests → Verify build → Present options → Execute choice → Clean up → Archive plans → Completion summary.

**Required reference:** Read `skills/_shared/verification-checklist.md` — every success claim requires fresh evidence in the current message.

**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/finishing-a-development-branch/`. See `skills/_shared/resolve-skill-path.md` for rationale.

## CRITICAL: Always Run From the Main Repo

**This skill MUST be run from the main repository directory, NOT from inside a worktree.**

Running from inside a worktree causes cascading failures:
- `git add` for KB entries fails (files are in main repo, not worktree)
- Worktree cleanup destroys the session CWD
- `git mv` for plan archival operates on wrong git index
- Test runners may pick up duplicate test files from other worktrees

**Step 1 (before anything else):** Verify CWD is the main repo, not a worktree.

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

### Step 1: Deployment Platform Audit

**Before running tests, check for deployment pitfalls that tests cannot catch.**

Read `CLAUDE.md` to determine the deployment platform. If the platform is Vercel (or not specified — Vercel is the default), load the Vercel section of the deployment pitfall catalog. If the platform is not Vercel, skip Vercel-specific checks but still run framework-agnostic checks (file system access, environment variables, dynamic requires).

Load `references/deployment-pitfall-catalog.md` for detection patterns and false-positive rules.

**Run these searches in parallel across `src/` (excluding `__tests__/` directories):**

1. **File System Access (CRITICAL)**
   - Grep for `__dirname` and `__filename`
   - Grep for `readFileSync` and `readFile` — check if paths use `__dirname` or dynamic variables
2. **Environment Variables (CRITICAL)**
   - Grep for `process\.env\[` (bracket access that defeats inlining)
   - Note: this check detects bracket-access bundling bugs only. Missing production env-var declarations are not gated by this skill — they fail loud at runtime with the variable name in the stack trace, so the framework's own error is the correct surface.
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
Stop. Don't proceed to Step 3.

**If only HIGH or lower:** Show findings as warnings, continue to Step 3.

**If no findings:** Report clean, continue to Step 3.

**Scope:** The default audit runs CRITICAL + HIGH checks. MEDIUM and LOW categories (timeouts, edge runtime, writable filesystem) are documented in the catalog for manual review but not checked automatically.

### Step 2: Manual Deploy Artifact Notice

**Purpose:** Surface a non-blocking reminder when the branch touches files in a "manual-deploy artifact" class (per `skills/_shared/manual-deploy-artifact-catalog.md`) — so the user doesn't ship code that depends on a forgotten manual production step. This is a notice, not a gate; nothing here demands the user paste proof.

**Catalog:** Read `skills/_shared/manual-deploy-artifact-catalog.md` for the artifact classes and their `detector_glob` / `detector_grep` patterns.

**Diff source:** Reuse the diff already computed in Step 1's "Module-Level Mutable State (HIGH)" sub-check:

```bash
git diff --name-only <base-branch>...HEAD
```

Also capture each file's status letter (A/D/R/M) via `git diff --name-status <base-branch>...HEAD`. Do NOT re-run Step 6's diff — that step has not executed yet.

**Procedure:**

1. **Detect.** Match each diff entry against every catalog entry's `detector_glob` / `detector_grep`. Bucket matches by artifact class. Exclude files matching catalog built-in exempt patterns (`**/seed/**`, `**/fixtures/**`, `**/__tests__/**`, `**/*.test.*`).

2. **Handle M-status on migrations.** For files matching the M1 detector (`supabase/migrations/*.sql`) with diff status `M` (modified, not added), STOP with:

   ```
   CRITICAL: Modified an existing migration file (<path>). This will NOT
   re-apply in Supabase — production will diverge from source. Create a
   new migration instead. Do not merge until resolved.
   ```

   This is the one case Step 2 still blocks on — modifying an applied migration is a correctness bug, not a forgotten step.

3. **Emit notice.** If any matches remain (after exemption filtering and the M-status block above), print:

   ```
   Manual-deploy notice: branch touches {N} file(s) requiring a manual production step.

   • <class-id> <class-name> ({N}):
       - <path 1>
       - <path 2>
       (up to 10; "+ N more" if exceeded)

   Prod step: <from catalog entry's "Prod step (for the plan entry)">

   Make sure this step is done after the deploy. Continuing to Step 3.
   ```

   Cap each class list at 10 entries with a truncation note "(+ N more)".

4. **If no catalog matches:** Print "Manual-deploy notice: no catalog matches detected." Continue to Step 3.

**Non-blocking:** Step 2 NEVER prompts the user, NEVER edits the plan, NEVER demands evidence. After printing the notice, immediately continue to Step 3.


### Step 3: Verify Tests

**Check for an autopilot verify result first.** If a `.finish-status` file exists inside the worktree path (the path given after `at` in the skill invocation, e.g., `/path/to/.worktrees/branch-name/.finish-status`) and it contains `status: SUCCESS`, skip Steps 1, 1a, and 1b and report:

```
Tests, build, and eval already verified by autopilot (verified_at: <timestamp>, eval: <eval value from file>). Skipping Steps 1, 1a, and 1b.
```

Then continue to Step 6.

**If no recent .finish-status, run the project's test suite with reduced worker parallelism** (≤2 parallel workers) to prevent memory exhaustion when running alongside other processes. For Jest: `npm test -- --maxWorkers=2`. For Vitest: `npx vitest run --pool=threads --maxWorkers=2`. For other runners, use the equivalent flag.

**If tests fail:**
```
Tests failing (<N> failures). Must fix before completing:

[Show failures]

Cannot proceed with merge/PR until tests pass.
```

Stop. Don't proceed to Step 11.

**If tests pass:** Continue to Step 4.

### Step 4: Verify Build

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

Stop. Don't proceed to Step 5.

**If build passes:** Continue to Step 5.

### Step 5: LLM Eval (auto-run if surface changed)

See `{base-directory}/references/llm-eval-gate.md` for the full workflow. Summary:

- Check `ANTHROPIC_API_KEY` and `e2e/eval-surface.yaml` / `e2e/trigger-map.yaml` configs — skip non-blocking if missing
- Match changed files against surface patterns (directory prefix, wildcard-in-path, exact match)
- Run scoped `promptfoo eval` scenarios from the trigger map; any exit 1 is a hard stop
- Record result for the completion summary (Passed / Partial / Skipped / Failed)

### Step 6: Architecture Doc Notice

**After all verification passes, check if the work changed architecture-relevant files.**

```bash
git diff --name-only <base-branch>...HEAD
```

Architecture-relevant patterns include framework convention paths (e.g., `src/app/api/` for Next.js, `src/routes/` for SvelteKit, `app/` for Rails), new pages, new lib modules, database schema changes, new hooks, and new external service integrations. The project's `CLAUDE.md` may extend or override this list.

**If architecture-relevant changes detected:** File one Kanban entry (`skills/_shared/kanban-entry-format.md`) with category `architecture-doc-update-needed`, listing the changed paths in the body. Then print:

```
Architecture-relevant files changed (N paths). Kanban entry filed for follow-up. Continuing to Step 7.
```

Continue to Step 7. Do NOT update `docs/architecture.md` inline — the diagram work happens during Kanban triage (where it gets proper attention), not on the merge path (where it gets rushed or skipped).

**If no architecture-relevant changes:** Skip silently, continue to Step 7.

### Step 7: Code Review

See `{base-directory}/references/code-review-scan.md` for the full workflow (covers Step 7 and Step 8). Summary:

- Dispatch the `aligned:code-reviewer` sub-agent with branch, base, worktree, and plan file
- CRITICAL findings block the merge — fix, re-run tests/build, re-dispatch
- Important findings are filed to the Kanban board (shared entry format); Suggestions are shown as context

### Step 8: Code Simplification Scan

See `{base-directory}/references/code-review-scan.md` for the full workflow. Summary:

- Dispatch the `aligned:code-simplifier` sub-agent in READ-ONLY mode
- File any returned findings to the Kanban board as `simplification` entries
- Non-blocking — always continue to Step 9

### Step 9: Mockup Fidelity Check

See `{base-directory}/references/mockup-fidelity-check.md` for the full workflow (covers Step 9 and Step 10). Summary:

- Skip Steps 1f and 1g if `.mockup-clean` exists in the worktree (autopilot already ran the fidelity loop)
- Locate the plan's `**Mockups:**` directory; skip silently if the branch has no mockups
- Dispatch a general-purpose sub-agent to compare mockup HTML against implementation source files
- Produce a drift report and hand off to Step 10 if unannounced deviations exist

### Step 10: Fix Mockup Deviations (user-directed)

See `{base-directory}/references/mockup-fidelity-check.md` for the full workflow. Summary:

- Present deviations and ask the user: fix all, fix specific, or skip
- For selected deviations, spawn parallel root-cause diagnosis sub-agents (COSMETIC/STRUCTURAL/DATA/LOGIC)
- Apply fixes, commit, re-verify (tests, build, optional eval, re-run fidelity check)
- Cycle up to 5 times; after that, present remaining deviations as informational

### Step 11: Determine Base Branch

Try `main` first, then fall back to `master`. Run each command separately (do NOT combine with `||`):

```bash
git merge-base HEAD main
```

If that fails:

```bash
git merge-base HEAD master
```

Or ask: "This branch split from main - is that correct?"

### Step 12: Present Options

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

### Step 13: Execute Choice

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

Verify tests on merged result with reduced worker parallelism (≤2 parallel workers) to prevent memory exhaustion. For Jest: `npm test -- --maxWorkers=2`. For Vitest: `npx vitest run --pool=threads --maxWorkers=2`. For other runners, use the equivalent flag.

Then: Cleanup worktree (Step 14), then archive plan docs (Step 15).

#### Option 2: Deploy to Production + Smoke Test

See `{base-directory}/references/deploy-smoke-test.md` for the full workflow. Summary:

- Parse scope (QUICK default, FULL on explicit request), then merge + push to remote like Option 1
- Run worktree cleanup (Step 14) before waiting for the deployment
- Wait for deployment via Vercel MCP (Path A, when `.claude/deployment.json` sets `vercelMcpAccess: true`) or timed wait + URL probe (Path B)
- Run Playwright smoke flows from `e2e/smoke-test-flows.md`; auth profiles come from `smokeTestProfiles` in `.claude/deployment.json`
- Report results (smoke failures are non-blocking — code is already deployed), then archive plan docs (Step 15)

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

Then: Cleanup worktree (Step 14)

### Step 14: Cleanup Worktree

**For Options 1, 2, 4:**

Since CWD is always the main repo (see "CRITICAL" section), worktree cleanup is straightforward.

**IMPORTANT: Only remove the worktree being finished.** Do NOT touch other worktrees — they may have active Ralph loops or other work in progress. Check `git worktree list` and only operate on the specific worktree for this branch.

**Step 14a: Remove worktree:**
```bash
git worktree remove <worktree-path> --force
```

**Step 14b: Delete branch:**
```bash
git branch -d <feature-branch>
```

**For Option 3:** Keep worktree.

### Step 15: Archive Plan Documents

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

### Step 16: Completion Summary

**After all steps complete, present a headline-first summary.**

Analyze the branch's commit history to understand what was built:

```bash
git log --oneline <base-branch>...<feature-branch>
```

Then present:

```
## Completion Summary

<Integration outcome + one-line overview, e.g., "Merged feature/x → main. <one sentence on what changed.>">

<Status line: gates that fired and their result, e.g., "Tests/build verified. Code review clean. 2 simplification findings filed.">
```

**If at least one gate failed, blocked, or surfaced findings**, append a fired-gates table below the status line:

```
| Gate | Result |
|------|--------|
| <one row per gate that fired AND produced output worth surfacing> |
```

**Rules:**
- Always show the integration outcome and status line
- Show the table ONLY when a gate failed, blocked, or surfaced findings; if everything was clean, the status line alone is the summary
- "Skipped — autopilot verified" rows are NOT noteworthy — the sentinel records them, do not enumerate
- "Not applicable" rows (e.g., Worktree when there's no worktree, Mockup fidelity when there are no mockups) are NEVER shown
- The Kanban-findings count is part of the status line, not a separate row

## Quick Reference

| Step | Action | Blocks on failure? |
|------|--------|--------------------|
| 1. Deployment audit | Scan for deployment pitfalls | CRITICAL: yes, HIGH: no |
| 2. Manual deploy notice | Scan diff against artifact catalog; print non-blocking notice | Only on M-status migration mods |
| 3. Verify tests | Run test suite (skipped if `.finish-status` SUCCESS) | Yes |
| 4. Verify build | Run build command (skipped if `.finish-status` SUCCESS) | Yes |
| 5. LLM eval | Run eval if surface changed (skipped if `.finish-status` SUCCESS) | Yes (fail), No (warn/pass) |
| 6. Architecture doc notice | File Kanban entry if architecture-relevant files changed | No |
| 7. Code review | Spawn code-reviewer agent, fix CRITICAL issues | Yes (CRITICAL) |
| 8. Simplification scan | Spawn code-simplifier agent, file Kanban entries | No |
| 9. Mockup fidelity | Compare implementation against brainstorming mockups (skipped if `.mockup-clean` exists) | No |
| 10. Fix deviations | Root-cause diagnose and fix unannounced mockup deviations (skipped if `.mockup-clean` exists) | No |
| 11. Base branch | Determine merge target | No |
| 12. Present options | Show 4 choices | No |
| 13. Execute | Run chosen workflow | N/A |
| 14. Cleanup | Remove worktree if applicable | N/A |
| 15. Archive plans | Move plan/design docs to completed/ | No |
| 16. Completion summary | Present changes overview + results table | No |

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
- **run-ralph.sh** (aligned plugin's `scripts/autopilot/`) — User runs manually after Ralph loop completes
- **autopilot.sh** (aligned plugin's `scripts/autopilot/`) — User runs manually after autopilot completes (autopilot stops at verification, does not merge)

**Pairs with:**
- **using-git-worktrees** - Cleans up worktree created by that skill
