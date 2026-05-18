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

# === SETTINGS-LINK BLOCK START ===
# Mirror project-level Claude config (.claude/settings.{local,}json) and MCP
# config (.mcp.json) from main repo into the worktree so sub-Claudes spawned
# by later phases (mockup, verify) inherit project-level permissions and MCP
# server definitions. Without this, `git rev-parse --show-toplevel` in the
# worktree returns the worktree path, Claude Code treats it as the project
# root, finds none of these files, and falls back to user-level config only —
# project allowlist entries like `Bash(pytest *)` and project MCP servers
# become invisible. The verify gate then halts on an interactive prompt that
# never resolves under the non-interactive autopilot. Symlinks (not copies)
# so edits to main during a run propagate. Existing worktree files are left
# alone — the using-git-worktrees skill writes a narrow Edit-only
# settings.local.json in human-driven setups and we must not clobber it.
settings_linked=0
for settings_rel in .claude/settings.local.json .claude/settings.json .mcp.json; do
  src="$PROJECT/$settings_rel"
  dest="$WORKTREE/$settings_rel"
  if [ -f "$src" ] && [ ! -e "$dest" ]; then
    mkdir -p "$(dirname "$dest")"
    ln -s "$src" "$dest"
    echo "Linked $settings_rel from main repo."
    settings_linked=$((settings_linked + 1))
  fi
done
if [ "$settings_linked" -eq 0 ] && [ ! -e "$WORKTREE/.claude/settings.local.json" ]; then
  echo "WARNING: No project-level Claude settings or .mcp.json to mirror from main." >&2
  echo "         Sub-Claudes will inherit only user-level (~/.claude/) permissions." >&2
  echo "         The verify gate may halt on permission prompts if your test runner" >&2
  echo "         (pytest, npm test, etc.) is not in the user-level allowlist." >&2
fi
# === SETTINGS-LINK BLOCK END ===

# Merge main so the plan file is available in the worktree.
# On failure, let git's native diagnostic print to stderr and exit 1;
# autopilot.sh's run_phase converts that to phase_crashed. Do NOT auto-abort —
# the user needs the MERGE_HEAD state preserved to resolve conflicts in place.
echo "Merging main into worktree..."
if ! git merge main --no-edit; then
  echo "ERROR: git merge main failed in $WORKTREE_DIR. Resolve in the worktree, commit, then re-run autopilot." >&2
  exit 1
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
