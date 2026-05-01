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
# Phase 1: Write implementation plan
# ============================================================

PLAN_FILE=""

export PROJECT DESIGN_DOC SENTINEL LOG PHASE_TIMEOUT
export WRITE_PLAN_PROMPT SKILL_FILE CHECKLIST_FILE KANBAN_FORMAT

report_stage 2 6 plan running
PLAN_PHASE_EXIT=0
bash "$SCRIPT_DIR/phases/plan.sh" || PLAN_PHASE_EXIT=$?
case "$PLAN_PHASE_EXIT" in
  0) report_stage 2 6 plan passed ;;
  3) report_stage 2 6 plan skipped ;;
  *) report_stage 2 6 plan failed; exit "$PLAN_PHASE_EXIT" ;;
esac

# Re-read PLAN_FILE from sentinel (phase wrote it)
if [ -f "$SENTINEL" ]; then
  PLAN_FILE="$(tail -1 "$SENTINEL")"
fi

if [ -z "$PLAN_FILE" ] || [ ! -f "$PLAN_FILE" ]; then
  echo "ERROR: Plan file missing after plan phase." >&2
  exit 1
fi
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

report_stage 3 6 worktree running
WORKTREE_PHASE_EXIT=0
bash "$SCRIPT_DIR/phases/worktree.sh" || WORKTREE_PHASE_EXIT=$?
case "$WORKTREE_PHASE_EXIT" in
  0) report_stage 3 6 worktree passed ;;
  *) report_stage 3 6 worktree failed; exit "$WORKTREE_PHASE_EXIT" ;;
esac

WORKTREE="$WORKTREE_DIR"
STATUS="$WORKTREE/.finish-status"
PLAN_IN_WORKTREE="$WORKTREE/docs/plans/$(basename "$PLAN_FILE")"
echo ""

# ============================================================
# Phase 3: Ralph loop
# ============================================================

report_stage 4 6 ralph running

# Check if all tasks are already complete
TOTAL_TASKS=0
DONE_TASKS=0
TASK_REGEX='^### (✅|🔄)?[[:space:]]*Task[[:space:]]*[0-9]'
DONE_REGEX='^### ✅[[:space:]]*Task[[:space:]]*[0-9]'
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

  RALPH_EXIT=0
  bash "$RALPH_SCRIPT" "$WORKTREE" "$PLAN_IN_WORKTREE" || RALPH_EXIT=$?

  if [ "$RALPH_EXIT" -ne 0 ]; then
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
report_stage 5 6 mockup running
MOCKUP_EXIT=0
bash "$SCRIPT_DIR/phases/mockup.sh" || MOCKUP_EXIT=$?
case "$MOCKUP_EXIT" in
  0) report_stage 5 6 mockup passed ;;
  3) report_stage 5 6 mockup skipped ;;
  *) report_stage 5 6 mockup failed; exit "$MOCKUP_EXIT" ;;
esac
echo ""

# ============================================================
# Phase 4: Verify branch
# ============================================================

export BRANCH WORKTREE PLAN_IN_WORKTREE PROJECT VERIFY_PROMPT PHASE_TIMEOUT STATUS
report_stage 6 6 verify running
VERIFY_EXIT=0
bash "$SCRIPT_DIR/phases/verify.sh" || VERIFY_EXIT=$?
case "$VERIFY_EXIT" in
  0) report_stage 6 6 verify passed ;;
  *) report_stage 6 6 verify failed; exit "$VERIFY_EXIT" ;;
esac
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
