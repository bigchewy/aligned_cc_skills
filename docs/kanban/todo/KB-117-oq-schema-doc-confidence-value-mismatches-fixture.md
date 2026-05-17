# KB-117: open-questions-schema.md describes invalid-bad-confidence.json with wrong confidence value

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code review)
- **Location:** `frameworks/reverse-engineered-brand/open-questions-schema.md:235`
- **Observed:** The schema reference doc line 235 reads: `Fails validation — \`confidence\` set to \`"certain"\` (not in enum)`. The actual fixture at `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/invalid-bad-confidence.json:28` uses `"confidence": "kinda-sure"` (per plan T1 Step 5). The fixture is correct; the schema reference doc is wrong.
- **Expected:** Update `open-questions-schema.md` line 235 to reference `"kinda-sure"` (matching the fixture) — or whatever invalid enum value the fixture actually uses.
- **Why out of scope:** Documentation drift caught during code review; non-blocking.
- **Severity:** MEDIUM
- **Created:** 2026-05-17
