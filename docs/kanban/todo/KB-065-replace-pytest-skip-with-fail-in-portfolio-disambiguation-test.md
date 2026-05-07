# KB-065: Replace pytest.skip with pytest.fail in portfolio disambiguation test

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (Step 1d code review)
- **Location:** `e2e/tests/test_brainstorming_handoff.py:106` (`test_portfolio_entry_with_missing_keywords_signals_disambiguation`)
- **Observed:** The test calls `pytest.skip("portfolio fixture missing 'Generic-brief case' entry — see Task 24 spec")` if the fixture heading is absent. The fixture currently contains the heading, so the test passes today. But if the fixture heading is ever renamed or deleted, the test will silently skip rather than fail — losing protection against fixture drift. Also: the comment references "Task 24 spec," which does not appear in the implementation plan (`docs/plans/2026-05-06-brainstorming-three-modes.md`).
- **Expected:** Replace `pytest.skip(...)` with `pytest.fail(...)` (or a plain `assert "Generic-brief case" in heading`) so a missing fixture heading fails loudly. Remove or correct the stale "Task 24 spec" comment.
- **Why out of scope:** Filed during code review after merge-readiness verification. Test is currently green; the change is a robustness fix to prevent silent regressions, not a correctness fix.
- **Severity:** LOW
- **Created:** 2026-05-06
