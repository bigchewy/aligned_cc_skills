# KB-146: setAssumptionState and setQuestionState are identical functions

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (Step 1e simplification scan)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html:1162-1190`
- **Observed:** Both functions share the same body: guard on null card, toggle-off when current state matches, otherwise set state and rebuild paste-back. The only difference is a comment in `setAssumptionState`. Future state-button changes have to be edited in two places.
- **Expected:** Collapse to a single `setCardState(btn, state)` function and update the two call sites.
- **Why out of scope:** Pre-existing duplication, not introduced by v0.4.1.
- **Severity:** LOW
- **Created:** 2026-05-18
