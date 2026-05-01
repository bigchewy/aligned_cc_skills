#!/usr/bin/env bash
# PHASE: mockup
# INPUTS:
#   WORKTREE (env var, absolute path)         — worktree directory
#   PLAN_IN_WORKTREE (env var, absolute path) — plan path inside worktree
#   MOCKUP_PROMPT (env var, absolute path)    — path to MOCKUP-FIDELITY.md
#   MAX_MOCKUP_ITERATIONS (env var, integer)  — fidelity loop cap
#   MOCKUP_TIMEOUT (env var, seconds)         — claude phase timeout
# OUTPUTS:
#   $WORKTREE/.mockup-clean — written when fidelity loop converges
# EXIT CODES:
#   0 — clean OR no mockups referenced OR max iterations reached with
#       deviations remaining (warning only — not a halt)
#   3 — skipped (already verified clean from a previous run)

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RALPH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=../lib/process.sh
source "$RALPH_DIR/lib/process.sh"

# Locals required by lib/process.sh — declared here for clarity since
# this script runs in a child shell.
PROMPT_FILE=""
CLAUDE_PID=""
WATCHDOG_PID=""
HEARTBEAT_PID=""

trap 'rm -f "$PROMPT_FILE" 2>/dev/null; stop_heartbeat; stop_watchdog; kill_claude' EXIT

# --- Skip if already clean from a previous run ---

if [ -f "$WORKTREE/.mockup-clean" ]; then
  echo "Mockup fidelity already verified — skipping."
  exit 3
fi

# --- Skip if plan does not reference mockups ---

HAS_MOCKUPS=false
if grep -q '^\*\*Mockups:\*\*' "$PLAN_IN_WORKTREE" 2>/dev/null; then
  MOCKUPS_VALUE="$(grep '^\*\*Mockups:\*\*' "$PLAN_IN_WORKTREE" | head -1 | sed 's/\*\*Mockups:\*\* *//')"
  if [ -n "$MOCKUPS_VALUE" ] && [ "$MOCKUPS_VALUE" != "N/A" ] && [ "$MOCKUPS_VALUE" != "none" ]; then
    HAS_MOCKUPS=true
  fi
fi

if [ "$HAS_MOCKUPS" = false ]; then
  echo "No mockups referenced in plan — skipping fidelity check."
  touch "$WORKTREE/.mockup-clean"
  exit 3
fi

echo "Mockups referenced in plan. Starting fidelity loop..."
echo "Max iterations: $MAX_MOCKUP_ITERATIONS"
echo ""

MOCKUP_ITERATION=1

while [ ! -f "$WORKTREE/.mockup-clean" ] && [ "$MOCKUP_ITERATION" -le "$MAX_MOCKUP_ITERATIONS" ]; do
  echo "--- Mockup fidelity iteration $MOCKUP_ITERATION ($(date '+%H:%M:%S')) ---"

  PROMPT_FILE="/tmp/.autopilot-mockup-$$"
  cat > "$PROMPT_FILE" <<PROMPT_EOF
$(cat "$MOCKUP_PROMPT")

Plan: $PLAN_IN_WORKTREE
Worktree: $WORKTREE
PROMPT_EOF

  cd "$WORKTREE"

  if ! run_claude_phase "Phase 3.5 (mockup fidelity, iteration $MOCKUP_ITERATION)" "$MOCKUP_TIMEOUT"; then
    echo "WARNING: Mockup fidelity iteration $MOCKUP_ITERATION failed." >&2
    echo "Continuing to verification phase — mockup deviations may persist." >&2
    rm -f "$PROMPT_FILE"
    PROMPT_FILE=""
    break
  fi
  rm -f "$PROMPT_FILE"
  PROMPT_FILE=""

  if [ -f "$WORKTREE/.mockup-clean" ]; then
    echo "--- Mockup fidelity: CLEAN ($(date '+%H:%M:%S')) ---"
  else
    echo "--- Mockup fidelity iteration $MOCKUP_ITERATION: fixes applied ($(date '+%H:%M:%S')) ---"
  fi
  echo ""

  MOCKUP_ITERATION=$((MOCKUP_ITERATION + 1))
done

if [ ! -f "$WORKTREE/.mockup-clean" ]; then
  echo "WARNING: Mockup fidelity not fully resolved after $MAX_MOCKUP_ITERATIONS iterations." >&2
  echo "Remaining deviations will be visible during review." >&2
fi

exit 0
