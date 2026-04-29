# KB-048: TDD red-phase evidence missing from commit messages

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code-reviewer)
- **Location:** `docs/ralph_loops/EXECUTE-PLAN.md` (process); commit `0b44266` on feature/ralph-autonomy-enforcement
- **Observed:** Plan 2026-04-28-ralph-autonomy-enforcement Task 5 specifies a TDD red phase where 4 of 5 sentinel tests must FAIL before Task 6 implements the fix. The commit `0b44266` ("test(ralph): add failing tests…") contains no captured pytest output documenting which assertions actually failed at red-phase commit time. The static-parse content alone is sufficient evidence the tests *would* have failed (the asserted strings did not yet exist in run-ralph.sh), but no explicit red-phase artifact is preserved in the commit trail.
- **Expected:** TDD red-phase commits should include the failing pytest output (or a one-line summary listing the failed test IDs) in the commit body, so the audit trail proves the test actually failed before the fix landed. Update the EXECUTE-PLAN.md TDD protocol (or the writing-plans Manual Steps Policy) to require this.
- **Why out of scope:** Process improvement — branch implementation is correct and tests pass on green; this is a documentation/audit-trail gap, not a code defect.
- **Severity:** LOW
- **Created:** 2026-04-28
