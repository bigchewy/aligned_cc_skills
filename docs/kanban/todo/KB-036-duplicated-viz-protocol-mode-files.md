# KB-036: Duplicated live visualization protocol across both mode files

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/brainstorming/modes/software.md:137-160` and `skills/brainstorming/modes/business.md:138-156`
- **Observed:** The four-step live visualization startup sequence, the pre-critique snapshot block, and the post-critique finalization block are reproduced verbatim across both business.md and software.md. Any future change to the protocol must be made in two places — divergence is already visible in minor wording differences between the two files.
- **Expected:** Extract the shared visualization protocol into a common reference (e.g., `skills/brainstorming/references/visualization-protocol.md`) and have both mode files reference it, reducing duplication and drift risk.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** HIGH
- **Created:** 2026-04-15
