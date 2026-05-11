# KB-035: OUTLIER_MAP duplicated between generation script and test parametrize list

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `scripts/generate-framework-registry.mjs` (OUTLIER_MAP) and `e2e/tests/test_registry_schemas.py:122-144`
- **Observed:** The 11 outlier frameworks are hardcoded in `OUTLIER_MAP` in the generation script and again as a `@pytest.mark.parametrize` list in `test_outlier_frameworks_have_correct_metadata`. Two sources of truth: adding or renaming an outlier in the script requires a parallel update in the test, or the test silently becomes stale.
- **Expected:** Either have the test read outlier entries from the YAML registry directly (filtering by a flag or known ID list), or extract the outlier list to a shared data file both can reference.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** HIGH
- **Created:** 2026-04-13
- **Resolved:** 2026-05-11 — Extracted to shared `frameworks/_outliers.json`. Script and test both read from it. RCA caught an existing divergence: script's OUTLIER_MAP had `6-step-process → gabor-mate` while registry and test agreed on `wise-eric` — proved the bug. Shared file uses canonical `wise-eric`.
