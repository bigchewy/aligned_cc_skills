# KB-039: diagram.md description hardcodes a single design-principles.md path

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/create-image/modes/diagram.md:5`
- **Observed:** The opening description states the file matches tokens "from the local repo's docs/design/design-principles.md", but the router resolves the path from three candidates and passes the result. The hardcoded path misleads contributors.
- **Expected:** Description should reference the resolved path from the router rather than hardcoding a specific path.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-04-15
