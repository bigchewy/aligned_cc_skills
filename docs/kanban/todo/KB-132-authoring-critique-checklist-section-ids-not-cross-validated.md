# KB-132: authoring-critique-checklist.md section IDs not cross-validated against authoring.md Phase 3 dispatch table

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code review of feature/framework-runner-refactor)
- **Location:** `skills/brainstorming/modes/authoring.md:178-181` (Phase 3 dispatch table) and `skills/brainstorming/authoring-critique-checklist.md` (section headers)
- **Observed:** Phase 3's dispatch table passes section ID lists like `["universal", "content"]`, `["universal", "decision"]` etc. to the critique orchestrator. These IDs are string literals pointing at headers in `authoring-critique-checklist.md`. If a checklist section header is renamed, the dispatch table silently passes stale IDs. `test_brainstorming_files.py` (L38-53) asserts checklist heading/section names exist, but does not cross-assert that the IDs in authoring.md's Phase 3 table match the checklist's actual section headers.
- **Expected:** Add a test that parses the Phase 3 dispatch table's section IDs out of `authoring.md` and asserts each ID is a header (or anchor) in `authoring-critique-checklist.md`. Mirrors the trigger-map/scenario validation pattern already in `test_trigger_map_scenarios.py`.
- **Why out of scope:** No mismatch observed yet; this is a silent-drift guard for future edits.
- **Severity:** MEDIUM
- **Created:** 2026-05-17
