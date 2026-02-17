# KB-006: business-brainstorming references a critic-registry from a different skill

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/business-brainstorming/SKILL.md:109-110`
- **Observed:** Step 1 of the critique panel reads `skills/brainstorming/critic-registry.md` — a registry built for technical design critique (e.g., The Architect, The Security Reviewer). business-brainstorming has no critic-registry of its own, so technical-design critics evaluate business strategy documents, producing mismatched critique.
- **Expected:** Either create a business-specific critic-registry under `skills/business-brainstorming/`, or add a filter/note that selects only domain-appropriate critics from the shared registry.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-02-17
