#!/bin/bash
# Auto-commit aligned_cc_skills changes.
# Runs via launchd every 10 minutes.

REPO_DIR="/Users/ericpage/software/aligned_cc_skills"
cd "$REPO_DIR" || exit 1

# Check if there are any changes (staged, unstaged, or untracked)
if git diff --quiet HEAD 2>/dev/null \
   && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    exit 0
fi

# Stage everything tracked + new files
git add -A

# Bail if staging produced nothing (e.g. only ignored files changed)
if git diff --cached --quiet; then
    exit 0
fi

# Build commit message from changed files
CHANGED=$(git diff --cached --name-only)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

git commit -m "Auto-snapshot: $TIMESTAMP

Changed:
$CHANGED"

# Push to origin (silent fail is fine — network may be unavailable)
git push origin main 2>/dev/null

echo "[$TIMESTAMP] Committed and pushed." >> "$REPO_DIR/scripts/autocommit.log"
