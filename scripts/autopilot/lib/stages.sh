#!/usr/bin/env bash
# lib/stages.sh — single source of truth for pipeline stage reporting.
# Usage: report_stage <phase-num> <total> <phase-name> <status>
#   status: running | passed | halted | skipped | failed

if [ -n "${_AUTOPILOT_STAGES_SH_LOADED:-}" ]; then return 0; fi
_AUTOPILOT_STAGES_SH_LOADED=1

set -u

report_stage() {
  local phase="$1"
  local total="$2"
  local name="$3"
  local status="$4"

  local glyph
  case "$status" in
    running)  glyph="▶" ;;
    passed)   glyph="✓" ;;
    halted)   glyph="✗" ;;
    skipped)  glyph="—" ;;
    failed)   glyph="✗" ;;
    *)        glyph="?" ;;
  esac

  printf "%s phase %s of %s: %-12s | %s\n" "$glyph" "$phase" "$total" "$name" "$status"
}
