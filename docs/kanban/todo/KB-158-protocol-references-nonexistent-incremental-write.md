# KB-158: Protocol references a non-existent incremental-write step in the runner

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/brainstorming/references/visualization-protocol.md:27`
- **Observed:** Line 27 instructs callers to "call the runner again" for incremental section updates and claims "the runner's Step 5 handles the incremental write." The runner has no such behavior — Step 5 is widget injection, a one-shot operation. The runner is a full render pipeline with no incremental-update mode. This instruction will mislead an LLM into re-running the entire pipeline (including the mermaid gate and browser-open) after every section, or will fail silently when "Step 5" does not behave as described.
- **Expected:** Correct line 27 to describe what the runner actually does (full re-render) or define the intended incremental-update behavior in the runner itself.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** HIGH
- **Created:** 2026-06-11
