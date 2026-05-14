#!/usr/bin/env bash
# PHASE: verify
# INPUTS:
#   BRANCH (env var)                          — feature/* branch name
#   WORKTREE (env var, absolute path)         — worktree directory
#   PLAN_IN_WORKTREE (env var, absolute path) — plan path inside worktree
#   PROJECT (env var, absolute path)          — main repo path
#   VERIFY_PROMPT (env var, absolute path)    — path to VERIFY-BRANCH.md
#   PHASE_TIMEOUT (env var, seconds)          — claude phase timeout
#   STATUS (env var, absolute path)           — $WORKTREE/.finish-status
# OUTPUTS:
#   $STATUS file written by claude with status: SUCCESS|FAILED
# EXIT CODES:
#   0 — verification passed (status: SUCCESS) OR re-using a SUCCESS status
#       from a previous run
#   1 — verification FAILED, status missing, or claude phase failed

set -u

# --- Model selection (override via VERIFY_MODEL / VERIFY_SUBAGENT_MODEL) ---
# Sonnet (not Haiku): verify interprets failing stack traces and build
# errors. A misclassification of a real failure as transient is the
# worst-case outcome of model downshifting.
export ANTHROPIC_MODEL="${VERIFY_MODEL:-sonnet}"
export CLAUDE_CODE_SUBAGENT_MODEL="${VERIFY_SUBAGENT_MODEL:-sonnet}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RALPH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=../lib/process.sh
source "$RALPH_DIR/lib/process.sh"
# shellcheck source=../lib/halt.sh
source "$RALPH_DIR/lib/halt.sh"

# Locals required by lib/process.sh — declared here for clarity since
# this script runs in a child shell.
PROMPT_FILE=""
CLAUDE_PID=""
WATCHDOG_PID=""
HEARTBEAT_PID=""

trap 'rm -f "$PROMPT_FILE" 2>/dev/null; stop_heartbeat; stop_watchdog; kill_claude' EXIT

# --- Skip if previous SUCCESS status is still valid ---

if [ -f "$STATUS" ]; then
  PREV_RESULT="$(grep '^status:' "$STATUS" 2>/dev/null | awk '{print $2}')"
  if [ "$PREV_RESULT" = "SUCCESS" ]; then
    echo "Verification already SUCCESS — skipping."
    exit 0
  fi
  # Stale failure status — clear and re-run
  rm -f "$STATUS"
fi

echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"

PROMPT_FILE="/tmp/.autopilot-verify-$$"
cat > "$PROMPT_FILE" <<PROMPT_EOF
$(cat "$VERIFY_PROMPT")

Branch: $BRANCH
Worktree: $WORKTREE
Plan: $PLAN_IN_WORKTREE
Main repo: $PROJECT
PROMPT_EOF

cd "$WORKTREE"

if ! run_claude_phase "Phase 4 (verification)" "$PHASE_TIMEOUT"; then
  echo "Verification phase failed to complete." >&2
  echo "The branch may still be in good shape — check manually." >&2
  exit 1
fi
rm -f "$PROMPT_FILE"
PROMPT_FILE=""

if [ ! -f "$STATUS" ]; then
  echo "ERROR: Verification completed but no status file was written." >&2
  echo "Claude may not have followed the VERIFY-BRANCH.md instructions." >&2
  exit 1
fi

RESULT="$(grep '^status:' "$STATUS" 2>/dev/null | awk '{print $2}')"
if [ "$RESULT" = "FAILED" ]; then
  FAILED_AT="$(grep '^failed_at:' "$STATUS" 2>/dev/null | awk '{print $2}')"
  HALT_PATH="$WORKTREE/.autopilot-halt" \
    write_halt verify_failed verify "Failed at: ${FAILED_AT:-unknown}; see $STATUS"
  exit 2
fi
if [ "$RESULT" != "SUCCESS" ]; then
  echo "Verification finished with status: ${RESULT:-<empty>}." >&2
  exit 1
fi

exit 0
