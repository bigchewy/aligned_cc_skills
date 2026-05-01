#!/usr/bin/env bash
set -u
# Note: intentionally NOT using set -e. Exit codes are checked explicitly
# after each critical command so we can print phase-specific diagnostics
# instead of dying silently.

# autopilot.sh — Full pipeline from design doc to verified branch
#
# Usage: autopilot.sh <project-path> <design-doc-path> [branch-name]
#
# Phases:
#   1. Write implementation plan (claude -p with writing-plans skill)
#   2. Create worktree + setup
#   3. Ralph loop (execute plan tasks one at a time)
#   4. Verify branch (tests, build, eval — no merge)
#
# The script stops after verification. The branch is NOT merged.
# Review the work, then merge manually or run the full finishing skill.
#
# Resume: Safe to re-run after interruption. Completed phases are detected
# and skipped automatically. The sentinel file is scoped to the design doc,
# so running with a different design doc starts a fresh pipeline.
#
# Environment variables:
#   MAX_ITERATIONS      — Ralph loop safety cap (default: 50)
#   ITERATION_TIMEOUT   — Ralph loop seconds per iteration (default: 900)
#   MAX_TIMEOUTS        — Ralph loop consecutive timeout cap (default: 5)
#   PHASE_TIMEOUT       — Timeout for plan-writing and verify phases (default: 3600 = 60 min)
#   MAX_MOCKUP_ITERATIONS — Mockup fidelity loop cap (default: 5)
#   MOCKUP_TIMEOUT      — Timeout per mockup fidelity iteration (default: 900 = 15 min)

PROJECT="${1:?Usage: autopilot.sh <project-path> <design-doc-path> [branch-name]}"
DESIGN_DOC="${2:?Usage: autopilot.sh <project-path> <design-doc-path> [branch-name]}"
BRANCH="${3:-}"
PHASE_TIMEOUT="${PHASE_TIMEOUT:-3600}"
MAX_MOCKUP_ITERATIONS="${MAX_MOCKUP_ITERATIONS:-5}"
MOCKUP_TIMEOUT="${MOCKUP_TIMEOUT:-900}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=lib/process.sh
source "$SCRIPT_DIR/lib/process.sh"

# Prompt files
WRITE_PLAN_PROMPT="$SCRIPT_DIR/WRITE-PLAN.md"
RALPH_SCRIPT="$SCRIPT_DIR/run-ralph.sh"
MOCKUP_PROMPT="$SCRIPT_DIR/MOCKUP-FIDELITY.md"
VERIFY_PROMPT="$SCRIPT_DIR/VERIFY-BRANCH.md"

# Skill files (referenced by WRITE-PLAN.md)
SKILL_FILE="$PLUGIN_ROOT/skills/writing-plans/SKILL.md"
CHECKLIST_FILE="$PLUGIN_ROOT/skills/writing-plans/plan-critique-checklist.md"
KANBAN_FORMAT="$PLUGIN_ROOT/skills/_shared/kanban-entry-format.md"

# --- Validation ---

for f in "$WRITE_PLAN_PROMPT" "$RALPH_SCRIPT" "$MOCKUP_PROMPT" "$VERIFY_PROMPT" "$SKILL_FILE" "$CHECKLIST_FILE" "$KANBAN_FORMAT"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: Missing required file: $f" >&2
    exit 1
  fi
done

PROJECT="$(cd "$PROJECT" && pwd)"
# Resolve DESIGN_DOC: relative paths are relative to PROJECT, not caller's cwd
if [[ "$DESIGN_DOC" != /* ]]; then
  DESIGN_DOC="$(cd "$PROJECT/$(dirname "$DESIGN_DOC")" && pwd)/$(basename "$DESIGN_DOC")"
else
  DESIGN_DOC="$(cd "$(dirname "$DESIGN_DOC")" && pwd)/$(basename "$DESIGN_DOC")"
fi

if [ ! -d "$PROJECT" ]; then
  echo "ERROR: Project directory does not exist: $PROJECT" >&2
  exit 1
fi

# Verify PROJECT is the main worktree, not a nested worktree
if [ -f "$PROJECT/.git" ]; then
  echo "ERROR: $PROJECT appears to be a git worktree, not the main repo." >&2
  echo "Pass the main repository path instead." >&2
  exit 1
fi

if [ ! -f "$DESIGN_DOC" ]; then
  echo "ERROR: Design doc does not exist: $DESIGN_DOC" >&2
  exit 1
fi

LOG="$PROJECT/.autopilot-log"
SENTINEL="$PROJECT/.autopilot-plan-path"
# STATUS is set after WORKTREE is known (Phase 2) so it lands inside the
# sandbox boundary.  Initialised empty here to satisfy set -u.
STATUS=""

# Log all output
if command -v stdbuf &>/dev/null; then
  exec > >(stdbuf -oL tee -a "$LOG") 2>&1
elif command -v gstdbuf &>/dev/null; then
  exec > >(gstdbuf -oL tee -a "$LOG") 2>&1
else
  exec > >(tee -a "$LOG") 2>&1
fi

# --- Process management ---
# Functions (cleanup, kill_claude, start_heartbeat, stop_heartbeat,
# start_watchdog, stop_watchdog, run_claude_phase) sourced from lib/process.sh.

PROMPT_FILE=""
CLAUDE_PID=""
WATCHDOG_PID=""
HEARTBEAT_PID=""

handle_signal() {
  echo ""
  echo "Interrupted — shutting down..." >&2
  kill_claude
  exit 130
}
trap handle_signal INT TERM
trap cleanup EXIT

echo "========================================"
echo "  Autopilot Pipeline"
echo "========================================"
echo "Project:    $PROJECT"
echo "Design doc: $DESIGN_DOC"
echo "Branch:     ${BRANCH:-<auto-detect from plan>}"
echo "Log:        $LOG"
echo ""

# ============================================================
# Phase 1: Write implementation plan
# ============================================================

PLAN_FILE=""

# Check sentinel — but only if it was created for THIS design doc
if [ -f "$SENTINEL" ]; then
  SENTINEL_DESIGN_DOC="$(head -1 "$SENTINEL")"
  SENTINEL_PLAN_PATH="$(tail -1 "$SENTINEL")"

  # Normalize sentinel design doc path to absolute for comparison
  # (sentinel may store relative or absolute paths depending on how it was written)
  if [[ "$SENTINEL_DESIGN_DOC" != /* ]]; then
    SENTINEL_DESIGN_DOC_ABS="$(cd "$PROJECT/$(dirname "$SENTINEL_DESIGN_DOC")" 2>/dev/null && pwd)/$(basename "$SENTINEL_DESIGN_DOC")"
  else
    SENTINEL_DESIGN_DOC_ABS="$SENTINEL_DESIGN_DOC"
  fi

  if [ "$SENTINEL_DESIGN_DOC_ABS" = "$DESIGN_DOC" ] && [ -f "$SENTINEL_PLAN_PATH" ]; then
    PLAN_FILE="$SENTINEL_PLAN_PATH"
    echo "=== Phase 1: SKIPPED (plan already exists) ==="
    echo "Plan file: $PLAN_FILE"
    echo ""
  else
    if [ "$SENTINEL_DESIGN_DOC_ABS" != "$DESIGN_DOC" ]; then
      echo "NOTE: Sentinel is for a different design doc. Starting fresh."
    else
      echo "WARNING: Sentinel points to missing file: $SENTINEL_PLAN_PATH"
    fi
    rm -f "$SENTINEL"
  fi
fi

if [ -z "$PLAN_FILE" ]; then
  echo "=== Phase 1: Writing Implementation Plan ==="
  echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"

  PROMPT_FILE="/tmp/.autopilot-write-plan-$$"
  cat > "$PROMPT_FILE" <<PROMPT_EOF
$(cat "$WRITE_PLAN_PROMPT")

Skill file: $SKILL_FILE
Checklist: $CHECKLIST_FILE
Kanban format: $KANBAN_FORMAT
Design document: $DESIGN_DOC
Project directory: $PROJECT
Plan path sentinel: $SENTINEL
PROMPT_EOF

  cd "$PROJECT"

  start_heartbeat "$PHASE_TIMEOUT" "plan writing"

  if ! run_claude_phase "Phase 1 (plan writing)" "$PHASE_TIMEOUT"; then
    stop_heartbeat
    exit 1
  fi
  stop_heartbeat
  rm -f "$PROMPT_FILE"
  PROMPT_FILE=""

  # Read plan path from sentinel (format: line 1 = design doc, line 2 = plan path)
  if [ -f "$SENTINEL" ]; then
    PLAN_FILE="$(tail -1 "$SENTINEL")"
  fi

  if [ -z "$PLAN_FILE" ] || [ ! -f "$PLAN_FILE" ]; then
    echo "ERROR: Could not find the plan file after Phase 1." >&2
    echo "Claude may not have written the sentinel file at $SENTINEL." >&2
    echo "Check the log at $LOG for details." >&2
    exit 1
  fi

  echo ""
  echo "Plan file: $PLAN_FILE"
  echo "=== Phase 1: Complete ($(date '+%H:%M:%S')) ==="
  echo ""
fi

# ============================================================
# Phase 2: Create worktree
# ============================================================

# Derive branch name from plan file if not provided
if [ -z "$BRANCH" ]; then
  PLAN_BASENAME="$(basename "$PLAN_FILE" .md)"
  # Strip leading date (YYYY-MM-DD-)
  FEATURE_SLUG="$(echo "$PLAN_BASENAME" | sed 's/^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}-//')"
  if [ -z "$FEATURE_SLUG" ]; then
    FEATURE_SLUG="$PLAN_BASENAME"
  fi
  BRANCH="feature/$FEATURE_SLUG"
fi

WORKTREE_DIR="$PROJECT/.worktrees/$(echo "$BRANCH" | sed 's|^feature/||')"

echo "=== Phase 2: Worktree Setup ==="

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

WORKTREE="$WORKTREE_DIR"
STATUS="$WORKTREE/.finish-status"

# Setup: install deps, link env files, merge main
cd "$WORKTREE"

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
  # Check if it's a conflict
  if git -C "$WORKTREE" rev-parse MERGE_HEAD &>/dev/null 2>&1; then
    echo "ERROR: Merge conflict when merging main into worktree." >&2
    echo "Resolve conflicts in $WORKTREE, then re-run this script." >&2
    git merge --abort 2>/dev/null || true
    exit 1
  fi
  # Non-conflict failure (e.g., already up to date with divergent message)
  echo "WARNING: git merge main exited $MERGE_EXIT (may already be up to date)."
fi

# Verify plan file exists in worktree
# Plan path in worktree: reconstructed from basename because the plan was committed
# to main and merged forward. This assumes writing-plans enforces docs/plans/ convention.
PLAN_IN_WORKTREE="$WORKTREE/docs/plans/$(basename "$PLAN_FILE")"
if [ ! -f "$PLAN_IN_WORKTREE" ]; then
  echo "ERROR: Plan file not found in worktree at $PLAN_IN_WORKTREE" >&2
  echo "Expected it to arrive via 'git merge main'." >&2
  exit 1
fi

echo "Worktree ready: $WORKTREE"
echo "Plan in worktree: $PLAN_IN_WORKTREE"
echo "=== Phase 2: Complete ==="
echo ""

# ============================================================
# Phase 3: Ralph loop
# ============================================================

echo "=== Phase 3: Ralph Loop ==="

# Check if all tasks are already complete
TOTAL_TASKS=0
DONE_TASKS=0
if grep -q "^### " "$PLAN_IN_WORKTREE" 2>/dev/null; then
  TOTAL_TASKS="$(grep -c "^### " "$PLAN_IN_WORKTREE" || true)"
  DONE_TASKS="$(grep -c "^### ✅" "$PLAN_IN_WORKTREE" || true)"
fi

if [ "$TOTAL_TASKS" -gt 0 ] && [ "$TOTAL_TASKS" -eq "$DONE_TASKS" ]; then
  echo "All $TOTAL_TASKS tasks already complete — skipping Ralph loop."
  echo "=== Phase 3: SKIPPED ==="
  echo ""
else
  if [ "$TOTAL_TASKS" -gt 0 ]; then
    echo "$DONE_TASKS/$TOTAL_TASKS tasks complete. Starting Ralph loop..."
  else
    echo "Starting Ralph loop..."
  fi
  echo ""

  RALPH_EXIT=0
  bash "$RALPH_SCRIPT" "$WORKTREE" "$PLAN_IN_WORKTREE" || RALPH_EXIT=$?

  if [ "$RALPH_EXIT" -ne 0 ]; then
    echo ""
    echo "ERROR: Ralph loop failed (exit code $RALPH_EXIT)." >&2
    echo "Progress is preserved — completed tasks are committed." >&2
    echo "Check the Ralph log at $WORKTREE/.ralph-log for details." >&2
    echo "Re-run this script to resume from the last completed task." >&2
    exit 1
  fi

  echo ""
  echo "=== Phase 3: Complete ==="
  echo ""
fi

# ============================================================
# Phase 3.5: Mockup fidelity loop
# ============================================================

echo "=== Phase 3.5: Mockup Fidelity ==="

# Check if already clean from a previous run
if [ -f "$WORKTREE/.mockup-clean" ]; then
  echo "Mockup fidelity already verified — skipping."
  echo "=== Phase 3.5: SKIPPED ==="
  echo ""
else
  # Quick check: does the plan reference mockups at all?
  HAS_MOCKUPS=false
  if grep -q '^\*\*Mockups:\*\*' "$PLAN_IN_WORKTREE" 2>/dev/null; then
    MOCKUPS_VALUE="$(grep '^\*\*Mockups:\*\*' "$PLAN_IN_WORKTREE" | head -1 | sed 's/\*\*Mockups:\*\* *//')"
    if [ -n "$MOCKUPS_VALUE" ] && [ "$MOCKUPS_VALUE" != "N/A" ] && [ "$MOCKUPS_VALUE" != "none" ]; then
      HAS_MOCKUPS=true
    fi
  fi

  if [ "$HAS_MOCKUPS" = false ]; then
    echo "No mockups referenced in plan — skipping fidelity check."
    touch "$WORKTREE/.mockup-clean"
    echo "=== Phase 3.5: SKIPPED (no mockups) ==="
    echo ""
  else
    echo "Mockups referenced in plan. Starting fidelity loop..."
    echo "Max iterations: $MAX_MOCKUP_ITERATIONS"
    echo ""

    MOCKUP_ITERATION=1

    while [ ! -f "$WORKTREE/.mockup-clean" ] && [ "$MOCKUP_ITERATION" -le "$MAX_MOCKUP_ITERATIONS" ]; do
      echo "--- Mockup fidelity iteration $MOCKUP_ITERATION ($(date '+%H:%M:%S')) ---"

      PROMPT_FILE="/tmp/.autopilot-mockup-$$"
      cat > "$PROMPT_FILE" <<PROMPT_EOF
$(cat "$MOCKUP_PROMPT")

Plan: $PLAN_IN_WORKTREE
Worktree: $WORKTREE
PROMPT_EOF

      cd "$WORKTREE"

      if ! run_claude_phase "Phase 3.5 (mockup fidelity, iteration $MOCKUP_ITERATION)" "$MOCKUP_TIMEOUT"; then
        echo "WARNING: Mockup fidelity iteration $MOCKUP_ITERATION failed." >&2
        echo "Continuing to verification phase — mockup deviations may persist." >&2
        rm -f "$PROMPT_FILE"
        PROMPT_FILE=""
        break
      fi
      rm -f "$PROMPT_FILE"
      PROMPT_FILE=""

      if [ -f "$WORKTREE/.mockup-clean" ]; then
        echo "--- Mockup fidelity: CLEAN ($(date '+%H:%M:%S')) ---"
      else
        echo "--- Mockup fidelity iteration $MOCKUP_ITERATION: fixes applied ($(date '+%H:%M:%S')) ---"
      fi
      echo ""

      MOCKUP_ITERATION=$((MOCKUP_ITERATION + 1))
    done

    if [ ! -f "$WORKTREE/.mockup-clean" ]; then
      echo "WARNING: Mockup fidelity not fully resolved after $MAX_MOCKUP_ITERATIONS iterations." >&2
      echo "Remaining deviations will be visible during review." >&2
    fi

    echo "=== Phase 3.5: Complete ==="
    echo ""
  fi
fi

# ============================================================
# Phase 4: Verify branch
# ============================================================

# Skip if we already have a successful status from a previous run
if [ -f "$STATUS" ]; then
  PREV_RESULT="$(grep '^status:' "$STATUS" 2>/dev/null | awk '{print $2}')"
  if [ "$PREV_RESULT" = "SUCCESS" ]; then
    echo "=== Phase 4: SKIPPED (previous verification passed) ==="
    echo ""
  else
    # Stale failure status — clear and re-run
    rm -f "$STATUS"
  fi
fi

if [ ! -f "$STATUS" ] || [ "$(grep '^status:' "$STATUS" 2>/dev/null | awk '{print $2}')" != "SUCCESS" ]; then
  echo "=== Phase 4: Verifying Branch ==="
  echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"

  # Clear any stale status file
  rm -f "$STATUS"

  PROMPT_FILE="/tmp/.autopilot-verify-$$"
  cat > "$PROMPT_FILE" <<PROMPT_EOF
$(cat "$VERIFY_PROMPT")

Branch: $BRANCH
Worktree: $WORKTREE
Plan: $PLAN_IN_WORKTREE
Main repo: $PROJECT
PROMPT_EOF

  cd "$WORKTREE"

  if ! run_claude_phase "Phase 4 (verification)" "$PHASE_TIMEOUT"; then
    echo "Verification phase failed to complete." >&2
    echo "The branch may still be in good shape — check manually." >&2
    exit 1
  fi
  rm -f "$PROMPT_FILE"
  PROMPT_FILE=""

  echo ""

  # Verify that Claude actually wrote a status file
  if [ ! -f "$STATUS" ]; then
    echo "WARNING: Verification completed but no status file was written." >&2
    echo "Claude may not have followed the VERIFY-BRANCH.md instructions." >&2
    echo "Check the log for verification output. Treating as inconclusive." >&2
    # Don't exit — fall through to the report with a warning
  fi

  echo "=== Phase 4: Complete ==="
  echo ""
fi

# ============================================================
# Report
# ============================================================

if [ -f "$STATUS" ]; then
  RESULT="$(grep '^status:' "$STATUS" 2>/dev/null | awk '{print $2}')"
  if [ "$RESULT" = "FAILED" ]; then
    echo ""
    echo "Autopilot finished, but verification failed."
    echo ""
    cat "$STATUS"
    echo ""
    echo "To fix this, either:"
    echo "  1. Re-run this script (completed phases will be skipped)"
    echo "  2. Fix manually in: $WORKTREE"
    echo ""
    echo "If mockup fixes caused the failure, also run:"
    echo "  rm $WORKTREE/.mockup-clean"
    echo "to re-enable the mockup fidelity loop on the next run."
    # Clean up status so re-run will re-verify
    rm -f "$STATUS"
    exit 1
  fi
fi

echo ""
echo "Done. All phases passed."
echo ""
echo "  Branch:   $BRANCH"
echo "  Worktree: $WORKTREE"
echo "  Plan:     $PLAN_IN_WORKTREE"
echo ""
echo "The branch is ready for review but hasn't been merged yet."
echo "To review and merge, open Claude in the project root and run the finishing skill:"
echo ""
echo "  cd $PROJECT"
echo "  claude"
echo "  /aligned:finishing-a-development-branch for $BRANCH at $WORKTREE"

# Clean up sentinel and status
rm -f "$SENTINEL"
rm -f "$STATUS"
