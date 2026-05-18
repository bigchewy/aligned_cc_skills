# KB-133: Extract shared test fixtures into e2e/tests/conftest.py

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier scan of feature/framework-runner-refactor)
- **Location:** `e2e/tests/test_shared_runners.py:3-7`, `e2e/tests/test_qa_pattern_parity.py`, `e2e/tests/test_contextual_recommendation.py`, `e2e/tests/test_brainstorming_files.py`, `e2e/tests/test_registry_schemas.py`
- **Observed:** Four test files independently define an identical REPO-root computation and a `read(rel)` helper. A fifth (`test_registry_schemas.py`) repeats the same pattern via `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` and repeated `open(REPO_ROOT / ...)` calls. Same two-line pattern copied four times with no shared home.
- **Expected:** Move REPO/`read` definitions into `e2e/tests/conftest.py` as session-scoped fixtures or top-level constants. Update the five files to import.
- **Why out of scope:** Refactor would touch 5 files; the duplication is small and stable. Defer to a focused cleanup pass.
- **Severity:** MEDIUM
- **Created:** 2026-05-17
