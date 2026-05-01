#!/usr/bin/env bash
# PHASE: worktree
# INPUTS:
#   PROJECT (env var, absolute path)        — main repo path
#   BRANCH (env var)                        — feature/* branch name
#   PLAN_FILE (env var, absolute path)      — plan path on main
#   WORKTREE_DIR (env var, absolute path)   — target worktree path (orchestrator computes)
# OUTPUTS:
#   Worktree created at $WORKTREE_DIR
#   npm install run (if package.json present and node_modules absent)
#   Env files mirrored from main (root + per-app symlinks)
#   git merge main performed; plan file present in worktree
# EXIT CODES:
#   0 — worktree ready, plan file in worktree
#   1 — worktree creation, npm install, or other unrecoverable failure
#   2 — halt-with-reason: uncommitted_main (merge conflict against main)

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RALPH_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=../lib/process.sh
source "$RALPH_DIR/lib/process.sh"

# Alias so the env-link block (moved verbatim from autopilot.sh) keeps
# its $WORKTREE references unchanged. WORKTREE_DIR is the canonical input.
WORKTREE="$WORKTREE_DIR"

# --- Worktree creation ---

if [ -d "$WORKTREE_DIR" ]; then
  echo "Worktree already exists: $WORKTREE_DIR"

  # Check for stale merge state
  if [ -f "$WORKTREE_DIR/.git" ] && git -C "$WORKTREE_DIR" rev-parse MERGE_HEAD &>/dev/null; then
    echo "WARNING: Worktree has an in-progress merge. Aborting it." >&2
    git -C "$WORKTREE_DIR" merge --abort 2>/dev/null || true
  fi
else
  echo "Creating worktree: $WORKTREE_DIR (branch: $BRANCH)"

  # Handle case where branch exists but worktree doesn't
  if git -C "$PROJECT" show-ref --verify --quiet "refs/heads/$BRANCH" 2>/dev/null; then
    echo "Branch $BRANCH already exists — attaching worktree to it."
    if ! git -C "$PROJECT" worktree add "$WORKTREE_DIR" "$BRANCH"; then
      echo "ERROR: Failed to create worktree for existing branch $BRANCH." >&2
      exit 1
    fi
  else
    if ! git -C "$PROJECT" worktree add "$WORKTREE_DIR" -b "$BRANCH"; then
      echo "ERROR: Failed to create worktree with new branch $BRANCH." >&2
      exit 1
    fi
  fi
fi

# Setup: install deps, link env files, merge main
cd "$WORKTREE_DIR"

if [ -f package.json ] && [ ! -d node_modules ]; then
  echo "Installing npm dependencies..."
  if ! npm install 2>&1 | tail -5; then
    echo "ERROR: npm install failed. Check the log for details." >&2
    exit 1
  fi
elif [ -f Cargo.toml ]; then
  echo "Rust project detected — skipping dep install (cargo builds on demand)."
elif [ -f pyproject.toml ]; then
  echo "Python project detected — ensure venv is active."
fi

# === ENV-LINK BLOCK START ===
# Link env files if they exist in main repo but not worktree.
# Root-level: handles single-package repos and provides the target
# that per-app symlinks resolve through.
for envfile in .env.local .env; do
  if [ -e "$PROJECT/$envfile" ] && [ ! -e "$WORKTREE/$envfile" ]; then
    ln -sf "$PROJECT/$envfile" "$WORKTREE/$envfile"
    echo "Linked $envfile from main repo."
  fi
done

# Per-app: monorepos symlink env files into app/package dirs (e.g.
# apps/foo/.env.local -> ../../.env.local). Those symlinks are gitignored
# and don't propagate to fresh worktrees, so mirror them from main.
# Only symlinks are mirrored, never regular files — a real per-app env
# file is user-managed state we shouldn't auto-touch.
while IFS= read -r -d '' src; do
  rel="${src#$PROJECT/}"
  dest="$WORKTREE/$rel"
  [ -e "$dest" ] && continue
  [ -d "$(dirname "$dest")" ] || continue
  ln -s "$(readlink "$src")" "$dest"
  echo "Mirrored $rel from main repo."
done < <(find "$PROJECT" -type l -name '.env*' \
           -not -path "$PROJECT/.git/*" \
           -not -path "$PROJECT/.worktrees/*" \
           -not -path "$PROJECT/node_modules/*" -print0 2>/dev/null)
# === ENV-LINK BLOCK END ===

# Merge main so the plan file is available in the worktree
echo "Merging main into worktree..."
MERGE_EXIT=0
git merge main --no-edit 2>&1 || MERGE_EXIT=$?
if [ "$MERGE_EXIT" -ne 0 ]; then
  if git -C "$WORKTREE_DIR" rev-parse MERGE_HEAD &>/dev/null 2>&1; then
    git -C "$WORKTREE_DIR" merge --abort 2>/dev/null || true
    # Halt-with-reason: emitted as structured fields. Task 18 introduces
    # lib/halt.sh and a write_halt helper; until then, write the file
    # inline. Format follows the same key:value shape consumers expect.
    cat > "$PROJECT/.autopilot-halt" <<HALT_EOF
reason: uncommitted_main
phase: worktree
detail: git merge main aborted; resolve in $WORKTREE_DIR
HALT_EOF
    echo "ERROR: halt — uncommitted_main; resolve in $WORKTREE_DIR" >&2
    exit 2
  fi
  # Non-conflict failure (e.g., already up to date with divergent message)
  echo "WARNING: git merge main exited $MERGE_EXIT (may already be up to date)."
fi

# Verify plan file exists in worktree
# Plan path in worktree: reconstructed from basename because the plan was committed
# to main and merged forward. This assumes writing-plans enforces docs/plans/ convention.
PLAN_IN_WORKTREE="$WORKTREE_DIR/docs/plans/$(basename "$PLAN_FILE")"
if [ ! -f "$PLAN_IN_WORKTREE" ]; then
  echo "ERROR: Plan file not found in worktree at $PLAN_IN_WORKTREE" >&2
  echo "Expected it to arrive via 'git merge main'." >&2
  exit 1
fi

echo "Worktree ready: $WORKTREE_DIR"
echo "Plan in worktree: $PLAN_IN_WORKTREE"
exit 0
