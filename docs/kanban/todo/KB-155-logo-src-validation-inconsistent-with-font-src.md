# KB-155: Logo src validation inconsistent with font src validation in _validate

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `frameworks/reverse-engineered-brand/scripts/render_review.py:55`
- **Observed:** Logo src validation (line 55) inlines the same two checks (remote URL? escapes folder?) as a compound boolean expression in a single `if`, while the font src validation (lines 50-53) raises separately for each check with distinct error messages. Same validation logic expressed two inconsistent ways inside the same function.
- **Expected:** Either inline the font src checks into compound `if`s (smaller code, less specific error messages) or expand the logo check to two separate `if`-raises matching the font pattern. Pick one style.
- **Why out of scope:** Style consistency — not a bug.
- **Severity:** MEDIUM
- **Created:** 2026-05-28
