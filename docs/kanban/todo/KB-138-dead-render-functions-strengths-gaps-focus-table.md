# KB-138: Dead render functions never called: renderStrengthsGaps, renderFocusTable

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (simplifier scan, reverse-engineered-brand-input-asks)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html:1536-1648`
- **Observed:** `renderStrengthsGaps` (targets DOM ids `strengths-list`, `gaps-list`) and `renderFocusTable` (targets `where-to-focus-first`) are defined but never called — not in `renderAll` and not in any DOMContentLoaded handler. The target DOM ids also do not exist in the HTML body, so the functions would silently no-op even if called. Creates confusion about which render pass surfaces strengths/gaps and focus data.
- **Expected:** Delete both functions and any helpers used only by them, OR add them to `renderAll` and create the corresponding DOM containers if the data is intended to render.
- **Why out of scope:** Pre-existing dead code, not introduced by this branch. The branch only modified the template by adding new render paths for input asks; these functions predate this work.
- **Severity:** MEDIUM
- **Created:** 2026-05-18
