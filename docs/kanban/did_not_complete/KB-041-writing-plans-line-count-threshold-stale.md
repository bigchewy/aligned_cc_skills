# KB-041: writing-plans SKILL.md line-count threshold in plan is stale

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code-reviewer)
- **Location:** `docs/plans/completed/2026-04-16-skill-audit-remediation.md` (Task 20 verification threshold)
- **Observed:** Task 20 in the skill-audit-remediation plan specifies a 440-line failure threshold for `skills/writing-plans/SKILL.md` post-extraction. After extraction the file is 469 lines. Both extraction targets (critique panel prompts and execution handoff templates) were correctly replaced with pointers. The ~395-line target and 440-line threshold underestimated the volume of orchestration logic, decision heuristics, and resolution instructions that the plan itself said to retain inline. The file size is correct; the plan's threshold is wrong.
- **Expected:** If the plan is ever re-used as a reference pattern, update the threshold to ~480 lines, or remove the hard threshold in favor of an "extraction targets replaced" check. Non-blocking — the extraction work on this branch is complete and correct.
- **Why out of scope:** Plan estimation error, not a code defect. Surfaced during plan-drift review of completed Wave 3 work.
- **Severity:** LOW
- **Created:** 2026-04-16
