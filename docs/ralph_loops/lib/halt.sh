#!/usr/bin/env bash
# lib/halt.sh — structured halt sentinel write/read/format.
# Schema: skills/_shared/autopilot-halt-format.md.

if [ -n "${_AUTOPILOT_HALT_SH_LOADED:-}" ]; then return 0; fi
_AUTOPILOT_HALT_SH_LOADED=1

set -u

: "${HALT_PATH:=}"

# write_halt <reason> <phase> [details]
# Atomic write via mv; first writer wins. Subsequent writers append a
# secondary-halt block rather than overwriting.
write_halt() {
  local reason="$1"
  local phase="$2"
  local details="${3:-}"
  local target="${HALT_PATH:-.autopilot-halt}"
  local tmp="${target}.tmp.$$"
  local log="${LOG:-(unknown)}"

  if [ -f "$target" ]; then
    {
      echo ""
      echo "secondary-halt:"
      echo "  reason: $reason"
      echo "  phase: $phase"
      echo "  details: $details"
    } >> "$target"
    return 0
  fi

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

# format_halt <reason>
# Echoes the canonical fix-instructions for the reason. Add cases here when
# adding new reasons (and update skills/_shared/autopilot-halt-format.md).
format_halt() {
  local reason="$1"
  case "$reason" in
    mcp_unreachable)
      cat <<'EOF'
The plan declares an MCP tool whose server is not defined in any
.mcp.json reachable from the worktree.

Fix one of:
  1. Define the server in .mcp.json (worktree, repo root, or ~/.claude/).
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
    env_var_missing)
      cat <<'EOF'
The plan declares an env var that is not set in the worktree environment.

Fix:
  Set the variable in your shell, in .env.local (root or per-app), or in
  the worktree's environment file. The autopilot mirrors per-app env
  symlinks from the main repo into the worktree.

Then re-run autopilot.sh.
EOF
      ;;
    manifest_drift)
      cat <<'EOF'
The plan body references an MCP tool or env var not in the manifest, or
the manifest declares a tool/var not in the body.

Fix:
  Re-run writing-plans to regenerate the manifest from the body. Do not
  hand-edit the front-matter.
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
    uncommitted_main)
      cat <<'EOF'
Main branch has uncommitted changes that would block 'git merge main'
into the worktree.

Fix:
  Commit or stash the changes on main, then re-run autopilot.sh.
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
    human_action_required)
      cat <<'EOF'
The Ralph loop encountered a task that requires human action that the
loop cannot perform autonomously.

Fix:
  Read the iteration's last output for the specific blocker. After
  completing the manual step, mark the task ✅ in the plan and re-launch.
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
    *)
      echo "Unknown halt reason: $reason"
      echo "Add a case to lib/halt.sh format_halt() and update"
      echo "skills/_shared/autopilot-halt-format.md."
      ;;
  esac
}
