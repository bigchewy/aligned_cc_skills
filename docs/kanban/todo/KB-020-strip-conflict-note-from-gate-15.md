# KB-020: Strip superseded-design conflict note from quality gate 15

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/generate-blog-post/SKILL.md:149`
- **Observed:** Gate 15 embeds a parenthetical that explains a conflict between the mockup and the design doc and instructs the executor to follow the design doc. This conflict resolution belongs in the decision log, not inside an operational quality gate that an LLM will evaluate at runtime.
- **Expected:** Remove the parenthetical note from gate 15. If the design decision needs to be preserved, move it to a decision log or commit message.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-03-23
