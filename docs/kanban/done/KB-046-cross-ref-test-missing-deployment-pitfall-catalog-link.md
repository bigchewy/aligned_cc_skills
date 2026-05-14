# KB-046: Cross-ref test missing deployment-pitfall-catalog → manual-deploy-artifact-catalog link

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code review for feature/manual-deploy-artifacts)
- **Location:** `e2e/tests/test_skill_cross_references.py`; referenced string at `skills/finishing-a-development-branch/references/deployment-pitfall-catalog.md:5`
- **Observed:** `deployment-pitfall-catalog.md` contains an intro note linking to `skills/_shared/manual-deploy-artifact-catalog.md` as its sibling catalog. That cross-reference is not covered by `test_skill_cross_references.py`, so if either file is renamed or moved, the link will silently rot.
- **Expected:** Add a `pytest.mark.parametrize` entry that asserts the deployment-pitfall-catalog contains the string `skills/_shared/manual-deploy-artifact-catalog.md` and that the target resolves to a file.
- **Why out of scope:** Hardening, not a behavior bug. One test-case addition; fine as a follow-up.
- **Severity:** LOW
- **Created:** 2026-04-20
