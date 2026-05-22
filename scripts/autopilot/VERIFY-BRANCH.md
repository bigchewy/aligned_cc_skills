# Verify Branch (Pre-Review)

You are verifying a development branch after automated implementation. Run the canonical verify gate, write `.finish-status`, then exit. Do NOT merge, clean up worktrees, or archive plan documents.

**Run from:** The worktree directory (CWD should already be set).

## Parameters

Read from the lines appended below this prompt:
- **Branch:** the feature branch name
- **Worktree:** the worktree path (should match CWD)
- **Plan:** the plan file path
- **Main repo:** the main repository path

## Process

Read `skills/finishing-a-development-branch/SKILL.md` and execute exactly:
- **Step 3: Run the test suite.** Run with reduced worker parallelism (≤2 parallel workers) to prevent memory exhaustion when running alongside other processes. For Jest: `npm test -- --maxWorkers=2`. For Vitest: `npx vitest run --pool=threads --maxWorkers=2`. For other runners, use the equivalent flag.
- **Step 4: Run the build command** (if defined; skip with note otherwise).
- **Step 5: LLM eval (if surface changed).** Apply the surface gate, scenario scoping, and per-scenario `npx promptfoo eval -c <scenario-path> --no-progress-bar` invocation as documented there.

Skip every other step in the finishing skill (deployment audit, manual-deploy notice, merge, cleanup, archival, simplification, architecture updates).

## Status File

Write `<worktree-path>/.finish-status` on every exit path:

```bash
# Success:
status: SUCCESS
branch: <feature-branch>
tests: passed
build: <passed/skipped>
eval: <passed/warned/skipped>
verified_at: <YYYY-MM-DD HH:MM:SS>

# Failure:
status: FAILED
branch: <feature-branch>
failed_at: <step name (tests | build | LLM eval)>
detail: <one-line error summary>
```

## Rules

- Non-interactive. No user prompts.
- Do NOT merge to any branch.
- Do NOT clean up worktrees.
- Do NOT archive plan documents.
- Do NOT run deployment audit (Step 1 in the finishing skill).
- Do NOT run code simplification scan (merge time).
- Do NOT update architecture docs (requires judgment).
- Write `.finish-status` on every exit path.
