#!/usr/bin/env bash
set -u

# Usage: run-ralph.sh <worktree-path> <plan-file-path>
#
# Runs the Ralph loop: executes plan tasks one at a time via claude -p,
# looping until all tasks are marked complete (.ralph-done sentinel).
#
# EXECUTE-PLAN.md is discovered relative to this script's location.
#
# Environment variables:
#   MAX_ITERATIONS      — safety cap (default: 50)
#   ITERATION_TIMEOUT   — seconds per iteration before kill (default: 900 = 15 min)
#   MAX_TIMEOUTS        — consecutive timeout cap before abort (default: 5)
#   HEARTBEAT_INTERVAL  — seconds between heartbeat messages (default: 30)
#   RALPH_MODEL         — Model for the loop (default: sonnet)
#   RALPH_SUBAGENT_MODEL — Subagent model for the loop (default: sonnet)

WORKTREE="${1:?Usage: run-ralph.sh <worktree-path> <plan-file-path>}"
PLAN="${2:?Usage: run-ralph.sh <worktree-path> <plan-file-path>}"
MAX_ITERATIONS="${MAX_ITERATIONS:-50}"
ITERATION_TIMEOUT="${ITERATION_TIMEOUT:-900}"
MAX_TIMEOUTS="${MAX_TIMEOUTS:-5}"
HEARTBEAT_INTERVAL="${HEARTBEAT_INTERVAL:-30}"
# After this many consecutive 🔄 BLOCKED marks on the same task, the wrapper
# auto-skips it (rewrites the heading to ⏭️) so the loop never halts for
# human intervention — autopilot is unattended by contract.
MAX_BLOCKED_ITERATIONS="${MAX_BLOCKED_ITERATIONS:-3}"

# --- Model selection (override via RALPH_MODEL / RALPH_SUBAGENT_MODEL) ---
# Sonnet for the ralph execute loop: up to 50 iterations of TDD task
# execution dominate total autopilot cost. Anthropic docs call Sonnet
# "for daily coding tasks" — this is the canonical use case.
export ANTHROPIC_MODEL="${RALPH_MODEL:-sonnet}"
export CLAUDE_CODE_SUBAGENT_MODEL="${RALPH_SUBAGENT_MODEL:-sonnet}"
export JEST_MAX_WORKERS="${JEST_MAX_WORKERS:-2}"
export VITEST_MAX_THREADS="${VITEST_MAX_THREADS:-2}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXECUTE="$SCRIPT_DIR/EXECUTE-PLAN.md"

# shellcheck source=lib/process.sh
source "$SCRIPT_DIR/lib/process.sh"
# shellcheck source=lib/blocked-gate.sh
source "$SCRIPT_DIR/lib/blocked-gate.sh"

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
# Use /tmp to avoid polluting the worktree (visible to git, user)
PROMPT_FILE="/tmp/.ralph-prompt-$$"
cat > "$PROMPT_FILE" <<PROMPT_EOF
$(cat "$EXECUTE")

Plan: $PLAN
Worktree: $WORKTREE
PROMPT_EOF

ITERATION=1
CONSECUTIVE_FAILURES=0
TIMEOUT_COUNT=0
CONSECUTIVE_TIMEOUTS=0

# --- Background process management ---

HEARTBEAT_PID=""
WATCHDOG_PID=""
CLAUDE_PID=""

# Ctrl+C and SIGTERM: set flag, kill claude, let the EXIT trap do final cleanup
INTERRUPTED=false
handle_signal() {
  INTERRUPTED=true
  echo ""
  echo "Interrupted — shutting down..." >&2
  if [ -n "$CLAUDE_PID" ]; then
    # Negative PID — kill the whole tree, not just claude (MCP children
    # are in claude's process group via _AUTOPILOT_SPAWN_SESSION).
    kill -TERM -- "-$CLAUDE_PID" 2>/dev/null || true
  fi
  # EXIT trap handles the rest
  exit 130
}
trap handle_signal INT TERM
trap cleanup EXIT
trap '' HUP  # ignore terminal hangup so a closed iTerm tab doesn't orphan an in-progress run

# --- Worktree-drift breadcrumb (debugs stale-worktree misdiagnoses) ---

print_worktree_drift_breadcrumb() {
  if ! git rev-parse --verify main >/dev/null 2>&1; then
    return 0
  fi
  local ahead behind
  ahead="$(git log --oneline main..HEAD 2>/dev/null | wc -l | tr -d ' ')"
  behind="$(git log --oneline HEAD..main 2>/dev/null | wc -l | tr -d ' ')"
  echo "  [drift] worktree vs main: ahead $ahead, behind $behind"
}

# --- Wrapper-side BLOCKED counter + auto-skip ---
# State in $WORKTREE/.ralph-block-counts: one "task=count" per line.
# After each iteration we bump counts for tasks currently 🔄, rewrite the
# heading to ⏭️ at the cap, and drop counts for tasks no longer 🔄.
# Under the unattended-autopilot contract this is the ONLY response path
# for "agent cannot proceed"; the loop never halts for human action.

BLOCK_COUNTS_FILE=".ralph-block-counts"

current_blocked_tasks() {
  grep -E '^### 🔄[[:space:]]*Task[[:space:]]*[0-9]+' "$PLAN" 2>/dev/null \
    | sed -E 's/^### 🔄[[:space:]]*Task[[:space:]]*([0-9]+).*/\1/'
}

get_block_count() {
  local task="$1"
  [ -f "$BLOCK_COUNTS_FILE" ] || { echo 0; return; }
  local n
  n="$(grep -E "^${task}=" "$BLOCK_COUNTS_FILE" 2>/dev/null | head -1 | cut -d= -f2)"
  echo "${n:-0}"
}

auto_skip_task() {
  local task_num="$1"
  local count="$2"
  local tmp="${PLAN}.autoskip.tmp"
  awk -v n="$task_num" -v count="$count" '
    BEGIN { in_task = 0; replaced = 0 }
    {
      if ($0 ~ /^### 🔄[[:space:]]*Task[[:space:]]*[0-9]+/) {
        line = $0
        sub(/^### 🔄[[:space:]]*Task[[:space:]]*/, "", line)
        if (match(line, /[0-9]+/) && substr(line, RSTART, RLENGTH) == n) {
          sub(/🔄/, "⏭️")
          in_task = 1; replaced = 0
          print; next
        } else {
          in_task = 0
        }
      } else if (in_task && $0 ~ /^### /) {
        in_task = 0
      }
      if (in_task && !replaced && $0 ~ /^> BLOCKED:/) {
        body = $0
        sub(/^> BLOCKED:[[:space:]]*/, "", body)
        printf "> AUTO-SKIPPED: %s (after %d consecutive blocks)\n", body, count
        replaced = 1
        next
      }
      print
    }
  ' "$PLAN" > "$tmp" && mv "$tmp" "$PLAN"
  echo "  [auto-skip] Task $task_num: $count consecutive BLOCKED iterations — heading rewritten to ⏭️"
  git add "$PLAN" 2>/dev/null || true
  git commit -m "wrapper: auto-skip Task $task_num after $count consecutive blocks" 2>/dev/null || true
}

apply_blocked_cap() {
  local task n
  local tmp="${BLOCK_COUNTS_FILE}.tmp"
  : > "$tmp"
  while IFS= read -r task; do
    [ -z "$task" ] && continue
    n=$(( $(get_block_count "$task") + 1 ))
    if [ "$n" -ge "$MAX_BLOCKED_ITERATIONS" ]; then
      auto_skip_task "$task" "$n"
    else
      echo "${task}=${n}" >> "$tmp"
    fi
  done < <(current_blocked_tasks | sort -u)
  mv "$tmp" "$BLOCK_COUNTS_FILE"
}

# --- All-settled check: write .ralph-done with AUTO-SKIPPED summary ---

write_done_with_summary() {
  local skipped_count
  skipped_count="$(grep -cE '^### ⏭️[[:space:]]*Task[[:space:]]*[0-9]+' "$PLAN" 2>/dev/null || true)"
  skipped_count="${skipped_count:-0}"
  {
    echo "All tasks settled."
    if [ "$skipped_count" -gt 0 ]; then
      echo ""
      echo "## AUTO-SKIPPED tasks"
      echo ""
      echo "$skipped_count task(s) auto-skipped after hitting MAX_BLOCKED_ITERATIONS=$MAX_BLOCKED_ITERATIONS."
      echo "Headings and AUTO-SKIPPED reasons are in the plan: $PLAN"
      echo "Verify-phase surfaces them; rewrite a heading prefix to retry."
    fi
  } > .ralph-done
}

check_all_settled_and_write_done() {
  local total settled
  total="$(grep -cE '^### (✅|🔄|⏭️)?[[:space:]]*Task[[:space:]]*[0-9]+' "$PLAN" 2>/dev/null || true)"
  settled="$(grep -cE '^### (✅|⏭️)[[:space:]]*Task[[:space:]]*[0-9]+' "$PLAN" 2>/dev/null || true)"
  if [ "$total" -gt 0 ] && [ "$total" -eq "$settled" ]; then
    write_done_with_summary
  fi
}

_spawn_pgid=""

start_system_sampler

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
  log_marker "ralph-iter-$ITERATION starting"
  print_worktree_drift_breadcrumb

  # Gate: if all open tasks are BLOCKED with identical reasons to the
  # previous iteration, skip the spawn. apply_blocked_cap still runs so
  # the BLOCKED counter increments and auto-skip still fires after
  # MAX_BLOCKED_ITERATIONS. This prevents back-to-back claude spawns that
  # produce no new information and thrash memory on a stressed system.
  if should_skip_blocked_spawn; then
    echo "  [gate] All open tasks BLOCKED, state unchanged — skipping spawn"
    apply_blocked_cap
    snapshot_blocked_state
    check_all_settled_and_write_done
    if [ -f .ralph-done ]; then
      rm .ralph-done
      echo "=== Ralph Loop Complete ==="
      echo ""
      echo "Next step: run /aligned:finishing-a-development-branch to merge, clean up, and archive."
      break
    fi
    echo "No sentinel found, starting next iteration..."
    echo ""
    ITERATION=$((ITERATION + 1))
    continue
  fi

  start_heartbeat "$ITERATION_TIMEOUT" "iteration $ITERATION"

  # Run claude in background so we can enforce a timeout.
  # Do NOT add --bare here. The flag restricts auth to ANTHROPIC_API_KEY
  # or apiKeyHelper (OAuth and keychain are never read, per `claude
  # --help`), which breaks Max-plan users on OAuth. Same constraint as
  # lib/process.sh:run_claude_phase. See
  # docs/lessons-learned/2026-05-14-autopilot-bare-oauth-incompat.md.
  # Spawned via _AUTOPILOT_SPAWN_SESSION so claude leads its own session
  # — kill_claude (and the watchdog) use negative-PID signalling to take
  # the MCP children with it instead of orphaning them to PID 1.
  "${_AUTOPILOT_SPAWN_SESSION[@]}" claude -p - < "$PROMPT_FILE" &
  CLAUDE_PID=$!
  _spawn_pgid="$CLAUDE_PID"

  start_watchdog "$ITERATION_TIMEOUT" "iteration $ITERATION"

  # Wait for claude to finish (or be killed by watchdog)
  TIMED_OUT=false
  EXIT_CODE=0
  if wait "$CLAUDE_PID" 2>/dev/null; then
    EXIT_CODE=0
  else
    EXIT_CODE=$?
  fi
  snapshot_post_wait "ralph-iter-$ITERATION" "$_spawn_pgid" "$EXIT_CODE"
  CLAUDE_PID=""

  stop_watchdog
  stop_heartbeat

  # Determine what happened
  if [ "$EXIT_CODE" -eq 143 ] || [ "$EXIT_CODE" -eq 137 ]; then
    # SIGTERM (143) or SIGKILL (137) — timeout killed the process
    TIMED_OUT=true
    TIMEOUT_COUNT=$((TIMEOUT_COUNT + 1))
    CONSECUTIVE_TIMEOUTS=$((CONSECUTIVE_TIMEOUTS + 1))
    CONSECUTIVE_FAILURES=0  # timeouts are not failures
    echo ""
    echo "WARNING: Iteration $ITERATION timed out after ${ITERATION_TIMEOUT}s (timeout #$TIMEOUT_COUNT, consecutive: $CONSECUTIVE_TIMEOUTS)" >&2
    echo "Progress (commits) persists — next iteration picks up from ✅ markers."
    if [ "$CONSECUTIVE_TIMEOUTS" -ge "$MAX_TIMEOUTS" ]; then
      echo "ERROR: $MAX_TIMEOUTS consecutive timeouts — task likely exceeds timeout. Aborting." >&2
      echo "Increase ITERATION_TIMEOUT (currently ${ITERATION_TIMEOUT}s) or investigate the stuck task." >&2
      echo "Check $LOG for details." >&2
      exit 1
    fi
  elif [ "$EXIT_CODE" -ne 0 ]; then
    CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
    CONSECUTIVE_TIMEOUTS=0  # non-timeout failure resets timeout streak
    echo "WARNING: claude -p exited with code $EXIT_CODE (failure $CONSECUTIVE_FAILURES of 3)" >&2
    if [ "$CONSECUTIVE_FAILURES" -ge 3 ]; then
      echo "ERROR: 3 consecutive claude failures. Aborting." >&2
      echo "Check $LOG for details." >&2
      exit 1
    fi
  else
    CONSECUTIVE_FAILURES=0
    CONSECUTIVE_TIMEOUTS=0
  fi

  echo ""
  if [ "$TIMED_OUT" = true ]; then
    echo "--- Iteration $ITERATION timed out ($(date '+%H:%M:%S')) ---"
  else
    echo "--- Iteration $ITERATION finished ($(date '+%H:%M:%S')) ---"
  fi

  # Apply wrapper-side BLOCKED cap (rewrites 🔄 → ⏭️ at the cap).
  apply_blocked_cap
  # Snapshot after cap so the next iteration's gate has the post-rewrite state.
  snapshot_blocked_state
  # If the cap just settled the last open task, synthesize .ralph-done so
  # the loop terminates cleanly with the AUTO-SKIPPED summary attached.
  check_all_settled_and_write_done

  if [ -f .ralph-done ]; then
    rm .ralph-done
    echo "=== Ralph Loop Complete ==="
    echo ""
    echo "Next step: run /aligned:finishing-a-development-branch to merge, clean up, and archive."
    break
  fi
  echo "No sentinel found, starting next iteration..."
  echo ""
  ITERATION=$((ITERATION + 1))
done
