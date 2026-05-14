# KB-031: Module-level I/O executes at import time in test files

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `e2e/tests/test_trigger_map_paths.py:29-30`
- **Observed:** `TRIGGER_DATA = load_trigger_map()` and `SURFACE_PATTERNS = load_surface_patterns()` run at module import time. If either YAML file is missing or malformed, pytest collection crashes with an unhandled exception instead of a clear test failure.
- **Expected:** Move YAML loading into pytest fixtures so failures produce useful test error messages
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-04-09
