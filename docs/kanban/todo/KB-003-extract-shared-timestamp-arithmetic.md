# KB-003: Extract shared timestamp arithmetic out of `is_due` and `days_since`

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `hooks/check-cron-results.sh:36-54`
- **Observed:** `is_due()` (lines 36-44) and `days_since()` (lines 46-54) both open the same timestamp file and compute `(now - last) / 86400`. Every dispatch site calls `is_due` followed immediately by `days_since` on the same file, reading it twice. The computation is duplicated and every invocation pair does redundant file I/O.
- **Expected:** Extract the shared arithmetic into a single function that returns both the days count and the due/not-due verdict, eliminating the duplicate file reads.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** MEDIUM
- **Created:** 2026-02-17
