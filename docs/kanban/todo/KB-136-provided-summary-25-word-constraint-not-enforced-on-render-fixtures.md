# KB-136: provided_summary 25-word constraint not enforced on render fixtures

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code review for reverse-engineered-brand-input-asks)
- **Location:** `tools/test_oq_schema_v040.py:48-100`
- **Observed:** `test_provided_summary_is_one_sentence_under_25_words` runs only against `valid-v040-minimal.json`. The parametrized `test_render_fixtures_updated_to_v040` checks for presence of `provided_summary` but not the word-count constraint. A render fixture with a verbose summary would pass all tests today. All current fixtures happen to be under 25 words, so no breakage exists — but the contract specified in `open-questions-schema.md:46` ("1 sentence, ≤25 words") is unenforced on the fixtures that actually feed the renderer.
- **Expected:** Extend `test_render_fixtures_updated_to_v040` to assert `len(folder["provided_summary"].split()) <= 25` for every folder in every render fixture. Same check belongs on the legacy fixture parametrization for consistency.
- **Why out of scope:** Plan tasks 11-13 specified the schema bump and fixture updates but did not scope the word-count test to render fixtures. Adding it now is a coverage tightening, not a plan deliverable.
- **Severity:** LOW
- **Created:** 2026-05-18
