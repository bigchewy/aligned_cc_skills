---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification
---

# Using Git Worktrees

## Overview

Git worktrees create isolated workspaces sharing the same repository, allowing work on multiple branches simultaneously without switching.

**Core principle:** Systematic directory selection + safety verification = reliable isolation.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## Directory Selection Process

Follow this priority order:

### 1. Check Existing Directories

Use the Glob tool to check for existing worktree directories:

```
Glob(".worktrees")    # Preferred (hidden)
Glob("worktrees")     # Alternative
```

**If found:** Use that directory. If both exist, `.worktrees` wins.

### 2. Check CLAUDE.md

Use the Grep tool to search for worktree directory preferences:

```
Grep("worktree.*director", path="CLAUDE.md", "-i": true)
```

**If preference specified:** Use it without asking.

### 3. Ask User

If no directory exists and no CLAUDE.md preference:

```
No worktree directory found. Where should I create worktrees?

1. .worktrees/ (project-local, hidden)
2. ~/.config/aligned/worktrees/<project-name>/ (global location)

Which would you prefer?
```

## Safety Verification

### For Project-Local Directories (.worktrees or worktrees)

**MUST verify directory is ignored before creating worktree:**

Check if the directory is ignored by running each command separately (do NOT combine with `||`):

```bash
git check-ignore -q .worktrees
```

If the first command fails (directory not ignored), also check the alternative:

```bash
git check-ignore -q worktrees
```

**If NOT ignored:**

Fix broken things immediately:
1. Add appropriate line to .gitignore
2. Commit the change
3. Proceed with worktree creation

**Why critical:** Prevents accidentally committing worktree contents to repository.

### For Global Directory (~/.config/aligned/worktrees)

No .gitignore verification needed - outside project entirely.

**Note:** If you find an existing `~/.config/superpowers/worktrees/` directory from a previous setup, you may use it as a fallback. The preferred location is `~/.config/aligned/worktrees/`.

## Creation Steps

### 1. Detect Project Name

```bash
project=$(basename "$(git rev-parse --show-toplevel)")
```

### 2. Create Worktree

```bash
# Determine full path
case $LOCATION in
  .worktrees|worktrees)
    path="$LOCATION/$BRANCH_NAME"
    ;;
  ~/.config/aligned/worktrees/*)
    path="~/.config/aligned/worktrees/$project/$BRANCH_NAME"
    ;;
esac

# Create worktree with new branch
git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

### 3. Run Project Setup

Auto-detect and run appropriate setup:

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then poetry install; fi

# Go
if [ -f go.mod ]; then go mod download; fi
```

### 4. Symlink Environment Files

Worktrees share the repo but not untracked files like `.env.local`. Symlink them from the main worktree so tests and local dev work:

First, get the main worktree path:

```bash
git worktree list
```

Parse the output to extract the path from the first line (text before the first space). Store this as `main_worktree`. Do NOT use piped commands (`| head | awk`).

Then use Glob to find env files and symlink each one individually:

```
Glob(".env*", path="$main_worktree")
```

For each env file found, create a symlink:

```bash
ln -sf "$main_worktree/.env.local" .env.local
```

**Why critical:** Without `.env.local`, tests that depend on environment variables will fail — and the error won't obviously point to a missing env file.

### 5. Create Worktree-Local Settings

Create `.claude/settings.local.json` in the worktree root to auto-approve Edit operations. Use the Write tool (do NOT use `cat` with heredoc):

```
mkdir -p .claude
```

Then use the Write tool to create `.claude/settings.local.json` with this content:

```json
{
  "permissions": {
    "allow": [
      "Edit"
    ]
  }
}
```

**Why:** Edit operations in worktrees are safe — the worktree is an isolated workspace. This eliminates approval prompts for every file edit during plan execution, while preserving the approval requirement on the main repo.

### 6. Verify Jest Config (Node.js projects)

If the project uses Jest with `testPathIgnorePatterns` that excludes `.worktrees`, verify the config is worktree-aware (uses `__dirname.includes('.worktrees')` to conditionally apply the pattern). If the config hardcodes the exclusion, tests will silently find zero matches. **Do not modify the config** — if it's not worktree-aware, report the issue and ask the user.

### 7. Verify Clean Baseline

Run tests to ensure worktree starts clean:

```bash
# Examples - use project-appropriate command
npm test
cargo test
pytest
go test ./...
```

**If tests fail:** Report failures, ask whether to proceed or investigate.

**If tests pass:** Report ready.

### 8. Report Location

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify ignored) |
| `worktrees/` exists | Use it (verify ignored) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check CLAUDE.md → Ask user |
| Directory not ignored | Add to .gitignore + commit |
| Tests fail during baseline | Report failures + ask |
| No package.json/Cargo.toml | Skip dependency install |
| `.env*` files in main worktree | Symlink to new worktree |

## Common Mistakes

### Skipping ignore verification

- **Problem:** Worktree contents get tracked, pollute git status
- **Fix:** Always use `git check-ignore` before creating project-local worktree

### Assuming directory location

- **Problem:** Creates inconsistency, violates project conventions
- **Fix:** Follow priority: existing > CLAUDE.md > ask

### Proceeding with failing tests

- **Problem:** Can't distinguish new bugs from pre-existing issues
- **Fix:** Report failures, get explicit permission to proceed

### Skipping environment file symlinks

- **Problem:** Tests fail with cryptic errors because `.env.local` isn't tracked by git and doesn't exist in the new worktree
- **Fix:** Always symlink `.env*` files from the main worktree after setup

### Hardcoding setup commands

- **Problem:** Breaks on projects using different tools
- **Fix:** Auto-detect from project files (package.json, etc.)

## Example Workflow

```
You: I'm using the using-git-worktrees skill to set up an isolated workspace.

[Check .worktrees/ - exists]
[Verify ignored - git check-ignore confirms .worktrees/ is ignored]
[Create worktree: git worktree add .worktrees/auth -b feature/auth]
[Run npm install]
[Symlink .env.local from main worktree]
[Run npm test - 47 passing]

Worktree ready at /path/to/project/.worktrees/auth
Tests passing (47 tests, 0 failures)
Ready to implement auth feature
```

## Red Flags

**Never:**
- Create worktree without verifying it's ignored (project-local)
- Skip baseline test verification
- Proceed with failing tests without asking
- Assume directory location when ambiguous
- Skip CLAUDE.md check

**Always:**
- Follow directory priority: existing > CLAUDE.md > ask
- Verify directory is ignored for project-local
- Auto-detect and run project setup
- Verify clean test baseline

## Integration

**Called by:**
- **brainstorming** (Phase 4) - REQUIRED when design is approved and implementation follows
- Any skill needing isolated workspace

**Pairs with:**
- **finishing-a-development-branch** - REQUIRED for cleanup after work complete
- **executing-plans** or **subagent-driven-development** - Work happens in this worktree
