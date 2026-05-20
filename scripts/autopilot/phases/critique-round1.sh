#!/usr/bin/env bash
# PHASE: critique-round-1
# INPUTS:
#   PROJECT (env var, absolute path)            — main repo path
#   DESIGN_DOC (env var, absolute path)         — design doc path
#   PLAN_FILE (env var, absolute path)          — written plan path
#   LOG (env var, absolute path)                — log file path
#   PHASE_TIMEOUT (env var, seconds)            — claude phase timeout
#   CRITIQUE_ROUND1_PROMPT (env var)            — path to CRITIQUE-ROUND1.md
#   CHECKLIST_FILE (env var)                    — path to plan-critique-checklist.md
#   CRITIQUE_PANEL_PROMPTS (env var)            — path to critique-panel-prompts.md
#   CRITIQUE_ROUND1_FLAG (env var, absolute)    — result flag file path
# OUTPUTS:
#   Plan file updated + committed; CRITIQUE_ROUND1_FLAG written
# EXIT CODES:
#   0 — critique complete; flag file written
#   1 — claude -p failed, or flag file not written after claude exited
#   3 — critique already complete for this plan (flag matches design-doc + plan-path)

set -u

export ANTHROPIC_MODEL="${CRITIQUE_MODEL:-sonnet}"
export CLAUDE_CODE_SUBAGENT_MODEL="${CRITIQUE_SUBAGENT_MODEL:-sonnet}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RALPH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=../lib/process.sh
source "$RALPH_DIR/lib/process.sh"

PROMPT_FILE=""
CLAUDE_PID=""
WATCHDOG_PID=""
HEARTBEAT_PID=""

trap 'rm -f "$PROMPT_FILE" 2>/dev/null; stop_heartbeat; stop_watchdog; kill_claude' EXIT

# --- Sentinel check: skip if critique already complete for this plan ---

if [ -f "$CRITIQUE_ROUND1_FLAG" ]; then
  FLAG_DESIGN_DOC="$(grep '^design-doc:' "$CRITIQUE_ROUND1_FLAG" 2>/dev/null | sed 's/^design-doc: //')"
  FLAG_PLAN_PATH="$(grep '^plan-path:' "$CRITIQUE_ROUND1_FLAG" 2>/dev/null | sed 's/^plan-path: //')"
  if [ "$FLAG_DESIGN_DOC" = "$DESIGN_DOC" ] && [ "$FLAG_PLAN_PATH" = "$PLAN_FILE" ]; then
    ROUND2_NEEDED="$(grep '^round-2-needed:' "$CRITIQUE_ROUND1_FLAG" 2>/dev/null | awk '{print $2}')"
    echo "Round 1 critique already complete for this plan — skipping."
    echo "  Flag:          $CRITIQUE_ROUND1_FLAG"
    echo "  Round 2 needed: ${ROUND2_NEEDED:-unknown}"
    exit 3
  else
    echo "NOTE: Flag file exists but for a different design doc or plan — re-running."
    rm -f "$CRITIQUE_ROUND1_FLAG"
  fi
fi

# --- Run critique via claude -p ---

echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"

FEATURE_SLUG="$(basename "$PLAN_FILE" .md | sed 's/^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}-//')"

PROMPT_FILE="/tmp/.autopilot-critique-round1-$$"
cat > "$PROMPT_FILE" <<PROMPT_EOF
$(cat "$CRITIQUE_ROUND1_PROMPT")

Checklist: $CHECKLIST_FILE
Critique panel prompts: $CRITIQUE_PANEL_PROMPTS
Plan file: $PLAN_FILE
Design document: $DESIGN_DOC
Project directory: $PROJECT
Feature slug: $FEATURE_SLUG
Round 1 flag file: $CRITIQUE_ROUND1_FLAG
PROMPT_EOF

cd "$PROJECT"

start_heartbeat "$PHASE_TIMEOUT" "critique-r1"

if ! run_claude_phase "Phase 4 (critique-r1)" "$PHASE_TIMEOUT"; then
  stop_heartbeat
  exit 1
fi
stop_heartbeat
rm -f "$PROMPT_FILE"
PROMPT_FILE=""

# Verify the flag file was written
if [ ! -f "$CRITIQUE_ROUND1_FLAG" ]; then
  echo "ERROR: Round 1 flag file not written: $CRITIQUE_ROUND1_FLAG" >&2
  echo "Claude may have failed to complete the critique phase." >&2
  [ -n "$LOG" ] && echo "Check the log at $LOG for details." >&2
  exit 1
fi

echo ""
echo "Round 1 critique complete."
echo "  Flag: $CRITIQUE_ROUND1_FLAG"
ROUND2_NEEDED="$(grep '^round-2-needed:' "$CRITIQUE_ROUND1_FLAG" 2>/dev/null | awk '{print $2}')"
echo "  Round 2 needed: ${ROUND2_NEEDED:-unknown}"
exit 0
