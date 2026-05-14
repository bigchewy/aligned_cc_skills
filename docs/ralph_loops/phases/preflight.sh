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

# === AUTH-COMPAT BLOCK START ===
# Defense-in-depth against the OAuth-incompat regression fixed on
# fix/autopilot-bare-oauth-incompat. The static tests in
# e2e/tests/test_autopilot_model_selection.py also enforce this, but if
# someone runs autopilot from a branch that bypassed CI, this block fails
# fast with a clear auth-cause message instead of letting the plan phase
# emit the cryptic "Could not find the plan file" downstream error.
#
# Inputs: $RALPH_DIR (resolved above)
# Halts: write_halt headless_auth_incompat preflight <message>; exit 2
# See:   docs/lessons-learned/2026-05-14-autopilot-bare-oauth-incompat.md
AUTH_COMPAT_CALL_SITES=(
  "$RALPH_DIR/lib/process.sh"
  "$RALPH_DIR/run-ralph.sh"
)
for _auth_compat_f in "${AUTH_COMPAT_CALL_SITES[@]}"; do
  if [ -f "$_auth_compat_f" ] && grep -q -- '--bare' "$_auth_compat_f"; then
    write_halt headless_auth_incompat preflight \
      "Headless call site '$_auth_compat_f' passes --bare to claude. --bare restricts auth to ANTHROPIC_API_KEY or apiKeyHelper (OAuth and keychain are never read, per 'claude --help'), which breaks Max-plan users. Revert the call site to 'claude -p - < \"\$PROMPT_FILE\"' (no --bare). See docs/lessons-learned/2026-05-14-autopilot-bare-oauth-incompat.md."
    exit 2
  fi
done
unset _auth_compat_f
# === AUTH-COMPAT BLOCK END ===

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
