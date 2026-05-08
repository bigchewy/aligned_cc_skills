# KB-058: Brainstorm post-critique regen silently loses tokens if `/tmp/.../live.html` is missing

- **Type:** bug
- **Discovered during:** root-cause-analysis (QA Engineer critique)
- **Location:** `skills/brainstorming/modes/software.md:233`, `skills/brainstorming/modes/business.md:203`
- **Observed:** The post-critique regeneration instruction says "copy the `:root` block verbatim from the live visualization at `/tmp/brainstorm-{topic}-{timestamp}/live.html`." `/tmp` is volatile on macOS — wiped by reboot, `tmpwatch`-style cleanup, or manual cleanup. Brainstorms that span a reboot, or sessions where the earlier copy step failed silently, lose the source of truth for the populated `:root` block. The agent then rewrites `docs/mockups/{session-name}.html` from `brainstorm-components.md`'s literal aligned defaults — silently. The committed artifact ends up in aligned brand even though the live visualization rendered correctly during the session.
- **Expected:** Before regenerating, verify `/tmp/brainstorm-{topic}-{timestamp}/live.html` exists. If missing, re-run the design-tokens lookup (project root → monorepo apps/packages → global fallback → placeholder check) and re-derive `:root` from the design-principles file. Better long-term: at step 3 of the initial visualization, also write a sidecar `docs/mockups/{session-name}.tokens.css` (or an HTML comment in the design doc header) that survives `/tmp` wipes.
- **Why out of scope:** Initial brand-token fix scoped to highest-priority gaps. Cross-reboot brainstorms are rare; the silent-fallback-to-aligned failure mode is real but narrow.
- **Severity:** MEDIUM
- **Created:** 2026-05-06
