# KB-055: check_mcp_tool duplicates upward directory walk

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `docs/ralph_loops/lib/manifest.sh:88-124`
- **Observed:** `check_mcp_tool` runs the same `while [ "$dir" != "/" ]` upward-walk idiom twice — once collecting `.mcp.json` paths (lines 88-96) and again collecting `.claude/settings.local.json` paths (lines 118-124). The only difference is the filename searched and the home-fallback list appended at the end. Any change to the walk logic (stop at a git root, add a fallback location, change the parent-of-/ termination) must be made in two places.
- **Expected:** Extract a helper, e.g., `walk_upward_collect <start-dir> <relative-filename>`, that echoes one path per line. Both callers reduce to a single `mapfile -t mcp_files < <(walk_upward_collect "$cwd" .mcp.json)` plus the home-fallback append. Reduces 14 lines to ~8.
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task.
- **Severity:** MEDIUM
- **Created:** 2026-04-30
