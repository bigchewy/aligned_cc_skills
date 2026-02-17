# KB-007: add-advisor and add-framework duplicate environment-detection block

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/add-advisor/SKILL.md:24-48` and `skills/add-framework/SKILL.md:20-45`
- **Observed:** Both skills contain an identical Step 0 environment detection section — same three infrastructure markers, same summary print block, same detection priority logic, differing only in the word "advisor" vs "framework". Any future change to the detection logic must be made in two places with no cross-reference.
- **Expected:** Extract the shared environment-detection block into a shared reference file (e.g., `skills/shared/environment-detection.md`) and have both skills reference it, or add cross-references so editors know to update both.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-02-17
