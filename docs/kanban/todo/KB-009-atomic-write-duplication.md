# KB-009: Atomic write instructions duplicated at every call site

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/_shared/kanban-html-generator.md:155-165`
- **Observed:** The atomic write pattern (write to .kanban.html.tmp, then rename) is defined in the shared file's Atomic Write section but restated parenthetically in all three callers: executing-plans/SKILL.md step 6, writing-plans/SKILL.md step 4, and EXECUTE-PLAN.md step 7. Three copies of a procedural definition that must stay in sync.
- **Expected:** Call sites should say "use the atomic write pattern" and trust the shared file to define it, removing the parenthetical restatements.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-02-20
