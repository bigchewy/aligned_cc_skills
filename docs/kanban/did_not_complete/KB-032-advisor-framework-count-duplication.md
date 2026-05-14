# KB-032: Advisor/framework count update instructions duplicated across two skills

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/add-advisor/SKILL.md:218-229`
- **Observed:** Steps 8c in `add-advisor/SKILL.md` and 7b in `add-framework/SKILL.md` are word-for-word identical — same numbered steps, same target files, same description pattern. When the files to update change, both blocks must be updated independently with no enforcement that they stay in sync.
- **Expected:** Extract shared count-update instructions to a referenced partial in `skills/_shared/`
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-04-09
