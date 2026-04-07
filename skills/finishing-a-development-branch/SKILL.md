---
name: finishing-a-development-branch
description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, deploy, or cleanup
---

# Finishing a Development Branch

## Overview

Guide completion of development work by presenting clear options and handling chosen workflow.

**Core principle:** Deployment audit → Verify tests → Verify build → Present options → Execute choice → Clean up → Archive plans → Completion summary.

**Required sub-skill:** verification-before-completion — every success claim requires fresh evidence in the current message.

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

### Step 1d: Code Review

**After all verification passes, dispatch a comprehensive code review against the plan.**

This step catches plan drift, missing error paths, and quality issues that tests and builds don't cover. The reviewer is a fresh sub-agent that hasn't seen the implementation conversation — it provides independent evaluation.

**Spawn the `aligned:code-reviewer` agent** via the Task tool:

```
subagent_type: "aligned:code-reviewer"
prompt: "Review the branch changes for this feature against the implementation plan.

  Branch: <branch-name>
  Base branch: <base-branch>
  Working directory: <worktree-path>
  Plan file: <plan-file-path>

  Run `git diff <base-branch>...HEAD` to see all changes on this branch.
  Read the plan file for context on what was intended.
  Follow all 7 review sections in your agent prompt.
  Pay special attention to Section 5 (Mock Error Path Coverage).

  Write your report as structured output to stdout.
  Use Read for files, Grep/Glob for searching. Do not use Bash for searching."
```

**If CRITICAL issues found:**
```
Code review found CRITICAL issues. Must fix before proceeding:

[Show CRITICAL findings]

Cannot proceed until critical issues are resolved.
```
Stop. Fix the issues in the worktree, commit, re-run tests (Step 1) and build (Step 1a), then re-dispatch the code reviewer.

**If only Important or Suggestions:** Show findings as context, continue to Step 1e. File Important findings to Kanban board using the standard entry format.

**If clean review:** Report clean, continue to Step 1e.

### Step 1e: Code Simplification Scan

**After all verification and doc updates, scan branch changes for simplification opportunities.**

This step is **non-blocking** — findings are filed to the Kanban board as improvement opportunities, but never prevent merge/PR.

**Spawn the `aligned:code-simplifier` agent** via the Task tool:

```
subagent_type: "aligned:code-simplifier"
prompt: "Analyze the branch changes for simplification opportunities.
  Base branch: <base-branch>
  Working directory: <project-root>

  CRITICAL CONSTRAINTS:
  - You are READ-ONLY. Do not use Edit, Write, NotebookEdit, or any file-modifying Bash commands.
  - Do NOT run git checkout, git switch, or any branch-switching command. The correct branch is already checked out.
  - Do NOT create Kanban entries or write files. Return ONLY a JSON array in your final message.
  - Use the Read tool to read files, not cat/Bash.
  - Allowed Bash: git diff, git log, git show, git ls-files only."
```

**If the agent returns findings** (non-empty JSON array):

1. Read `{base-directory}/../_shared/kanban-entry-format.md` for the KB template and counter instructions (resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load)
2. For each finding, file a KB entry with:
   - **Type:** `simplification`
   - **Discovered during:** `finishing-a-development-branch (code-simplifier)`
   - **Why out of scope:** `Simplification opportunity — not a bug or part of the current task`
   - Map finding fields: title → KB title, `file:line_range` → Location, observed → Observed, suggestion → Expected, severity → Severity
3. Commit the Kanban entries. **If CWD is a worktree**, use `git -C <main-repo-path> add/commit` (KB files are in main repo). If CWD is the main repo, use bare `git add/commit`.

**Report to user:**
```
Code simplification scan: N opportunities filed to Kanban board.
```

**If the agent returns no findings:** Report silently:
```
Code simplification scan: clean.
```

Continue to Step 1f.

### Step 1f: Mockup Fidelity Check

**After all verification and scans, check if the branch's design has associated mockups.**

This step is **non-blocking** — deviations are reported so the user can decide whether to fix them before merge.

1. **Find the plan file:** Scan both `docs/plans/*.md` and `docs/plans/completed/*.md` for the plan associated with this branch (match by branch name pattern). The plan may already be in `completed/` if executing-plans archived it. Read the plan header's `**Mockups:**` field for the mockups directory path. If the plan has no `**Mockups:**` field, fall back to the `**Source Design Doc:**` field and check that design doc for a `**Mockups:**` field.

2. **Check for mockups:** If a mockups path was found, verify the directory exists. If no mockups path was found or the directory doesn't exist, skip silently — not all features have UI components.

3. **If mockups exist, dispatch a fidelity check agent** via Task tool (`subagent_type=general-purpose`, `model=sonnet`):

   ```
   "You are a mockup fidelity checker. Compare the brainstorming mockups against
   the actual implementation to find visual deviations.

   You have access to Glob, Grep, and Read tools. Do not use Bash for searching.

   Step 1: Read each HTML mockup file in `{mockups-dir}/`. For each file, extract:
   - Page/component layout structure
   - Components present (buttons, cards, lists, inputs, etc.)
   - Data displayed (column names, field labels, example content)
   - Interactive elements (tabs, accordions, hover states, modals)

   Step 2: Read the plan file at `{plan-file-path}`. For each UI task that has a
   mockup verification step, note which source files it creates/modifies and which
   mockup file it references. This gives you the mockup-to-source-file mapping.
   Then read those implementation source files.

   Step 3: Compare mockup elements against implementation. For each mockup:
   - What matches the implementation
   - What deviates (present in mockup but missing/different in code)
   - What was added (present in code but not in mockup)

   Step 4: Search the plan file for 'MOCKUP DEVIATION' annotations — these are
   intentional deviations documented during execution.

   Return a JSON report:
   {
     \"mockups_checked\": N,
     \"matches\": [\"brief description of what matches\"],
     \"deviations\": [
       {
         \"mockup\": \"filename.html\",
         \"element\": \"what's different\",
         \"type\": \"missing|changed|added\",
         \"intentional\": true/false,
         \"annotation\": \"text of MOCKUP DEVIATION note, if any\",
         \"source_files\": [\"src/components/Foo.tsx\"]
       }
     ]
   }

   IMPORTANT: For each deviation, include the source_files array listing
   the implementation file paths you read when comparing against the mockup.
   Downstream steps depend on this field."
   ```

4. **Report findings:**

```
## Mockup Fidelity Check

Mockups checked: N
- Matches: N elements verified
- Intentional deviations: N (documented with MOCKUP DEVIATION)
- Unannounced deviations: N

### Unannounced Deviations (if any)
- [mockup file]: [element] — [missing|changed|added]
```

**If no unannounced deviations:** Report clean, continue to Step 1g.

**If unannounced deviations exist:** Show them, continue to Step 1g.

**If no mockups found:** Skip silently, continue to Step 1g.

### Step 1g: Fix Mockup Deviations (user-directed)

**If Step 1f found no unannounced deviations (or was skipped):** Skip silently, continue to Step 2.

**If unannounced deviations exist**, present:

```
⚠ {N} unannounced mockup deviations found:
{bullet list of deviation summaries — one line each}

Would you like to fix any of these before proceeding?
1. Fix all
2. Fix specific (list numbers)
3. Skip — accept deviations as-is

Which option?
```

**If skip:** Continue to Step 2.

**If fix all or fix specific:**

**Step 1g-i: Root-cause diagnosis.** For each selected deviation, spawn a sub-agent in parallel (`subagent_type=general-purpose`, `model=sonnet`). Each agent receives:

```
You are a mockup deviation analyst. Determine the root cause of this deviation
between a design mockup and the implementation.

Deviation: {deviation summary}
Mockup file: {mockup file path}
Element: {element description}
Type: {missing|changed|added}
Implementation file(s): {source file paths from Step 1f agent report}

You are READ-ONLY. Do not use Edit, Write, NotebookEdit, or any file-modifying
Bash commands. Use Read for files, Grep/Glob for searching.

Investigation steps:
1. Read the mockup file. Identify the intended design for this element.
2. Read the implementation file(s). Find the code that renders this element.
3. Trace the gap. Classify the root cause:
   - COSMETIC: Wrong value in the right place (color, spacing, font, size)
   - STRUCTURAL: Wrong component, missing component, or wrong composition
   - DATA: Correct component but fed wrong data or missing data binding
   - LOGIC: Conditional rendering or state logic doesn't match mockup intent

For STRUCTURAL, DATA, and LOGIC causes, trace one level deeper: why was
this built differently? Check git blame on the relevant lines — was the
mockup created after the code was written? Was a shared component reused
that doesn't support the mockup's design? Is there a data model mismatch?

Return a JSON object:
{
  "deviation": "{summary}",
  "root_cause_type": "COSMETIC|STRUCTURAL|DATA|LOGIC",
  "root_cause": "Specific explanation of why the deviation exists",
  "fix_scope": {
    "files": ["file paths that need changes"],
    "description": "What needs to change and where"
  },
  "risk": "What else could break if this is changed naively"
}
```

If any sub-agent fails or returns unparseable output, report which deviations could not be analyzed and ask the user whether to attempt those fixes without root-cause analysis or skip them.

**Step 1g-ii: Synthesize and fix.** Collect all successful agent reports. Present:

```
## Deviation Root Causes

| # | Deviation | Type | Root Cause | Files |
|---|-----------|------|------------|-------|
| 1 | ...       | COSMETIC | ... | ... |
| ...

### Common Themes (if any)
{shared root causes or patterns across deviations}

### Risks
{any cross-cutting risks from the agent reports}
```

If multiple diagnoses target the same file, review them together before applying fixes — later diagnoses may be subsumed by earlier ones.

After presenting, apply fixes to files in the worktree using absolute paths (do not `cd` into the worktree — see CRITICAL section). Address the identified root causes, not just the surface symptoms.

Commit fixes to the feature branch before re-verifying. Run each command separately (do NOT chain with `&&`):

```bash
git -C <worktree-path> add <files>
```

```bash
git -C <worktree-path> commit -m "fix: resolve mockup deviations"
```

This gives each fix cycle a clean rollback point.

**Step 1g-iii: Re-verify.** After committing fixes:
1. Re-run tests (Step 1) and build (Step 1a)
2. If any fixed files match LLM behavior surface patterns, also re-run Step 1b (LLM eval)
3. Re-run the mockup fidelity check (Step 1f) to confirm deviations are resolved

**Cycle limit:** Track the number of completed fix-then-verify cycles. Keep iterating until all unannounced deviations are resolved or the user chooses to skip.

- **After each cycle:** If unannounced deviations remain, present them and ask the user: fix or accept?
- **After cycle 5:** If deviations still remain after 5 fix cycles, present them as informational. Do NOT offer to fix again — the deviations likely require manual intervention or a design decision. Continue to Step 2.

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

**Step 4a: Merge to main** — Same as Option 1's merge logic (checkout, pull, merge).

**Step 4b: Push to remote** — `git push origin <base-branch>`. Record push timestamp for deployment matching.

**Step 4c: Worktree cleanup** — Run Step 5 now.

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

**If deployment fails:** Report and skip smoke tests. Covers: state `ERROR` (show deployment URL), API call failure (show error message), timeout after 10 minutes (suggest checking dashboard).

**Path B: `vercelMcpAccess` is false (or `.vercel/project.json` missing)**

No Vercel API available. Wait `deployWaitSeconds` (default 120s) for auto-deploy, then check if production URL responds (Playwright navigate, expect 2xx). If no response or no `productionUrl` configured, report and skip smoke tests.

**Step 4e: Run smoke tests**

Read `e2e/smoke-test-flows.md` for the flow definitions. The production URL comes from `productionUrl` in `.claude/deployment.json` (Path B) or the Vercel deployment URL (Path A).

Before each Playwright session, kill stale Chrome: run `pkill -f mcp-chrome` (ignore if no matching processes), wait 2s, verify clean with `pgrep -f mcp-chrome`.

**If `smokeTestProfiles` is empty** (or no `e2e/auth/` directory): Run flows directly using `playwright-headless`. QUICK = flows tagged `[QUICK]`, FULL = all flows.

**If `smokeTestProfiles` has entries:** For each profile, navigate with that profile's Playwright MCP connection. If redirected to `/login`, report auth expired and skip that profile. Otherwise run flows based on scope. Kill stale Chrome between profiles.

**Step 4f: Report results** — Show deployment info (commit, URL, verification method) and PASS/FAIL per flow with failure details. Smoke test failures are non-blocking — code is already deployed. Then: Archive plan docs (Step 6).

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

## Kanban Entry Format

When filing a Kanban entry, read `{base-directory}/../_shared/kanban-entry-format.md` for the template and counter instructions (resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load). Use `finishing-a-development-branch` as the "Discovered during" value.

## Integration

**Called by:**
- **executing-plans** (Step 6) — After all tasks complete
- **run-ralph.sh** (aligned plugin's `docs/ralph_loops/`) — User runs manually after Ralph loop completes
- **autopilot.sh** (aligned plugin's `docs/ralph_loops/`) — User runs manually after autopilot completes (autopilot stops at verification, does not merge)

**Pairs with:**
- **using-git-worktrees** - Cleans up worktree created by that skill
