# Restore finishing-a-development-branch Regressions

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Merge the archived version's deploy+smoke test workflow back into the current plugin version of `finishing-a-development-branch`, preserving all current improvements.

**Source Design Doc:** N/A (this plan is based on the root cause analysis comparing `/Users/ericpage/software/archived-claude-local/skills/finishing-a-development-branch/SKILL.md` against `/Users/ericpage/software/aligned_cc_skills/skills/finishing-a-development-branch/SKILL.md`)

**Architecture:** The current plugin version lost ~190 lines of deploy+smoke test workflow when Option 2 was changed from "Deploy to production + smoke test" to "Push and create a Pull Request". The fix merges the archived version's content back while preserving the current version's improvements (platform detection, lessons-learned gate, generalized paths). The reference file (`deployment-pitfall-catalog.md`) is already correct and does not need changes.

**Sequential dependency:** Tasks 1-9 must complete in order — Tasks 1-8 all modify `skills/finishing-a-development-branch/SKILL.md`. Complete and commit each task before starting the next.

**Tech Stack:** Markdown (skill definitions), Git

---

## Context for the Implementer

### What happened
When skills were migrated from `~/.claude/` (archived-claude-local) to the plugin repo (aligned_cc_skills), the `finishing-a-development-branch` skill lost its Option 2 "Deploy to production + smoke test" workflow. It was replaced with a simpler "Push and create a Pull Request" option. Several supporting sections (CRITICAL safety section, common mistakes, red flags) were also lost or truncated.

### Source files to reference
- **Archived (source of truth for lost content):** `/Users/ericpage/software/archived-claude-local/skills/finishing-a-development-branch/SKILL.md`
- **Current (base to edit):** `/Users/ericpage/software/aligned_cc_skills/skills/finishing-a-development-branch/SKILL.md`

### What to KEEP from current version (do NOT revert these)
- **Step 0 platform detection:** Reads `CLAUDE.md` for deployment platform, falls back to Vercel. Title "Deployment Platform Audit" (not "Vercel Deployment Audit")
- **Step 0 reference file:** `references/deployment-pitfall-catalog.md` (not `references/vercel-pitfall-catalog.md`)
- **Step 1b eval invocation:** `/aligned:eval-failure-triage` skill syntax (not "dispatch agent via Task tool")
- **Step 1c architecture paths:** CLAUDE.md-based with framework examples (not hardcoded Next.js paths)
- **Lessons-Learned Gate:** Entirely new section, keep as-is
- **Integration section callers:** `executing-plans (Step 6)` and `autopilot (Phase 6)` (not `subagent-driven-development`)
- **Generalized language:** "deployment" instead of "Vercel" in most contexts; "the project's test command" instead of hardcoded `npm test`

### What to RESTORE from archived version
- **CRITICAL: Always Run From the Main Repo** section (between Overview and The Process)
- **Step 3 Option 2:** "Deploy to production + smoke test" (not "Push and create a Pull Request")
- **Step 4 Option 2:** Full deploy+smoke test workflow (Steps 4a-4f, ~130 lines)
- **Step 1d KB commit:** Worktree-aware `git -C` guidance
- **Quick Reference tables:** Smoke Test column restored, Option 2 row corrected
- **Common Mistakes:** Restore lost entries (worktree CWD, Vercel MCP access, smoke test scope, plan archival, git mv untracked)
- **Red Flags:** Restore all lost "Always:" items
- **Core principle:** Add "→ Archive plans" back at end

---

## ✅ Task 1: Add "CRITICAL: Always Run From the Main Repo" Section

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md`

**Step 1: Read both source files**

Read the archived SKILL.md lines 16-39 for the CRITICAL section content.
Read the current SKILL.md to understand the insertion point (after the Overview section, before "## The Process").

**Step 2: Insert the CRITICAL section**

After the "Announce at start" line and before `## The Process`, insert this section adapted from archived lines 16-39. Use the archived content but update the language for the plugin context:

```markdown
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
```

**Step 3: Verify insertion**

Read the file and confirm:
- The CRITICAL section appears between Overview and The Process
- No duplicate headings
- The markdown renders correctly (no broken code fences)

**Step 4: Commit**

```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "fix: restore CRITICAL always-run-from-main-repo section"
```

---

## ✅ Task 2: Restore Core Principle and Step 1d KB Commit Guidance

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md`

**Step 1: Fix the core principle line**

Find:
```
**Core principle:** Deployment audit → Verify tests → Verify build → Present options → Execute choice → Clean up.
```

Replace with:
```
**Core principle:** Deployment audit → Verify tests → Verify build → Present options → Execute choice → Clean up → Archive plans.
```

**Step 2: Restore worktree-aware KB commit guidance in Step 1d**

> **Architectural note:** This guidance says "If CWD is a worktree..." which technically contradicts the CRITICAL section's "CWD must always be the main repo." This is intentional defense-in-depth — the CRITICAL section is the primary enforcement, but if somehow violated, the `git -C` fallback prevents silent data loss. The archived version had both, and both should be preserved.

In Step 1d (Code Simplification Scan), find item 4 which currently reads:
```
4. Commit the Kanban entries to the main repo.
```

Replace with the archived version's worktree-aware guidance:
```
4. Commit the Kanban entries. **If CWD is a worktree**, KB files are written to the main repo's `docs/kanban/` via absolute paths — use `git -C <main-repo-path> add` and `git -C <main-repo-path> commit` (not bare `git add` from the worktree). If CWD is the main repo, use bare `git add/commit` as normal.
```

**Step 3: Verify changes**

Read the modified lines and confirm both changes are correct.

**Step 4: Commit**

```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "fix: restore core principle archive step and KB commit worktree guidance"
```

---

## ✅ Task 3: Restore Step 3 Options and Step 4 Option 2 Deploy+Smoke Test Workflow

This is the largest task — it restores the primary lost functionality.

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md`

**Step 1: Read both source files completely**

Read archived SKILL.md in full (focus on lines 254-487 for Step 3 + Step 4 Option 2).
Read current SKILL.md in full (focus on lines 231-310 for Step 3 + Step 4 Options).

**Step 2: Replace Step 3 options**

Find the current Step 3 options block:
```
1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work
```

Replace with the archived version's options:
```
1. Merge back to <base-branch> locally
2. Deploy to production + smoke test
3. Keep the branch as-is (I'll handle it later)
4. Discard this work
```

**Step 3: Replace Step 4 Option 1 merge logic**

Replace the current Option 1 section (which has worktree branching with `git -C`) with the archived version's simpler approach that assumes CWD is the main repo:

```markdown
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
```

**Step 4: Replace Step 4 Option 2 entirely**

Remove the current PR-creation Option 2 and replace it with the archived version's deploy+smoke test workflow. Copy archived lines 299-487, but make these adaptations for the plugin context:

1. Keep the archived workflow structure exactly (Steps 4a-4f)
2. In Step 4e, keep the reference to `e2e/smoke-test-flows.md` (project-specific)
3. Keep the `.claude/deployment.json` config format exactly as archived
4. Keep the Vercel MCP integration exactly as archived
5. Keep the Playwright smoke test logic exactly as archived
6. In Step 4f's closing line (archived line 487), remove the parenthetical "(or deferred if session CWD was inside the worktree)" — this deference is eliminated by the CRITICAL section which requires main-repo CWD

The full Option 2 content from archived should be inserted. Read the archived file lines 299-487 and copy them into the current file, replacing the PR-creation Option 2, applying adaptation #6 above.

**Step 5: Verify Options 3 and 4 are unchanged**

Read the file and confirm Options 3 (Keep As-Is) and 4 (Discard) remain intact after the Option 2 replacement.

**Step 6: Commit**

```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "fix: restore deploy+smoke test as Option 2, replacing PR creation"
```

---

## ✅ Task 4: Restore Step 5 Worktree Cleanup (Simplified Version)

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md`

**Step 1: Replace Step 5 with archived version**

The archived version has a simpler Step 5 that assumes CWD is the main repo (consistent with the restored CRITICAL section). Replace the current complex Step 5 (which has CWD detection, cd+pwd verification, etc.) with the archived version:

```markdown
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
```

**Step 2: Verify the replacement**

Read Step 5 and confirm:
- "Only remove the worktree being finished" warning is present
- "Ralph loops" mention is present (from archived)
- 2-step cleanup (5a remove worktree, 5b delete branch)
- Option 3 exception

**Step 3: Commit**

```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "fix: simplify Step 5 worktree cleanup assuming main-repo CWD"
```

---

## Task 5: Restore Quick Reference Tables

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md`

**Step 1: Replace the option behavior table**

Find the current quick reference option table and replace it with the archived version's table that includes the Smoke Test column and correct Option 2 behavior:

```markdown
| Option | Merge | Push | Smoke Test | Keep Worktree | Cleanup Branch | Archive Plans |
|--------|-------|------|------------|---------------|----------------|---------------|
| 1. Merge locally | yes | - | - | - | yes | yes |
| 2. Deploy + smoke test | yes | yes | yes | - | yes | yes |
| 3. Keep as-is | - | - | - | yes | - | - |
| 4. Discard | - | - | - | - | yes (force) | - |
```

**Step 2: Verify the step reference table uses "Deployment" language**

The step reference table should keep current's generalized language:

```markdown
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
```

**Step 3: Commit**

```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "fix: restore quick reference tables with smoke test column"
```

---

## Task 6: Restore Common Mistakes Section

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md`

**Step 1: Read both versions' Common Mistakes sections**

Read archived lines 590-639 and current lines 429-457.

**Step 2: Replace the Common Mistakes section**

The merged section should contain ALL entries from archived, with current's improved CWD explanation for the worktree entry, and updated terminology ("deployment audit" instead of "Vercel audit"):

```markdown
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
```

Note: The "Wrong smoke test scope" entry was generalized from archived's project-specific paths (`src/app/(app)/quick-consult/`, `src/app/(app)/board/`) to generic guidance about "critical flow paths". The "Worktree cleanup when CWD is safe" entry was adapted from archived to align with the simplified Step 5 (original referenced Step 5a which no longer exists as a CWD-check step).

**Step 3: Commit**

```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "fix: restore all common mistakes including worktree, MCP, and smoke test entries"
```

---

## Task 7: Restore Red Flags Section

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md`

**Step 1: Replace the Red Flags section**

Replace the current truncated Red Flags with the full set from archived, updated with current terminology:

```markdown
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
```

**Step 2: Commit**

```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "fix: restore complete red flags section with deployment and smoke test items"
```

---

## Task 8: Update Frontmatter Description

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md`

**Step 1: Update the description to reflect deploy+smoke test**

Find:
```yaml
description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup
```

Replace with:
```yaml
description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, deploy, or cleanup
```

(Changed "PR" to "deploy" since Option 2 is now deploy+smoke test, not PR creation)

**Step 2: Commit**

```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "fix: update frontmatter description to reflect deploy option"
```

---

## Task 9: Fix Integration Section Callers

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md`

**Step 1: Read the current Integration section**

The current Integration section still references `subagent-driven-development` (a stale/renamed skill) and has `executing-plans (Step 5)` (should be Step 6). Verify by reading the file's Integration section.

**Step 2: Replace the Integration section**

Find the current Integration block and replace it with:

```markdown
## Integration

**Called by:**
- **executing-plans** (Step 6) - After all tasks complete
- **autopilot** (Phase 6) - After pipeline completes

**Pairs with:**
- **using-git-worktrees** - Cleans up worktree created by that skill
```

Note: `subagent-driven-development` was renamed to `autopilot`. The `executing-plans` step number was updated from 5 to 6 to match the current executing-plans skill.

**Step 3: Commit**

```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "fix: update integration section callers to current skill names"
```

---

## Task 10: Full File Verification Pass

**Files:**
- Read: `skills/finishing-a-development-branch/SKILL.md` (full file)
- Read: `skills/finishing-a-development-branch/references/deployment-pitfall-catalog.md`

**Step 1: Verify all sections are present and correctly ordered**

Read the full SKILL.md and verify this section order:
1. Frontmatter
2. Overview (with core principle including "→ Archive plans")
3. CRITICAL: Always Run From the Main Repo
4. The Process
5. Step 0: Deployment Platform Audit (with platform detection from current)
6. Step 1: Verify Tests
7. Step 1a: Verify Build
8. Step 1b: LLM Eval
9. Step 1c: Architecture Doc Update
10. Step 1d: Code Simplification Scan (with worktree-aware KB guidance)
11. Step 2: Determine Base Branch
12. Step 3: Present Options (4 options with "Deploy to production + smoke test")
13. Step 4: Execute Choice
    - Option 1: Merge Locally (assumes main-repo CWD)
    - Option 2: Deploy to Production + Smoke Test (Steps 4a-4f)
    - Option 3: Keep As-Is
    - Option 4: Discard
14. Step 5: Cleanup Worktree (simplified, assumes main-repo CWD)
15. Step 6: Archive Plan Documents
16. Quick Reference (both tables, with Smoke Test column)
17. Common Mistakes (all 12 entries)
18. Red Flags (complete Never/Always lists)
19. Lessons-Learned Gate (kept from current)
20. Kanban Entry Format
21. Integration

**Step 2: Verify cross-references**

Grep for references within the file to confirm:
- "CRITICAL" section is referenced in Step 4 Option 1, Step 5, Common Mistakes
- `references/deployment-pitfall-catalog.md` is referenced (not `vercel-pitfall-catalog.md`)
- `.claude/deployment.json` is referenced in Step 4 Option 2
- `e2e/smoke-test-flows.md` is referenced in Step 4 Option 2
- `/aligned:eval-failure-triage` is referenced (not agent dispatch)

**Step 3: Verify reference file exists**

Confirm `skills/finishing-a-development-branch/references/deployment-pitfall-catalog.md` exists and is populated.

**Step 4: Check other skills' references**

Grep across `skills/**/*.md` for references to `finishing-a-development-branch` to confirm no interface changes break callers:
- `executing-plans` should reference this skill
- `autopilot` should reference this skill
- `kanban-resolve` should reference this skill

The 4-option interface is internal to the skill (user-facing), so callers are unaffected by the Option 2 change.

---

## Task 11: Bump Plugin Version

**Files:**
- Modify: `.claude-plugin/plugin.json`

**Step 1: Read current version**

Read `.claude-plugin/plugin.json` to find current version.

**Step 2: Bump patch version**

Increment the patch version (e.g., 0.3.0 → 0.3.1) since this is a bugfix.

**Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: bump version to 0.3.1 for finishing-skill regression fix"
```

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Step 5 cleanup approach | Restore archived's simple version | Keep current's complex CWD detection |
| 2 | Option 1 merge logic | Assume main-repo CWD | Keep current's worktree branching |
| 3 | Smoke test scope entry | Generalize path references | Keep archived's project-specific paths |
| 4 | Scope of fixes | Only finishing-a-development-branch | Fix all 7 skills flagged by agent |

### Appendix: Decision Details

#### Decision 1: Step 5 cleanup approach
**Chose:** Restore archived's simple version (assume CWD is main repo)
**Why:** The restored CRITICAL section enforces that CWD must be the main repo. Given this precondition, the complex CWD detection in current's Step 5 is unnecessary defensive code. The simpler version is clearer and consistent with the CRITICAL section's guarantee. The complex version was added BECAUSE the CRITICAL section was removed — restoring the CRITICAL section makes the complex version redundant.
**Alternatives rejected:**
- Keep current's complex version: Adds ~20 lines of defensive code for a condition the CRITICAL section prevents. Creates confusion about whether worktree CWD is allowed or not.

#### Decision 2: Option 1 merge logic
**Chose:** Assume main-repo CWD (direct git commands, no `git -C`)
**Why:** Consistent with restored CRITICAL section. The archived version's approach is simpler and more reliable. The `git -C` branching in current was added as a workaround for the missing CRITICAL section — restoring the root cause (CRITICAL section) eliminates the need for the workaround.
**Alternatives rejected:**
- Keep current's branching logic: Contradicts the CRITICAL section which says "always run from main repo". Having both an enforcement rule AND a fallback for violating it sends mixed signals.

#### Decision 3: Smoke test scope entry
**Chose:** Generalize the "Wrong smoke test scope" common mistake to reference "critical flow paths" instead of project-specific paths
**Why:** The archived version referenced va-web-app-specific paths (`src/app/(app)/quick-consult/`, `src/app/(app)/board/`). These are meaningless in other projects. The generalized guidance ("critical flow paths") conveys the same principle without being project-specific.
**Alternatives rejected:**
- Keep archived's specific paths: Only useful for va-web-app, violates the plugin's repo-agnostic design.
- Remove the entry entirely: The principle (match scope to change impact) is universally valuable.

#### Decision 4: Scope of fixes
**Chose:** Only fix finishing-a-development-branch
**Why:** The other skills flagged by the agent analysis were verified as false positives (writing-plans features ARE present in current) or intentional changes (depersonalization, path normalization, generalization for plugin architecture). The add-advisor symlink simplification is a minor reduction in specificity, not a broken workflow. Only finishing-a-development-branch has confirmed lost functionality.
**Alternatives rejected:**
- Fix all 7 skills: Would introduce unnecessary churn for intentional changes. The agent's analysis conflated generalization (correct) with regression (incorrect) for most skills.

---

## Critique Panel Results

**Round 1 findings applied:**
- Fixed line count estimate (~130 → ~190)
- Added sequential dependency note in header
- Added architectural note to Task 2 Step 2 about defense-in-depth tension
- Added adaptation #6 to Task 3 Step 4 (remove archived line 487 parenthetical)
- Added missing "Worktree cleanup when CWD is safe" to Task 6 Common Mistakes (12 entries total)
- Added Task 9 to fix stale Integration section callers
- Renumbered Task 10 → Task 11
