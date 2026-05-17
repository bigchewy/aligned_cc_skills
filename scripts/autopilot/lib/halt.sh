#!/usr/bin/env bash
# lib/halt.sh — structured halt sentinel write/read/format.
# Schema: skills/_shared/autopilot-halt-format.md.

if [ -n "${_AUTOPILOT_HALT_SH_LOADED:-}" ]; then return 0; fi
_AUTOPILOT_HALT_SH_LOADED=1

set -u

: "${HALT_PATH:=}"

# write_halt <reason> <phase> [details]
# Atomic write via mv. The orchestrator exits on the first halt, so only
# one halt is emitted per run; across runs the user deletes the sentinel
# before re-running. Overwrites unconditionally.
write_halt() {
  local reason="$1"
  local phase="$2"
  local details="${3:-}"
  local target="${HALT_PATH:-.autopilot-halt}"
  local tmp="${target}.tmp.$$"
  local log="${LOG:-(unknown)}"

  {
    echo "reason: $reason"
    echo "phase: $phase"
    echo "log: $log"
    echo "next-action: see fix-instructions below"
    if [ -n "$details" ]; then
      echo "details: $details"
    fi
    echo "fix-instructions: |"
    format_halt "$reason" | sed 's/^/  /'
  } > "$tmp"
  mv "$tmp" "$target"
}

# read_halt [path]
# Echoes the sentinel content. Exit 0 if found, 1 otherwise.
read_halt() {
  local path="${1:-${HALT_PATH:-.autopilot-halt}}"
  [ -f "$path" ] || return 1
  cat "$path"
}

# is_transient_error <log-path>
# Returns 0 (true) if the tail of the log shows a transient external error
# that resolves on re-run — Anthropic API stream timeouts, 5xx responses,
# upstream overload, network blips, OAuth refresh races. The orchestrator
# uses this to decide whether a non-zero phase exit should write a
# phase_crashed halt: transient errors skip the halt so a plain re-run
# resumes from sentinel-tracked state with no manual cleanup.
#
# Pattern selection is conservative: only signatures the Anthropic CLI
# emits on transient infrastructure failures. Application-side stack
# traces and shell-script crashes still fall through to phase_crashed.
is_transient_error() {
  local log="${1:-}"
  [ -n "$log" ] && [ -f "$log" ] || return 1
  tail -100 "$log" 2>/dev/null | grep -qE \
    'API Error:.*(Stream idle timeout|Overloaded|overloaded|50[234]|Connection error|fetch failed|ECONNRESET|ETIMEDOUT|socket hang up|EAI_AGAIN)|Bedrock.*ThrottlingException|Request timed out'
}

# format_halt <reason>
# Echoes the canonical fix-instructions for the reason. Add cases here when
# adding new reasons (and update skills/_shared/autopilot-halt-format.md).
format_halt() {
  local reason="$1"
  case "$reason" in
    mcp_unreachable)
      cat <<'EOF'
The plan declares an MCP tool whose server is not defined in any
.mcp.json reachable from the main repo.

Fix one of:
  1. Define the server in .mcp.json (repo root, ~/.claude/, or ~/).
  2. Remove the offending mcp__*__* reference from the plan body and
     regenerate the manifest (writing-plans does this automatically).

Then re-run autopilot.sh.
EOF
      ;;
    mcp_tool_not_allowlisted)
      cat <<'EOF'
The plan declares an MCP tool that is defined in .mcp.json but is not in
this project's .claude/settings.local.json allowlist.

Fix one of:
  1. Open a Claude session in this repo and accept the permission prompt
     once: this writes the tool to the allowlist.
  2. Remove the offending mcp__*__* reference from the plan body and
     regenerate the manifest.

Then re-run autopilot.sh.
EOF
      ;;
    manifest_malformed)
      cat <<'EOF'
The plan's YAML front-matter is present but unparseable.

Fix:
  Inspect the plan file: the front-matter must start with `---` on line 1
  and end with `---` on its own line. Body content follows. If the file
  was truncated (e.g., SIGKILL during plan write), re-run writing-plans
  to regenerate.
EOF
      ;;
    verify_failed)
      cat <<'EOF'
Verification failed (tests, build, or LLM eval).

Fix:
  Read .finish-status in the worktree for the failure category, fix the
  underlying issue, then re-run autopilot.sh. The autopilot will resume
  from the verify phase.
EOF
      ;;
    phase_crashed)
      cat <<'EOF'
A phase script exited unexpectedly. The autopilot wrote this halt because
no other halt was emitted before the crash.

Fix:
  Read the log for the last 10 lines of stderr (in the details: field of
  this sentinel, if captured). Fix the underlying issue, then re-run.
EOF
      ;;
    headless_auth_incompat)
      cat <<'EOF'
A headless claude call site passes --bare. Per `claude --help`, --bare
restricts Anthropic auth to ANTHROPIC_API_KEY or apiKeyHelper — OAuth
and keychain are never read. Autopilot must work for Max-plan OAuth
users, so --bare is incompatible.

Fix:
  Remove --bare from the call site named in the details: field above.
  The canonical invocation is:
      claude -p - < "$PROMPT_FILE" &
  (no --bare). After removing it, re-run autopilot.sh.

Background: see docs/lessons-learned/2026-05-14-autopilot-bare-oauth-incompat.md
for the original incident and the upstream-feedback gap (no per-flag
opt-out exists for --bare's non-auth benefits).
EOF
      ;;
    *)
      echo "Unknown halt reason: $reason"
      echo "Add a case to lib/halt.sh format_halt() and update"
      echo "skills/_shared/autopilot-halt-format.md."
      ;;
  esac
}
