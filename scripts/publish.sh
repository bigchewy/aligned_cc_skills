#!/bin/bash
# One-command publish: sync from local skills, commit changes, push.
#
# Usage:
#   ./scripts/publish.sh              # sync + commit + push
#   ./scripts/publish.sh --dry-run    # sync only, show diff, don't commit/push
#   ./scripts/publish.sh -m "msg"     # custom commit message
#
# Tip: add a shell alias for zero-friction publishing:
#   alias aligned-publish="cd ~/software/aligned_cc_skills && ./scripts/publish.sh"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"

DRY_RUN=false
CUSTOM_MSG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    -m)        CUSTOM_MSG="$2"; shift 2 ;;
    *)         echo "Unknown arg: $1"; exit 1 ;;
  esac
done

cd "$PLUGIN_ROOT"

# Step 1: Sync from local
echo "=== Step 1: Sync from local ==="
"$SCRIPT_DIR/sync-from-local.sh"

# Step 2: Check for changes
echo ""
echo "=== Step 2: Checking for changes ==="

if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  echo "No changes detected. Nothing to publish."
  exit 0
fi

# Build a summary of what changed
CHANGED_SKILLS=()
for file in $(git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard); do
  if [[ "$file" == skills/* ]]; then
    skill_name=$(echo "$file" | cut -d/ -f2)
    # Deduplicate
    if [[ ! " ${CHANGED_SKILLS[*]:-} " =~ " $skill_name " ]]; then
      CHANGED_SKILLS+=("$skill_name")
    fi
  fi
done

echo "Changed skills: ${CHANGED_SKILLS[*]:-none}"
echo ""
git diff --stat
echo ""

if $DRY_RUN; then
  echo "=== Dry run complete. Run without --dry-run to commit and push. ==="
  exit 0
fi

# Step 3: Commit
echo "=== Step 3: Committing ==="

git add -A

if [ -n "$CUSTOM_MSG" ]; then
  COMMIT_MSG="$CUSTOM_MSG"
elif [ ${#CHANGED_SKILLS[@]} -eq 0 ]; then
  COMMIT_MSG="sync: update from local"
elif [ ${#CHANGED_SKILLS[@]} -le 3 ]; then
  COMMIT_MSG="sync: update ${CHANGED_SKILLS[*]}"
else
  COMMIT_MSG="sync: update ${#CHANGED_SKILLS[@]} skills (${CHANGED_SKILLS[*]:0:3} ...)"
fi

git commit -m "$COMMIT_MSG"

# Step 4: Push with retry
echo ""
echo "=== Step 4: Pushing ==="

BRANCH=$(git rev-parse --abbrev-ref HEAD)
MAX_RETRIES=4
DELAY=2

for attempt in $(seq 1 $MAX_RETRIES); do
  if git push -u origin "$BRANCH" 2>&1; then
    echo ""
    echo "=== Published successfully ==="
    exit 0
  fi

  if [ "$attempt" -lt "$MAX_RETRIES" ]; then
    echo "Push failed (attempt $attempt/$MAX_RETRIES). Retrying in ${DELAY}s..."
    sleep $DELAY
    DELAY=$((DELAY * 2))
  fi
done

echo "ERROR: Push failed after $MAX_RETRIES attempts."
exit 1
