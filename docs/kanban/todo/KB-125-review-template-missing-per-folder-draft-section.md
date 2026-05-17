# KB-125: review-template.html missing per-folder Draft section from mockup

- **Type:** mockup-deviation
- **Discovered during:** finishing-a-development-branch (mockup fidelity check)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html` (folder panel rendering)
- **Observed:** The mockup at `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html` shows a `Draft — <file>.md` section on every folder panel with auto-generated headings (Market category, Customer alternatives, Unique value, Differentiated features, Role summary, Goals and pressures, Buying committee position) ABOVE the Assumptions and Questions sections. The implementation renders only Assumptions + Questions, dropping the Draft section entirely.
- **Expected:** Render a Draft summary per slice — either by reading the produced markdown file and inlining headings/excerpts, or by extending the OPEN_QUESTIONS schema with a `draft_outline` field per dispatched slice and rendering that.
- **Why out of scope:** Found after Task 12's three-commit cycle; the Draft section requires either filesystem reads at render time (not how the renderer works today) or a schema extension. Non-blocking — Assumptions + Questions panel is functional without it.
- **Severity:** HIGH
- **Created:** 2026-05-17
