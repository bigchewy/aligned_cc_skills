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

Determine the base branch (try `main`, then `master`).

```bash
git diff --name-only <base-branch>...HEAD
```

Check if any changed files match LLM behavior surface patterns (advisor prompts, framework prompts, prompt builders, personalization logic). Look for eval configuration in `e2e/eval-config.ts` or similar.

**If surface files changed:** Run the project's eval command.
- **fail** (exit code 1) — Write status file with `status: FAILED` and `failed_at: LLM eval`. Exit.
- **warn** (exit 0 with warnings) — Note warning. Continue.
- **pass** (clean exit 0) — Continue.

**If no surface files changed:** Skip silently. Continue.

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
