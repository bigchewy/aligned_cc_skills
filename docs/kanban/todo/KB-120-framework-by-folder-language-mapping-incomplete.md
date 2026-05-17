# KB-120: FRAMEWORK_BY_FOLDER maps `language` only to brand-voice, missing messaging-distillation

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code review)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html:1109`
- **Observed:** The `FRAMEWORK_BY_FOLDER` map maps `language` → `brand-voice`. But the `language/` folder can contain both `voice.md` (owned by brand-voice) and `messaging.md` (owned by messaging-distillation). The paste-back generator always suggests `brand-voice` for any question in `language/`, even messaging-related ones. The paste-back prompt copy will be wrong for messaging questions.
- **Expected:** Resolve folder→framework mapping at the slice level rather than the folder level — e.g., `language/voice.md` → `brand-voice`, `language/messaging.md` → `messaging-distillation`. Either store the per-slice mapping in the OQ entry's `framework` field at PHASE 3 time, or expand the JS lookup to disambiguate by `file` substring.
- **Why out of scope:** Found during code review; users can manually pick the correct framework when pasting back. Non-blocking but produces wrong-by-default paste-backs for messaging OQs.
- **Severity:** MEDIUM
- **Created:** 2026-05-17
