# KB-016: add-framework has no registry update step while add-advisor does

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/add-framework/SKILL.md:182-192`
- **Observed:** add-advisor Step 8b requires updating advisors/registry.md, which use-advisor reads as its primary discovery source. add-framework has no equivalent registry step, and use-framework relies solely on glob discovery. An advisor file created outside the add-advisor skill will produce a stale registry, causing use-advisor's primary lookup to miss the new advisor while the glob fallback still finds it — silent partial failure. Frameworks are immune to this because glob is their only discovery mechanism.
- **Expected:** Either add a frameworks registry with a matching update step in add-framework, or remove the advisor registry in favor of glob-only discovery (matching the framework pattern).
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-03-12
