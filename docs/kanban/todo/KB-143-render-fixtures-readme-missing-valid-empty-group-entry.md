# KB-143: render fixtures README missing valid-empty-group.json entry

- **Type:** doc
- **Discovered during:** finishing-a-development-branch (Step 1d code review)
- **Location:** `frameworks/reverse-engineered-brand/test-fixtures/render/README.md`
- **Observed:** `valid-empty-group.json` was created by plan Task 8 Step 6 but the fixtures README's inventory table does not list it. Users browsing the README as the canonical fixture inventory will not know this file exists or what scenario it covers.
- **Expected:** Add a row to the README table describing `valid-empty-group.json` — what shape it has and what render behavior it exercises (group with zero asks → callout container hidden, group with no open questions → empty-state copy).
- **Why out of scope:** Doc-only gap; renderer behavior and fixture content are both correct.
- **Severity:** LOW
- **Created:** 2026-05-18
