# Plan Execution Handoff — Output Templates

This file contains the user-facing message templates that writing-plans outputs after saving a plan. The writing-plans SKILL.md uses its own logic to pick between Option A and Option B, then substitutes `{worktree-path}`, `{plan-file-path}`, `{feature-name}`, and `{plugin-root}` before presenting the selected option.

## Contents

- Standard handoff (worktree path known)
- Worktree-not-created handoff (worktree path unknown)

## Standard handoff (worktree path known)

````
## Next Steps

### Option A: Interactive execution (smaller plans, judgment calls needed)
Copy into a new Claude Code session:
> `cd {worktree-path}` then use `/aligned:executing-plans` to execute `{plan-file-path}`.

### Option B: Ralph loop execution (larger plans)
Run from any terminal:
```bash
cd {worktree-path}
bash {plugin-root}/docs/ralph_loops/run-ralph.sh "$(pwd)" "$(pwd)/docs/plans/YYYY-MM-DD-<feature-name>.md"
```

````

**After execution completes** (any option), run `/aligned:finishing-a-development-branch` in a new session from the main repo to merge, clean up the worktree, and archive the plan.

## Worktree-not-created handoff (worktree path unknown)

If the worktree path is not known (e.g., writing-plans was invoked without a prior brainstorming session):

````
### Option A: Interactive execution (smaller plans)
Copy into a new Claude Code session:
> Use /aligned:using-git-worktrees to create a worktree for branch `feature/{feature-name}`. Once ready, merge main (`git merge main --no-edit`) to bring in the plan, then use `/aligned:executing-plans` to execute `{worktree-path}/docs/plans/YYYY-MM-DD-<feature-name>.md`.

### Option B: Ralph loop execution (larger plans)
First create the worktree:
```bash
git -C /path/to/your/project worktree add .worktrees/{feature-name} -b feature/{feature-name}
```
```bash
cd .worktrees/{feature-name}
npm install
ln -sf ../../.env.local .env.local
git merge main --no-edit
```
Then run:
```bash
cd .worktrees/{feature-name}
bash {plugin-root}/docs/ralph_loops/run-ralph.sh "$(pwd)" "$(pwd)/docs/plans/YYYY-MM-DD-<feature-name>.md"
```
**IMPORTANT:** If the worktree setup above failed, do NOT run the script — it would execute against your main repo.

````

**After execution completes** (any option), run `/aligned:finishing-a-development-branch` in a new session from the main repo to merge, clean up the worktree, and archive the plan.
