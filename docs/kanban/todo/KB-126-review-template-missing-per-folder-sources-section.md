# KB-126: review-template.html missing per-folder "Sources cited" section from mockup

- **Type:** mockup-deviation
- **Discovered during:** finishing-a-development-branch (mockup fidelity check)
- **Location:** `frameworks/reverse-engineered-brand/review-template.html` (.source-list CSS retained but no rendering code)
- **Observed:** The mockup shows a "Sources cited in this folder" sub-section on Strategy and Personas panels listing src-id / src-title / src-meta entries. The implementation retains the `.source-list` CSS (lines 727-743) but no JS references it and no DOM is built for it.
- **Expected:** Render a sources list per folder by reading the slice's `sources:` frontmatter (after slices are produced) or by adding a `sources` array per slice in the OPEN_QUESTIONS schema. Or, if the section is intentionally dropped, delete the dead `.source-list` CSS.
- **Why out of scope:** Found during mockup fidelity scan; non-blocking.
- **Severity:** MEDIUM
- **Created:** 2026-05-17
