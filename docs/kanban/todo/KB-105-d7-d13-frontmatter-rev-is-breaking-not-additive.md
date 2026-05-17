# KB-105: D7/D13 frontmatter rev is breaking, not additive

- **Type:** design defect (schema versioning miscategorization)
- **Severity:** LOW
- **Source:** Round 1 critique of reverse-engineered-brand revamp (L3)
- **Critics:** Architect, QA Engineer
- **Parent design:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`

## Finding (verbatim from critique)

> **L3. D7/D13 frontmatter rev is breaking, not additive** `[Architect, QA Engineer]`
> `best_guess` → `inferred_value`, `what_i_wrote` → `draft_excerpt`, `sources` → `evidence` are renames. Action: note explicitly in D13 — schema is breaking (0.1 → 0.2); existing `.open-questions.json` won't load; regenerate brand folder.

## Proposed action

Update D13 in the design to explicitly note:
- Schema rev is breaking: 0.1 → 0.2 (not additive)
- Field renames: `best_guess` → `inferred_value`, `what_i_wrote` → `draft_excerpt`, `sources` → `evidence`
- Existing `.open-questions.json` files will not load with the new schema
- Migration: regenerate brand folder (no automated migration provided)

## Created

2026-05-16
