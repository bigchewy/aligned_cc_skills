# KB-021: Remove redundant 'Key principles' block that restates MDX template

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/generate-blog-post/SKILL.md:113-119`
- **Observed:** The 7-bullet 'Key principles' block after the MDX output template restates facts already shown in the template itself: blockquote syntax is demonstrated with `>`, heroImage path pattern is visible in the frontmatter block, and the description field's purpose is stated inline. Three of the seven bullets add no information the template doesn't already convey.
- **Expected:** Remove or significantly trim the Key principles block, keeping only bullets that add information not already evident from the template.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-03-23
