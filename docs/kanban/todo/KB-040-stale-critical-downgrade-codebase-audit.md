# KB-040: Stale severity downgrade rule in codebase-audit Kanban handoff

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/codebase-audit/SKILL.md:179`
- **Observed:** The Kanban handoff mapping in `codebase-audit/SKILL.md` downgrades CRITICAL findings to HIGH with the justification "KB has no CRITICAL level". This branch (feature/skill-audit-remediation, Task 14) added CRITICAL as a valid severity to `skills/_shared/kanban-entry-format.md`. The rationale is now false, so CRITICAL audit findings will be silently filed at the wrong severity.
- **Expected:** Remove the CRITICAL→HIGH downgrade rule; let CRITICAL findings propagate at full severity when filed to the Kanban board.
- **Why out of scope:** Simplification opportunity surfaced by code-simplifier scan after Wave 2 Kanban deduplication — not part of the current plan's task set.
- **Severity:** HIGH
- **Created:** 2026-04-16
