#!/usr/bin/env bash
# lib/process.sh — shared process management for autopilot.sh and run-ralph.sh.
# Sourced by both. Provides heartbeat, watchdog, cleanup, run_claude_phase.

# Idempotent source guard
if [ -n "${_AUTOPILOT_PROCESS_SH_LOADED:-}" ]; then return 0; fi
_AUTOPILOT_PROCESS_SH_LOADED=1

set -u
# Note: errexit is intentionally NOT enabled. Sourced libs inherit caller
# flags; we use explicit exit-code checks throughout (Decision 7 in the
# autopilot redesign).

# Callers must declare these globals before sourcing:
#   PROMPT_FILE, CLAUDE_PID, WATCHDOG_PID, HEARTBEAT_PID, LOG
# Initialise to "" if unset.
: "${PROMPT_FILE:=}"
: "${CLAUDE_PID:=}"
: "${WATCHDOG_PID:=}"
: "${HEARTBEAT_PID:=}"
: "${LOG:=}"

cleanup() {
  [ -n "$PROMPT_FILE" ] && rm -f "$PROMPT_FILE"
  stop_heartbeat
  stop_watchdog
  kill_claude
}

kill_claude() {
  if [ -n "$CLAUDE_PID" ]; then
    kill "$CLAUDE_PID" 2>/dev/null || true
    wait "$CLAUDE_PID" 2>/dev/null || true
    CLAUDE_PID=""
  fi
}

start_heartbeat() {
  local timeout="$1"
  local label="$2"
  (
    elapsed=0
    while true; do
      sleep 30
      elapsed=$((elapsed + 30))
      remaining=$((timeout - elapsed))
      if [ "$remaining" -lt 0 ]; then remaining=0; fi
      rem_min=$((remaining / 60))
      rem_sec=$((remaining % 60))
      printf "  [heartbeat] %s — %ds elapsed (%dm%02ds remaining)\n" "$label" "$elapsed" "$rem_min" "$rem_sec"
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
  local timeout="$1"
  local phase="$2"
  (
    sleep "$timeout"
    echo ""
    echo "  [timeout] $phase exceeded ${timeout}s — killing claude" >&2
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

# run_claude_phase <phase-name> <timeout-seconds>
# Reads prompt from $PROMPT_FILE. Sets CLAUDE_EXIT_CODE.
run_claude_phase() {
  local phase="$1"
  local timeout="$2"

  # Do NOT add --bare here. The flag restricts auth to ANTHROPIC_API_KEY
  # or apiKeyHelper (OAuth and keychain are never read, per `claude
  # --help`), which breaks Max-plan users on OAuth. Preflight catches
  # this at runtime; tests catch it at CI; do not test the guards.
  # See docs/lessons-learned/2026-05-14-autopilot-bare-oauth-incompat.md.
  claude -p - < "$PROMPT_FILE" &
  CLAUDE_PID=$!

  start_watchdog "$timeout" "$phase"

  CLAUDE_EXIT_CODE=0
  if ! wait "$CLAUDE_PID" 2>/dev/null; then
    CLAUDE_EXIT_CODE=$?
  fi
  CLAUDE_PID=""

  stop_watchdog

  if [ "$CLAUDE_EXIT_CODE" -eq 143 ] || [ "$CLAUDE_EXIT_CODE" -eq 137 ]; then
    echo ""
    echo "ERROR: $phase timed out after ${timeout}s." >&2
    return 1
  elif [ "$CLAUDE_EXIT_CODE" -ne 0 ]; then
    echo ""
    echo "ERROR: $phase failed (claude -p exited with code $CLAUDE_EXIT_CODE)." >&2
    [ -n "$LOG" ] && echo "Check the log at $LOG for details." >&2
    return 1
  fi

  return 0
}
