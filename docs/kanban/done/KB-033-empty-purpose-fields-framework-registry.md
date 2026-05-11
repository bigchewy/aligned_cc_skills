# KB-033: 20 framework entries have empty purpose fields

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code-reviewer)
- **Location:** `frameworks/registry.yaml` (20 entries) and `scripts/generate-framework-registry.mjs:116`
- **Observed:** 20 framework entries have `purpose: ""`. The `dotMatch` fallback at script line 116 always produces an empty purpose string for frameworks whose prompt.md first lines use period-terminated sentences without a ` — purpose` clause. Empty strings render as blank in the HTML catalog and any consumer displaying purpose descriptions. Schema test passes because it checks key presence, not non-empty value.
- **Expected:** Populate the 20 empty purpose fields from framework prompt content, or fix the extraction regex to derive a purpose from the prompt body. Also add non-empty assertion to the schema test so this fails loudly.
- **Why out of scope:** Data quality issue requiring manual review or script enhancement — not part of the current merge decision
- **Severity:** HIGH
- **Created:** 2026-04-13
- **Resolved:** 2026-05-11 — Data already backfilled (0 empty purpose fields in current registry). Added `test_purpose_is_non_empty` and `test_use_when_is_non_empty` to `e2e/tests/test_registry_schemas.py` to prevent regression. Added warning in `scripts/generate-framework-registry.mjs` when period-terminated first line produces empty purpose.
