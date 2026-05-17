# KB-116: Reverse-engineered-brand prompt.md Hand-off contract paragraph contradicts PHASE 2 AUTO_MODE dispatch

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code review)
- **Location:** `frameworks/reverse-engineered-brand/prompt.md:31`
- **Observed:** The Hand-off contract paragraph at line 31 reads: "The orchestrator synthesizes the output *shape* of each sub-framework directly from the source material. It does **NOT** invoke the sub-frameworks at runtime." PHASE 2 now does the opposite — it dispatches sub-frameworks in AUTO_MODE. This paragraph survived the T20 intro update but was not caught.
- **Expected:** Rewrite the paragraph to describe the AUTO_MODE dispatch model: the orchestrator dispatches sub-frameworks at runtime in AUTO_MODE, each sub-framework synthesizes its own output, and the orchestrator aggregates results.
- **Why out of scope:** Important finding flagged after implementation was complete; non-blocking for merge but should be addressed before users encounter the framework.
- **Severity:** HIGH
- **Created:** 2026-05-17
