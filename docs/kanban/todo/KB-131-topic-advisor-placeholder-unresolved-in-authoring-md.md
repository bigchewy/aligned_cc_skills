# KB-131: {topic_advisor} placeholder never explicitly bound in authoring.md Phase 2b/2c/2d

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code review of feature/framework-runner-refactor)
- **Location:** `skills/brainstorming/modes/authoring.md:99-165`
- **Observed:** Phase 2b/2c/2d use `{topic_advisor}` as a placeholder throughout the structured Q&A dispatch (e.g., "the matched advisor's prompt in the proxy dispatch," "top-scoring advisor's prompt"). Unlike `software.md` (which uses a fixed `The Architect`), the binding from Phase 1 result to the `{topic_advisor}` substitution is implicit. The parity test (`test_qa_pattern_parity.py`) only checks the anchor sentence — it does not verify that `{topic_advisor}` is contextualized. A future PARITY MARKER sync could carry the placeholder verbatim and break the binding.
- **Expected:** Either (a) add an explicit "Resolving {topic_advisor}" subsection at the top of Phase 2b/2c/2d describing how the Phase 1 result populates the placeholder, or (b) make the substitution mechanical (replace placeholder with concrete identifier at dispatch time) and document it.
- **Why out of scope:** Implementation works as intended in current dispatches; this is hardening against future drift. Deferring to focused follow-up.
- **Severity:** MEDIUM
- **Created:** 2026-05-17
