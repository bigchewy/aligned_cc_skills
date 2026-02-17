# KB-005: business-write-plan runs Round 2 critique unconditionally

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/business-write-plan/SKILL.md:110-124`
- **Observed:** Every other critique-capable skill (business-brainstorming, brainstorming, writing-plans, create-design-principles) gates Round 2 on whether Round 1 found medium or high severity issues. business-write-plan always launches a second critique sub-agent regardless of Round 1 findings, producing unconditional overhead and inconsistent behavior across the skill family.
- **Expected:** Gate Round 2 on Round 1 severity, consistent with all other critique-capable skills. Saves one opus sub-agent invocation per use when Round 1 is clean.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-02-17

## Triage (2026-02-17)

- **Verdict:** CONFIRM
- **Evidence:** `skills/business-write-plan/SKILL.md:120` begins "**Round 2:**" with no conditional gate. Lines 120-124 unconditionally instruct launching a second sub-agent. All four peer skills use "**Round 2 (conditional):**" with "Only run if Round 1 found medium or high severity issues." (`brainstorming/SKILL.md:77-78`, `business-brainstorming/SKILL.md:128-129`, `writing-plans/SKILL.md:356-357`, `create-design-principles/SKILL.md:287`).
- **Root Cause:** Copy-omission. The conditional gate was standardized across the skill family but `business-write-plan` was not updated to match. The omission is unintentional — no CLAUDE.md philosophy supports always running two critique rounds.
- **Risk Assessment:** Near zero. The change only affects when Round 2 fires (skipped when Round 1 is clean). No external contracts, no tests, no imports, no API shapes involved.
- **Validated Fix:** In `skills/business-write-plan/SKILL.md`, change line 120 from `**Round 2:**` to `**Round 2 (conditional):**` and insert "Only run if Round 1 found medium or high severity issues." as the first line of the Round 2 section. Exact wording matches peer skills.
- **Files Affected:** `skills/business-write-plan/SKILL.md` (lines 120-121 only)
- **Estimated Scope:** Small — 2 lines changed, no logic complexity
