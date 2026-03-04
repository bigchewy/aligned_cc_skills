#!/bin/bash
# Checks if an eval coverage audit is overdue (7+ days since last run).
# Used as a UserPromptSubmit hook — stdout is injected into Claude's context.
# Self-gating: only fires in projects with an e2e/ directory.

[ ! -d "$PWD/e2e" ] && exit 0

TIMESTAMP_FILE="$PWD/e2e/.eval-audit-last-run"
INTERVAL_DAYS=7

now=$(date +%s)

if [ ! -f "$TIMESTAMP_FILE" ]; then
  echo "[EVAL AUDIT] No eval coverage audit has ever been recorded. Suggest running /aligned:eval-audit to the user."
  exit 0
fi

raw=$(cat "$TIMESTAMP_FILE")
# Support both Unix epoch and ISO 8601 timestamps
if echo "$raw" | grep -qE '^[0-9]+$'; then
  last_check="$raw"
else
  last_check=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$raw" +%s 2>/dev/null || date -d "$raw" +%s 2>/dev/null || echo 0)
fi
elapsed=$(( now - last_check ))
days_since=$(( elapsed / (24 * 60 * 60) ))

if [ "$days_since" -ge "$INTERVAL_DAYS" ]; then
  echo "[EVAL AUDIT] Last eval coverage audit was $days_since day(s) ago. Suggest running /aligned:eval-audit to the user."
fi

exit 0
