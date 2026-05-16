# KB-077: STATUS file parsing duplicated across three call sites

- **Type:** bug
- **Discovered during:** code-simplifier (autopilot script review)
- **Location:** `docs/ralph_loops/autopilot.sh:332`, `docs/ralph_loops/phases/verify.sh:47`, `docs/ralph_loops/phases/verify.sh:84`
- **Observed:** The pattern `grep '^status:' "$STATUS" 2>/dev/null | awk '{print $2}'` appears at all three sites — three places parsing the same structured file format with the same brittle two-process pipeline. A format change to the status file requires hunting all three sites.
- **Expected:** Add `read_status()` to `lib/halt.sh` (which already owns the halt format) or a new `lib/status.sh`. Replace the three grep/awk pipelines with a function call.
- **Why out of scope:** Pure refactor; coordinate with KB-074 since both touch `lib/halt.sh`.
- **Severity:** MEDIUM
- **Created:** 2026-05-16
