# KB-148: valid-legacy-v0.4.0.json is a near-duplicate of fixture-tiny.json

- **Type:** test-redundancy
- **Discovered during:** finishing-a-development-branch (Step 1e simplification scan)
- **Location:** `frameworks/reverse-engineered-brand/test-fixtures/render/valid-legacy-v0.4.0.json` vs. `fixture-tiny.json`
- **Observed:** The two fixtures differ only in `schema_version` string, Unicode escape normalization of em-dashes, and the absence of `display_groups`. The full OQ/folder payload is duplicated. Any future change to the scenario in `fixture-tiny.json` must be manually mirrored to `valid-legacy-v0.4.0.json`; a missed update produces a false pass or false fail on the legacy `legacyFolderAsGroup()` code path.
- **Expected:** Derive the legacy fixture from the tiny fixture at test time (strip `display_groups`, downgrade `schema_version`) OR document a "legacy fixture mirrors tiny exactly minus display_groups" rule with a generator script.
- **Why out of scope:** Fixture generation is renderer-validation infrastructure; lives outside the v0.4.1 ship.
- **Severity:** LOW
- **Created:** 2026-05-18
