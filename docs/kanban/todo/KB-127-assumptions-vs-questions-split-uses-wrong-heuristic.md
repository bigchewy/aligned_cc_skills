# KB-127: Assumptions vs Questions split uses confidence heuristic instead of explicit kind field

- **Type:** mockup-deviation
- **Discovered during:** finishing-a-development-branch (mockup fidelity check)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html` (renderOQCard / panel rendering)
- **Observed:** The implementation derives assumption-vs-question split from `confidence != 'low'` for assumptions and `confidence == 'low'` for questions. The mockup mixes some P0/HIGH cards into the Assumptions list and some P1/MED cards into the Questions list — the split is by `oq-card data-kind` (`assumption|question`) emitted at extract time, not derived from confidence. The current heuristic will misclassify any MED-confidence true question or LOW-confidence assumption.
- **Expected:** Add a `kind: "assumption" | "question"` field to the OQ schema in `open-questions-schema.md` and emit it during PHASE 2.4. Use that field in the renderer instead of confidence.
- **Why out of scope:** Found during mockup fidelity scan; requires schema and PHASE 2.4 update. Coordinate with KB-118 (other undocumented fields).
- **Severity:** HIGH
- **Created:** 2026-05-17
