# KB-078: Design-doc path resolution duplicated between autopilot.sh and plan.sh

- **Type:** bug
- **Discovered during:** code-simplifier (autopilot script review)
- **Location:** `scripts/autopilot/autopilot.sh:79-83`, `scripts/autopilot/phases/plan.sh:48-51`
- **Observed:** Both files re-implement the same relative/absolute path normalization (two-branch if/else, `cd-dirname/basename` idiom, `$PROJECT` anchor) for the design-doc / sentinel-design-doc input. The same decision is made twice with no shared helper. If the `cd` silently fails on a malformed path in one location, the other won't catch it; if one branch acquires a guard, the other won't.
- **Expected:** Extract into a `lib/paths.sh` helper (e.g., `resolve_path <maybe-relative> <project-root>`) and call from both sites.
- **Why out of scope:** Pure refactor; touches input handling so should be batched with deliberate test coverage.
- **Severity:** MEDIUM
- **Created:** 2026-05-16
