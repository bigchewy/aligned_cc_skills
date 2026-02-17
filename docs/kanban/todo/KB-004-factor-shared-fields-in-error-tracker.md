# KB-004: Factor shared fields out of the two return objects in `processEvent`

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `hooks/error-tracker.js:28-62`
- **Observed:** The `PostToolUseFailure` branch (lines 33-43) and the `PostToolUse` branch (lines 48-58) each build a return object with four identical fields: `ts`, `sid`, `tool`, `cwd`. Any change to these fields must be made in two places.
- **Expected:** Extract the shared fields into a `base` object, then spread into each branch's return value.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-02-17
