# KB-160: Completed autopilot runs never exit after their terminal closes

- **Type:** bug
- **Discovered during:** root-cause-analysis (2026-06-12 sentinel-clobber incident)
- **Location:** `scripts/autopilot/autopilot.sh:240` (`trap '' HUP`), `scripts/autopilot/autopilot.sh:123-129` (`exec > >(tee -a "$LOG")`)
- **Observed:** On 2026-06-12, PID 26932 (the opco-rollup-system run) was still alive hours after printing its final "Done. All phases passed." report, with its `tee` child (PID 26934) holding `.autopilot-log` open. A second lingering pair existed for an interrupted run. Both orphans tee into the SAME shared `.autopilot-log`, so a later run's log gets interleaved writes from dead runs. Suspected mechanism (UNCERTAIN — needs verification): `trap '' HUP` keeps the script alive after its iTerm tab closes, and the `tee` process substitution then blocks writing buffered output to the dead pty, so the parent bash never finishes waiting on it at exit. Manual `kill` of both PIDs was required.
- **Expected:** A completed (or interrupted) run's process tree exits on its own. Possible directions once the mechanism is verified: redirect the procsub's terminal-facing output defensively, `trap '' PIPE` + non-blocking final flush, or explicitly close/`exec >&-` the procsub before the final exit.
- **Why out of scope:** The blocking mechanism is unverified — fixing blind risks breaking live log streaming for attended runs. Needs a reproduction (run autopilot in a tab, close the tab, observe) before choosing a fix layer.
- **Severity:** LOW
- **Created:** 2026-06-12
