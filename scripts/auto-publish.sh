#!/bin/bash
# Watch ~/.claude/skills/ for changes and auto-publish.
# Debounces rapid changes (waits 5s after last change before publishing).
#
# Prerequisites:
#   macOS:  brew install fswatch
#   Linux:  sudo apt install inotify-tools
#
# Usage:
#   ./scripts/auto-publish.sh          # watch and auto-publish
#   ./scripts/auto-publish.sh --once   # sync once on next change, then exit
#
# To run on login (macOS):
#   Add to ~/.zshrc or use a LaunchAgent:
#   nohup ~/software/aligned_cc_skills/scripts/auto-publish.sh &>/tmp/aligned-auto-publish.log &
#
# To run on login (Linux systemd):
#   See auto-publish.service in this directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
WATCH_DIR="$HOME/.claude/skills"
DEBOUNCE_SECS=5
ONCE=false

[[ "${1:-}" == "--once" ]] && ONCE=true

if [ ! -d "$WATCH_DIR" ]; then
  echo "ERROR: $WATCH_DIR does not exist."
  exit 1
fi

echo "=== Aligned Auto-Publisher ==="
echo "Watching: $WATCH_DIR"
echo "Debounce: ${DEBOUNCE_SECS}s"
echo "Press Ctrl-C to stop."
echo ""

do_publish() {
  echo ""
  echo "[$(date '+%H:%M:%S')] Change detected. Publishing..."
  cd "$PLUGIN_ROOT"
  if "$SCRIPT_DIR/publish.sh"; then
    echo "[$(date '+%H:%M:%S')] Published."
  else
    echo "[$(date '+%H:%M:%S')] Publish failed (see output above)."
  fi
  echo ""
  echo "Watching for changes..."
}

# macOS: use fswatch
if command -v fswatch &>/dev/null; then
  if $ONCE; then
    fswatch -1 --event=Updated --event=Created --event=Removed \
      --include='\.md$' --exclude='.*' "$WATCH_DIR"
    do_publish
  else
    # fswatch with latency acts as a debounce
    fswatch --latency="$DEBOUNCE_SECS" \
      --event=Updated --event=Created --event=Removed \
      --include='\.md$' --exclude='.*' "$WATCH_DIR" | while read -r _; do
      do_publish
    done
  fi

# Linux: use inotifywait
elif command -v inotifywait &>/dev/null; then
  while true; do
    inotifywait -r -q -e modify,create,delete \
      --include='\.md$' "$WATCH_DIR"

    # Debounce: wait for rapid changes to settle
    sleep "$DEBOUNCE_SECS"

    # Drain any additional events that queued up during debounce
    while inotifywait -r -q -t 1 -e modify,create,delete \
      --include='\.md$' "$WATCH_DIR" 2>/dev/null; do
      sleep 1
    done

    do_publish

    $ONCE && exit 0
  done

else
  echo "ERROR: No file watcher found."
  echo ""
  echo "Install one:"
  echo "  macOS:  brew install fswatch"
  echo "  Linux:  sudo apt install inotify-tools"
  exit 1
fi
