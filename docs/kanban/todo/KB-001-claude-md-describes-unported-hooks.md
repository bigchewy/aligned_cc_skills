# KB-001: CLAUDE.md describes hook infrastructure that does not exist in repo

- **Type:** doc-staleness
- **Discovered during:** doc-staleness-detector
- **Location:** `CLAUDE.md`
- **Observed:** Lines 70-81 describe a SessionStart hook (`hooks/check-cron-results.sh`) that outputs `[CRON STATUS]`, `[DOC STALENESS]`, and `[CODE SIMPLIFIER]` tags, plus a UserPromptSubmit hook that outputs `[TEST AUDIT]`. However, the actual repo contains only `hooks/hooks.json` with a single UserPromptSubmit hook that runs `cat e2e/.eval-audit-last-run 2>/dev/null`. The file `hooks/check-cron-results.sh` does not exist. No SessionStart hooks are configured. The described tag-based dispatch system (`[CRON STATUS]`, `[DOC STALENESS]`, `[CODE SIMPLIFIER]`, `[TEST AUDIT]`) is not implemented in this repo.
- **Expected:** CLAUDE.md should either (a) reflect only the hooks currently present in the repo (the single eval-audit recency check), or (b) clearly mark the hooks section as "planned -- will be added by Phase B migration" so developers are not confused. The Phase B migration plan (Task 2: Port All 5 Hook Scripts, Task 3: Update hooks.json) is the intended fix, but until those tasks execute, the CLAUDE.md is misleading.
- **Source commits:** CLAUDE.md was updated on 2026-02-17 to describe target-state hooks, but hooks/ source was last modified 2026-02-13 and has not been updated to match. The doc is ahead of the code, not behind it.
- **Severity:** MEDIUM
- **Created:** 2026-02-17
