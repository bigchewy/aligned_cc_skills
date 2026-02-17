#!/bin/bash
# Checks if a test suite audit is overdue (1+ days since last run).
# Used as a UserPromptSubmit hook — stdout is injected into Claude's context.
# Self-gating: only fires in projects with a test config file.

[ ! -f "$PWD/jest.config.js" ] && [ ! -f "$PWD/jest.config.ts" ] && [ ! -f "$PWD/vitest.config.ts" ] && [ ! -f "$PWD/vitest.config.js" ] && exit 0

TIMESTAMP_FILE="$HOME/.claude/last-test-audit.timestamp"
INTERVAL_DAYS=1

now=$(date +%s)

if [ ! -f "$TIMESTAMP_FILE" ]; then
  date +%s > "$TIMESTAMP_FILE"
  echo "[TEST AUDIT] No test suite audit has ever been recorded. BLOCKING: Tell the user a test audit is needed, run /test-auditor, and do NOT work on the user's request until it completes."
  exit 0
fi

last_check=$(cat "$TIMESTAMP_FILE")
elapsed=$(( now - last_check ))
days_since=$(( elapsed / (24 * 60 * 60) ))

if [ "$days_since" -ge "$INTERVAL_DAYS" ]; then
  date +%s > "$TIMESTAMP_FILE"
  echo "[TEST AUDIT] Last test suite audit was $days_since day(s) ago. BLOCKING: Tell the user a test audit is needed, run /test-auditor, and do NOT work on the user's request until it completes."
fi

exit 0
