# KB-037: Undefined placeholder {session-name} with no derivation rule

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/brainstorming/modes/business.md:154-156` and `skills/brainstorming/modes/software.md:155-160`
- **Observed:** The pre-critique snapshot step instructs the agent to copy from `/tmp/brainstorm-{topic}-{timestamp}/live.html` to `docs/mockups/{session-name}.html`, but `{session-name}` is never defined or derived anywhere in either mode file or the SKILL.md router. The only naming convention given is for the design document (`YYYY-MM-DD-<topic>-design.md`), leaving the agent to guess the mockup filename — making the copy step and the critique panel's `visual-artifacts` config unreliable.
- **Expected:** Define a derivation rule for `{session-name}` (e.g., `YYYY-MM-DD-{topic}`) or reuse the design document's naming convention, and document it in the visualization startup section so agents construct a deterministic path.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** HIGH
- **Created:** 2026-04-15
