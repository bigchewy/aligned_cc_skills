---
name: kanban-resolve
description: "Triages and resolves all accumulated Kanban board items in a single automated pass. Use when the board has multiple pending items in docs/kanban/todo/ to process as a batch."
---

# Kanban Resolve

Orchestrates end-to-end resolution of all Kanban board items: triage, plan, execute, finish.

**Announce at start:** "I'm using the kanban-resolve skill to process the Kanban board."

## Phase 1: Scan

List all `KB-*.md` files in `docs/kanban/todo/` using Glob.

If empty, report "No items in the Kanban board" and stop.

Ensure `docs/kanban/did_not_complete/` directory exists (create with `mkdir -p docs/kanban/did_not_complete/` if needed).

## Phase 2: Triage

Launch the `kanban-triage` agent via Task tool for each KB item. Batch in parallel groups of up to 5. Wait for each batch to complete before launching the next. Report progress between batches: "Batch N/M complete: X triaged (Y CONFIRM, Z CLOSE, W failed)."

**Task prompt format for each item:**
```
Triage docs/kanban/todo/KB-NNN-slug.md
```

No overrides. Let the triage agent follow its standard process.

**If a triage agent fails:** Note the KB item as "triage failed" and continue with remaining items.

After all triage batches complete:

1. **Recover orphaned files:** Scan `docs/kanban/in-progress/` for any remaining KB files (these are failed triages that crashed after moving from `todo/` but before completing). Move each back to `docs/kanban/todo/`. Log them as triage failures.

2. **Collect verdicts** from each triage agent's Task output. Build two lists:
   - **Actionable:** CONFIRM and REVISE items (become plan tasks)
   - **Skipped:** CLOSE items

3. **Route CLOSE items:** Move each CLOSE item from `docs/kanban/done/` to `docs/kanban/did_not_complete/`. The triage agent moved them to `done/` per its standard process — the orchestrator reroutes them here because `done/` is reserved for items that were actually executed.

**Do NOT commit yet.** File moves are staged but uncommitted until the user approves in Phase 4.

**If all items are CLOSE or failed:** Report summary to the user. No plan needed — commit the file moves and stop.

## Phase 3: Build Plan

Create `docs/plans/YYYY-MM-DD-kanban-resolve.md` (replace `YYYY-MM-DD` with today's date) using the writing-plans output format.

**Grouping:** Combine KB items that share the same mechanical fix into a single task. Two items share a fix pattern when they apply identical code changes to different files (e.g., replacing inline `NextResponse.json` errors with `ApiErrors` methods). Keep items separate when the changes differ structurally (e.g., "migrate to utility" vs. "split large file").

**Plan structure:**

```markdown
# Kanban Board Resolution Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Resolve N Kanban board items (M actionable, K skipped)
**Source Design Doc:** N/A
**Architecture:** Mechanical refactoring — no architectural changes
**Tech Stack:** [read from CLAUDE.md Tech Stack section]

---

## Skipped Items

| KB | Title | Reason |
|----|-------|--------|
| KB-NNN | [title from KB entry] | [CLOSE reason from triage verdict] |

---

### Task 1: [Title — may group multiple KBs]

**KBs:** KB-NNN, KB-NNN (if grouped)

**Files:**
- Modify: `path/to/file.ts`

**Step 1:** [From triage's validated fix]
**Step 2:** ...
**Step N:** Run `npm run build` to verify compilation
**Step N+1:** Run `npm test` to verify no regressions
**Step N+2:** Commit changes

---

### Task N: ...

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|-------------|------------------------|
| 1 | Item grouping | [describe] | [alternatives] |

### Appendix: Decision Details
[Why items were grouped or kept separate]
```

Every task MUST end with build verification (`npm run build`), test verification (`npm test`), and a commit step.

**Override writing-plans "Fact-Check + Critique Panel" requirement:** Skip the critique panel. Triage agents already performed 5-phase root cause analysis on each item individually, including fix validation and risk assessment. The plan groups pre-validated mechanical changes — it does not introduce new architectural decisions. If grouping creates tasks that modify the same file, note the dependency in the plan's Decision Log so executing-plans respects ordering.

**Scale check:** If the plan has more than 10 tasks after grouping, warn the user in Phase 4: "This plan has N tasks. Executing in a single session may hit context window limits and degrade quality on later tasks. Consider splitting into 2-3 runs or using the Ralph Wiggum loop for fresh context per task." Include this in the Phase 4 summary so the user can choose the execution strategy before approving.

## Phase 4: Present for Approval

Summarize to the user:
- Total items triaged: N (M actionable, K skipped)
- Skipped items with reasons (user may override any CLOSE verdict)
- Task groupings and estimated scope
- Any triage failures
- Scale warning if applicable (>10 tasks)

**Wait for user approval before proceeding.**

After approval, commit the triage file moves:
```
git add docs/kanban/
git commit -m "chore: triage kanban board items"
```

## Phase 5: Setup and Execute

After approval and triage commit:

1. Verify you are on `main`:
   ```
   git branch --show-current
   ```

2. Commit the plan file to main:
   ```
   git add docs/plans/YYYY-MM-DD-kanban-resolve.md
   git commit -m "docs: add kanban resolution plan"
   ```

3. Create feature branch and worktree:
   ```
   git worktree add .worktrees/kanban-resolve-YYYY-MM-DD -b kanban-resolve-YYYY-MM-DD
   ```
   If the `git worktree add` command fails because the worktree already exists:
   1. Check for uncommitted changes: `git -C .worktrees/kanban-resolve-YYYY-MM-DD status --porcelain`
   2. If changes exist, warn the user: "Existing worktree has uncommitted changes from a previous run. Stash, commit, or discard?" Wait for decision.
   3. Once clean, run each command separately (do NOT chain with `&&`):
      - `git worktree remove .worktrees/kanban-resolve-YYYY-MM-DD --force`
      - `git branch -D kanban-resolve-YYYY-MM-DD`
   4. Retry the `git worktree add` command.

4. Verify the worktree exists: run `ls <worktree-path>` via Bash. Then invoke `/aligned:executing-plans` via the Skill tool.

5. **After executing-plans completes:** It will report completion and instruct you to tell the user to run `/aligned:finishing-a-development-branch` manually. Disregard that instruction — this skill orchestrates the full lifecycle and handles finishing in Phase 6. Note: executing-plans will also archive the plan file to `docs/plans/completed/` in its Step 5. This is expected; Phase 6's finishing skill will detect the plan was already archived and skip re-archiving.

### Phase 5 Blocker Recovery

If executing-plans stops before completing all tasks (blocker, repeated verification failure, context degradation):

1. **Capture state:** Note which tasks completed successfully and which remain.
2. **Report to user:** "Executing-plans stopped at task N of M. Tasks 1-N completed. Remaining: [list]."
3. **Present options:**
   - **(a) Fix and resume:** Describe the blocker. If resolvable, fix it and continue executing remaining tasks.
   - **(b) Finish partial work:** Proceed to Phase 6 with what's done. Remaining KB items stay in `docs/kanban/done/` with their triage annotations for pickup in a future session.
   - **(c) Discard:** Abandon the worktree. Move completed KB items back to `todo/` for a fresh run.

Wait for user decision before proceeding.

## Phase 6: Finish

After executing-plans reports completion, invoke `/aligned:finishing-a-development-branch` via the Skill tool. Follow its verification gates and deployment options.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Launching all triages at once | Batch in parallel groups of 5, wait between batches |
| Building plan before all triages complete | Wait for every triage to finish |
| Including CLOSE items as plan tasks | CLOSE items go to `did_not_complete/` only |
| Not grouping similar items | Combine items with identical mechanical fixes |
| Skipping build+test verification per task | Every task ends with `npm run build` and `npm test` |
| Proceeding without plan approval | Always pause for user review after Phase 4 |
| Committing file moves before user approval | Defer `git add`/`git commit` until after Phase 4 |
| Not scanning `in-progress/` after triage | Orphaned files from failed triages must be recovered |
| Force-removing an existing worktree without checking for uncommitted changes | Check `git status --porcelain` first, ask user |
| Ignoring executing-plans' completion message about finishing | This skill handles finishing in Phase 6 — disregard that instruction |
| Not reporting progress between triage batches | Show batch N/M and verdict counts between batches |
