#!/usr/bin/env bash
set -euo pipefail

# Usage: run-ralph.sh <worktree-path> <plan-file-path>
#
# Runs the Ralph loop: executes plan tasks one at a time via claude -p,
# looping until all tasks are marked complete (.ralph-done sentinel).
#
# EXECUTE-PLAN.md is discovered relative to this script's location.
#
# Environment variables:
#   MAX_ITERATIONS  — safety cap (default: 50)

WORKTREE="${1:?Usage: run-ralph.sh <worktree-path> <plan-file-path>}"
PLAN="${2:?Usage: run-ralph.sh <worktree-path> <plan-file-path>}"
MAX_ITERATIONS="${MAX_ITERATIONS:-50}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXECUTE="$SCRIPT_DIR/EXECUTE-PLAN.md"

if [ ! -f "$EXECUTE" ]; then
  echo "ERROR: EXECUTE-PLAN.md not found at $EXECUTE" >&2
  exit 1
fi

if [ ! -d "$WORKTREE" ]; then
  echo "ERROR: Worktree directory does not exist: $WORKTREE" >&2
  exit 1
fi

if [ ! -f "$PLAN" ]; then
  echo "ERROR: Plan file does not exist: $PLAN" >&2
  exit 1
fi

# Resolve plan to absolute path before cd (Finding #6)
PLAN="$(cd "$(dirname "$PLAN")" && pwd)/$(basename "$PLAN")"

cd "$WORKTREE"
rm -f .ralph-done

# Log all output to file (Finding #7)
LOG="$WORKTREE/.ralph-log"
exec > >(tee -a "$LOG") 2>&1

PROMPT="$(cat "$EXECUTE")

Plan: $PLAN
Worktree: $WORKTREE"

ITERATION=1
CONSECUTIVE_FAILURES=0
echo "=== Ralph Loop Started ==="
echo "Worktree: $WORKTREE"
echo "Plan: $PLAN"
echo "Log: $LOG"
echo "Max iterations: $MAX_ITERATIONS"
echo ""

while :; do
  # Iteration cap (Finding #1)
  if [ "$ITERATION" -gt "$MAX_ITERATIONS" ]; then
    echo "ERROR: Reached iteration cap ($MAX_ITERATIONS). Aborting." >&2
    echo "Check $LOG for details. Increase with MAX_ITERATIONS=N." >&2
    exit 1
  fi

  echo "--- Iteration $ITERATION starting ($(date '+%H:%M:%S')) ---"

  # Check exit code (Finding #2)
  if claude -p - <<< "$PROMPT"; then
    CONSECUTIVE_FAILURES=0
  else
    EXIT_CODE=$?
    CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
    echo "WARNING: claude -p exited with code $EXIT_CODE (failure $CONSECUTIVE_FAILURES of 3)" >&2
    if [ "$CONSECUTIVE_FAILURES" -ge 3 ]; then
      echo "ERROR: 3 consecutive claude failures. Aborting." >&2
      echo "Check $LOG for details." >&2
      exit 1
    fi
  fi

  echo ""
  echo "--- Iteration $ITERATION finished ($(date '+%H:%M:%S')) ---"

  if [ -f .ralph-done ]; then
    rm .ralph-done
    echo "=== Ralph Loop Complete ==="
    echo ""
    echo "Next step: run /aligned:finishing-a-development-branch to merge, clean up, and archive."
    break
  fi
  echo "No .ralph-done found, starting next iteration..."
  echo ""
  ITERATION=$((ITERATION + 1))
done
