# KB-043: executing-plans Step 2 mode definition is a forward reference

- **Type:** simplification
- **Discovered during:** 2026-04-16-skill-audit-round3.md / Step 1e (finishing-a-development-branch)
- **Location:** `skills/executing-plans/SKILL.md:42-43`
- **Observed:** After Task 1's dedupe, Step 2 describes execution mode as "autonomous by default (defined in Overview)" and defers to the Overview for the full definition. A reader starting at Step 2 — the most likely entry point during execution — must scroll back to the Overview to understand the mode behavior. The previous triplicated version was self-contained at point of use.
- **Expected:** Either (a) restate the two-sentence canonical rule at Step 2 (accepting controlled duplication for readability) or (b) collapse the Overview block and the Step 2 block into one location that reads naturally top-to-bottom. Option (a) is closer to the original ergonomics; option (b) requires restructuring.
- **Why out of scope:** The round-3 audit flagged triplication as the primary defect. Consolidating was the fix. Whether the consolidation location is optimal is a secondary readability question; not in the plan's scope.
- **Severity:** MEDIUM
- **Created:** 2026-04-16
