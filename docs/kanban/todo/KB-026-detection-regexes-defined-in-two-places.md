# KB-026: Detection regexes defined in two places

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/portability-audit/SKILL.md:39-52`
- **Observed:** Phase 2 lists all P1-P3 detection regexes inline in SKILL.md, and the same regexes are restated verbatim in portability-pitfall-catalog.md. When a regex needs updating, it must be changed in both files or they drift out of sync.
- **Expected:** Single source of truth for detection regexes — either inline in SKILL.md or in the catalog, not both.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-04-07
