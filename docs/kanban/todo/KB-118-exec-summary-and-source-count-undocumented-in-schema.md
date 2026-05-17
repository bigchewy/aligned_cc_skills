# KB-118: exec_summary and source_count are undocumented schema fields

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code review)
- **Location:** `frameworks/reverse-engineered-brand/open-questions-schema.md` (missing fields); `frameworks/reverse-engineered-brand/review-template.html` (renderExecNarrative, renderExecSnapshot consume them); `frameworks/reverse-engineered-brand/test-fixtures/render/fixture-realistic.json` (only fixture that includes them)
- **Observed:** `renderExecNarrative()` reads `OPEN_QUESTIONS.exec_summary` (sub-fields: `raw_material`, `primary_research`, `confidence_intro`). `renderExecSnapshot()` reads `OPEN_QUESTIONS.source_count`. Both fields appear in `fixture-realistic.json` but neither is defined in `open-questions-schema.md`. The schema's top-level structure table lists only `schema_version`, `folders`, `behavioral_alternatives`, `competitors`, `open_questions`.
- **Expected:** Add `exec_summary` (object with `raw_material`, `primary_research`, `confidence_intro` sub-fields) and `source_count` to the documented schema. Update PHASE 3's blob-building instructions to populate them. Otherwise the executive summary section and source-count tile will render blank on every real run.
- **Why out of scope:** Schema/renderer drift caught during code review; renderer null-guards prevent crashes, but the exec summary tab will silently render empty until PHASE 3 is updated to populate the fields.
- **Severity:** HIGH
- **Created:** 2026-05-17
