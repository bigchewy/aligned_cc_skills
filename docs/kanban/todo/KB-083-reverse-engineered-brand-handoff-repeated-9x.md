# KB-083: Orchestrator hand-off instruction repeated 9 times in reverse-engineered-brand prompt

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (Step 1e, branch `feature/ai-native-brand-folder`)
- **Location:** `frameworks/reverse-engineered-brand/prompt.md:65-214`
- **Observed:** Across the orchestrator's nine sub-framework phases (Phases 2–10), the hand-off prose is near-verbatim: "Do NOT write the file to disk. Instead, output the complete assembled markdown... so the orchestrator can capture it" and "Yield the completed X as assembled-but-unwritten markdown conforming to `docs/brand-folder-spec.md § Y`. Do not write to disk." If the hand-off protocol changes (e.g., the orchestrator switches from in-memory capture to staged files), nine locations in this file require updating.
- **Expected:** Extract the hand-off contract into a single reference paragraph and have each phase cite it (e.g., "Apply the orchestrator hand-off contract from §X"). Phase-specific bridge prose stays inline.
- **Why out of scope:** Discovered during finishing-a-development-branch — not part of the original plan and not blocking merge.
- **Severity:** MEDIUM
- **Created:** 2026-05-16
