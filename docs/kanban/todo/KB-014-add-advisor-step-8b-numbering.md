# KB-014: Rename add-advisor Step 8b to a full numbered step

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/add-advisor/SKILL.md:198-217`
- **Observed:** The registry update is labeled '8b' rather than a top-level step number, making it read as optional or secondary to Step 8. It is a required, distinct operation — a contributor could complete Step 8 (place the file) and proceed to Step 9 (commit) without touching the registry, leaving discovery broken for all sessions that use the registry as primary source.
- **Expected:** Promote Step 8b to a full numbered step (e.g., Step 9) and renumber subsequent steps accordingly.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-03-12
