# KB-081: Mode-detection block duplicated across brand-folder sub-frameworks

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (Step 1e, branch `feature/ai-native-brand-folder`)
- **Location:** `frameworks/brand-voice/prompt.md:23-26`, `frameworks/buyer-persona/prompt.md`, `frameworks/messaging-distillation/prompt.md`, `frameworks/competitive-battle-card/prompt.md`, `frameworks/proof-points-audit/prompt.md`
- **Observed:** The mode-detection paragraph ("At PHASE 1, confirm whether you are running standalone or as a sub-framework...") plus the WAIT-discipline preamble and `IMPORTANT: This framework is interactive...` banner are duplicated near-verbatim across all five sub-frameworks. If the hand-off contract or interactivity contract changes, five files must be updated in sync with no mechanical enforcement.
- **Expected:** Extract the shared preamble into a single source (e.g., `frameworks/_shared/orchestrated-mode-preamble.md`) and have each sub-framework `prompt.md` reference it, or inline-include it via a build step.
- **Why out of scope:** Discovered during finishing-a-development-branch — not part of the original plan and not blocking merge.
- **Severity:** MEDIUM
- **Created:** 2026-05-16
