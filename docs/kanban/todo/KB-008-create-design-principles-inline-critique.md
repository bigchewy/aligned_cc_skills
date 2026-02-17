# KB-008: create-design-principles embeds critique prompts inline instead of referencing checklist

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/create-design-principles/SKILL.md:258-288`
- **Observed:** Other critique-capable skills dispatch critics by instructing sub-agents to read an external checklist file (e.g., `design-critique-checklist.md`). create-design-principles instead embeds full sub-agent prompts inline in SKILL.md. The external checklist exists at `skills/create-design-principles/design-critique-checklist.md` but the inline prompts shadow it — the checklist file can diverge from what SKILL.md actually dispatches without any obvious breakage.
- **Expected:** Refactor the inline critique prompts to reference the external checklist file, consistent with brainstorming and writing-plans patterns.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-02-17
