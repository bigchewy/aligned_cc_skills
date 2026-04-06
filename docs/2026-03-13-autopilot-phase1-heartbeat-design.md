# Design: Phase 1 Heartbeat for autopilot.sh

**Date:** 2026-03-13
**Scope:** `docs/ralph_loops/autopilot.sh` — Phase 1 only

## Problem

The "Writing Plans" phase of autopilot.sh runs `claude -p` with no activity indicator. The only output is the "Started" timestamp and then silence until completion or timeout (default 45 min). This makes it unclear whether the phase is actively working or has errored out.

## Solution

Add a heartbeat to Phase 1 that prints elapsed time and timeout countdown every 30 seconds. Reuse the same background-subprocess pattern already proven in `run-ralph.sh`.

### Output format

```
=== Phase 1: Writing Implementation Plan ===
Started: 2026-03-13 14:22:07
  [heartbeat] plan writing — 30s elapsed (44m30s remaining)
  [heartbeat] plan writing — 60s elapsed (44m00s remaining)
  [heartbeat] plan writing — 90s elapsed (43m30s remaining)
  ...
Plan file: docs/plans/2026-03-13-foo-plan.md
=== Phase 1: Complete (14:45:32) ===
```

### Implementation

1. Add `start_heartbeat()` and `stop_heartbeat()` functions to `autopilot.sh`, adapted from `run-ralph.sh`'s existing heartbeat. The key difference: include timeout countdown using `PHASE_TIMEOUT`.

2. Call `start_heartbeat` before `run_claude_phase` in the Phase 1 block, and `stop_heartbeat` after it returns.

3. Add `stop_heartbeat` to the `cleanup()` trap so interrupted runs don't leave orphan processes.

### What does NOT change

- Phases 3.5 and 4 remain silent (user confirmed these are fast enough)
- No new env vars — heartbeat interval is hardcoded at 30s
- No timeout changes — 45-min default is sufficient (observed max ~25-30 min)
- `run-ralph.sh` is untouched
