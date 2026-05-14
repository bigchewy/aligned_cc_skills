# KB-029: Extract duplicated section-slicing logic in distinctness scorer

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `e2e/scorers/distinctness.py:39-78`
- **Observed:** The pattern of iterating regex matches and slicing output into name/content dicts is written four times across parse_persona_sections — once for multi-header markdown (lines 40-45), once for multi-numbered (55-64), and once each for the single-header fallbacks (68-72, 74-78). Any change to the extraction logic must be applied in all four places.
- **Expected:** Extract the shared slice-between-matches logic into a helper function that all four branches call.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-04-08
