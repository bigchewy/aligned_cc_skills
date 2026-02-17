# KB-002: Remove `find` command that violates project's own file-search rule

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `hooks/check-cron-results.sh:67`
- **Observed:** Line 67 uses `find "$PWD/docs/kanban/todo" -name '*.md'` to count kanban entries. CLAUDE.md (both global and project) explicitly bans Bash `find` for file search, requiring Glob instead. This hook ships a pattern it instructs Claude never to use — a direct contradiction.
- **Expected:** Replace `find` with a glob pattern or `ls` count that doesn't contradict the project's own rules.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-02-17
