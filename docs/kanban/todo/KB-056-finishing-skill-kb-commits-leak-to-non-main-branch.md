# KB-056: KB-commit instructions across skills silently target whatever branch the main repo is on

- **Type:** bug
- **Discovered during:** root-cause-analysis (after finishing-a-development-branch session)
- **Primary location:** `skills/finishing-a-development-branch/references/code-review-scan.md:80` (Step 1d/1e KB-filing)
- **Sibling locations** (same pattern, lower acuity — surfaced by Phase 5 completeness check):
  - `skills/executing-plans/SKILL.md:120-123` — files KB entries during execution; no commit branch guidance.
  - `skills/codebase-audit/SKILL.md` Phase 4 — files KB entries; no commit instructions, operator commits manually.
  - `skills/eval-audit/SKILL.md:64` — files KB entries to `docs/kanban/todo/`; no commit branch guidance.
  - `skills/_shared/kanban-entry-format.md` — the shared format doc says to "write" and "commit" but does not specify a branch.
- **Observed:** code-review-scan.md instructs "If CWD is the main repo, use bare `git add/commit`" — silent on which branch the main repo's HEAD is on. When the operator invokes the skill while the main repo is checked out to a feature/sister branch (normal — operators work on branches), KB commits land on that sister branch, not on `main`. Cherry-picking to the worktree's branch is then required to recover, and the misplaced commits remain stranded as add/add conflict bait against future merges. Reproduced this run on `feature/autopilot-orchestration-impl` finishing — KB-051..055 leaked to `feature/autopilot-monorepo-env-linking` (commits `3ef9b2c`, `2a98150`) before being cherry-picked, then the sister branch was deleted. The sibling skills above share the same latent exposure: any KB entry commit while the main repo is not on `main` lands somewhere wrong.
- **Expected:** Centralize the guard. Add a `skills/_shared/kanban-commit-guard.md` (or extend `kanban-entry-format.md`) that mandates one of:
  (a) Pre-flight check — verify `git -C <main-repo> branch --show-current` is `main`/`master` before any KB commit; fail loudly otherwise.
  (b) Preferred — commit KB findings to the worktree branch directly (when operating from a worktree). They ride into main on the feature merge; no cross-branch state to manage. Semantically tighter: KB findings ARE findings from that branch's review.
  Then update each skill that files KB entries to reference the shared guard.
- **Why out of scope:** The current finishing run completed and was salvaged via cherry-pick + branch delete. This is a structural fix to prevent recurrence across the skill family.
- **Severity:** MEDIUM
- **Created:** 2026-04-30
