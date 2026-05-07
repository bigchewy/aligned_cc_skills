# KB-060: Critique-checklist boilerplate duplicated across four files

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (Step 1e simplifier scan)
- **Location:** `skills/brainstorming/{design,research,authoring,planning}-critique-checklist.md` (the `## Important` block and `## Critique Output Format` output-table skeleton in each)
- **Observed:** The `## Important` block (rules: "never use Bash grep", "report what IS wrong", "evidence per issue", "do NOT rewrite") and the `## Critique Output Format` output-table skeleton are copied verbatim across all four checklist files. A rule change must be applied in four places. The brainstorming-three-modes branch added three of these four files, so the duplication is largely new.
- **Expected:** Extract the shared boilerplate to a single source — likely `skills/brainstorming/references/critique-checklist-template.md` or similar — and have each checklist file reference it. Each checklist file then contains only its mode-specific criteria.
- **Why out of scope:** Filed during simplifier scan after merge-readiness verification. Refactor would touch all four checklists and require coordinated updates to the brainstorming SKILL.md handoff branches that reference them.
- **Severity:** MEDIUM
- **Created:** 2026-05-06
