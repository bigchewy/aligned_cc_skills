# KB-010: Output location logic split between shared file and its callers

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/_shared/kanban-html-generator.md:148-155`
- **Observed:** The Output Location section defines where to write .kanban.html, but both writing-plans/SKILL.md and executing-plans/SKILL.md each carry their own partial restatement of the same rule. The writing-plans addition also introduces a main-worktree-vs-execution-worktree distinction not reflected in the shared file's Output Location section, making it an incomplete source of truth.
- **Expected:** Consolidate output location logic in the shared file's Output Location section (including the main-worktree-vs-execution-worktree distinction). Callers should reference the shared file without restating rules.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-02-20
