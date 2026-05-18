# KB-145: Init split leaves textarea event listeners unwired on readyState fallback path

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (Step 1e simplification scan)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html` — DOMContentLoaded handler (~lines 1943-1958) vs. readyState fallback (~lines 1986-1991)
- **Observed:** The DOMContentLoaded handler wires textarea `input` listeners for `.oq-form textarea` (rebuild-pasteback-on-input) and paste-back textareas (dirty-mark-on-input). The `readyState !== 'loading'` fallback block calls the four `render*` / `sync*` / `rebuild*` functions but does NOT replicate the textarea listener wiring. If the script runs late enough that `readyState` is already past `'loading'`, the listeners are never attached and user edits don't trigger paste-back rebuilds.
- **Expected:** Hoist the four init calls *and* the listener wiring into a single `initRenderer()` function, then call it from both the DOMContentLoaded handler and the readyState fallback. Removes the split-init footgun entirely.
- **Why out of scope:** Pre-existing pattern (predates this branch); the user-visible primary use case (static HTML opened directly) does not hit the readyState path. Filed for follow-up cleanup.
- **Severity:** MEDIUM
- **Created:** 2026-05-18
