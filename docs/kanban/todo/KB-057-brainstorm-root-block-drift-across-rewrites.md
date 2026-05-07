# KB-057: Brainstorm `:root` block can drift across live.html rewrites

- **Type:** bug
- **Discovered during:** root-cause-analysis (QA Engineer critique)
- **Location:** `skills/brainstorming/modes/software.md:160`, `skills/brainstorming/modes/business.md:159`
- **Observed:** During a brainstorm, the agent rewrites `live.html` repeatedly as design sections are validated. The instruction "Preserve the `:root` block exactly as written in step 3" is one-line guidance buried in step 5 of the visualization phase, read once at session start. Across many rewrites and growing context-token pressure, the agent's working memory of the populated `:root` block can drift back toward the canonical aligned defaults. There is no checksum, no compare-before-write, no anchor file the agent can re-read cheaply.
- **Expected:** Wrap the `:root` block in `<!-- BRAND-TOKENS-START -->` / `<!-- BRAND-TOKENS-END -->` HTML comment markers (same pattern as `<!-- LIVE-REFRESH-START -->`). On every rewrite, instruct the agent to copy the marker block verbatim from the previous file rather than re-derive it. This converts an instruction-following problem (which drifts) into a copy-paste-from-file problem (which doesn't).
- **Why out of scope:** Initial brand-token fix (2026-05-06) addressed three higher-priority gaps the QA engineer flagged (naming-convention contract, monorepo lookup, placeholder detection). Drift is a slower-burn concern — a session has to run long enough for it to manifest. User scoped this to a follow-up.
- **Severity:** MEDIUM
- **Created:** 2026-05-06
