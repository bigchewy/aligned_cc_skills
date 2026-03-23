# KB-022: Remove Decision Log appendix from executed plan

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `docs/plans/2026-03-23-blog-html-rendering.md:521-565`
- **Observed:** The Decision Log appendix is 45 lines of rationale for choices already baked into the implemented tasks. Once the plan is executed, the appendix has no operational value — it records why decisions were made, not what to do. Decision rationale belongs in commit messages or a separate ADR, not inline in an execution plan.
- **Expected:** Remove the Decision Log appendix before archiving the plan, or strip it during the archive step.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-03-23
