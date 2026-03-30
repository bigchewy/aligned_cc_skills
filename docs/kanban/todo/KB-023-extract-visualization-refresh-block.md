# KB-023: Extract duplicated visualization refresh block into shared orchestration file

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/brainstorming/SKILL.md:213-228`, `skills/business-brainstorming/SKILL.md:154-169`
- **Observed:** The visualization refresh conditional is near-identical prose duplicated across both skills. The branch extracted critique panel orchestration into a shared file but left this block in both SKILL.md files; the next edit to the refresh logic will require touching two files and will likely diverge them.
- **Expected:** Extract into `skills/_shared/critique-panel-orchestration.md` with a configuration parameter, or a separate shared file
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** HIGH
- **Created:** 2026-03-30
