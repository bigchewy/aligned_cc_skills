# KB-153: GONE_IDS in test_readme_freshness.py is a point-in-time allowlist with no expiry mechanism

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `e2e/tests/test_readme_freshness.py:9-19`
- **Observed:** The test asserts that 22 hard-coded IDs do not appear in the README files. Once the READMEs are clean this test permanently passes, leaving the list as dead data. Any future advisor/framework migration requires manually appending to this list or the guard silently provides no coverage.
- **Expected:** Derive disallowed IDs by diffing README contents against the live registries (IDs present in a README but absent from the current registry are violations), making the guard self-maintaining. Note: this is a design change rather than a pure complexity cut — triage should weigh it against YAGNI for a solo-dev, low-migration-frequency workflow.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task.
- **Severity:** MEDIUM
- **Created:** 2026-05-24
