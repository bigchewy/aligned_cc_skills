# KB-024: Consolidate duplicated nested sub-tabs rule

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/brainstorming/SKILL.md:152-159`, `skills/business-brainstorming/SKILL.md`
- **Observed:** The nested sub-tabs rule appears in both SKILL.md files at different verbosity levels — brainstorming has a 5-line version with the pattern spelled out, business-brainstorming has a 1-line compressed version. These describe the same behavioral contract and will drift further on the next edit.
- **Expected:** Consolidate into one canonical location (shared file or critique-panel-orchestration.md)
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-03-30
