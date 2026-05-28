# KB-154: Flatten font-src validation loop (4 levels deep)

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `frameworks/reverse-engineered-brand/scripts/render_review.py:44-53`
- **Observed:** Four levels of nesting (`for key → for face → for src → if not src → if remote → if escapes`) iterate over font src fields in `_validate`. An early-continue or a helper that yields non-null src values from a face would reduce this to two levels.
- **Expected:** Refactor to a flat loop or helper iterator that produces `(src, kind)` pairs, validated once each.
- **Why out of scope:** Simplification opportunity — not a bug, current code is correct and tested.
- **Severity:** MEDIUM
- **Created:** 2026-05-28
