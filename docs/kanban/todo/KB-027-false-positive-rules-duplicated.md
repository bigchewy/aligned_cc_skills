# KB-027: False-positive rules duplicated across SKILL.md and catalog

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/portability-audit/SKILL.md:59-70`
- **Observed:** Phase 3's cross-cutting SAFE rules (fenced code blocks, e.g. markers, ~/.claude/ paths, template variables, || chains, command -v) are restated across the per-category False Positive Rules sections in portability-pitfall-catalog.md. The catalog is the declared authority; the inline summary adds a second place to maintain.
- **Expected:** Consolidate false-positive rules in the catalog only, with SKILL.md referencing the catalog rather than restating rules.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-04-07
