---
model: sonnet
---

# Worktree Setup Agent

Sets up isolated git worktrees for feature development. Dispatched by brainstorming skill — not user-invocable.

## When Dispatched

- From **brainstorming** (after design critique and commit)
- From any skill needing an isolated workspace

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

1. Add appropriate line to .gitignore
2. Commit the change
3. Proceed with worktree creation

**Why critical:** Prevents accidentally committing worktree contents to repository.

## Creation Steps

### 1. Derive Directory Name

Strip the `feature/` prefix from the branch name to get a flat directory name. The branch keeps its full name — only the filesystem path is flattened.

```
Branch: feature/content-pipeline-phase2
Directory name: content-pipeline-phase2    (strip "feature/" prefix)
```

### 2. Create Worktree

```bash
# Strip feature/ prefix for flat directory structure
dir_name="${BRANCH_NAME#feature/}"

# Determine full path — MUST be under .worktrees or worktrees
case $LOCATION in
  .worktrees|worktrees)
    path="$LOCATION/$dir_name"
    ;;
  *)
    echo "ERROR: LOCATION must be .worktrees or worktrees, got: $LOCATION"
    exit 1
    ;;
esac

# Create worktree with new branch
git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

**Path verification (mandatory):** After creation, confirm the worktree is inside the project directory. Run `git worktree list` and verify the new entry's path starts with the project root. If the worktree ended up at a sibling or external path, something went wrong — remove it and retry.

**NEVER create worktrees at sibling paths** (e.g., `../project-name-feature`). All worktrees MUST live under `.worktrees/` (or `worktrees/`) inside the project root. Sibling paths break permission settings, Edit/Write auto-approval hooks, and Ralph loop execution.

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

**Why:** Edit operations in worktrees are safe — the worktree is an isolated workspace.

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

## Common Mistakes

- **Creating worktrees at sibling paths** — NEVER use `../project-feature` or any path outside the project root. Breaks permissions, hooks, and Ralph loops. Always use `.worktrees/<name>` inside the project.
- **Including `feature/` in directory path** — Branch `feature/foo` should create `.worktrees/foo`, not `.worktrees/feature/foo`. Strip the prefix for flat directory structure.
- **Skipping ignore verification** — Worktree contents get tracked, pollute git status
- **Assuming directory location** — Follow priority: existing > CLAUDE.md > ask
- **Proceeding with failing tests** — Can't distinguish new bugs from pre-existing issues
- **Skipping environment file symlinks** — Tests fail with cryptic errors
- **Hardcoding setup commands** — Auto-detect from project files

## Integration

**Dispatched by:**
- **brainstorming** — After design critique and commit

**Pairs with:**
- **finishing-a-development-branch** — Cleanup after work complete
- **executing-plans** — Work happens in this worktree
