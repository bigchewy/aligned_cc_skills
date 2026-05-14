# KB-050: Phase 3 critique prompt is a run-on sentence covering four distinct instructions

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/writing-plans/references/critique-panel-prompts.md:67`
- **Observed:** Phase 3 fuses manual-deploy catalog walking, autonomy-violations scanning, design-fidelity evaluation, and decision-log review into one unbroken paragraph. Phase 1 and Phase 2 each use explicit sub-bullets for multi-step instructions. The autonomy-violations addition lengthens an already dense block, making it harder for the executing LLM to distinguish where one instruction ends and the next begins.
- **Expected:** Restructure Phase 3 to mirror the sub-bullet pattern used in Phase 1 and Phase 2: one bullet per distinct instruction (manual-deploy walk, autonomy-violations scan, design-fidelity check, decision-log review).
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-04-28
