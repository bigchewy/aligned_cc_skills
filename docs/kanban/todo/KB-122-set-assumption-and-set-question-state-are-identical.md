# KB-122: setAssumptionState and setQuestionState are identical functions under different names

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (simplification scan)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html:1028-1056`
- **Observed:** Both functions perform identical operations: get the card, compare current state to the passed state, toggle off or set, call `clearSelected` and `rebuildPasteBack`. The only behavioral distinction (assumptions use approve/reject, questions use answered/skipped/leave) is already encoded in the button `onclick` attributes and does not require separate functions.
- **Expected:** Collapse both into a single `setCardState(btn, state)` function. Update the two sets of call sites accordingly.
- **Why out of scope:** Found during simplification scan; non-blocking.
- **Severity:** MEDIUM
- **Created:** 2026-05-17
