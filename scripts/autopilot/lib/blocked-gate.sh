#!/usr/bin/env bash
# lib/blocked-gate.sh — short-circuit claude spawns when BLOCKED state is
# unchanged since the previous iteration.
#
# Background: when a task is marked 🔄 BLOCKED, the next ralph iteration
# spawns a fresh claude that reads the plan, re-discovers "still BLOCKED,
# same reason", and exits. That spawn costs ~30s of wall time, one LLM
# round-trip, and one process worth of RAM — to produce information the
# wrapper already has. Repeated 2× before MAX_BLOCKED_ITERATIONS fires
# auto-skip, this is three back-to-back claude spawns producing identical
# answers; on a memory-pressured system that has been observed to trigger
# swap thrashing.
#
# The gate compares (task_num, reason_body) for every 🔄 task to a
# snapshot from the previous iteration. If identical AND every open task
# is BLOCKED, the wrapper skips the spawn — apply_blocked_cap still runs,
# so the BLOCKED counter still increments and auto-skip still fires after
# MAX_BLOCKED_ITERATIONS.
#
# Sourced by run-ralph.sh. Reads: $PLAN. Writes: $BLOCKED_SNAPSHOT_FILE.

# Idempotent source guard
if [ -n "${_AUTOPILOT_BLOCKED_GATE_SH_LOADED:-}" ]; then return 0; fi
_AUTOPILOT_BLOCKED_GATE_SH_LOADED=1

BLOCKED_SNAPSHOT_FILE=".ralph-blocked-snapshot"

# Extract current BLOCKED state from $PLAN as sorted "task_num|reason" lines.
# Emits nothing if there are no 🔄 tasks. Used for both snapshot writes
# and live comparison.
_extract_blocked_state() {
  awk '
    /^### 🔄[[:space:]]*Task[[:space:]]*[0-9]+/ {
      line = $0
      sub(/^### 🔄[[:space:]]*Task[[:space:]]*/, "", line)
      if (match(line, /[0-9]+/)) {
        task = substr(line, RSTART, RLENGTH)
        in_task = 1
        reason = ""
      }
      next
    }
    in_task && /^> BLOCKED:[[:space:]]*/ {
      reason = $0
      sub(/^> BLOCKED:[[:space:]]*/, "", reason)
      print task "|" reason
      in_task = 0
      next
    }
    in_task && /^### / { in_task = 0 }
  ' "$PLAN" 2>/dev/null | sort -u
}

# Count open (non-✅, non-⏭️) tasks. Used by the gate to ensure we only
# skip the spawn when *every* open task is BLOCKED. If there's a 🔄 task
# AND a still-open Task without any marker, claude has work to do on the
# unmarked one and we must spawn.
_count_open_tasks() {
  grep -cE '^###[[:space:]]+(🔄[[:space:]]*)?Task[[:space:]]*[0-9]+' "$PLAN" 2>/dev/null \
    | head -1
}

_count_blocked_tasks() {
  grep -cE '^### 🔄[[:space:]]*Task[[:space:]]*[0-9]+' "$PLAN" 2>/dev/null \
    | head -1
}

# Write the current BLOCKED state to the snapshot file. Called once per
# iteration after apply_blocked_cap, so the NEXT iteration's gate has a
# baseline to compare against.
snapshot_blocked_state() {
  _extract_blocked_state > "$BLOCKED_SNAPSHOT_FILE"
}

# Returns 0 (true) if the spawn should be skipped, 1 (false) if claude
# must run. Skip conditions, all required:
#   1. A snapshot exists from the previous iteration.
#   2. Current BLOCKED state matches the snapshot exactly.
#   3. At least one BLOCKED task is present (something to gate on).
#   4. Every open task is BLOCKED (no non-BLOCKED work for claude to do).
should_skip_blocked_spawn() {
  [ -f "$BLOCKED_SNAPSHOT_FILE" ] || return 1

  local current previous blocked_count open_count
  current="$(_extract_blocked_state)"
  previous="$(cat "$BLOCKED_SNAPSHOT_FILE" 2>/dev/null)"

  # No BLOCKED tasks now → claude needs to run to advance unblocked work.
  [ -z "$current" ] && return 1

  # State changed → claude needs to re-evaluate.
  [ "$current" = "$previous" ] || return 1

  blocked_count="$(_count_blocked_tasks)"
  blocked_count="${blocked_count:-0}"
  open_count="$(_count_open_tasks)"
  open_count="${open_count:-0}"

  # If there are non-BLOCKED open tasks, claude has work to do; don't skip.
  [ "$open_count" -gt "$blocked_count" ] 2>/dev/null && return 1

  return 0
}
