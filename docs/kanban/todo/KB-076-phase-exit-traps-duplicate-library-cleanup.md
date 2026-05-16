# KB-076: Phase EXIT traps reinvent `cleanup()` from lib/process.sh

- **Type:** bug
- **Discovered during:** code-simplifier (autopilot script review)
- **Location:** `scripts/autopilot/phases/plan.sh:40`, `scripts/autopilot/phases/mockup.sh:35`, `scripts/autopilot/phases/verify.sh:42`
- **Observed:** All three phases define an identical EXIT trap: `trap 'rm -f "$PROMPT_FILE" 2>/dev/null; stop_heartbeat; stop_watchdog; kill_claude' EXIT`. `lib/process.sh` already exports `cleanup()` that does this; `autopilot.sh` uses `trap cleanup EXIT`. The three phases are reinventing what the library provides — if `cleanup()` changes, the three phase traps silently diverge.
- **Expected:** Replace each phase's inline trap with `trap cleanup EXIT`, sourcing `lib/process.sh` consistently.
- **Why out of scope:** Pure refactor; verify `$PROMPT_FILE` cleanup behavior matches `cleanup()` first.
- **Severity:** HIGH
- **Created:** 2026-05-16
