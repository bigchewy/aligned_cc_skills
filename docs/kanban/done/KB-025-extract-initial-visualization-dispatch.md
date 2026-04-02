# KB-025: Extract duplicated initial visualization dispatch block into shared file

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/brainstorming/SKILL.md:141-150`, `skills/business-brainstorming/SKILL.md:111-124`
- **Observed:** The initial session-document-generator dispatch template is structurally identical in both SKILL.md files, including the same dispatch template, the same 'Do not pause for user review' note, and the same output path pattern. This is the same extraction opportunity as the critique panel but was not addressed by this branch.
- **Expected:** Extract into a shared file or add to critique-panel-orchestration.md
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-03-30
