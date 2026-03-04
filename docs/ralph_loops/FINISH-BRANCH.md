# Finish Branch (Non-Interactive Merge to Main)

You are finishing a development branch by merging it to main. This is a non-interactive pipeline step — no user prompts, no option menus. Hardcoded to merge-to-main.

**CRITICAL: Run from the main repo directory, NOT from inside a worktree.**

## Parameters

Read the parameters appended below this prompt:
- **Branch:** The feature branch to merge
- **Worktree:** The worktree path to clean up
- **Plan:** The plan file path to archive
- **Main repo:** The main repo path (CWD should already be here)

## Step 0: Verify CWD

```bash
pwd
git rev-parse --show-toplevel
```

If CWD is inside a worktree, print "ERROR: Must run from main repo, not worktree" and exit.

## Step 1: Verify Tests

Run the project's test command (detect from `package.json`, `Cargo.toml`, `pyproject.toml`, or `CLAUDE.md`).

**If tests fail:** Print failures. Write status file (see Status File below) with `status: FAILED` and `failed_at: pre-merge tests`. Exit. Do not proceed.

**If tests pass:** Continue.

## Step 2: Verify Build

Run the project's build command.

**If build fails:** Print error. Write status file (see Status File below). Exit. Do not proceed.

**If build passes:** If tests passed in Step 1 but the build caught an issue tests missed, write a lesson to `docs/lessons-learned/YYYY-MM-DD-short-description.md` using the project's lesson template (if it exists). Continue.

## Step 3: LLM Eval (if surface changed)

Determine the base branch (try `main`, then `master`).

```bash
git diff --name-only <base-branch>...HEAD
```

Check if any changed files match LLM behavior surface patterns (advisor prompts, framework prompts, prompt builders, personalization logic) defined in the project's eval configuration.

**If surface files changed:** Run the project's eval command.
- **fail** (exit code 1) — Print scorecard. Write status file with `status: FAILED` and `failed_at: LLM eval`. Exit. Do not proceed.
- **warn** (exit 0 with warnings) — Continue with warning shown.
- **pass** (clean exit 0) — Continue silently.

**If no surface files changed:** Skip silently.

## Step 4: Code Simplification Scan (non-blocking)

Spawn the `aligned:code-simplifier` agent:

```
subagent_type: "aligned:code-simplifier"
prompt: "Analyze the branch changes for simplification opportunities.
  Base branch: <base-branch>
  Working directory: <project-root>

  CRITICAL CONSTRAINTS:
  - You are READ-ONLY. Do not use Edit, Write, NotebookEdit, or any file-modifying Bash commands.
  - Do NOT run git checkout, git switch, or any branch-switching command.
  - Do NOT create Kanban entries or write files. Return ONLY a JSON array in your final message.
  - Use the Read tool to read files, not cat/Bash.
  - Allowed Bash: git diff, git log, git show, git ls-files only."
```

If findings are returned, file KB entries per `skills/_shared/kanban-entry-format.md`. Commit them.

Report: "Code simplification scan: N opportunities filed to Kanban board." or "Code simplification scan: clean."

Continue regardless of findings.

## Step 5: Merge to Main

Determine the base branch (try `main`, then `master`). Run each command separately:

```bash
git checkout <base-branch>
```

```bash
git pull
```

```bash
git merge <feature-branch>
```

## Step 6: Verify Tests on Merged Result

Run the project's test command again to verify the merge didn't break anything.

**If tests fail:** Print failures. Write status file (see Status File below) with `status: FAILED` and `failed_at: post-merge tests`. The merge is done but tests are broken — the status file ensures the caller knows. Exit.

**If tests pass:** Continue.

## Step 7: Cleanup Worktree

Only remove the specific worktree for this branch. Do NOT touch other worktrees.

```bash
git worktree remove <worktree-path> --force
```

```bash
git branch -d <feature-branch>
```

## Step 8: Archive Plan Documents

Move the plan file to `docs/plans/completed/`:

1. Check if `docs/plans/` exists. If not, skip.
2. Verify the plan file is tracked with `git ls-files <plan-path>`. For untracked files, use plain `mv`.
3. Move:

```bash
mkdir -p docs/plans/completed
git mv <plan-file> docs/plans/completed/
```

Also check for associated design documents with the same date prefix and topic. Move those too.

4. Commit:

```bash
git commit -m "chore: archive completed plan docs to docs/plans/completed/"
```

## Step 9: Completion Summary

Analyze the branch's commit history:

```bash
git log --oneline <base-branch>...<feature-branch>
```

Print:

```
## Completion Summary

<1-3 sentence overview of what was built.>

| Step | Result |
|------|--------|
| Tests | <N/N passing> |
| Build | <Passed / Failed> |
| LLM eval | <Passed / Warned / Skipped — reason> |
| Code simplification | <N findings filed / Clean> |
| Merge | <Merged feature/x → main> |
| Worktree | <Removed> |
| Plan archive | <Archived N files / No plans found> |
```

Write the status file:

```bash
cat > <main-repo-path>/.finish-status <<'STATUS'
status: SUCCESS
branch: <feature-branch>
merged_to: <base-branch>
worktree: removed
plan: archived
STATUS
```

Then exit.

## Status File

**Every exit path MUST write `<main-repo-path>/.finish-status`** before exiting. This file is the only signal the background caller has about what happened.

On success, write the file in Step 9 (above).

On failure, write the file before exiting with the failure details:

```bash
cat > <main-repo-path>/.finish-status <<'STATUS'
status: FAILED
branch: <feature-branch>
failed_at: <step name, e.g., "pre-merge tests", "build", "post-merge tests">
detail: <one-line error summary>
STATUS
```

**Failure exit points that must write the status file:**
- Step 1 (tests fail)
- Step 2 (build fails)
- Step 3 (LLM eval fails)
- Step 6 (post-merge tests fail — merge already done, note this in detail)

The caller checks for this file after the background process completes.

## Rules

- Non-interactive. No user prompts, no option menus.
- ONE path: merge to main. No deploy, no keep-as-is, no discard.
- Run from the main repo directory, never from a worktree.
- Only remove the worktree being finished — do not touch others.
- Verify plan file tracking before `git mv`.
- Do NOT run deployment audit (for production deploys only).
- Do NOT update architecture docs (requires judgment).
- Do NOT check mockup fidelity (already checked per-task in Ralph loop).
