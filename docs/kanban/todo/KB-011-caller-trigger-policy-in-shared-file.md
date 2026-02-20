# KB-011: Caller trigger policy encoded in shared generator file

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/_shared/kanban-html-generator.md:7-14`
- **Observed:** The "When to Generate" section lists which callers trigger generation and under what conditions, duplicating trigger logic that each caller already owns. Encoding per-caller trigger policy in the shared file creates a second place to update when any caller changes its trigger conditions.
- **Expected:** Remove per-caller trigger enumeration from the shared file. The shared file's responsibility is generation mechanics; trigger policy belongs exclusively in the callers.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-02-20
