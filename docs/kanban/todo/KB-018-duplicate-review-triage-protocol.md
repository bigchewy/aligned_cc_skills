# KB-018: Duplicate review triage protocol across blog post and deck skills

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/generate-blog-post/SKILL.md:194-211`, `skills/generate-deck/SKILL.md:188-195`
- **Observed:** The requestor/rep triage flow (accept all, cherry-pick, add context, conflict resolution, sub-agent failure handling) is written out in full in both skills. The logic is structurally identical; only the actor label differs. Divergence between the two copies is a maintenance liability every time the review protocol evolves.
- **Expected:** Extract the review triage protocol into a shared reference and include by reference from each skill.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** HIGH
- **Created:** 2026-03-23
