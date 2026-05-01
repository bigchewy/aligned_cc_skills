# KB-056: finishing-a-development-branch silently commits KB findings to whatever branch the main repo is on

- **Type:** bug
- **Discovered during:** root-cause-analysis (after finishing-a-development-branch session)
- **Location:** `skills/finishing-a-development-branch/references/code-review-scan.md:80` (and Step 1e equivalent)
- **Observed:** Step 1d (code review) and Step 1e (simplification scan) instruct: "If CWD is the main repo, use bare `git add/commit`" to file Kanban entries. The instruction is silent on which branch the main repo's HEAD is on. If the operator invokes the skill while the main repo is checked out to a feature/sister branch (which is normal — operators typically work on a branch), KB commits land on that sister branch, not on `main`. Cherry-picking to the worktree's branch is then required to recover, and the misplaced commits remain stranded on the sister branch as add/add conflict bait against future merges. Reproduced this run on `feature/autopilot-orchestration-impl` finishing — KB-051..055 leaked to `feature/autopilot-monorepo-env-linking` (commits `3ef9b2c`, `2a98150`) before being cherry-picked.
- **Expected:** Either (a) skill checks `git -C <main-repo> branch --show-current` before any KB commit and fails loudly (or auto-switches to `main`) if not on `main`; or, preferred, (b) commit KB findings to the worktree's branch directly — they ride into `main` on the feature merge and there's no cross-branch state to manage. Option (b) is also semantically tighter: KB findings ARE findings from that branch's review.
- **Why out of scope:** The current finishing run completed and was salvaged via cherry-pick + branch delete. This is a structural fix to prevent recurrence.
- **Severity:** MEDIUM
- **Created:** 2026-04-30
