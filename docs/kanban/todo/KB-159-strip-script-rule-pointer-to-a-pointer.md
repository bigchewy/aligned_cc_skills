# KB-159: Post-critique strip-script rule routes through a pointer-to-a-pointer

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `skills/brainstorming/references/visualization-protocol.md:46`
- **Observed:** Line 46 says "apply the strip-script rule from `{base-directory}/references/shared-rules.md`." This branch moved the canonical strip rule into `skills/_shared/visualization-runner.md` and reduced `shared-rules.md` to a one-line pointer back to the runner. The protocol now chains two indirections (protocol → shared-rules → runner) where the protocol could reference the runner directly, as it does everywhere else on this branch.
- **Expected:** Point line 46 at the runner's strip-rule section directly.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-06-11
