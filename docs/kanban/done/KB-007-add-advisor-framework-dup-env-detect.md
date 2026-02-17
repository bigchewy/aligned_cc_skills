# KB-007: add-advisor and add-framework duplicate environment-detection block

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/add-advisor/SKILL.md:24-48` and `skills/add-framework/SKILL.md:20-45`
- **Observed:** Both skills contain an identical Step 0 environment detection section — same three infrastructure markers, same summary print block, same detection priority logic, differing only in the word "advisor" vs "framework". Any future change to the detection logic must be made in two places with no cross-reference.
- **Expected:** Extract the shared environment-detection block into a shared reference file (e.g., `skills/shared/environment-detection.md`) and have both skills reference it, or add cross-references so editors know to update both.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-02-17

## Triage (2026-02-17)

- **Verdict:** REVISE
- **Evidence:** The Step 0 sections ARE structurally parallel but are NOT content-identical. `skills/add-advisor/SKILL.md:33-39` has a three-row detection table with rows for Advisor registry, Avatar generation, and Eval infrastructure, plus a four-field print summary (Prompt path, Registry, Avatars, Evals). `skills/add-framework/SKILL.md:30-45` has a three-row detection table with rows for Framework registry, Eval infrastructure, and Build script, plus a four-field print summary (Framework path, Registry, Evals, Build). The KB description overstates similarity by saying they differ "only in the word 'advisor' vs 'framework'" — in fact, the infrastructure tables have different rows entirely.
- **Root Cause:** `add-framework` was authored as a structural parallel to `add-advisor`, inheriting the same Step 0 pattern. The duplication is incidental — no deliberate choice to duplicate, just natural parallel authorship. Isolated to these two files; no other skills have a Step 0 environment detection section.
- **Risk Assessment:** The maintenance risk is real but narrower than the KB implies. Because the detection tables diverge meaningfully (Avatar vs Build), changes to one skill's detection logic rarely apply to the other. The shared risk is limited to the four-step path-detection algorithm (priority order) and the general print-summary pattern — both stable boilerplate. A shared extraction file would require parameterization or templates that make the human-readable skill file harder to follow; markdown skill files have no import mechanism, so "shared" means added indirection with no tooling enforcement. Risk of proposed fix (mutual editor notes): essentially zero — pure documentation, no behavior change.
- **Validated Fix:** Reject the extraction approach (option a from the KB) — it does not fit the markdown medium and adds indirection without enforcement. Implement the cross-reference approach (option b) as targeted editor notes. Add one note to each file's Step 0 section:
  - In `skills/add-advisor/SKILL.md`, after the print summary block (after line 48), add: `> **Editor note:** A parallel environment detection section exists in \`skills/add-framework/SKILL.md\` (Step 0). If you change the path-detection priority order here, apply the equivalent change there.`
  - In `skills/add-framework/SKILL.md`, after the print summary block (after line 45), add: `> **Editor note:** A parallel environment detection section exists in \`skills/add-advisor/SKILL.md\` (Step 0). If you change the path-detection priority order here, apply the equivalent change there.`
- **Files Affected:** `skills/add-advisor/SKILL.md`, `skills/add-framework/SKILL.md`
- **Estimated Scope:** Small — one line added to each file, pure documentation, no behavior change.
