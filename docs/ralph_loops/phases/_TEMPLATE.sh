#!/usr/bin/env bash
# PHASE: <phase-name>
# INPUTS:
#   PROJECT (env var, absolute path) — main repo path
#   PLAN_FILE (env var, absolute path) — plan path on main
# OUTPUTS:
#   <sentinels written, files created>
# EXIT CODES:
#   0 — phase passed, autopilot may proceed
#   2 — halt-with-reason; .autopilot-halt has structured details
#   3 — skip (phase not applicable for this run)

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RALPH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=../lib/process.sh
source "$RALPH_DIR/lib/process.sh"

# Phase logic goes here. Each phase MUST exit with one of {0, 2, 3}; any
# other exit code is treated by the orchestrator as a crash and a halt
# sentinel is written with reason=phase_crashed.

exit 0
