# KB-156: CAP constant duplicated across both pipeline scripts

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `frameworks/reverse-engineered-brand/scripts/curate_open_questions.py:18` and `frameworks/reverse-engineered-brand/scripts/render_review.py:17`
- **Observed:** `CAP = 15` is defined in both scripts. They participate in the same pipeline — the curator enforces the cap on write and the renderer enforces it on read. A divergence would silently corrupt output.
- **Expected:** Extract to a small shared module (e.g. `frameworks/reverse-engineered-brand/scripts/_constants.py`) and import in both. Trade-off: two stdlib-only files instead of one each; cross-import adds a tiny coupling.
- **Why out of scope:** Two files duplicating one integer is acceptable now; flag if they diverge.
- **Severity:** LOW
- **Created:** 2026-05-28
