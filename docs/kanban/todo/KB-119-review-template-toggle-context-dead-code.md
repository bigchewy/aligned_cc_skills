# KB-119: toggleContext JS function and .oq-context-toggle CSS retained as dead code in review-template.html

- **Type:** dead-code
- **Discovered during:** finishing-a-development-branch (code review)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html:457-468` (CSS), `frameworks/reverse-engineered-brand/review-template.html:1016-1022` (JS)
- **Observed:** Plan T12 Step 5 explicitly required deletion of the `toggleContext` JS function — `<details>` is native and needs no JS. The implementation retained the function with a comment claiming "kept for backward compat", but no HTML in the body references `oq-context-toggle`. There is no backward-compat HTML to support; the comment is factually incorrect.
- **Expected:** Delete the `toggleContext` function (lines 1016-1022) and the `.oq-context-toggle` CSS rules (lines 457-468). The `<details>` elements throughout the template already provide the toggle behavior natively.
- **Why out of scope:** Found during code review; non-blocking but violates the plan's explicit deletion requirement.
- **Severity:** LOW
- **Created:** 2026-05-17
