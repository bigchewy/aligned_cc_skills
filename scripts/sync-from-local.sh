#!/bin/bash
# Sync skills from ~/.claude/skills/ to the aligned plugin repo.
# Applies generalization transforms from transforms.txt.
#
# Usage: cd ~/software/aligned_cc_skills && ./scripts/sync-from-local.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
LOCAL_SKILLS="$HOME/.claude/skills"
TRANSFORMS="$SCRIPT_DIR/transforms.txt"
VA_REPO="$HOME/software/va-web-app"

# Cross-platform sed in-place (macOS requires '' arg, Linux does not)
sedi() {
  if [[ "$OSTYPE" == darwin* ]]; then
    sed -i '' "$@"
  else
    sed -i "$@"
  fi
}

# Skills to sync (excludes kickstart, eval-audit, design-principles — authored directly in plugin)
SYNC_SKILLS=(
  brainstorming
  writing-plans
  executing-plans
  finishing-a-development-branch
  test-driven-development
  verification-before-completion
  systematic-debugging
  eval-failure-triage
  using-git-worktrees
  mockup-generator
  autopilot
)

echo "=== Aligned Plugin Sync ==="
echo "Source: $LOCAL_SKILLS"
echo "Target: $PLUGIN_ROOT/skills/"
echo ""

# Sync each skill directory
for skill in "${SYNC_SKILLS[@]}"; do
  src="$LOCAL_SKILLS/$skill"
  dst="$PLUGIN_ROOT/skills/$skill"

  if [ ! -d "$src" ]; then
    echo "SKIP: $skill (not found at $src)"
    continue
  fi

  echo "SYNC: $skill"

  # Remove old contents (preserve directory)
  rm -rf "$dst"
  mkdir -p "$dst"

  # Copy all files (preserving subdirectory structure)
  cp -R "$src"/* "$dst"/

  # Remove development artifacts that shouldn't ship
  rm -f "$dst/CREATION-LOG.md"
  rm -f "$dst/test-academic.md"
  rm -f "$dst/test-pressure-"*.md

  # Apply transforms to all .md files
  find "$dst" -name "*.md" -type f | while read -r file; do
    while IFS='|' read -r old new; do
      # Skip empty lines and comments
      [ -z "$old" ] && continue
      [[ "$old" == \#* ]] && continue
      # Use | as sed delimiter since paths contain /
      sedi "s|$old|$new|g" "$file"
    done < "$TRANSFORMS"
  done

  # Handle the Vercel catalog rename for finishing-a-development-branch
  if [ "$skill" = "finishing-a-development-branch" ]; then
    if [ -f "$dst/references/vercel-pitfall-catalog.md" ]; then
      mv "$dst/references/vercel-pitfall-catalog.md" "$dst/references/deployment-pitfall-catalog.md"
    fi
  fi
done

# Sync Steve Jobs advisor
echo ""
echo "SYNC: Steve Jobs advisor"
cp "$VA_REPO/src/lib/advisors/prompts/steve-jobs.md" "$PLUGIN_ROOT/agents/steve-jobs.md"

echo ""
echo "=== Sync complete ==="
echo "Review changes with: git diff"
echo "Commit with: git add -A && git commit -m 'sync: update skills from local'"
