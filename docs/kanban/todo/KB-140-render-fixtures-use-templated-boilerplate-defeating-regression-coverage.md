# KB-140: Render fixtures use templated boilerplate that defeats regression coverage

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (simplifier scan, reverse-engineered-brand-input-asks)
- **Location:** `frameworks/reverse-engineered-brand/test-fixtures/render/{fixture-tiny,fixture-realistic,fixture-stress}.json`
- **Observed:** Every OQ `rationale` field uses an identical template string ("Synthesized from {source} as the strongest convergent signal..."), 39 instances in fixture-realistic, 130 in fixture-stress. The `why_it_matters` fields in fixture-tiny.json also share a common tail sentence across all 6 OQs. These fixtures cannot catch regressions in the rationale or why_it_matters rendering path because all values are structurally identical — a bug that corrupts one would corrupt them all in the same way, and no comparison test would fail.
- **Expected:** Rewrite fixtures with realistic per-OQ variation — different rationale wording, different evidence framings, different why_it_matters per OQ. Treat fixtures as test data, not as filler.
- **Why out of scope:** Plan task 13 updated fixtures to v0.4.0 shape, not to content variety. The bulk-template approach predates this branch and the branch preserved it.
- **Severity:** MEDIUM
- **Created:** 2026-05-18
