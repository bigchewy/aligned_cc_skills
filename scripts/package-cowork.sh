#!/usr/bin/env bash
# Package the aligned plugin as a .zip for upload to Claude Desktop Cowork.
# Frameworks are excluded — copy them into your project's frameworks/ directory.
#
# Usage: bash scripts/package-cowork.sh
#
# Output: aligned-cowork.zip in the repo root (git-ignored).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="$REPO_ROOT/aligned-cowork.zip"

# Remove previous build
rm -f "$OUTPUT"

cd "$REPO_ROOT"

zip -r "$OUTPUT" \
  .claude-plugin \
  skills \
  agents \
  advisors \
  hooks \
  CLAUDE.md \
  README.md \
  LICENSE \
  -x '*.DS_Store' \
  -x '*/.DS_Store'

COUNT=$(zipinfo -1 "$OUTPUT" | wc -l | tr -d ' ')
SIZE=$(du -h "$OUTPUT" | cut -f1)
echo ""
echo "Packaged: $OUTPUT ($SIZE, $COUNT files)"
echo ""
echo "To include frameworks in your demo project:"
echo "  mkdir -p /path/to/demo-project/frameworks"
echo "  cp -R $REPO_ROOT/frameworks/ /path/to/demo-project/frameworks/"
echo ""
echo "Upload via: Cowork > Customize > Browse plugins > Upload"
