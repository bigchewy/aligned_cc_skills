#!/usr/bin/env bash
# PHASE: critique-round-2
# INPUTS:
#   PROJECT, DESIGN_DOC, PLAN_FILE, LOG, PHASE_TIMEOUT (env vars)
#   CRITIQUE_ROUND2_PROMPT (env var)            — path to CRITIQUE-ROUND2.md
#   CHECKLIST_FILE, CRITIQUE_PANEL_PROMPTS      — shared critique resources
#   CRITIQUE_ROUND1_FLAG (env var, absolute)    — Round 1 result flag (read round-2-needed)
#   CRITIQUE_ROUND2_FLAG (env var, absolute)    — Round 2 completion flag (write on success)
# EXIT CODES:
#   0 — critique complete; flag file written
#   1 — Round 1 flag missing, or claude -p failed
#   3 — Round 2 not needed (Round 1 found no HIGH/MEDIUM), or already done

set -u

# Driver on sonnet; Round 2 critics run on haiku (scoped-to-changes work)
export ANTHROPIC_MODEL="${CRITIQUE_MODEL:-sonnet}"
export CLAUDE_CODE_SUBAGENT_MODEL="${CRITIQUE_R2_SUBAGENT_MODEL:-haiku}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RALPH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=../lib/process.sh
source "$RALPH_DIR/lib/process.sh"

PROMPT_FILE=""
CLAUDE_PID=""
WATCHDOG_PID=""
HEARTBEAT_PID=""

trap 'rm -f "$PROMPT_FILE" 2>/dev/null; stop_heartbeat; stop_watchdog; kill_claude' EXIT

# --- Check Round 1 result: abort if not needed ---

if [ ! -f "$CRITIQUE_ROUND1_FLAG" ]; then
  echo "ERROR: Round 1 flag file not found: $CRITIQUE_ROUND1_FLAG" >&2
  echo "Run critique round 1 first." >&2
  exit 1
fi

ROUND2_NEEDED="$(grep '^round-2-needed:' "$CRITIQUE_ROUND1_FLAG" 2>/dev/null | awk '{print $2}')"
if [ "$ROUND2_NEEDED" != "true" ]; then
  echo "Round 1 found no HIGH/MEDIUM issues — skipping Round 2."
  exit 3
fi

# --- Sentinel check: skip if Round 2 already complete ---

if [ -f "$CRITIQUE_ROUND2_FLAG" ]; then
  FLAG_DESIGN_DOC="$(grep '^design-doc:' "$CRITIQUE_ROUND2_FLAG" 2>/dev/null | sed 's/^design-doc: //')"
  if [ "$FLAG_DESIGN_DOC" = "$DESIGN_DOC" ]; then
    echo "Round 2 critique already complete — skipping."
    echo "  Flag: $CRITIQUE_ROUND2_FLAG"
    exit 3
  else
    echo "NOTE: Round 2 flag exists for a different design doc — re-running."
    rm -f "$CRITIQUE_ROUND2_FLAG"
  fi
fi

# --- Run critique via claude -p ---

echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"

FEATURE_SLUG="$(basename "$PLAN_FILE" .md | sed 's/^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}-//')"

PROMPT_FILE="/tmp/.autopilot-critique-round2-$$"
cat > "$PROMPT_FILE" <<PROMPT_EOF
$(cat "$CRITIQUE_ROUND2_PROMPT")

Critique panel prompts: $CRITIQUE_PANEL_PROMPTS
Plan file: $PLAN_FILE
Design document: $DESIGN_DOC
Project directory: $PROJECT
Feature slug: $FEATURE_SLUG
Round 1 flag file: $CRITIQUE_ROUND1_FLAG
Round 2 flag file: $CRITIQUE_ROUND2_FLAG
PROMPT_EOF

cd "$PROJECT"

start_heartbeat "$PHASE_TIMEOUT" "critique round 2"

if ! run_claude_phase "Phase 2c (critique round 2)" "$PHASE_TIMEOUT"; then
  stop_heartbeat
  exit 1
fi
stop_heartbeat
rm -f "$PROMPT_FILE"
PROMPT_FILE=""

echo ""
echo "Round 2 critique complete."
echo "  Flag: $CRITIQUE_ROUND2_FLAG"
exit 0
