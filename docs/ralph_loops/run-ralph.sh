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
#   MAX_ITERATIONS      — safety cap (default: 50)
#   ITERATION_TIMEOUT   — seconds per iteration before kill (default: 300 = 5 min)
#   HEARTBEAT_INTERVAL  — seconds between heartbeat messages (default: 30)

WORKTREE="${1:?Usage: run-ralph.sh <worktree-path> <plan-file-path>}"
PLAN="${2:?Usage: run-ralph.sh <worktree-path> <plan-file-path>}"
MAX_ITERATIONS="${MAX_ITERATIONS:-50}"
ITERATION_TIMEOUT="${ITERATION_TIMEOUT:-300}"
HEARTBEAT_INTERVAL="${HEARTBEAT_INTERVAL:-30}"

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

# Resolve plan to absolute path before cd
PLAN="$(cd "$(dirname "$PLAN")" && pwd)/$(basename "$PLAN")"

cd "$WORKTREE"
rm -f .ralph-done

# Log all output to file, with line-buffered tee for real-time terminal output
LOG="$WORKTREE/.ralph-log"
if command -v stdbuf &>/dev/null; then
  exec > >(stdbuf -oL tee -a "$LOG") 2>&1
elif command -v gstdbuf &>/dev/null; then
  exec > >(gstdbuf -oL tee -a "$LOG") 2>&1
else
  # Fallback: standard tee (may buffer on some systems)
  exec > >(tee -a "$LOG") 2>&1
fi

# Write prompt to a temp file so backgrounded claude can read from it
PROMPT_FILE="$WORKTREE/.ralph-prompt"
cat > "$PROMPT_FILE" <<PROMPT_EOF
$(cat "$EXECUTE")

Plan: $PLAN
Worktree: $WORKTREE
PROMPT_EOF

ITERATION=1
CONSECUTIVE_FAILURES=0
TIMEOUT_COUNT=0

# --- Background process management ---

HEARTBEAT_PID=""
WATCHDOG_PID=""
CLAUDE_PID=""

start_heartbeat() {
  (
    elapsed=0
    while true; do
      sleep "$HEARTBEAT_INTERVAL"
      elapsed=$((elapsed + HEARTBEAT_INTERVAL))
      echo "  [heartbeat] iteration $ITERATION — ${elapsed}s elapsed"
    done
  ) &
  HEARTBEAT_PID=$!
}

stop_heartbeat() {
  if [ -n "$HEARTBEAT_PID" ]; then
    kill "$HEARTBEAT_PID" 2>/dev/null || true
    wait "$HEARTBEAT_PID" 2>/dev/null || true
    HEARTBEAT_PID=""
  fi
}

start_watchdog() {
  (
    sleep "$ITERATION_TIMEOUT"
    echo ""
    echo "  [timeout] iteration $ITERATION exceeded ${ITERATION_TIMEOUT}s — killing claude"
    # Kill the claude process group to include any child processes
    kill "$CLAUDE_PID" 2>/dev/null || true
  ) &
  WATCHDOG_PID=$!
}

stop_watchdog() {
  if [ -n "$WATCHDOG_PID" ]; then
    kill "$WATCHDOG_PID" 2>/dev/null || true
    wait "$WATCHDOG_PID" 2>/dev/null || true
    WATCHDOG_PID=""
  fi
}

cleanup() {
  stop_heartbeat
  stop_watchdog
  if [ -n "$CLAUDE_PID" ]; then
    kill "$CLAUDE_PID" 2>/dev/null || true
  fi
  rm -f "$PROMPT_FILE"
}
trap cleanup EXIT

# --- Main loop ---

echo "=== Ralph Loop Started ==="
echo "Worktree: $WORKTREE"
echo "Plan: $PLAN"
echo "Log: $LOG"
echo "Max iterations: $MAX_ITERATIONS"
echo "Iteration timeout: ${ITERATION_TIMEOUT}s"
echo ""

while :; do
  # Iteration cap
  if [ "$ITERATION" -gt "$MAX_ITERATIONS" ]; then
    echo "ERROR: Reached iteration cap ($MAX_ITERATIONS). Aborting." >&2
    echo "Check $LOG for details. Increase with MAX_ITERATIONS=N." >&2
    exit 1
  fi

  echo "--- Iteration $ITERATION starting ($(date '+%H:%M:%S')) ---"

  start_heartbeat

  # Run claude in background so we can enforce a timeout
  claude -p - < "$PROMPT_FILE" &
  CLAUDE_PID=$!

  start_watchdog

  # Wait for claude to finish (or be killed by watchdog)
  TIMED_OUT=false
  EXIT_CODE=0
  if wait "$CLAUDE_PID" 2>/dev/null; then
    EXIT_CODE=0
  else
    EXIT_CODE=$?
  fi
  CLAUDE_PID=""

  stop_watchdog
  stop_heartbeat

  # Determine what happened
  if [ "$EXIT_CODE" -eq 143 ] || [ "$EXIT_CODE" -eq 137 ]; then
    # SIGTERM (143) or SIGKILL (137) — timeout killed the process
    TIMED_OUT=true
    TIMEOUT_COUNT=$((TIMEOUT_COUNT + 1))
    CONSECUTIVE_FAILURES=0  # timeouts are not failures
    echo ""
    echo "WARNING: Iteration $ITERATION timed out after ${ITERATION_TIMEOUT}s (timeout #$TIMEOUT_COUNT)" >&2
    echo "Progress (commits) persists — next iteration picks up from ✅ markers."
  elif [ "$EXIT_CODE" -ne 0 ]; then
    CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
    echo "WARNING: claude -p exited with code $EXIT_CODE (failure $CONSECUTIVE_FAILURES of 3)" >&2
    if [ "$CONSECUTIVE_FAILURES" -ge 3 ]; then
      echo "ERROR: 3 consecutive claude failures. Aborting." >&2
      echo "Check $LOG for details." >&2
      exit 1
    fi
  else
    CONSECUTIVE_FAILURES=0
  fi

  echo ""
  if [ "$TIMED_OUT" = true ]; then
    echo "--- Iteration $ITERATION timed out ($(date '+%H:%M:%S')) ---"
  else
    echo "--- Iteration $ITERATION finished ($(date '+%H:%M:%S')) ---"
  fi

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
