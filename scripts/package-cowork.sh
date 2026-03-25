#!/usr/bin/env bash
# Package the aligned plugin as a .zip for upload to Claude Desktop Cowork.
# Usage: bash scripts/package-cowork.sh
#
# Output: aligned-plugin.zip in the repo root (git-ignored).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="$REPO_ROOT/aligned-plugin.zip"

# Remove previous build
rm -f "$OUTPUT"

cd "$REPO_ROOT"

zip -r "$OUTPUT" \
  .claude-plugin \
  skills \
  agents \
  advisors \
  frameworks \
  hooks \
  CLAUDE.md \
  README.md \
  LICENSE \
  -x '*.DS_Store' \
  -x '*/.DS_Store'

SIZE=$(du -h "$OUTPUT" | cut -f1)
echo ""
echo "Packaged: $OUTPUT ($SIZE)"
echo "Upload via: Cowork > Customize > Browse plugins > Upload"
