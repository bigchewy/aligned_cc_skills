# KB-066: Mockup/verify model-propagation tests use bare asserts without diagnostic messages

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code-reviewer)
- **Location:** `e2e/tests/test_autopilot_model_env_propagation.py:123-124` (mockup case) and the parallel block in `test_verify_phase_propagates_sonnet_to_claude`
- **Observed:** `test_mockup_phase_propagates_sonnet_to_claude` and `test_verify_phase_propagates_sonnet_to_claude` use bare `assert` statements with no message string. If the stub claude is never invoked (e.g., env_dump empty), the failure surfaces as a context-free `AssertionError`, forcing the developer to re-read the test to understand what failed. Compare to `test_plan_phase_propagates_sonnet_to_claude` (renamed from `test_plan_phase_propagates_opus_to_claude` when the plan-phase default downshifted in b390a1d), which includes an f-string assertion message showing the actual env value.
- **Expected:** Match the plan-phase test pattern — include an assertion message that shows the offending env var name and its observed value (e.g., `f"mockup.sh should propagate ANTHROPIC_MODEL=sonnet to claude; got {env.get('ANTHROPIC_MODEL')!r}"`).
- **Why out of scope:** Debuggability improvement, not a correctness defect — tests pass and verify the right invariant. Surfaced after merge readiness.
- **Severity:** LOW
- **Created:** 2026-05-14
