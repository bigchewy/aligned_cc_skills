# oq-schema fixtures

Schema reference examples for the rich internal OQ emission shape (`open-questions-schema.md` §"Rich internal emission shape"). These are not automated test inputs — automated tests consume `test-fixtures/curation/` and `test-fixtures/render/`.

## Fixtures

| File | Description |
|---|---|
| `valid-rich-shape-minimal.json` | Two-entry `open_questions` array covering the full 18-field rich shape: one question-type OQ (confidence=medium, question present, inferred_value null) and one assumption-type OQ (confidence=high, inferred_value present, question null). Both entries use realistic brand-decision-shaped content. |
