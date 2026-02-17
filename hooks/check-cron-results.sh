#!/bin/bash
# SessionStart hook — shows audit summary and signals when checks are due.
#
# Settings audit runs via background launchd cron (global, no LLM needed).
# Doc staleness and code simplifier are project-scoped and only run when
# Claude Code is active in a repo — this hook signals when they're due.

now=$(date +%s)

# Derive project key from $PWD (replace / with -)
project_key=$(echo "$PWD" | sed 's|/|-|g')
project_result_dir="$HOME/.claude/cron-results/$project_key"

format_age() {
  local ts_file="$1"
  if [ ! -f "$ts_file" ]; then
    echo "never"
    return
  fi
  local last=$(cat "$ts_file")
  local days=$(( (now - last) / 86400 ))
  local date_str=$(date -r "$last" "+%Y-%m-%d %H:%M" 2>/dev/null || echo "unknown")
  echo "${date_str} (${days}d ago)"
}

read_result() {
  local file="$1"
  if [ ! -f "$file" ]; then
    echo "no data"
  else
    cat "$file"
  fi
}

# Adaptive interval: clean → 5 days, issues → 2 days, never run → due immediately
is_due() {
  local result_file="$1" timestamp_file="$2"
  [ ! -f "$timestamp_file" ] && return 0
  local interval_days=2
  [ -f "$result_file" ] && [ "$(cat "$result_file")" = "clean" ] && interval_days=5
  local last=$(cat "$timestamp_file")
  local days=$(( (now - last) / 86400 ))
  [ "$days" -ge "$interval_days" ]
}

days_since() {
  local timestamp_file="$1"
  if [ ! -f "$timestamp_file" ]; then
    echo "never"
    return
  fi
  local last=$(cat "$timestamp_file")
  echo "$(( (now - last) / 86400 ))"
}

# Read results — settings is global, others are project-scoped
settings_result=$(read_result "$HOME/.claude/last-settings-audit.result")
settings_age=$(format_age "$HOME/.claude/last-settings-audit.timestamp")

doc_result=$(read_result "$project_result_dir/last-doc-staleness-check.result")
doc_age=$(format_age "$project_result_dir/last-doc-staleness-check.timestamp")

code_result=$(read_result "$project_result_dir/last-code-simplifier.result")
code_age=$(format_age "$project_result_dir/last-code-simplifier.timestamp")

# Override "issues" → "clean (issues resolved)" if kanban todo is empty
todo_count=$(find "$PWD/docs/kanban/todo" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
if [ "$doc_result" = "issues" ] && [ "$todo_count" = "0" ]; then
  doc_result="clean (issues resolved)"
fi
if [ "$code_result" = "issues" ] && [ "$todo_count" = "0" ]; then
  code_result="clean (issues resolved)"
fi

# Always output the summary
echo "[CRON STATUS] Background audit results:"
echo "  Settings Security:  ${settings_result}  — last run: ${settings_age}"
echo "  Doc Staleness:      ${doc_result}  — last run: ${doc_age}"
echo "  Code Simplifier:    ${code_result}  — last run: ${code_age}"

# Signal when project-scoped checks are due (dispatched by Claude, not cron)
dispatch_tags=""

if [ -d "$PWD/docs" ] && [ ! -f "$PWD/.skip-doc-staleness" ]; then
  if is_due "$project_result_dir/last-doc-staleness-check.result" \
            "$project_result_dir/last-doc-staleness-check.timestamp"; then
    days=$(days_since "$project_result_dir/last-doc-staleness-check.timestamp")
    dispatch_tags+="[DOC STALENESS] Last doc staleness check was ${days} day(s) ago — dispatch doc-staleness-detector agent."$'\n'
  fi
fi

if [ -d "$PWD/src" ]; then
  if is_due "$project_result_dir/last-code-simplifier.result" \
            "$project_result_dir/last-code-simplifier.timestamp"; then
    days=$(days_since "$project_result_dir/last-code-simplifier.timestamp")
    dispatch_tags+="[CODE SIMPLIFIER] Last code simplifier scan was ${days} day(s) ago — dispatch code-simplifier-full agent."$'\n'
  fi
fi

if is_due "$HOME/.claude/last-settings-audit.result" \
          "$HOME/.claude/last-settings-audit.timestamp"; then
  days=$(days_since "$HOME/.claude/last-settings-audit.timestamp")
  dispatch_tags+="[SETTINGS AUDIT] Last settings security audit was ${days} day(s) ago — dispatch audit-settings agent."$'\n'
fi

# Output dispatch tags and instructions
if [ -n "$dispatch_tags" ]; then
  echo ""
  echo "$dispatch_tags"
fi

echo ""
echo "Present this summary to the user. IMPORTANT: Include the last-run date for each audit so the user can verify cron frequency."
if [ -n "$dispatch_tags" ]; then
  echo "Dispatch any due audits in the background before addressing the user's request."
fi

exit 0
