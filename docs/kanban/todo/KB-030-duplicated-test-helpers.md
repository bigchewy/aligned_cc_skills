# KB-030: Duplicated helper functions across two test files

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `e2e/tests/test_trigger_map_paths.py:14-26`
- **Observed:** `load_surface_patterns()` and `expand_pattern()` are defined identically in both `test_trigger_map_paths.py` and `test_eval_surface_patterns.py`. Any change to pattern-expansion logic must be made in two places, and the files will silently diverge.
- **Expected:** Extract shared helpers to `conftest.py` or a shared test utilities module
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-04-09
