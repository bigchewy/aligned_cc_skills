# KB-013: Evaluate test-driven-development skill for deprecation

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (mockup fidelity research)
- **Location:** `skills/test-driven-development/SKILL.md`
- **Observed:** The test-driven-development skill is never directly invoked by any other skill or agent. Its content has been absorbed into the pipeline: writing-plans generates TDD-structured task specs, EXECUTE-PLAN.md instructs "Follow TDD," code-reviewer references testing-anti-patterns.md directly, and CLAUDE.md enforces TDD globally. The skill is listed as "(invoked by pipeline)" in README but nothing actually invokes it.
- **Expected:** Either deprecate the skill (remove from plugin.json, update README) or confirm it still serves a purpose as a standalone reference. Key dependencies to preserve: create-new-skill lists it as "REQUIRED BACKGROUND" (conceptual, not invocation), and code-reviewer references testing-anti-patterns.md (the support doc, not the skill itself).
- **Why out of scope:** Research finding during mockup fidelity gap analysis — not part of the current task
- **Severity:** LOW
- **Created:** 2026-02-25
