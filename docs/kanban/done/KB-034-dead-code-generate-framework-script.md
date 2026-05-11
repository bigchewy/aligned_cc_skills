# KB-034: Dead code in generate-framework-registry.mjs (unused OUTPUT_PATH, no-op --dry-run)

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `scripts/generate-framework-registry.mjs:13,274`
- **Observed:** Line 13 defines `OUTPUT_PATH` but it is never referenced — only `DRAFT_PATH` is used. Line 274 reads `dryRun ? DRAFT_PATH : DRAFT_PATH` — both branches resolve to the same path, so `--dry-run` silently overwrites the draft with no distinction from a normal run. The flag is documented in the file header but has no effect on the full-run code path.
- **Expected:** Either remove `OUTPUT_PATH` or use it as the non-dry-run target. Fix the ternary so `--dry-run` has a meaningful effect or remove the flag.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task
- **Severity:** HIGH
- **Created:** 2026-04-13
- **Resolved:** 2026-05-11 — Removed unused `OUTPUT_PATH` const, removed no-op `--dry-run` flag, renamed pass1-only output to `PASS1_DRAFT_PATH`, updated header comment.
