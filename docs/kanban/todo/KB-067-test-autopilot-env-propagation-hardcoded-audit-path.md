# KB-067: Hardcoded audit-file path creates fragile skip guard in test

- **Type:** simplification
- **Discovered during:** finishing-a-development-branch (code-simplifier)
- **Location:** `e2e/tests/test_autopilot_model_env_propagation.py:149-153`
- **Observed:** `test_plan_phase_invokes_claude_with_bare_flag` reads a specific plan file by hardcoded date-stamped path (`2026-05-14-autopilot-model-downshift-audit.md`) to decide whether to skip. Once that file is archived to `docs/plans/completed/` (which this skill does on merge) or removed entirely, the condition silently evaluates differently than intended — the skip guard becomes dead logic and the test's purpose statement no longer matches its runtime behavior.
- **Expected:** Either drop the skip guard entirely (the test is meaningful regardless of audit verdict — the `--bare` flag is now permanent), or read the value from a stable contract (e.g., a `verdict` field embedded in `lib/process.sh` itself or a parameterized constant in the test).
- **Why out of scope:** Simplification opportunity — not a bug or part of the current task.
- **Severity:** MEDIUM
- **Created:** 2026-05-14
