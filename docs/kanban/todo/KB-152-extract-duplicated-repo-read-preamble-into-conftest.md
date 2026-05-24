# KB-152: Extract duplicated REPO/read() preamble into conftest.py

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `e2e/tests/conftest.py:1-7` (target); duplicated across 7 test files
- **Observed:** Seven test files (`test_resolve_advisor_source.py`, `test_shared_runners.py`, `test_authoring_mode_resolver.py`, `test_research_mode_resolver.py`, `test_critique_panel_resolver.py`, `test_contextual_recommendation.py`, `test_add_advisor_no_avatar.py`) each define the identical 5-line preamble: `REPO = Path(__file__).resolve().parents[2]` and `def read(rel): return (REPO / rel).read_text()`. A `conftest.py` already exists in the same directory but only adds a `sys.path` entry.
- **Expected:** Move `REPO` and `read()` into `e2e/tests/conftest.py` (as a fixture or module-level helper) so the eight-plus copies collapse to one and future test files inherit them.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task.
- **Severity:** MEDIUM
- **Created:** 2026-05-24
