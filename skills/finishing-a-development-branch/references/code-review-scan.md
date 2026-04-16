# Code Review + Simplification Scan — Workflow Reference

Extracted from finishing-a-development-branch SKILL.md. Orchestrates the code-reviewer and code-simplifier sub-agents before merge.

## Contents

- Step 1d: Code Review
- Step 1e: Code Simplification Scan

### Step 1d: Code Review

**After all verification passes, dispatch a comprehensive code review against the plan.**

This step catches plan drift, missing error paths, and quality issues that tests and builds don't cover. The reviewer is a fresh sub-agent that hasn't seen the implementation conversation — it provides independent evaluation.

**Spawn the `aligned:code-reviewer` agent** via the Task tool:

```
subagent_type: "aligned:code-reviewer"
prompt: "Review the branch changes for this feature against the implementation plan.

  Branch: <branch-name>
  Base branch: <base-branch>
  Working directory: <worktree-path>
  Plan file: <plan-file-path>

  Run `git diff <base-branch>...HEAD` to see all changes on this branch.
  Read the plan file for context on what was intended.
  Follow all 7 review sections in your agent prompt.
  Pay special attention to Section 5 (Mock Error Path Coverage).

  Write your report as structured output to stdout.
  Use Read for files, Grep/Glob for searching. Do not use Bash for searching."
```

**If CRITICAL issues found:**
```
Code review found CRITICAL issues. Must fix before proceeding:

[Show CRITICAL findings]

Cannot proceed until critical issues are resolved.
```
Stop. Fix the issues in the worktree, commit, re-run tests (Step 1) and build (Step 1a), then re-dispatch the code reviewer.

**If only Important or Suggestions:** Show findings as context, continue to Step 1e. File Important findings to Kanban board using the standard entry format.

**If clean review:** Report clean, continue to Step 1e.

### Step 1e: Code Simplification Scan

**After all verification and doc updates, scan branch changes for simplification opportunities.**

This step is **non-blocking** — findings are filed to the Kanban board as improvement opportunities, but never prevent merge/PR.

**Spawn the `aligned:code-simplifier` agent** via the Task tool:

```
subagent_type: "aligned:code-simplifier"
prompt: "Analyze the branch changes for simplification opportunities.
  Base branch: <base-branch>
  Working directory: <project-root>

  CRITICAL CONSTRAINTS:
  - You are READ-ONLY. Do not use Edit, Write, NotebookEdit, or any file-modifying Bash commands.
  - Do NOT run git checkout, git switch, or any branch-switching command. The correct branch is already checked out.
  - Do NOT create Kanban entries or write files. Return ONLY a JSON array in your final message.
  - Use the Read tool to read files, not cat/Bash.
  - Allowed Bash: git diff, git log, git show, git ls-files only."
```

**If the agent returns findings** (non-empty JSON array):

1. Read `{base-directory}/../_shared/kanban-entry-format.md` for the KB template and counter instructions (see Path Resolution note in SKILL.md)
2. For each finding, file a KB entry with:
   - **Type:** `simplification`
   - **Discovered during:** `finishing-a-development-branch (code-simplifier)`
   - **Why out of scope:** `Simplification opportunity — not a bug or part of the current task`
   - Map finding fields: title → KB title, `file:line_range` → Location, observed → Observed, suggestion → Expected, severity → Severity
3. Commit the Kanban entries. **If CWD is a worktree**, use `git -C <main-repo-path> add/commit` (KB files are in main repo). If CWD is the main repo, use bare `git add/commit`.

**Report to user:**
```
Code simplification scan: N opportunities filed to Kanban board.
```

**If the agent returns no findings:** Report silently:
```
Code simplification scan: clean.
```

Continue to Step 1f.
