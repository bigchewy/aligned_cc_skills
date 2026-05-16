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
: "${_AUTOPILOT_CLEANED:=}"

# Session-spawn prefix. claude must be the leader of a new session so its
# pid == pgid, which lets kill_claude target the whole tree (claude + MCP
# server children + subagents) via negative-PID signalling. Without this,
# `kill $CLAUDE_PID` only hits the leader and children orphan to launchd.
# perl is used unconditionally rather than `setsid` because util-linux
# `setsid` may fork-then-exec under some conditions, which would make $!
# capture a short-lived wrapper PID instead of the real session leader.
# perl is in macOS core and on every reasonable Linux; POSIX::setsid + exec
# preserve the PID through to the target.
if ! command -v perl >/dev/null 2>&1; then
  echo "ERROR: lib/process.sh requires /usr/bin/perl for session-spawn." >&2
  return 1
fi
_AUTOPILOT_SPAWN_SESSION=(perl -e 'use POSIX qw(setsid); setsid() or die "setsid: $!"; exec { $ARGV[0] } @ARGV or die "exec $ARGV[0]: $!"')

cleanup() {
  # Idempotent: handle_signal triggers exit, which re-enters cleanup via the
  # EXIT trap. Double-firing kill on a recycled PID is the kind of thing
  # that mauls unrelated processes.
  [ -n "$_AUTOPILOT_CLEANED" ] && return 0
  _AUTOPILOT_CLEANED=1
  [ -n "$PROMPT_FILE" ] && rm -f "$PROMPT_FILE"
  stop_heartbeat
  stop_watchdog
  kill_claude
}

kill_claude() {
  if [ -n "$CLAUDE_PID" ]; then
    # Negative PID = signal the whole process group (claude + MCP children +
    # subagents). Falls back silently if the group is already gone.
    kill -TERM -- "-$CLAUDE_PID" 2>/dev/null || true
    # Grace period for clean shutdown before SIGKILL. 3 seconds is enough
    # for MCP servers to release ports / flush logs without hanging the
    # script if claude is wedged in an uninterruptible state.
    local n=0
    while [ "$n" -lt 3 ] && kill -0 -- "-$CLAUDE_PID" 2>/dev/null; do
      sleep 1
      n=$((n + 1))
    done
    kill -KILL -- "-$CLAUDE_PID" 2>/dev/null || true
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
    # Negative PID — kill the whole tree, not just the leader.
    kill -TERM -- "-$CLAUDE_PID" 2>/dev/null || true
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
  # Spawned via _AUTOPILOT_SPAWN_SESSION so claude becomes its own session
  # leader; this is what makes kill_claude's negative-PID kill reach the
  # MCP server children instead of orphaning them.
  "${_AUTOPILOT_SPAWN_SESSION[@]}" claude -p - < "$PROMPT_FILE" &
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
