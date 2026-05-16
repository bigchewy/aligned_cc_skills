# KB-082: "Confidence-upgrade close" duplicated between buyer-persona and messaging-distillation

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (Step 1e, branch `feature/ai-native-brand-folder`)
- **Location:** `frameworks/buyer-persona/prompt.md:246-253` and `frameworks/messaging-distillation/prompt.md:419-425`
- **Observed:** The post-assembly "three things that would raise this to high confidence" close uses the same three-item structure and near-identical framing in both frameworks (interview transcripts / win-loss data / Skeptic review). A change to the confidence-upgrade pattern requires editing two files.
- **Expected:** Either (a) extract the close into a shared snippet referenced from both prompts, or (b) accept the duplication if the two frameworks intentionally diverge on the three upgrade triggers — if (b), document the divergence so a future editor doesn't accidentally re-converge them.
- **Why out of scope:** Discovered during finishing-a-development-branch — not part of the original plan and not blocking merge.
- **Severity:** MEDIUM
- **Created:** 2026-05-16
