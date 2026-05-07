# KB-063: "Key Principles" bullets duplicated across all five brainstorming mode files

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (Step 1e simplifier scan)
- **Location:** `skills/brainstorming/modes/research.md:225-234`, `skills/brainstorming/modes/authoring.md:359-363`, `skills/brainstorming/modes/planning.md:298-300`, `skills/brainstorming/modes/software.md`, `skills/brainstorming/modes/business.md`
- **Observed:** The bullets "One question at a time", "Multiple choice preferred", and "Gates are mandatory" appear verbatim in all five mode files. These are process-wide constraints, not mode-specific principles; repeating them in five places means any wording change requires five edits, and the three new mode files added three more copies of this pattern.
- **Expected:** Move the shared principles to one location — either the brainstorming SKILL.md (referenced once and applied across all modes) or a `references/shared-principles.md` file linked from each mode. Each mode file then carries only mode-specific principles.
- **Why out of scope:** Filed during simplifier scan after merge-readiness verification. The duplication pre-existed in software.md and business.md; the new modes copied the convention rather than introducing a refactor.
- **Severity:** MEDIUM
- **Created:** 2026-05-06
