# KB-062: Critique-checklist structure tests not parameterized

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (Step 1e simplifier scan)
- **Location:** `e2e/tests/test_brainstorming_files.py:35-72`
- **Observed:** `test_research_critique_checklist_structure`, `test_authoring_critique_checklist_structure`, and `test_planning_critique_checklist_structure` each open with the same four lines (read file, assert top heading, assert three fixed sections), then diverge only on criterion names. A new mode checklist requires a new near-identical test function rather than adding one entry to a parameterized table.
- **Expected:** Convert to a single `pytest.mark.parametrize` test that takes (checklist_path, expected_top_heading, expected_criterion_names) and runs the shared structural assertions once per mode. Adding a new mode then becomes one parametrize entry.
- **Why out of scope:** Filed during simplifier scan after merge-readiness verification. Tests are passing as-is; refactor is a maintainability improvement, not a correctness fix.
- **Severity:** MEDIUM
- **Created:** 2026-05-06
