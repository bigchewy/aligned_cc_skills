#!/usr/bin/env bash
set -u
# Note: intentionally NOT using set -e. Exit codes are checked explicitly
# after each critical command so we can print phase-specific diagnostics
# instead of dying silently.

# autopilot.sh — Full pipeline from design doc to verified branch
#
# Usage: autopilot.sh <project-path> <design-doc-path> [branch-name]
#
# Phases:
#   1. Write implementation plan (claude -p with writing-plans skill)
#   2. Create worktree + setup
#   3. Ralph loop (execute plan tasks one at a time)
#   4. Verify branch (tests, build, eval — no merge)
#
# The script stops after verification. The branch is NOT merged.
# Review the work, then merge manually or run the full finishing skill.
#
# Resume: Safe to re-run after interruption. Completed phases are detected
# and skipped automatically. The sentinel file is scoped to the design doc,
# so running with a different design doc starts a fresh pipeline.
#
# Environment variables:
#   MAX_ITERATIONS      — Ralph loop safety cap (default: 50)
#   ITERATION_TIMEOUT   — Ralph loop seconds per iteration (default: 900)
#   MAX_TIMEOUTS        — Ralph loop consecutive timeout cap (default: 5)
#   PHASE_TIMEOUT       — Timeout for plan-writing and verify phases (default: 3600 = 60 min)
#   MAX_MOCKUP_ITERATIONS — Mockup fidelity loop cap (default: 5)
#   MOCKUP_TIMEOUT      — Timeout per mockup fidelity iteration (default: 900 = 15 min)

PROJECT="${1:?Usage: autopilot.sh <project-path> <design-doc-path> [branch-name]}"
DESIGN_DOC="${2:?Usage: autopilot.sh <project-path> <design-doc-path> [branch-name]}"
BRANCH="${3:-}"
PHASE_TIMEOUT="${PHASE_TIMEOUT:-3600}"
MAX_MOCKUP_ITERATIONS="${MAX_MOCKUP_ITERATIONS:-5}"
MOCKUP_TIMEOUT="${MOCKUP_TIMEOUT:-900}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=lib/process.sh
source "$SCRIPT_DIR/lib/process.sh"
# shellcheck source=lib/stages.sh
source "$SCRIPT_DIR/lib/stages.sh"
# shellcheck source=lib/halt.sh
source "$SCRIPT_DIR/lib/halt.sh"

# Prompt files
WRITE_PLAN_PROMPT="$SCRIPT_DIR/WRITE-PLAN.md"
RALPH_SCRIPT="$SCRIPT_DIR/run-ralph.sh"
MOCKUP_PROMPT="$SCRIPT_DIR/MOCKUP-FIDELITY.md"
VERIFY_PROMPT="$SCRIPT_DIR/VERIFY-BRANCH.md"

# Skill files (referenced by WRITE-PLAN.md)
SKILL_FILE="$PLUGIN_ROOT/skills/writing-plans/SKILL.md"
CHECKLIST_FILE="$PLUGIN_ROOT/skills/writing-plans/plan-critique-checklist.md"
KANBAN_FORMAT="$PLUGIN_ROOT/skills/_shared/kanban-entry-format.md"

# --- Validation ---

for f in "$WRITE_PLAN_PROMPT" "$RALPH_SCRIPT" "$MOCKUP_PROMPT" "$VERIFY_PROMPT" "$SKILL_FILE" "$CHECKLIST_FILE" "$KANBAN_FORMAT"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: Missing required file: $f" >&2
    exit 1
  fi
done

PROJECT="$(cd "$PROJECT" && pwd)"
# Resolve DESIGN_DOC: relative paths are relative to PROJECT, not caller's cwd
if [[ "$DESIGN_DOC" != /* ]]; then
  DESIGN_DOC="$(cd "$PROJECT/$(dirname "$DESIGN_DOC")" && pwd)/$(basename "$DESIGN_DOC")"
else
  DESIGN_DOC="$(cd "$(dirname "$DESIGN_DOC")" && pwd)/$(basename "$DESIGN_DOC")"
fi

if [ ! -d "$PROJECT" ]; then
  echo "ERROR: Project directory does not exist: $PROJECT" >&2
  exit 1
fi

# Verify PROJECT is the main worktree, not a nested worktree
if [ -f "$PROJECT/.git" ]; then
  echo "ERROR: $PROJECT appears to be a git worktree, not the main repo." >&2
  echo "Pass the main repository path instead." >&2
  exit 1
fi

if [ ! -f "$DESIGN_DOC" ]; then
  echo "ERROR: Design doc does not exist: $DESIGN_DOC" >&2
  exit 1
fi

LOG="$PROJECT/.autopilot-log"
SENTINEL="$PROJECT/.autopilot-plan-path"
# STATUS is set after WORKTREE is known (Phase 2) so it lands inside the
# sandbox boundary.  Initialised empty here to satisfy set -u.
STATUS=""

# Log all output
if command -v stdbuf &>/dev/null; then
  exec > >(stdbuf -oL tee -a "$LOG") 2>&1
elif command -v gstdbuf &>/dev/null; then
  exec > >(gstdbuf -oL tee -a "$LOG") 2>&1
else
  exec > >(tee -a "$LOG") 2>&1
fi

# --- Halt protocol ---
# Pre-worktree halts live in the main repo; post-worktree halts live in the
# worktree (HALT_PATH is reassigned after the worktree phase).
HALT_PATH="$PROJECT/.autopilot-halt"
export HALT_PATH

# Pre-existing halt: surface and exit cleanly (re-run guidance)
if [ -f "$HALT_PATH" ]; then
  echo ""
  echo "Previous run halted. Sentinel content:"
  echo ""
  cat "$HALT_PATH"
  echo ""
  echo "Resolve the issue per fix-instructions above, delete .autopilot-halt, then re-run."
  exit 0
fi

# Helper to dispatch on phase exit code per the contract.
# Used for: preflight, plan, worktree, mockup, verify.
# NOT used for ralph (it has its own positional-arg signature; see below).
run_phase() {
  local n="$1" total="$2" name="$3" script="$4"
  report_stage "$n" "$total" "$name" running
  local exit_code=0
  bash "$script" || exit_code=$?
  case "$exit_code" in
    0) report_stage "$n" "$total" "$name" passed; return 0 ;;
    2)
      report_stage "$n" "$total" "$name" halted
      echo ""
      read_halt "$HALT_PATH"
      echo ""
      exit 0  # Clean halt — not a failure
      ;;
    3) report_stage "$n" "$total" "$name" skipped; return 3 ;;
    *)
      report_stage "$n" "$total" "$name" failed
      # Phase crashed (non-2 non-3 non-zero); write halt if no other halt exists
      if [ ! -f "$HALT_PATH" ]; then
        write_halt phase_crashed "$name" "Phase exited with code $exit_code"
      fi
      exit 1
      ;;
  esac
}

# --- Process management ---
# Functions (cleanup, kill_claude, start_heartbeat, stop_heartbeat,
# start_watchdog, stop_watchdog, run_claude_phase) sourced from lib/process.sh.

PROMPT_FILE=""
CLAUDE_PID=""
WATCHDOG_PID=""
HEARTBEAT_PID=""

handle_signal() {
  echo ""
  echo "Interrupted — shutting down..." >&2
  kill_claude
  exit 130
}
trap handle_signal INT TERM
trap cleanup EXIT

echo "========================================"
echo "  Autopilot Pipeline"
echo "========================================"
echo "Project:    $PROJECT"
echo "Design doc: $DESIGN_DOC"
echo "Branch:     ${BRANCH:-<auto-detect from plan>}"
echo "Log:        $LOG"
echo ""

# ============================================================
# Phase 1: Preflight (pre-plan) — env-only checks
# ============================================================

PLAN_FILE=""

export PROJECT DESIGN_DOC SENTINEL LOG PHASE_TIMEOUT
export WRITE_PLAN_PROMPT SKILL_FILE CHECKLIST_FILE KANBAN_FORMAT
export PLAN_FILE  # may be empty pre-Phase-2; preflight handles

run_phase 1 6 preflight "$SCRIPT_DIR/phases/preflight.sh" || true

# ============================================================
# Phase 2: Write implementation plan
# ============================================================

run_phase 2 6 plan "$SCRIPT_DIR/phases/plan.sh" || true

# Re-read PLAN_FILE from sentinel (phase wrote it)
if [ -f "$SENTINEL" ]; then
  PLAN_FILE="$(tail -1 "$SENTINEL")"
fi

if [ -z "$PLAN_FILE" ] || [ ! -f "$PLAN_FILE" ]; then
  echo "ERROR: Plan file missing after plan phase." >&2
  exit 1
fi
export PLAN_FILE
echo ""

# ============================================================
# Phase 1.5: Preflight (post-plan) — full manifest validation
# Re-run preflight now that PLAN_FILE exists; banner labels this as
# phase 1.5 so it's distinguishable from the pre-plan invocation.
# ============================================================

run_phase 1.5 6 preflight "$SCRIPT_DIR/phases/preflight.sh" || true
echo ""

# ============================================================
# Phase 2: Create worktree
# ============================================================

# Derive branch name from plan file if not provided
if [ -z "$BRANCH" ]; then
  PLAN_BASENAME="$(basename "$PLAN_FILE" .md)"
  # Strip leading date (YYYY-MM-DD-)
  FEATURE_SLUG="$(echo "$PLAN_BASENAME" | sed 's/^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}-//')"
  if [ -z "$FEATURE_SLUG" ]; then
    FEATURE_SLUG="$PLAN_BASENAME"
  fi
  BRANCH="feature/$FEATURE_SLUG"
fi

WORKTREE_DIR="$PROJECT/.worktrees/$(echo "$BRANCH" | sed 's|^feature/||')"
export PROJECT BRANCH PLAN_FILE WORKTREE_DIR

run_phase 3 6 worktree "$SCRIPT_DIR/phases/worktree.sh"

WORKTREE="$WORKTREE_DIR"
STATUS="$WORKTREE/.finish-status"
PLAN_IN_WORKTREE="$WORKTREE/docs/plans/$(basename "$PLAN_FILE")"

# Reassign HALT_PATH to the worktree for post-worktree phases
HALT_PATH="$WORKTREE/.autopilot-halt"
export HALT_PATH
echo ""

# ============================================================
# Phase 3: Ralph loop
# ============================================================

report_stage 4 6 ralph running

# Check if all tasks are already complete
TOTAL_TASKS=0
DONE_TASKS=0
TASK_REGEX='^### (✅|🔄|⏭️)?[[:space:]]*Task[[:space:]]*[0-9]'
# A task is "settled" if it is ✅ (completed) or ⏭️ (auto-skipped by the
# wrapper after MAX_BLOCKED_ITERATIONS consecutive blocks). Both states
# mean the ralph loop has nothing more to do for that task.
DONE_REGEX='^### (✅|⏭️)[[:space:]]*Task[[:space:]]*[0-9]'
if grep -qE "$TASK_REGEX" "$PLAN_IN_WORKTREE" 2>/dev/null; then
  TOTAL_TASKS="$(grep -cE "$TASK_REGEX" "$PLAN_IN_WORKTREE" || true)"
  DONE_TASKS="$(grep -cE "$DONE_REGEX" "$PLAN_IN_WORKTREE" || true)"
fi

if [ "$TOTAL_TASKS" -gt 0 ] && [ "$TOTAL_TASKS" -eq "$DONE_TASKS" ]; then
  echo "All $TOTAL_TASKS tasks already complete — skipping Ralph loop."
  report_stage 4 6 ralph skipped
  echo ""
else
  if [ "$TOTAL_TASKS" -gt 0 ]; then
    echo "$DONE_TASKS/$TOTAL_TASKS tasks complete. Starting Ralph loop..."
  else
    echo "Starting Ralph loop..."
  fi
  echo ""

  # Ralph uses positional args + sentinels rather than the run_phase
  # exit-code contract. Under the unattended-autopilot policy the loop
  # never halts for human action; tasks that can't proceed are routed
  # through the wrapper's BLOCKED + auto-skip path (run-ralph.sh).
  RALPH_EXIT=0
  bash "$RALPH_SCRIPT" "$WORKTREE" "$PLAN_IN_WORKTREE" || RALPH_EXIT=$?

  if [ "$RALPH_EXIT" -ne 0 ]; then
    report_stage 4 6 ralph failed
    echo ""
    echo "ERROR: Ralph loop failed (exit code $RALPH_EXIT)." >&2
    echo "Progress is preserved — completed tasks are committed." >&2
    echo "Check the Ralph log at $WORKTREE/.ralph-log for details." >&2
    echo "Re-run this script to resume from the last completed task." >&2
    exit 1
  fi

  echo ""
  report_stage 4 6 ralph passed
  echo ""
fi

# ============================================================
# Phase 3.5: Mockup fidelity loop
# ============================================================

export WORKTREE PLAN_IN_WORKTREE MOCKUP_PROMPT MAX_MOCKUP_ITERATIONS MOCKUP_TIMEOUT
run_phase 5 6 mockup "$SCRIPT_DIR/phases/mockup.sh" || true  # mockup never halts
echo ""

# ============================================================
# Phase 4: Verify branch
# ============================================================

export BRANCH WORKTREE PLAN_IN_WORKTREE PROJECT VERIFY_PROMPT PHASE_TIMEOUT STATUS
run_phase 6 6 verify "$SCRIPT_DIR/phases/verify.sh"
echo ""

# ============================================================
# Report
# ============================================================

if [ -f "$STATUS" ]; then
  RESULT="$(grep '^status:' "$STATUS" 2>/dev/null | awk '{print $2}')"
  if [ "$RESULT" = "FAILED" ]; then
    echo ""
    echo "Autopilot finished, but verification failed."
    echo ""
    cat "$STATUS"
    echo ""
    echo "To fix this, either:"
    echo "  1. Re-run this script (completed phases will be skipped)"
    echo "  2. Fix manually in: $WORKTREE"
    echo ""
    echo "If mockup fixes caused the failure, also run:"
    echo "  rm $WORKTREE/.mockup-clean"
    echo "to re-enable the mockup fidelity loop on the next run."
    # Clean up status so re-run will re-verify
    rm -f "$STATUS"
    exit 1
  fi
fi

echo ""
echo "Done. All phases passed."
echo ""
echo "  Branch:   $BRANCH"
echo "  Worktree: $WORKTREE"
echo "  Plan:     $PLAN_IN_WORKTREE"
echo ""
echo "The branch is ready for review but hasn't been merged yet."
echo "To review and merge, open Claude in the project root and run the finishing skill:"
echo ""
echo "  cd $PROJECT"
echo "  claude"
echo "  /aligned:finishing-a-development-branch for $BRANCH at $WORKTREE"

# Clean up sentinel and status
rm -f "$SENTINEL"
rm -f "$STATUS"
