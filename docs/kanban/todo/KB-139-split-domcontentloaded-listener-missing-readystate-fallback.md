# KB-139: Split DOMContentLoaded listener for input asks lacks readyState fallback

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (simplifier scan, reverse-engineered-brand-input-asks)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html:1989-2013, 2132-2135`
- **Observed:** The v0.4.0 additions wire `renderInputAsks` and `renderPerTabCallouts` through a second, parallel `DOMContentLoaded` listener at line 2132. The existing listener at line 1989 already guards with `if (document.readyState !== 'loading')` to handle the case where the DOM is already parsed before the script executes. The new listener has no such guard — in any execution context where DOMContentLoaded has already fired, the Inputs Needed section and per-tab callouts silently render empty. The established pattern is to add new functions to `renderAll` (single dispatch), not bolt on a parallel listener.
- **Expected:** Move `renderInputAsks(data)` and `renderPerTabCallouts(data)` into `renderAll`, then delete the second `DOMContentLoaded` listener. The existing guarded listener handles both initial and post-load execution.
- **Why out of scope:** The branch shipped a working implementation against the standard load order (script at end of body). Restructuring to use `renderAll` is a refactor, not a correctness fix in the deployed context.
- **Severity:** MEDIUM
- **Created:** 2026-05-18
