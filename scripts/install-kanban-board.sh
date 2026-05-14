#!/bin/bash
# Propagate scripts/generate-kanban-board.js + scripts/hooks/post-commit
# into every repo under ~/software/ that already has docs/kanban/.
#
# Idempotent — safe to re-run. Per-repo outcome is one of:
#   installed     — files added, hooksPath set, board generated
#   updated       — files refreshed (was already installed)
#   skipped       — not a git repo, or no docs/kanban/ directory
#   manual        — existing custom hooks would be bypassed by core.hooksPath;
#                   move them into scripts/hooks/ first, then re-run
#
# Does NOT commit anything. After running, each touched repo will have
# uncommitted changes you can stage and commit at your leisure.
#
# Usage:
#   bash scripts/install-kanban-board.sh --dry-run     # show plan only
#   bash scripts/install-kanban-board.sh               # apply across ~/software/*
#   bash scripts/install-kanban-board.sh /path1 /path2 # apply to specific repos

set -e

DRY_RUN=0
TARGETS=()
for arg in "$@"; do
  case "$arg" in
    --dry-run|-n) DRY_RUN=1 ;;
    --help|-h)
      sed -n '2,21p' "$0"
      exit 0
      ;;
    *) TARGETS+=("$arg") ;;
  esac
done

ALIGNED_REPO="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_SCRIPT="$ALIGNED_REPO/scripts/generate-kanban-board.cjs"
SOURCE_HOOK="$ALIGNED_REPO/scripts/hooks/post-commit"

if [ ! -f "$SOURCE_SCRIPT" ] || [ ! -f "$SOURCE_HOOK" ]; then
  echo "ERROR: source files missing in $ALIGNED_REPO/scripts/"
  echo "       Expected: $SOURCE_SCRIPT"
  echo "             and: $SOURCE_HOOK"
  exit 1
fi

if [ ${#TARGETS[@]} -eq 0 ]; then
  for d in "$HOME"/software/*/; do
    [ -d "$d" ] && TARGETS+=("${d%/}")
  done
fi

if [ ${#TARGETS[@]} -eq 0 ]; then
  echo "No targets. Pass repo paths or ensure ~/software/* exists."
  exit 0
fi

if [ "$DRY_RUN" -eq 1 ]; then
  echo "=== DRY RUN — no files modified ==="
fi
echo "Source files: $ALIGNED_REPO/scripts/{generate-kanban-board.cjs,hooks/post-commit}"
echo "Targets: ${#TARGETS[@]}"
echo ""

installed=0
updated=0
skipped=0
manual=0

for repo in "${TARGETS[@]}"; do
  name=$(basename "$repo")

  # Resolve to absolute paths for comparison
  repo_abs=$(cd "$repo" 2>/dev/null && pwd || echo "$repo")
  if [ "$repo_abs" = "$ALIGNED_REPO" ]; then
    printf "%-40s  skipped   (source repo)\n" "$name"
    skipped=$((skipped+1))
    continue
  fi

  if [ ! -d "$repo/.git" ]; then
    printf "%-40s  skipped   (not a git repo)\n" "$name"
    skipped=$((skipped+1))
    continue
  fi

  if [ ! -d "$repo/docs/kanban" ]; then
    printf "%-40s  skipped   (no docs/kanban/)\n" "$name"
    skipped=$((skipped+1))
    continue
  fi

  # If core.hooksPath isn't set yet and the repo has its own custom hooks,
  # we'd silently bypass them. Flag instead of stomping.
  current_hooks_path=$(git -C "$repo" config --get core.hooksPath 2>/dev/null || true)
  if [ -z "$current_hooks_path" ]; then
    custom_hooks=""
    if [ -d "$repo/.git/hooks" ]; then
      while IFS= read -r h; do
        [ -n "$custom_hooks" ] && custom_hooks="$custom_hooks $h" || custom_hooks="$h"
      done < <(find "$repo/.git/hooks" -maxdepth 1 -type f ! -name '*.sample' -exec basename {} \; 2>/dev/null)
    fi
    if [ -n "$custom_hooks" ]; then
      printf "%-40s  manual    (custom hooks present: %s)\n" "$name" "$custom_hooks"
      manual=$((manual+1))
      continue
    fi
  elif [ "$current_hooks_path" != "scripts/hooks" ]; then
    printf "%-40s  manual    (core.hooksPath=%s, would override)\n" "$name" "$current_hooks_path"
    manual=$((manual+1))
    continue
  fi

  was_installed=0
  [ -f "$repo/scripts/generate-kanban-board.cjs" ] && was_installed=1
  # Detect a stale .js copy from an earlier install (CommonJS extension fix)
  has_stale_js=0
  [ -f "$repo/scripts/generate-kanban-board.js" ] && has_stale_js=1

  if [ "$DRY_RUN" -eq 1 ]; then
    label="would install"
    [ "$was_installed" -eq 1 ] && label="would update "
    printf "%-40s  %s (\n" "$name" "$label"
    [ "$was_installed" -eq 0 ] && echo "                                            + scripts/generate-kanban-board.cjs"
    [ "$was_installed" -eq 0 ] && echo "                                            + scripts/hooks/post-commit"
    [ "$was_installed" -eq 1 ] && echo "                                            ~ refresh both files"
    [ "$has_stale_js" -eq 1 ] && echo "                                            - scripts/generate-kanban-board.js (stale, will be removed)"
    [ "$current_hooks_path" != "scripts/hooks" ] && echo "                                            + git config core.hooksPath scripts/hooks"
    if [ -f "$repo/.gitignore" ] && ! grep -qF "docs/kanban/board.html" "$repo/.gitignore" 2>/dev/null; then
      echo "                                            + .gitignore: docs/kanban/board.html"
    fi
    echo "                                          )"
    if [ "$was_installed" -eq 1 ]; then updated=$((updated+1)); else installed=$((installed+1)); fi
    continue
  fi

  # Apply
  mkdir -p "$repo/scripts/hooks"
  cp "$SOURCE_SCRIPT" "$repo/scripts/generate-kanban-board.cjs"
  cp "$SOURCE_HOOK" "$repo/scripts/hooks/post-commit"
  chmod +x "$repo/scripts/hooks/post-commit"
  # Remove stale .js if a prior install left one behind
  [ "$has_stale_js" -eq 1 ] && rm -f "$repo/scripts/generate-kanban-board.js"

  if [ "$current_hooks_path" != "scripts/hooks" ]; then
    git -C "$repo" config core.hooksPath scripts/hooks
  fi

  if [ -f "$repo/.gitignore" ] && ! grep -qF "docs/kanban/board.html" "$repo/.gitignore" 2>/dev/null; then
    echo "docs/kanban/board.html" >> "$repo/.gitignore"
  fi

  if command -v node >/dev/null 2>&1; then
    node "$repo/scripts/generate-kanban-board.cjs" >/dev/null 2>&1 || \
      echo "                                            (board generation failed; run manually to see error)"
  fi

  if [ "$was_installed" -eq 1 ]; then
    printf "%-40s  updated\n" "$name"
    updated=$((updated+1))
  else
    printf "%-40s  installed\n" "$name"
    installed=$((installed+1))
  fi
done

echo ""
echo "Summary:"
printf "  installed:  %d\n" "$installed"
printf "  updated:    %d\n" "$updated"
printf "  skipped:    %d  (not a git repo or no docs/kanban/)\n" "$skipped"
printf "  manual:     %d  (existing hooks would be bypassed)\n" "$manual"

if [ "$DRY_RUN" -eq 1 ]; then
  echo ""
  echo "This was a dry run. Re-run without --dry-run to apply."
fi
