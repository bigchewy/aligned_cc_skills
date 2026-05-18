# KB-142: Cross-group dedup in renderInputAsks() has no fixture coverage

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (Step 1d code review)
- **Location:** `frameworks/reverse-engineered-brand/test-fixtures/render/valid-dedupe-collision.json`
- **Observed:** Fixture contains a single `display_group` with two pre-deduped asks. The renderer's `renderInputAsks()` (review-template.html ~line 2007-2034) deduplicates via `seen[key]` *across* groups. With only one group in the fixture, the cross-group dedup branch is never exercised.
- **Expected:** A fixture with two distinct display_groups that each contain the same ask text — the rendered flat `<ul>` should contain a single `<li>` for that ask. The current `valid-dedupe-collision.json` already documents this intent via `_dedupe_test_note` but the structural shape doesn't match.
- **Why out of scope:** Renderer code is correct (Important rather than CRITICAL). Fix is fixture restructuring, not code, and doesn't block the v0.4.1 merge.
- **Severity:** MEDIUM
- **Created:** 2026-05-18
