# KB-019: Dead content in generate-one-pager below halt notice

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/generate-one-pager/SKILL.md:10-24`
- **Observed:** The skill opens with an explicit STOP instruction that prevents execution, but the file continues with a "Planned Behavior" section describing steps the model is told never to run. This content is unreachable by definition and will silently drift out of sync with the implemented skills it is meant to preview.
- **Expected:** Remove the dead content below the halt notice, or move it to a separate planning doc.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-03-23
