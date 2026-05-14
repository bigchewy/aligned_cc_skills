# KB-045: Orphaned `plan-with-env-var.md` fixture

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code review for feature/manual-deploy-artifacts)
- **Location:** `e2e/fixtures/manual-deploy/plans/plan-with-env-var.md`
- **Observed:** Fixture exists on disk but no test in `e2e/tests/test_manual_deploy_integration.py` references it. The file's purpose is ambiguous — may be dead scaffolding, or may be intended to cover M2 post-scan plan shape that was never wired to a test. Current M2 coverage is limited to a string check against `expected-outputs/post-automation-m2.md`, which is weaker than a structural test.
- **Expected:** Either (a) add a structural test that consumes `plan-with-env-var.md` to verify the M2 post-scan plan layout, or (b) delete the fixture if it is unused scaffolding.
- **Why out of scope:** Discovered during merge-time review. Deciding between (a) and (b) requires checking the original task intent; not worth blocking the merge for.
- **Severity:** MEDIUM
- **Created:** 2026-04-20
