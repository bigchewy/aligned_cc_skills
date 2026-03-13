# KB-015: Remove dead repo-grouping reasoning from use-advisor Step 2

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/use-advisor/SKILL.md:35`
- **Observed:** The instruction 'Do not group by repo — all advisors live in a single flat directory' justifies a constraint by referencing a repo-grouping concept that was removed in this consolidation branch. No repo concept exists anywhere else in the skill. A new contributor would search for this concept, find nothing, and be confused about what they're being told to avoid.
- **Expected:** Simplify to 'List all advisors in a single flat list' — remove the negative justification referencing a removed concept.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-03-12
