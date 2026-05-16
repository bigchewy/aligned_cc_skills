# KB-068: autopilot sentinel can disappear between halt and resume, defeating phase-2 skip

- **Type:** bug
- **Discovered during:** root-cause-analysis (Planted positioning-defense autopilot resume incident, 2026-05-14)
- **Location:**
  - `scripts/autopilot/autopilot.sh:103` (SENTINEL declaration)
  - `scripts/autopilot/autopilot.sh:367` (success-exit deletion)
  - `scripts/autopilot/phases/plan.sh:44-65` (sentinel-check + conditional deletion)
- **Observed:** When autopilot halts at the verify phase (exit-code-2 from `run_phase`, autopilot.sh:144-149) and is later re-run, phase 2 (plan-write) is supposed to skip via the sentinel mechanism: `plan.sh:44-56` reads `.autopilot-plan-path`, compares its first line (design-doc path) to the current invocation's `$DESIGN_DOC`, and if they match AND the plan file referenced on line 2 still exists, exits with code 3 (skip). The skip should leave the plan untouched.
  
  In the Planted incident on 2026-05-14, this skip did not fire on resume. Autopilot phase 2 began rewriting the plan from scratch, which would have clobbered an executed plan (1,779 lines, 21 tasks) for which 17+ task commits had already been made on the feature branch. The user noticed within ~90 seconds and killed the process before the new plan was written, so no work was lost — but the failure mode is a data-loss vector if the user steps away during a resume.
  
  Direct cause: the sentinel file `$PROJECT/.autopilot-plan-path` was absent at resume time. With no sentinel, `plan.sh` falls through to a fresh plan write (`plan.sh:67-110`).
  
  Why the sentinel was absent: investigation could not determine which of the two deletion sites fired. The script has exactly two `rm -f "$SENTINEL"` paths:
  
  1. **`plan.sh:63`** — fires from the sentinel-validation block when (a) the stored design doc does not match the current invocation's design doc, OR (b) the stored plan file no longer exists. Both sub-cases are silenced with bare `rm -f`; the log only distinguishes them via the preceding echo (lines 58-62), not via any structured marker.
  
  2. **`autopilot.sh:367`** — fires at end of script on the success path (all 6 phases passed). On a verify-halt, `run_phase` calls `exit 0` at line 149 *before* reaching this line, so this deletion should NOT fire during a halt. But the post-halt `.autopilot-log` shows the script exited at 19:06 and the sentinel was already absent by the 20:39 re-run, suggesting one of three things happened: (i) the success-path `rm -f` fired despite the halt path being taken; (ii) a previous concurrent autopilot run with a different design doc triggered `plan.sh:63` and cleaned it up; (iii) some user-side action removed it.
  
  The forensic problem: neither deletion site logs *which* sentinel was removed, *what was in it*, or *which code path* triggered the removal. With no logs and no audit trail, root-causing this requires reasoning from the absence of evidence, which is what made the Planted incident investigation inconclusive.

- **Expected:**
  
  1. **Make sentinel deletion observable.** Both `rm -f "$SENTINEL"` sites should log the sentinel's contents and which code path is removing it, e.g.:
     ```bash
     echo "[sentinel] removing $SENTINEL (reason: design-doc-mismatch, was: $SENTINEL_CONTENT)" >&2
     rm -f "$SENTINEL"
     ```
     Without this, post-incident forensics are impossible.
  
  2. **Verify exit-path behavior matches the comment.** `autopilot.sh:366` ("Clean up sentinel and status") is reached only via fall-through from the success path. Confirm there's no path (signal, trap, subshell) where this line runs after a verify-halt. If there's any ambiguity, gate it explicitly: `[ "$ALL_PASSED" = "true" ] && rm -f "$SENTINEL"`.
  
  3. **Make the sentinel resilient to concurrent autopilot runs.** Two autopilot instances against different design docs in the same `$PROJECT` will collide on `$PROJECT/.autopilot-plan-path`. Each will see the other's sentinel as a mismatch and delete it. Either (a) namespace the sentinel by design-doc hash (`$PROJECT/.autopilot-plan-path-${DESIGN_DOC_HASH}`), or (b) refuse to run if a sentinel exists for a *different* design doc until the user resolves the conflict. The current "silently nuke the other run's sentinel" behavior is hostile.
  
  4. **Consider an integrity check before phase-2 fresh-write.** If `plan.sh` is about to write a fresh plan but a worktree already exists for the derived branch name (and that worktree has commits ahead of main), refuse and prompt the user. Today's safeguard relies entirely on the sentinel; when the sentinel is gone, there's no second line of defense against clobbering executed work.

- **Why out of scope:** This was surfaced during a Planted-repo investigation. Fixing it requires modifying the autopilot script itself, which lives here (`aligned_cc_skills`). The Planted incident was resolved by killing the autopilot process before the plan was rewritten; the autopilot itself was never the work-of-record for that session's actual feature work. So no urgency on Planted's side. But the failure mode is dangerous enough that someone WILL lose work to this eventually if it isn't fixed.

- **Severity:** HIGH — silent data-loss vector. The user must catch the clobber within the plan-phase window (typically 60-120 seconds before claude begins streaming changes to the plan file) or risk losing an executed plan. The script gives no warning that the resume-skip failed; it just starts writing.

- **Created:** 2026-05-15
