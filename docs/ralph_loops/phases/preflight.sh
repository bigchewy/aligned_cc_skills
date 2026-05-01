#!/usr/bin/env bash
# PHASE: preflight
# INPUTS:
#   PROJECT (env var)    — main repo path
#   PLAN_FILE (env var)  — plan path on main; may not exist yet on first invocation
#   HALT_PATH (env var)  — absolute path to .autopilot-halt (orchestrator sets this)
# OUTPUTS:
#   .autopilot-halt (sentinel) — written if preflight halts
# EXIT CODES:
#   0 — preflight passed (manifest valid OR no plan yet)
#   2 — halt-with-reason; .autopilot-halt has structured details
#   3 — skip (plan exists but has no manifest — backward-compat path)

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RALPH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=../lib/manifest.sh
source "$RALPH_DIR/lib/manifest.sh"
# shellcheck source=../lib/halt.sh
source "$RALPH_DIR/lib/halt.sh"

# If plan doesn't exist yet (first-ever invocation), skip — phase 1.5 catches it.
if [ ! -f "${PLAN_FILE:-}" ]; then
  echo "preflight: no plan file yet; deferring manifest checks to post-plan re-run"
  exit 0
fi

# Parse manifest. parse_manifest exits: 0 = parsed, 1 = malformed, 3 = absent.
PARSE_EXIT=0
parse_manifest "$PLAN_FILE" >/dev/null || PARSE_EXIT=$?
case "$PARSE_EXIT" in
  3)
    echo "preflight: no manifest in plan — skip (backward-compat)"
    exit 3
    ;;
  1)
    write_halt manifest_malformed preflight "Front-matter present but unparseable"
    exit 2
    ;;
esac

# Validate env vars
for var in "${MANIFEST_ENV_VARS[@]+"${MANIFEST_ENV_VARS[@]}"}"; do
  if ! check_env_var "$var"; then
    write_halt env_var_missing preflight "Variable '$var' is unset or empty"
    exit 2
  fi
done

# Validate MCP tools — walk from worktree CWD upward
for tool in "${MANIFEST_MCP_TOOLS[@]+"${MANIFEST_MCP_TOOLS[@]}"}"; do
  RESULT="$(check_mcp_tool "$tool" "${PROJECT:-$PWD}")"
  RC=$?
  case "$RC" in
    0) ;;  # ok
    *)
      write_halt "$RESULT" preflight "Tool '$tool' failed: $RESULT"
      exit 2
      ;;
  esac
done

echo "preflight: all manifest checks passed"
exit 0
