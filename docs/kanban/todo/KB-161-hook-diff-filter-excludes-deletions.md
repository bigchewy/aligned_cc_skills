# KB-161: Version-bump hook's diff-filter excludes deletions

- **Type:** bug
- **Discovered during:** subagent-driven-development (final whole-branch review)
- **Location:** `scripts/hooks/pre-commit:18`
- **Observed:** The hook's trigger check uses `git diff --cached --name-only --diff-filter=ACMR` against shipped-content paths, which excludes pure deletions (`D`). A commit that only deletes shipped files (no other Added/Copied/Modified/Renamed file under those paths in the same commit) stages no version bump and silently never reaches the Claude Code plugin cache.
- **Expected:** Add `D` to the diff-filter so deletion-only commits touching shipped-content paths also trigger the version bump.
- **Why out of scope:** Found during a final branch review of unrelated work; changing the hook itself belongs on its own reviewed branch, not folded into this one.
- **Severity:** LOW
- **Created:** 2026-08-31
