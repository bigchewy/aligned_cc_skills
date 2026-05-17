# KB-114: Ralph loop aborts on 3 consecutive transient API errors

- **Type:** bug
- **Discovered during:** root-cause-analysis
- **Location:** `scripts/autopilot/run-ralph.sh:298-306`
- **Observed:** The ralph loop tracks `CONSECUTIVE_FAILURES` across iterations and aborts with `exit 1` after three consecutive non-zero `claude -p` exits, regardless of cause. During an Anthropic API outage (stream timeouts, 502/503, overload), three consecutive iterations can fail with transient errors, tripping the cap. The orchestrator (`autopilot.sh:298-306`) handles ralph failure without writing a halt sentinel, so re-runs work — but the loop ends earlier than necessary and the user-facing message ("3 consecutive claude failures. Aborting.") doesn't distinguish a real bug from a transient outage.
- **Expected:** When `is_transient_error "$LOG"` matches the iteration's failure, either (a) decrement/reset `CONSECUTIVE_FAILURES` and continue with a brief backoff, or (b) keep the cap but emit a clearer message naming the transient condition and recommend re-run. Pick (a) for short outages and (b) for longer ones — design choice to confirm with user.
- **Why out of scope:** Original report was specifically about the halt sentinel blocking re-runs. That blocking is fixed in `autopilot.sh:run_phase` (transient-aware skip of `write_halt phase_crashed`). Ralph already doesn't write a halt, so re-runs work — just less efficiently during outages. Expanding scope to add transient-aware retry inside ralph would change loop semantics (backoff strategy, retry budget, how to distinguish "API is down for hours" from "this task is wedged") in ways the user didn't authorize.
- **Severity:** MEDIUM
- **Created:** 2026-05-17
