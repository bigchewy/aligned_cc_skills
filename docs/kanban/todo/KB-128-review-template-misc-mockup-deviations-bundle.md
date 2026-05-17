# KB-128: Bundle of low-priority mockup deviations in review-template.html

- **Type:** mockup-deviation
- **Discovered during:** finishing-a-development-branch (mockup fidelity check)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html`
- **Observed:** Bundled low-priority deviations from the mockup fidelity scan, none individually severe:
  1. **Folder tab label casing:** Implementation uses lowercase folder tab labels (`strategy`, `language`, `audiences`, `personas`, `market`, `proof`, `design`). Mockup uses Title-Case.
  2. **Competitor card dt rows:** Mockup uses Category / ICP / Voice. Implementation uses Positioning / ICP / Pricing / Voice — `Category → Positioning` relabel is undocumented; `Pricing` is intentional per Task 13's `pricing_signal` schema.
  3. **Section-list hierarchy:** Mockup shows 2-tier nested labels (e.g., Strategy → Positioning + Narrative). Implementation derives single-level labels from `framework_dispatches[].fills`.
  4. **Section count badge:** Mockup uses semantic `status-partial` / `status-weak` classes tied to qualitative state. Implementation hard-codes `status-partial` and shows only raw count.
  5. **Subtitle line:** Mockup shows `Brainstorming session: reverse-engineered-brand-revamp`. Implementation shows `{org-name}` (already in H1, duplicates).
  6. **FRAMEWORK_NOTE empty:** Mockup includes `targeting the Director of Care Management persona` suffix for persona paste-backs. Implementation declares `FRAMEWORK_NOTE = {}` so the suffix is dropped.
  7. **Paste-back button order:** Mockup: Regenerate → Copy (Copy is primary). Implementation: Copy → Regenerate (Regenerate is primary). Affordance inverted.
- **Expected:** Address each item in subsequent polish work. Most are 1-2 line fixes.
- **Why out of scope:** Found during mockup fidelity scan; bundled because each is low-cost and low-impact individually. Non-blocking.
- **Severity:** LOW
- **Created:** 2026-05-17
