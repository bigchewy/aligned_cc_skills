# KB-124: OQ schema validation rules duplicated verbatim between prompt.md and open-questions-schema.md

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (simplification scan)
- **Location:** `frameworks/reverse-engineered-brand/prompt.md:211-224` (and `open-questions-schema.md` for the duplicated content)
- **Observed:** PHASE 2 Check 3 (required fields, null-on-GAP rule) and Check 4 (slot-validator algorithm, no-slot-merging rule) in `prompt.md` reproduce the same field lists, enum constraints, and kebab algorithm already defined as authoritative in `open-questions-schema.md`. Two sources of truth for the same validation contract can drift; the schema doc is already the declared canonical reference.
- **Expected:** Reduce `prompt.md` checks 3 and 4 to short references that point at the schema doc's named sections (e.g., "Apply the schema validation rules from open-questions-schema.md §Required fields and §Slot validator"). Keep one canonical source.
- **Why out of scope:** Found during simplification scan; non-blocking.
- **Severity:** MEDIUM
- **Created:** 2026-05-17
