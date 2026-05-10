#!/usr/bin/env bash
# lib/manifest.sh — parse YAML front-matter from plan files and validate
# against executor environment. See skills/_shared/plan-manifest-format.md.

if [ -n "${_AUTOPILOT_MANIFEST_SH_LOADED:-}" ]; then return 0; fi
_AUTOPILOT_MANIFEST_SH_LOADED=1

set -u

# Globals populated by parse_manifest. Reset on each call.
MANIFEST_MCP_TOOLS=()

# parse_manifest <plan-file>
# Exit codes: 0 = manifest parsed, 1 = malformed, 3 = no manifest present.
# Echoes the parsed entries, one per line, prefixed with "mcp:".
parse_manifest() {
  local plan="$1"
  MANIFEST_MCP_TOOLS=()

  [ -f "$plan" ] || { echo "ERROR: plan file not found: $plan" >&2; return 1; }

  # Detect front-matter: file MUST start with `---\n`, then YAML, then `\n---\n`.
  local first_line
  first_line="$(head -1 "$plan")"
  if [ "$first_line" != "---" ]; then
    return 3  # no manifest
  fi

  # Extract YAML between the two `---` markers using awk
  local yaml
  yaml="$(awk 'NR==1 && /^---$/ {flag=1; next} flag && /^---$/ {exit} flag {print}' "$plan")"

  # Detect malformed: no closing `---` means yaml read to EOF (file ended)
  # Use the line count of yaml vs the file: if file has no second '---' line, fail.
  if ! awk 'NR>1 && /^---$/ {found=1; exit} END {exit !found}' "$plan"; then
    echo "ERROR: malformed front-matter (no closing '---')" >&2
    return 1
  fi

  # Use Python (already a dev-dep via pytest) to parse YAML reliably.
  local parsed
  parsed="$(printf '%s\n' "$yaml" | python3 -c '
import sys, yaml
try:
  d = yaml.safe_load(sys.stdin) or {}
except yaml.YAMLError as e:
  print("YAML_ERROR", file=sys.stderr); sys.exit(1)
for t in (d.get("mcp-tools-required") or []):
  print(f"mcp:{t}")
' 2>&1)" || { echo "ERROR: malformed YAML" >&2; return 1; }

  while IFS= read -r line; do
    case "$line" in
      mcp:*) MANIFEST_MCP_TOOLS+=("${line#mcp:}"); echo "$line" ;;
    esac
  done <<< "$parsed"

  return 0
}

# check_mcp_tool <tool-string> [worktree-cwd]
# Walks .mcp.json upward from worktree → main repo → $HOME/.claude/.
# Exit 0 = server defined and tool allowlisted, 2 = halt (server unreachable
# or tool not allowlisted).
# Echoes one of: "ok", "mcp_unreachable", "mcp_tool_not_allowlisted"
check_mcp_tool() {
  local tool="$1"
  local cwd="${2:-$PWD}"
  local server="${tool#mcp__}"
  server="${server%%__*}"

  # Walk upward; accumulate .mcp.json paths in order
  local dir="$(cd "$cwd" && pwd -P)"
  local mcp_files=()
  while [ "$dir" != "/" ]; do
    [ -f "$dir/.mcp.json" ] && mcp_files+=("$dir/.mcp.json")
    dir="$(dirname "$dir")"
  done
  [ -f "$HOME/.claude/.mcp.json" ] && mcp_files+=("$HOME/.claude/.mcp.json")
  [ -f "$HOME/.mcp.json" ] && mcp_files+=("$HOME/.mcp.json")

  # Server check via python (jq may not be available)
  local found=0
  for f in "${mcp_files[@]+"${mcp_files[@]}"}"; do
    # Pass $f and $server via env, not string interpolation, to avoid
    # quoting hazards if a path contains apostrophes.
    if MCP_FILE="$f" MCP_SERVER="$server" python3 -c "
import json, os, sys
d = json.load(open(os.environ['MCP_FILE']))
sys.exit(0 if os.environ['MCP_SERVER'] in (d.get('mcpServers') or {}) else 1)
" 2>/dev/null; then
      found=1
      break
    fi
  done
  if [ "$found" -eq 0 ]; then
    echo "mcp_unreachable"
    return 2
  fi

  # Allowlist check: walk settings.local.json from worktree → main → $HOME/.claude
  local settings_files=()
  dir="$(cd "$cwd" && pwd -P)"
  while [ "$dir" != "/" ]; do
    [ -f "$dir/.claude/settings.local.json" ] && settings_files+=("$dir/.claude/settings.local.json")
    dir="$(dirname "$dir")"
  done
  [ -f "$HOME/.claude/settings.local.json" ] && settings_files+=("$HOME/.claude/settings.local.json")

  for f in "${settings_files[@]+"${settings_files[@]}"}"; do
    if SETTINGS_FILE="$f" MCP_TOOL="$tool" python3 -c "
import json, os
d = json.load(open(os.environ['SETTINGS_FILE']))
allow = ((d.get('permissions') or {}).get('allow') or [])
exit(0 if os.environ['MCP_TOOL'] in allow else 1)
" 2>/dev/null; then
      echo "ok"
      return 0
    fi
  done

  echo "mcp_tool_not_allowlisted"
  return 2
}
