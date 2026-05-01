# KB-053: lib/halt.sh write_halt leaves tmp file on format_halt failure

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code-reviewer)
- **Location:** `docs/ralph_loops/lib/halt.sh:19-46`
- **Observed:** `write_halt` redirects all formatted output into `tmp="${target}.tmp.$$"` and only `mv`s to the target after the redirection completes. If the inner `format_halt` call fails (or any subshell command in the block aborts), the `mv` is never reached and `${target}.tmp.<pid>` is left orphaned next to the halt path. Realistic failure modes are narrow (`sed` unavailable, disk full mid-write) but the orphan accumulates across failed runs.
- **Expected:** Add a trap in `write_halt` to remove the tmp file if the function exits without performing the `mv`, e.g., `trap 'rm -f "$tmp"' RETURN` (with awareness that `RETURN` traps require a function-scope trap and `set -E`-style propagation considerations) — or refactor to write directly and accept the non-atomic risk for this small file (the original atomic-mv pattern protects readers from a partial halt; the trade-off may be worth revisiting).
- **Why out of scope:** Cosmetic — the orphaned tmp file does not affect halt detection or autopilot correctness.
- **Severity:** LOW
- **Created:** 2026-04-30
