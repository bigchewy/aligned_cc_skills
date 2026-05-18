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
: "${SAMPLER_PID:=}"
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
  stop_system_sampler
  kill_claude
}

# ---------------------------------------------------------------------------
# Observability — process-leak diagnostic
# See scripts/autopilot/INSTRUMENTATION.md for field meanings and analysis
# one-liners.
#
# Two complementary streams:
#   $LOG.processes — one block per claude exit (snapshot_post_wait).
#                    Answers: did sub-agent claudes or MCP children
#                    survive past `wait`? Captures group members AND all
#                    claude processes system-wide (catches setsid-escaped
#                    sub-agents that pgrep -g would miss).
#   $LOG.system    — periodic samples (start_system_sampler), every
#                    SAMPLER_INTERVAL seconds (default 15). Answers: what
#                    was the system doing during peak / just before a
#                    crash? Captures load avg, swap usage, vm_stat, and
#                    every claude/node process with rss/%cpu/etime/time.
#                    Iteration boundaries appear as `==== MARKER ====`
#                    lines written by run-ralph.sh via log_marker.
#
# No behavior change. Failures are swallowed so logging cannot break a run.
# ---------------------------------------------------------------------------

snapshot_post_wait() {
  local label="$1"
  local pgid="$2"        # the claude PID at spawn time; pid == pgid by setsid
  local exit_code="$3"   # the exit code wait returned (or "killed")
  local out
  if [ -n "$LOG" ]; then out="${LOG}.processes"; else return 0; fi
  local ts survivors=0 group_lines="" system_node=0 system_claude=0 all_claudes=""
  ts="$(date '+%Y-%m-%d %H:%M:%S')"
  if [ -n "$pgid" ]; then
    survivors="$(pgrep -g "$pgid" 2>/dev/null | wc -l | tr -d ' ')"
    if [ "$survivors" -gt 0 ] 2>/dev/null; then
      group_lines="$(ps -o pid=,pgid=,ppid=,rss=,pcpu=,etime=,comm= -g "$pgid" 2>/dev/null)"
    fi
  fi
  # System-wide counts. system_claude is critical because Task-tool
  # sub-agents may call setsid and escape the parent pgid; pgrep -g would
  # miss them but a global claude scan catches them.
  system_node="$(pgrep -x node 2>/dev/null | wc -l | tr -d ' ')"
  system_claude="$(pgrep -x claude 2>/dev/null | wc -l | tr -d ' ')"
  # All claude processes anywhere on the system, with pgid/sid/ppid/etime
  # so an orphaned sub-agent (ppid=1) or a session-escaped child
  # (sid != parent pgid) is visible. macOS `ps -o comm=` returns the full
  # exec path (e.g. /Users/x/.local/bin/claude) for processes launched
  # by absolute path, so we extract the basename to match either form.
  all_claudes="$(ps -axo pid=,pgid=,ppid=,sid=,rss=,pcpu=,etime=,time=,comm= 2>/dev/null | awk '{ n = split($NF, a, "/"); if (a[n] == "claude") print }')"
  {
    echo "==== POST-WAIT [$ts] label=$label pgid=${pgid:-<empty>} exit=$exit_code ===="
    echo "survivors_in_group=$survivors system_claude=$system_claude system_node=$system_node"
    if [ -n "$group_lines" ]; then
      echo "--- group members (pid pgid ppid rss %cpu etime comm) ---"
      echo "$group_lines"
    fi
    if [ -n "$all_claudes" ]; then
      echo "--- all claude processes (pid pgid ppid sid rss %cpu etime time comm) ---"
      echo "$all_claudes"
    fi
    echo ""
  } >> "$out" 2>/dev/null || true
}

# Emit a free-form marker into the sampler log. Use to mark iteration
# boundaries (e.g., from run-ralph.sh) so post-hoc analysis can correlate
# system samples to which ralph iteration was active.
log_marker() {
  local msg="$1"
  local out
  if [ -n "$LOG" ]; then out="${LOG}.system"; else return 0; fi
  {
    echo "==== MARKER $(date '+%Y-%m-%d %H:%M:%S') $msg ===="
  } >> "$out" 2>/dev/null || true
}

start_system_sampler() {
  # Capture system state every SAMPLER_INTERVAL seconds (default 15) to
  # $LOG.system. Targets node/claude/chrom processes plus load avg and
  # (macOS) vm_stat. Cheap; runs until stop_system_sampler is called.
  [ -n "$SAMPLER_PID" ] && return 0
  local interval="${SAMPLER_INTERVAL:-15}"
  local out
  if [ -n "$LOG" ]; then out="${LOG}.system"; else return 0; fi
  # Redirect stdio to /dev/null so the orphaned `sleep` child (which gets
  # reparented to init after SIGKILL) doesn't keep the parent's stdout
  # pipe open. Without this, `subprocess.run(capture_output=True)` from
  # pytest blocks on EOF until the sleep finishes naturally.
  (
    # Exit immediately on SIGTERM so stop_system_sampler doesn't have to
    # wait out the current sleep. Without this trap, bash's default
    # SIGTERM handling defers exit until the foreground `sleep` returns,
    # which can be up to SAMPLER_INTERVAL seconds (default 15).
    trap 'exit 0' TERM
    while true; do
      sleep "$interval"
      {
        echo "==== SAMPLE $(date '+%Y-%m-%d %H:%M:%S') ===="
        echo "load: $(uptime 2>/dev/null | sed 's/.*load average://')"
        if command -v sysctl >/dev/null 2>&1; then
          echo "swap: $(sysctl -n vm.swapusage 2>/dev/null)"
        fi
        if command -v vm_stat >/dev/null 2>&1; then
          echo "--- vm_stat (first 8 lines) ---"
          vm_stat 2>/dev/null | head -8
        fi
        # Basename-extraction match: comm may be either bare ("node") or
        # a full path ("/Users/x/.local/bin/claude") depending on how the
        # binary was exec'd. Splitting on "/" and matching the last
        # segment catches both forms. Without this, paths-launched
        # binaries (claude on macOS) silently miss and the detail block
        # under-reports while system_claude/system_node counts (which use
        # pgrep -x) keep working — a confusing inconsistency.
        echo "--- claude and node processes (pid pgid ppid rss %cpu etime time comm) ---"
        ps -axo pid=,pgid=,ppid=,rss=,pcpu=,etime=,time=,comm= 2>/dev/null \
          | awk '{ n = split($NF, a, "/"); name = a[n]; if (name == "claude" || name == "node") print }' \
          | head -60
        echo ""
      } >> "$out" 2>/dev/null
    done
  ) </dev/null >/dev/null 2>&1 &
  SAMPLER_PID=$!
}

stop_system_sampler() {
  if [ -n "$SAMPLER_PID" ]; then
    # SIGTERM first (the subshell traps it and exits cleanly), brief poll
    # for exit, then SIGKILL as fallback. The fallback exists because
    # bash 3.2 (macOS default) can defer trap execution while a foreground
    # `sleep` is running — without escalation, this wait can block for up
    # to SAMPLER_INTERVAL seconds.
    kill -TERM "$SAMPLER_PID" 2>/dev/null || true
    local n=0
    while [ "$n" -lt 5 ] && kill -0 "$SAMPLER_PID" 2>/dev/null; do
      sleep 0.1
      n=$((n + 1))
    done
    kill -KILL "$SAMPLER_PID" 2>/dev/null || true
    wait "$SAMPLER_PID" 2>/dev/null || true
    SAMPLER_PID=""
  fi
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
  local _spawn_pgid="$CLAUDE_PID"

  start_watchdog "$timeout" "$phase"

  CLAUDE_EXIT_CODE=0
  if ! wait "$CLAUDE_PID" 2>/dev/null; then
    CLAUDE_EXIT_CODE=$?
  fi
  snapshot_post_wait "$phase" "$_spawn_pgid" "$CLAUDE_EXIT_CODE"
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
