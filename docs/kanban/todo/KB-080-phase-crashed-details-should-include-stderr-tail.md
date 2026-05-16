# KB-080: `phase_crashed` sentinel `details:` only carries exit code, not stderr tail

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code-reviewer Suggestion 2 on simplify-autopilot-halt-merge-handling)
- **Location:** `docs/ralph_loops/autopilot.sh:156` (the `write_halt phase_crashed` callsite) and `docs/ralph_loops/lib/halt.sh:110-118` (the `phase_crashed` heredoc)
- **Observed:** The `phase_crashed` fix-instructions promise "Read the log for the last 10 lines of stderr (in the details: field of this sentinel, if captured)." The "if captured" qualifier is honest, but in practice the callsite at `autopilot.sh:156` writes only `"Phase exited with code $exit_code"` as details — never a stderr tail. A user hitting a merge conflict under the new worktree.sh behavior (exits 1, autopilot writes `phase_crashed`) reads the sentinel and finds only `details: Phase exited with code 1` — no hint that the conflict files are listed in the log.
- **Expected:** Either (a) capture the last 10 lines of `.autopilot-log` into the details field at `autopilot.sh:156` before calling write_halt, or (b) rewrite the `phase_crashed` heredoc to drop the "in the details: field" parenthetical and point users to the log path directly. Option (b) is simpler; option (a) is more user-friendly.
- **Why out of scope:** Surfaces a long-standing inaccuracy in the heredoc rather than a regression from the simplify-halt branch. Worth fixing alongside other autopilot UX improvements (KB-075/076/077/078 cluster).
- **Severity:** LOW
- **Created:** 2026-05-16
