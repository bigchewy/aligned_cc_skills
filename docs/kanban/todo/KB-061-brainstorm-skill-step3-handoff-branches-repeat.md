# KB-061: Five near-identical handoff branches in brainstorming SKILL.md Step 3

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (Step 1e simplifier scan)
- **Location:** `skills/brainstorming/SKILL.md:138-177`
- **Observed:** Each `**If X mode:**` block in Step 3 is structurally identical: read the mode file, restate `{base-directory}` twice, reference the mode-specific checklist, reference the shared orchestration file. The three new modes added three more copies of the same 6-line pattern. The only variation is the mode name and checklist filename, both of which could be table-driven rather than repeated prose.
- **Expected:** Replace the five repeated branches with a single parameterized lookup — e.g., a small mode→checklist table plus one set of handoff instructions that substitutes the right filename. Reduces five copies to one + one row per mode.
- **Why out of scope:** Filed during simplifier scan after merge-readiness verification. The structure was retained as-is to keep the diff focused on adding modes rather than refactoring existing handoff prose; future mode additions or text changes would benefit from the consolidation.
- **Severity:** MEDIUM
- **Created:** 2026-05-06
