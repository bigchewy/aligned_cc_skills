# OQ Schema Fixtures (Layer 1)

These JSON fixtures exercise the PHASE 2.4 ready-to-load gate's schema validator. They
are read manually during framework development — there is no automated runner.

| Fixture | Expected gate behavior |
|---|---|
| `valid-minimal.json` | Pass |
| `valid-with-alternatives.json` | Pass |
| `valid-gap-slice.json` | Pass (GAP entries allow `null` for `framework_slot` + `deepen_with`) |
| `invalid-missing-impact.json` | Hard-fail (`field: impact` missing) |
| `invalid-bad-confidence.json` | Hard-fail (`field: confidence` not in enum) |
| `invalid-compound-question.json` | WARNING — compound-question regex match; does NOT block |

Schema reference: `frameworks/reverse-engineered-brand/open-questions-schema.md`.
