# KB-147: iaEl duplicates the existing ce/tx/ap DOM-helper trio

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (Step 1e simplification scan)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html:2001-2068`
- **Observed:** `iaEl(tag, opts)` does what `ce(tag, cls)` plus an optional `textContent` assignment already does. It was added in v0.4.0 work (renderInputAsks and renderPerTabCallouts) without extending `ce`. The codebase now has two APIs for creating DOM elements; new contributors will pick whichever they encounter first.
- **Expected:** Extend `ce` to accept an options object, or pick one helper and migrate all call sites to it. Single DOM-creation API per file.
- **Why out of scope:** Pre-existing v0.4.0 carryover, not v0.4.1 code.
- **Severity:** LOW
- **Created:** 2026-05-18
