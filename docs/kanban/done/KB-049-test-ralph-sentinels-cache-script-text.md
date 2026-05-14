# KB-049: test_ralph_sentinels reads run-ralph.sh five times — cache at module level

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `e2e/tests/test_ralph_sentinels.py:16-17`
- **Observed:** The `_read()` helper calls `RUN_RALPH.read_text()` on every invocation, and all five test functions call it independently, producing five separate disk reads per test run. The file content is invariant across the session.
- **Expected:** Replace `_read()` with a module-level constant `SCRIPT_TEXT = RUN_RALPH.read_text(encoding="utf-8")` and have each test reference `SCRIPT_TEXT`. Misconfiguration of the path then surfaces once at import time as a single clear failure, rather than propagating as five redundant test failures.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-04-28
