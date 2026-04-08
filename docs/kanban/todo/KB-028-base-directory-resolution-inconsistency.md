# KB-028: Duplicate {base-directory} resolution contract with inconsistent fallback coverage

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/persona-panel/modes/persona-creation-flow.md:73-74`
- **Observed:** The `{base-directory}` resolution contract is explained inline at SKILL.md lines 54 and 81, and again in persona-creation-flow.md Phase 4 with an additional Glob fallback strategy not present in SKILL.md. A fourth instance at SKILL.md lines 21-23 uses the token without any resolution guidance. Three different forms across two files.
- **Expected:** Single canonical definition of the `{base-directory}` resolution contract, referenced from all usage sites
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-04-08
