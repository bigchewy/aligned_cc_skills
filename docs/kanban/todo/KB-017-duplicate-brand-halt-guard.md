# KB-017: Duplicate brand halt guard across content skills

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/generate-blog-post/SKILL.md:36-37`, `skills/generate-deck/SKILL.md:45-46`, `skills/generate-one-pager/SKILL.md:14-15`
- **Observed:** The identical halt guard block — check for `brand/CLAUDE.md`, halt with the same error message — is copied verbatim into all three content generation skills. When the error message or the required path changes, it will be updated in one place and silently stale in the others.
- **Expected:** Extract the brand halt guard into a shared reference (e.g., `skills/_shared/brand-guard.md`) and include by reference from each skill.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** HIGH
- **Created:** 2026-03-23
