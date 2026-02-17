# KB-005: business-write-plan runs Round 2 critique unconditionally

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/business-write-plan/SKILL.md:110-124`
- **Observed:** Every other critique-capable skill (business-brainstorming, brainstorming, writing-plans, create-design-principles) gates Round 2 on whether Round 1 found medium or high severity issues. business-write-plan always launches a second critique sub-agent regardless of Round 1 findings, producing unconditional overhead and inconsistent behavior across the skill family.
- **Expected:** Gate Round 2 on Round 1 severity, consistent with all other critique-capable skills. Saves one opus sub-agent invocation per use when Round 1 is clean.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-02-17
