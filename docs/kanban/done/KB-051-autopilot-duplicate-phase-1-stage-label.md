# KB-051: Duplicate "phase 1 of 6" label for two preflight invocations

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code-reviewer)
- **Location:** `docs/ralph_loops/autopilot.sh:192,218`
- **Observed:** `autopilot.sh` calls `run_phase 1 6 preflight` twice — once before plan generation (line 192, when the plan does not yet exist) and once after (line 218, when the manifest can actually be validated). Both calls report themselves as "phase 1 of 6" via the stage reporter, so the user sees `▶ phase 1 of 6: preflight | running` printed twice on every run. The first invocation is a no-op when `PLAN_FILE` is empty (preflight exits 0 early), but it still prints. Pipeline correctness is unaffected.
- **Expected:** Either suppress the `report_stage` call for the first preflight invocation (since it's a guard, not a real phase), or label it differently (e.g., "phase 0/6: preflight (early)") to make the duplication visible and intentional rather than confusing.
- **Why out of scope:** UX issue, non-blocking; surfaced in code review post-implementation.
- **Severity:** LOW
- **Created:** 2026-04-30
