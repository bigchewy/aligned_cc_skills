# KB-075: stdbuf/tee log setup duplicated in autopilot.sh and run-ralph.sh

- **Type:** bug
- **Discovered during:** code-simplifier (autopilot script review)
- **Location:** `scripts/autopilot/autopilot.sh:109-115` and `scripts/autopilot/run-ralph.sh:66-73`
- **Observed:** The 6-line stdbuf → gstdbuf → tee fallback block is duplicated verbatim in both drivers. `lib/process.sh` is the shared library for both; the block belongs there. Two copies means a bug fix or a new fallback (e.g., a third buffering tool) must be applied twice and can drift.
- **Expected:** Extract into `lib/process.sh` as `setup_log <path>` and call from both drivers.
- **Why out of scope:** Pure refactor; safe to batch with other process.sh consolidations (KB-077).
- **Severity:** HIGH
- **Created:** 2026-05-16
