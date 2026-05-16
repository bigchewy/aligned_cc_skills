---
---
# Simplify Autopilot Halt + Merge Handling Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Delete the misnamed `uncommitted_main` halt reason and its surrounding dead code (auto-abort of merge state, secondary-halt append, non-conflict failure swallower) so the autopilot pipeline halt taxonomy reflects only failure modes that actually fire.

**Source Design Doc:** `N/A` — this plan implements the root-cause analysis written in conversation on 2026-05-16 (filed as `docs/kanban/todo/KB-074-uncommitted-main-halt-reason-mislabeled.md`).

**Architecture:** When `git merge main` fails inside the worktree phase, let it fail with git's native diagnostic (which is more informative than any heredoc we maintain) and exit non-zero — `autopilot.sh`'s `run_phase` already converts that into `phase_crashed`. No halt-with-reason, no auto-abort destroying the conflict state, no secondary-halt append in `lib/halt.sh`. The drift-detector test `test_format_halt_cases_match_write_halt_callsites` enforces that `format_halt` cases and `write_halt` callsites stay in balance; pairing halt.sh and worktree.sh changes in one commit keeps the detector green between commits.

**Tech Stack:** Bash (POSIX-ish, the autopilot's existing style — `set -u`, no `set -e`); pytest + subprocess for assertions over the bash scripts. No new dependencies.

---

## Prerequisites

None — all work happens on a clean worktree branch off main.

---

### Task 1: Drop test assertions for removed surfaces

**Files:**
- Modify: `e2e/tests/test_halt_protocol.py` (the `EXPECTED_REASONS` list, the `test_format_halt_echoes_canonical_fix` parametrize, and the `test_write_halt_secondary_appends_not_overwrites` function)
- Modify: `e2e/tests/test_phase_contracts.py` (the `uncommitted_main` assertion in `test_phase_worktree_*` and the `worktree` entry in the `test_halt_emitting_phase_sources_lib_halt` parametrize — both block Task 2)

This task only weakens assertions — it does not yet change any shell script. Tests must still pass after this task because the removed assertions become silent rather than failing.

**Ordering dependency:** Task 2 removes the `write_halt uncommitted_main` callsite AND the `source "$RALPH_DIR/lib/halt.sh"` line from `worktree.sh`. Two assertions in `test_phase_contracts.py` will fail when Task 2 lands unless this task pre-emptively removes them: (1) the `assert "uncommitted_main" in text` at line 159, and (2) `"worktree"` in the `["preflight", "worktree", "verify"]` parametrize at line 167 of `test_halt_emitting_phase_sources_lib_halt`. Both come out here.

**Step 1: Drop `uncommitted_main` from `EXPECTED_REASONS`**

In `e2e/tests/test_halt_protocol.py`, remove the `"uncommitted_main",` line from `EXPECTED_REASONS` (currently the 4th item in the list).

After edit, the list should read:

```python
EXPECTED_REASONS = [
    "mcp_unreachable",
    "mcp_tool_not_allowlisted",
    "manifest_malformed",
    "verify_failed",
    "phase_crashed",
]
```

**Step 2: Drop the `uncommitted_main` parametrize row**

In `test_format_halt_echoes_canonical_fix`, delete the line:

```python
    ("uncommitted_main", "git merge main"),
```

The remaining four parametrize rows stay as-is.

**Step 3: Delete `test_write_halt_secondary_appends_not_overwrites`**

Delete the entire function (match by function name, not line number) along with the blank line above it. The next remaining test should be the `@pytest.mark.parametrize(...)`-decorated `test_format_halt_echoes_canonical_fix`.

**Step 4: Remove the `uncommitted_main` assertion in `test_phase_contracts.py`**

In `e2e/tests/test_phase_contracts.py`, delete the explanatory comment `# Emits the structured halt for uncommitted-main case` and the immediately-following `assert "uncommitted_main" in text` (match by content, not line number). Both live inside the worktree-phase header conformance test.

**Step 5: Remove `worktree` from the halt-source parametrize**

In the same file, the parametrize on `test_halt_emitting_phase_sources_lib_halt` reads:

```python
@pytest.mark.parametrize("phase_name", ["preflight", "worktree", "verify"])
```

Change it to:

```python
@pytest.mark.parametrize("phase_name", ["preflight", "verify"])
```

Once Task 2 lands, `worktree.sh` will neither source `lib/halt.sh` nor call `write_halt` — it has no halt-emitting code path. Keeping it in this parametrize would assert behavior the file intentionally no longer has.

**Step 6: Run the affected tests; expect PASS**

```bash
python3 -m pytest e2e/tests/test_halt_protocol.py e2e/tests/test_phase_contracts.py -q
```

Expected: all remaining tests pass. (Baseline before this task: `test_halt_protocol.py` is 12 passed. After this task: 10 passed in that file — three parametrize/assertion paths removed, one whole test removed. `test_phase_contracts.py` is unchanged in count but has two fewer assertions in its body.)

**Step 7: Commit**

```bash
git add e2e/tests/test_halt_protocol.py e2e/tests/test_phase_contracts.py
git commit -m "test: drop assertions for uncommitted_main, secondary-halt, and worktree halt-source"
```

---

### Task 2: Delete `uncommitted_main` halt reason from code

**Files:**
- Modify: `docs/ralph_loops/lib/halt.sh` (the `uncommitted_main)` case in `format_halt()`)
- Modify: `docs/ralph_loops/phases/worktree.sh` (the EXIT CODES header comment, the `source "$RALPH_DIR/lib/halt.sh"` line, and the merge-failure handling block)

These two files must change together. The drift-detector test (`test_format_halt_cases_match_write_halt_callsites`) enforces that `format_halt` cases and `write_halt` callsites stay in balance across all `.sh` files in `lib/` and `phases/`; pairing the changes in one commit ensures the detector never sees an imbalanced state between commits.

**Step 1: Delete the `uncommitted_main` case in `lib/halt.sh`**

In `docs/ralph_loops/lib/halt.sh`, locate the `uncommitted_main)` case block (currently around line 100). Delete the entire case — from `    uncommitted_main)` through the closing `      ;;` — including the heredoc. No replacement; the case statement now has six entries instead of seven.

**Step 2: Replace the merge-failure block in `worktree.sh`**

In `docs/ralph_loops/phases/worktree.sh`, locate the comment `# Merge main so the plan file is available in the worktree` (match by comment text). Replace the entire block from that comment through the end of the `if [ "$MERGE_EXIT" -ne 0 ]; then ... fi` (the one matching the comment about non-conflict failure) with:

```bash
# Merge main so the plan file is available in the worktree.
# On failure, let git's native diagnostic print to stderr and exit 1;
# autopilot.sh's run_phase converts that to phase_crashed. Do NOT auto-abort —
# the user needs the MERGE_HEAD state preserved to resolve conflicts in place.
if ! git merge main --no-edit; then
  echo "ERROR: git merge main failed in $WORKTREE_DIR. Resolve in the worktree, commit, then re-run autopilot." >&2
  exit 1
fi
```

This removes three pieces of complexity at once:
- The `MERGE_EXIT=0` / `||` / `if [ "$MERGE_EXIT" -ne 0 ]` shape — replaced by a direct `if !` guard.
- The `MERGE_HEAD`-detection + `git merge --abort` + `write_halt uncommitted_main` branch — gone.
- The "Non-conflict failure (e.g., already up to date with divergent message)" warning branch — gone (its message was wrong; "already up to date" exits 0, and the warning silently continued past real failures like a dirty worktree).

**Behavior change to acknowledge:** Non-conflict, non-zero exits from `git merge main` previously logged a warning and continued execution. They now exit 1. This is correct — the prior path silently swallowed real failures (e.g., dirty worktree blocking the merge) by mislabeling them as "may already be up to date." Treat as an intentional behavioral correction, not a regression.

**Step 3: Update the EXIT CODES header comment in `worktree.sh`**

Near the top of `worktree.sh`, in the EXIT CODES section, the comment reads:

```
#   2 — halt-with-reason: uncommitted_main (merge conflict against main)
```

Delete that entire line. Worktree no longer emits exit code 2; the surviving codes are 0 (success) and 1 (any failure).

**Step 4: Remove the `lib/halt.sh` source line in `worktree.sh`**

With the `write_halt` call gone, `worktree.sh` no longer uses anything from `lib/halt.sh`. Delete these two lines from the source block near the top of the file:

```bash
# shellcheck source=../lib/halt.sh
source "$RALPH_DIR/lib/halt.sh"
```

`lib/process.sh` is still sourced (worktree.sh doesn't currently use anything from process.sh either, but that's outside this plan's scope — leave it for now).

**Step 5: Run halt-protocol tests**

```bash
python3 -m pytest e2e/tests/test_halt_protocol.py -q
```

Expected: PASS. The drift detector confirms `format_halt` cases match `write_halt` callsites — both lost `uncommitted_main` together.

**Step 6: Run the full e2e suite**

```bash
python3 -m pytest e2e/tests/ -q
```

Expected: PASS. Task 1 already cleared the `test_phase_contracts.py` assertions that referenced `uncommitted_main` and the worktree halt-source parametrize, so the surviving structural checks (env-link block, header fields, `WORKTREE_DIR` env-read) still hold.

**Step 7: Commit**

```bash
git add docs/ralph_loops/lib/halt.sh docs/ralph_loops/phases/worktree.sh
git commit -m "fix(autopilot): delete misnamed uncommitted_main halt + abort-on-conflict

The uncommitted_main halt reason fired for merge conflicts (real) while
its name and fix-instructions described a different scenario (dirty
main) that the code path could never produce. Worse, the handler called
git merge --abort, destroying the conflict state the user needed to
resolve in place. Replace with a plain failure: git's stderr is more
informative than the heredoc we maintained, and MERGE_HEAD now stays
set so the user can cd into the worktree and resolve directly.

Closes KB-074."
```

---

### Task 3: Simplify `write_halt` — remove secondary-halt append

**Files:**
- Modify: `docs/ralph_loops/lib/halt.sh` (the existing-file branch in `write_halt`)

`autopilot.sh:144-159` exits on the first halt (exit code 2 routes to `read_halt` + `exit 0`; non-2-non-3-non-0 writes `phase_crashed` only if no halt exists, then `exit 1`). A second `write_halt` in the same run is unreachable. Across runs, the user deletes the sentinel before re-running. The append branch is dead code with a test (already deleted in Task 1) that exercised a fictional state machine.

**Step 1: Delete the existing-file branch in `write_halt`**

In `docs/ralph_loops/lib/halt.sh`, locate the block starting with `if [ -f "$target" ]; then` (currently around line 23) and ending with the matching `fi` before the `{` that opens the primary write. Delete the entire `if [ -f "$target" ]; then ... fi` block, including the `return 0` inside it.

The simplified `write_halt` should read (excerpt — only showing the function body around the deleted block):

```bash
write_halt() {
  local reason="$1"
  local phase="$2"
  local details="${3:-}"
  local target="${HALT_PATH:-.autopilot-halt}"
  local tmp="${target}.tmp.$$"
  local log="${LOG:-(unknown)}"

  {
    echo "reason: $reason"
    echo "phase: $phase"
    echo "log: $log"
    echo "next-action: see fix-instructions below"
    if [ -n "$details" ]; then
      echo "details: $details"
    fi
    echo "fix-instructions: |"
    format_halt "$reason" | sed 's/^/  /'
  } > "$tmp"
  mv "$tmp" "$target"
}
```

The atomic `mv` from `.tmp.$$` to `$target` still gives first-writer-wins-via-overwrite semantics within a single run; since the orchestrator exits on first halt, "first writer wins" reduces to "only writer."

**Step 2: Run halt-protocol tests**

```bash
python3 -m pytest e2e/tests/test_halt_protocol.py -q
```

Expected: PASS. No test exercises the deleted branch (we removed `test_write_halt_secondary_appends_not_overwrites` in Task 1).

**Step 3: Commit**

```bash
git add docs/ralph_loops/lib/halt.sh
git commit -m "refactor(autopilot): remove unreachable secondary-halt append in write_halt

The orchestrator exits on the first halt (autopilot.sh:144-159), so a
second write_halt in the same run is unreachable. The append branch
existed to handle a state machine that doesn't exist."
```

---

### Task 4: Delete stale-merge-state auto-abort from `worktree.sh`

**Files:**
- Modify: `docs/ralph_loops/phases/worktree.sh` (the "Check for stale merge state" block when the worktree pre-exists)

With Task 2 applied, `MERGE_HEAD` being set on entry means a prior autopilot run hit conflicts that the user has not resolved. Auto-aborting the merge destroys that recovery state — exactly the bug Task 2 fixed for the same-run case, repeated for the cross-run case. The simplest correct behavior is: do nothing on entry; let the subsequent `git merge main` fail naturally with git's "You have not concluded your merge (MERGE_HEAD exists)" message, which is already a clear diagnostic.

**Step 1: Delete the stale-merge-state check**

In `docs/ralph_loops/phases/worktree.sh`, locate the block that begins `  # Check for stale merge state` (currently around line 37) inside the `if [ -d "$WORKTREE_DIR" ]; then` branch. Delete from that comment through the closing `  fi` of the inner check (currently line 41), removing the now-empty line between the `echo "Worktree already exists..."` and the start of the outer `else` branch.

After this change, the existing-worktree branch should read:

```bash
if [ -d "$WORKTREE_DIR" ]; then
  echo "Worktree already exists: $WORKTREE_DIR"
else
  echo "Creating worktree: $WORKTREE_DIR (branch: $BRANCH)"
  ...
```

**Step 2: Run the full e2e suite**

```bash
python3 -m pytest e2e/tests/ -q
```

Expected: PASS. (`test_phase_contracts.py` may assert on the worktree.sh structure — verify the changes don't violate its expectations.)

**Step 3: Commit**

```bash
git add docs/ralph_loops/phases/worktree.sh
git commit -m "fix(autopilot): stop auto-aborting prior merge state in worktree phase

If MERGE_HEAD is set on entry, a prior autopilot run hit conflicts the
user hasn't resolved. Auto-aborting destroys that recovery state. Let
the subsequent git merge main fail naturally — git's own message is
clearer than what we were doing silently."
```

---

### Task 5: Update halt-format reference doc

**Files:**
- Modify: `skills/_shared/autopilot-halt-format.md` (taxonomy table and write-protocol section)

This doc is the user-facing reference for the halt taxonomy. The drift-detector test only enforces parity between halt.sh and callsites; the doc has to be brought in line manually.

**Step 1: Remove the `uncommitted_main` row from the taxonomy table**

In `skills/_shared/autopilot-halt-format.md`, locate the row beginning `| \`uncommitted_main\` |` (currently line 41) and delete the entire line. The table loses one row; the remaining six rows are correct.

**Step 2: Soften the secondary-halt reference**

The write-protocol section mentions "If `$HALT_PATH` already exists, append a `secondary-halt:` block rather than overwriting — preserves evidence" (currently around line 24). With Task 3 applied, this is no longer the behavior. Delete that sentence (item 3 in the numbered list). Renumber subsequent items so item 4 becomes 3.

**Step 3: Run the doc-existence test**

```bash
python3 -m pytest e2e/tests/test_halt_protocol.py::test_halt_format_doc_lists_all_reasons -q
```

Expected: PASS. With `uncommitted_main` already removed from `EXPECTED_REASONS` in Task 1, this test verifies the doc lists the remaining five reasons in `EXPECTED_REASONS` (`mcp_unreachable`, `mcp_tool_not_allowlisted`, `manifest_malformed`, `verify_failed`, `phase_crashed`). Note that `headless_auth_incompat` exists in `format_halt()` and remains documented in the taxonomy table, but is not in `EXPECTED_REASONS` — that's pre-existing state, not affected by this plan.

**Step 4: Commit**

```bash
git add skills/_shared/autopilot-halt-format.md
git commit -m "docs(autopilot): align halt-format doc with simplified taxonomy"
```

---

### Task 6: Full-suite verification

**Files:** None — verification only.

**Step 1: Run the full e2e suite**

```bash
python3 -m pytest e2e/tests/ -q
```

Expected: all tests pass. If any test fails that wasn't expected to be touched by this plan, stop and investigate before claiming completion. Likely culprits if something does fail: a test that grepped `worktree.sh` for the old structure (e.g., `test_phase_contracts.py` checking exit codes 0/1/2 instead of 0/1).

**Step 2: Smoke-check the new merge-failure path manually**

```bash
bash -n docs/ralph_loops/phases/worktree.sh
bash -n docs/ralph_loops/lib/halt.sh
```

Expected: both exit 0 (syntax-clean).

**Step 3: Confirm the drift detector still has teeth**

```bash
python3 -m pytest e2e/tests/test_halt_protocol.py::test_format_halt_cases_match_write_halt_callsites -v
```

Expected: PASS. This is the test that would fail-fast if a future change re-introduces drift between `format_halt` cases and `write_halt` callsites — make sure it's still being exercised.

No commit for this task.

---

## Manual Steps (Post-Automation)

None.

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | What to do with `uncommitted_main` | Delete entirely; let `git merge` print its own diagnostic | Rename to `worktree_merge_conflict` + rewrite heredoc; keep but make the trigger condition match the name |
| 2 | Whether to preserve MERGE_HEAD on failure | Yes — exit 1, no auto-abort | Auto-abort (current behavior); auto-abort + write a halt with conflict file list |
| 3 | Whether to keep secondary-halt append in `write_halt` | Delete | Keep as defensive future-proofing |
| 4 | Whether to keep stale-merge-state auto-abort in entry path | Delete | Convert to exit-1-with-guidance; keep auto-abort |
| 5 | TDD order | Tests first (drop assertions), then code (drop reasons + callsites paired) | Code first; alternating per-feature |

### Appendix: Decision Details

#### Decision 1: Delete `uncommitted_main` entirely

**Chose:** Delete the halt reason; convert the failure path to a plain non-zero exit from worktree.sh and let `autopilot.sh`'s `run_phase` write `phase_crashed` if needed.

**Why:** `git merge main` already prints exactly which files conflict and what state they're in. The current heredoc reduplicates that information at lower fidelity (no file paths, no conflict markers, just "resolve in worktree"). Maintaining the heredoc creates a second source of truth that has already drifted once — the reason name and fix-instructions described "uncommitted on main," a scenario the code path cannot actually produce (`git merge main` from a separate worktree merges the *committed* ref `refs/heads/main`; main's working tree being dirty is irrelevant). The mismatch caused a real user-impact incident on 2026-05-15: main was clean, the halt fired anyway for a merge conflict, and the fix-instructions sent the user to investigate a non-problem.

**Alternatives rejected:**
- *Rename to `worktree_merge_conflict` + rewrite heredoc.* Preserves the halt-with-structured-fix machinery, but the machinery doesn't earn its keep when the underlying tool already prints clear diagnostics. Two surfaces to maintain (`halt.sh` + taxonomy doc), drift risk again in the future.
- *Keep name, fix the trigger condition.* Would require adding a pre-merge `git -C "$PROJECT" diff --quiet && git -C "$PROJECT" diff --cached --quiet` check on main. But uncommitted state on main doesn't actually block the merge into the worktree, so the check would be testing for a non-failure.

#### Decision 2: Preserve MERGE_HEAD on failure (no auto-abort)

**Chose:** When `git merge main` fails in worktree.sh, exit 1 without calling `git merge --abort`. The user `cd`s into the worktree and resolves with the conflict markers still present.

**Why:** The existing auto-abort destroys the exact state the user needs. After the previous incident the user had to manually re-run `git merge main` to surface the conflicts again, which is busywork the script created. Preserving MERGE_HEAD makes the recovery path `cd $worktree && git status && fix && git add && git commit && cd $project && rm .autopilot-halt && re-run-autopilot` — same number of steps without the synthetic re-merge.

**Alternatives rejected:**
- *Auto-abort (status quo).* Forces the user to re-trigger the merge to see conflict state.
- *Auto-abort + write a halt that lists the conflict files.* More user-friendly than current, but reduplicates `git status` output and requires parsing git porcelain in bash. Not worth the complexity when leaving MERGE_HEAD set achieves the same outcome with zero code.

#### Decision 3: Delete the secondary-halt append branch in `write_halt`

**Chose:** Remove the `if [ -f "$target" ]; then ... append ... return 0; fi` block. `write_halt` always overwrites via the atomic `mv` from `.tmp.$$`.

**Why:** The orchestrator at `autopilot.sh:144-159` exits on the first halt — exit code 2 routes through `read_halt` and `exit 0`; non-2-non-3-non-0 writes `phase_crashed` only if no halt exists, then `exit 1`. A second `write_halt` in the same run is unreachable. Across runs, the contract in `autopilot-halt-format.md` says the user deletes the sentinel before re-running. The append branch handled a state machine that doesn't exist; the test for it (`test_write_halt_secondary_appends_not_overwrites`) exercised an unreachable code path and is being deleted in Task 1.

**Alternatives rejected:**
- *Keep as defensive future-proofing.* The pattern across this codebase is favoring "fits the actual contract" over "guards against hypothetical contract violations." Dead branches accumulate cognitive load and create drift surfaces.

#### Decision 4: Delete the stale-merge-state auto-abort

**Chose:** Remove the `worktree.sh:36-41` block that detects MERGE_HEAD on entry to a pre-existing worktree and auto-aborts.

**Why:** Same logic as Decision 2 at the cross-run boundary. If a prior run left MERGE_HEAD set, that IS the conflict state the user is supposed to resolve. Auto-aborting on the next run nukes their context. The subsequent `git merge main` call will fail with git's clear "You have not concluded your merge (MERGE_HEAD exists). Please, commit your changes before you merge." — pointing the user to the right action.

**Alternatives rejected:**
- *Convert to exit-1-with-guidance.* Considered: detect MERGE_HEAD on entry, print "worktree has unresolved merge; resolve and re-run", exit 1. Less risky than auto-abort, but the subsequent `git merge main` produces an equivalent message for free. The extra check is just noise.

#### Decision 5: TDD order — tests first

**Chose:** Task 1 weakens test assertions (drops `uncommitted_main` from EXPECTED_REASONS, drops the parametrize row, deletes the secondary-halt test); Tasks 2–4 then change code. The drift detector (`test_format_halt_cases_match_write_halt_callsites`) stays green throughout because the paired changes in halt.sh and worktree.sh land in the same commit.

**Why:** With the drift detector as a safety, removing assertions before removing implementations means each task ends in a green state. The alternative — change halt.sh first, then worktree.sh — produces a red state in between that's hard to revert without losing the half-done work.

**Alternatives rejected:**
- *Code first, then tests.* Produces a red state in the middle. With paired changes (halt.sh + worktree.sh in one commit) this is short-lived but still risks getting stuck.
- *Alternating per-feature.* More commits, no real benefit. The five-task structure already separates the four conceptual changes (delete reason, simplify write_halt, drop stale-merge auto-abort, sync taxonomy doc).
