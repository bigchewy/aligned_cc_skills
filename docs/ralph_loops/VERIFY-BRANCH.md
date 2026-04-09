# Verify Branch (Pre-Review)

<!-- Coupling note: Steps 1-3 mirror FINISH-BRANCH.md Steps 1-3 (and
     finishing-a-development-branch/SKILL.md Steps 1-1b). Update in tandem. -->

You are verifying a development branch after automated implementation. Run all verification checks, report results, then exit. Do NOT merge, clean up worktrees, or archive plan documents.

**Run from:** The worktree directory (CWD should already be set).

## Parameters

Read the parameters appended below this prompt:
- **Branch:** the feature branch name
- **Worktree:** the worktree path (should match CWD)
- **Plan:** the plan file path
- **Main repo:** the main repository path

## Step 1: Verify Tests

Detect the project's test command from `package.json`, `Cargo.toml`, `pyproject.toml`, or `CLAUDE.md`.

Run the test suite.

**If tests fail:** Print failures. Write status file (see Status File below) with `status: FAILED` and `failed_at: tests`. Exit.

**If tests pass:** Continue.

## Step 2: Verify Build

Detect and run the project's build command.

**If no build command exists** (e.g., no `build` script in package.json): Skip, report "No build command — skipped." Continue.

**If build fails:** Print error. Write status file with `status: FAILED` and `failed_at: build`. Exit.

**If build passes:** Continue.

## Step 3: LLM Eval (if surface changed)

> Reduced non-interactive variant. Canonical logic is in `skills/finishing-a-development-branch/SKILL.md` Step 1b.

Determine the base branch (try `main`, then `master`).

**1. Config guard.** Check `ANTHROPIC_API_KEY` is set (`printenv ANTHROPIC_API_KEY`). If not set, skip with note "ANTHROPIC_API_KEY not set." Read `e2e/eval-surface.yaml` and `e2e/trigger-map.yaml`. If either is missing, skip with note "Eval config missing."

**2. Surface gate.** Get changed files via `git diff --name-only <base-branch>...HEAD`. Match against patterns in `e2e/eval-surface.yaml`:
- Directory globs (`advisors/prompts/**`): match paths starting with the directory prefix
- Wildcard patterns (`frameworks/*/prompt.md`): match paths like `frameworks/X/prompt.md`
- Specific files: exact string match

If no surface files changed, skip silently. Continue.

**3. Scenario scoping.** Look up changed surface files in `e2e/trigger-map.yaml`. Collect deduplicated scenarios.

**4. Run scoped evals.** For each scenario, run sequentially from the `e2e/` directory:

```bash
npx promptfoo eval -c <scenario-path> --no-progress-bar
```

**5. Interpret:**
- All exit 0 → Continue.
- Any exit 1 → Write status file with `status: FAILED` and `failed_at: LLM eval`. Exit.

**If no eval command exists:** Skip, report "No eval configured — skipped." Continue.

## Step 4: Write Status and Report

Write the status file:

```bash
cat > <main-repo-path>/.finish-status <<'STATUS'
status: SUCCESS
branch: <feature-branch>
tests: passed
build: <passed/skipped>
eval: <passed/warned/skipped>
STATUS
```

Print a verification summary:

```
## Verification Summary

| Check | Result |
|-------|--------|
| Tests | <N passing / N failing> |
| Build | <Passed / Skipped — no build command> |
| LLM eval | <Passed / Warned / Skipped — reason> |

Branch is ready for review.
```

Then exit.

## Status File

**Every exit path MUST write `<main-repo-path>/.finish-status`** before exiting.

On success, write the file in Step 4 above.

On failure, write:

```bash
cat > <main-repo-path>/.finish-status <<'STATUS'
status: FAILED
branch: <feature-branch>
failed_at: <step name>
detail: <one-line error summary>
STATUS
```

## Rules

- Non-interactive. No user prompts.
- Do NOT merge to any branch.
- Do NOT clean up worktrees.
- Do NOT archive plan documents.
- Do NOT run deployment audit (that's for production deploys via the full finishing skill).
- Do NOT run code simplification scan (that's for merge time).
- Do NOT update architecture docs (requires judgment).
- Write `.finish-status` on every exit path.
