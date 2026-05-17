# KB-121: moveJargonChipsIntoContext is dead code — operates on static cards that no longer exist

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (simplification scan)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html:1572-1587`
- **Observed:** moveJargonChipsIntoContext scans DOM for `.oq-card` elements with `.chip-slot` / `.chip-deepen` in their header and moves them into a context block. All cards are now rendered by `renderOQCard`, which already injects the `oq-context-meta` strip into the `<details>` block before the card is appended. There are zero static `.oq-card` elements in the HTML body, so this function is a no-op every time it runs.
- **Expected:** Delete the function and its caller. Static-card migration is complete.
- **Why out of scope:** Found during simplification scan; non-blocking.
- **Severity:** MEDIUM
- **Created:** 2026-05-17
