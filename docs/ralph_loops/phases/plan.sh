#!/usr/bin/env bash
# PHASE: plan
# INPUTS:
#   PROJECT (env var, absolute path)        — main repo path
#   DESIGN_DOC (env var, absolute path)     — design doc path
#   SENTINEL (env var, absolute path)       — .autopilot-plan-path file
#   LOG (env var, absolute path)            — log file path
#   PHASE_TIMEOUT (env var, seconds)        — claude phase timeout
#   WRITE_PLAN_PROMPT (env var)             — path to WRITE-PLAN.md
#   SKILL_FILE (env var)                    — path to writing-plans SKILL.md
#   CHECKLIST_FILE (env var)                — path to plan-critique-checklist.md
#   KANBAN_FORMAT (env var)                 — path to kanban-entry-format.md
# OUTPUTS:
#   Plan file committed to main; SENTINEL written with
#   line 1 = design-doc path, line 2 = plan-path
# EXIT CODES:
#   0 — plan written; PLAN_FILE readable from sentinel
#   1 — claude -p failed, sentinel missing, or plan file missing
#   3 — plan already exists for THIS design doc (sentinel match, skip)

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RALPH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=../lib/process.sh
source "$RALPH_DIR/lib/process.sh"

# Locals required by lib/process.sh — already defaulted there, but
# declared here for clarity since this script runs in a child shell.
PROMPT_FILE=""
CLAUDE_PID=""
WATCHDOG_PID=""
HEARTBEAT_PID=""

trap 'rm -f "$PROMPT_FILE" 2>/dev/null; stop_heartbeat; stop_watchdog; kill_claude' EXIT

# --- Sentinel check: skip if a plan already exists for THIS design doc ---

if [ -f "$SENTINEL" ]; then
  SENTINEL_DESIGN_DOC="$(head -1 "$SENTINEL")"
  SENTINEL_PLAN_PATH="$(tail -1 "$SENTINEL")"

  if [[ "$SENTINEL_DESIGN_DOC" != /* ]]; then
    SENTINEL_DESIGN_DOC_ABS="$(cd "$PROJECT/$(dirname "$SENTINEL_DESIGN_DOC")" 2>/dev/null && pwd)/$(basename "$SENTINEL_DESIGN_DOC")"
  else
    SENTINEL_DESIGN_DOC_ABS="$SENTINEL_DESIGN_DOC"
  fi

  if [ "$SENTINEL_DESIGN_DOC_ABS" = "$DESIGN_DOC" ] && [ -f "$SENTINEL_PLAN_PATH" ]; then
    echo "Plan file: $SENTINEL_PLAN_PATH"
    exit 3
  else
    if [ "$SENTINEL_DESIGN_DOC_ABS" != "$DESIGN_DOC" ]; then
      echo "NOTE: Sentinel is for a different design doc. Starting fresh."
    else
      echo "WARNING: Sentinel points to missing file: $SENTINEL_PLAN_PATH"
    fi
    rm -f "$SENTINEL"
  fi
fi

# --- Write the plan via claude -p ---

echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"

PROMPT_FILE="/tmp/.autopilot-write-plan-$$"
cat > "$PROMPT_FILE" <<PROMPT_EOF
$(cat "$WRITE_PLAN_PROMPT")

Skill file: $SKILL_FILE
Checklist: $CHECKLIST_FILE
Kanban format: $KANBAN_FORMAT
Design document: $DESIGN_DOC
Project directory: $PROJECT
Plan path sentinel: $SENTINEL
PROMPT_EOF

cd "$PROJECT"

start_heartbeat "$PHASE_TIMEOUT" "plan writing"

if ! run_claude_phase "Phase 1 (plan writing)" "$PHASE_TIMEOUT"; then
  stop_heartbeat
  exit 1
fi
stop_heartbeat
rm -f "$PROMPT_FILE"
PROMPT_FILE=""

# Verify the sentinel was written and points at a real plan file.
PLAN_FILE=""
if [ -f "$SENTINEL" ]; then
  PLAN_FILE="$(tail -1 "$SENTINEL")"
fi

if [ -z "$PLAN_FILE" ] || [ ! -f "$PLAN_FILE" ]; then
  echo "ERROR: Could not find the plan file after Phase 1." >&2
  echo "Claude may not have written the sentinel file at $SENTINEL." >&2
  [ -n "$LOG" ] && echo "Check the log at $LOG for details." >&2
  exit 1
fi

echo ""
echo "Plan file: $PLAN_FILE"
exit 0
