# KB-137: No fixture test for voice-rewrite Step 3.2b tuple-merge logic

- **Type:** bug
- **Discovered during:** finishing-a-development-branch (code review for reverse-engineered-brand-input-asks)
- **Location:** `frameworks/reverse-engineered-brand/prompt.md:389-432`, `frameworks/reverse-engineered-brand/voice-rewrite.md`
- **Observed:** Step 3.2b in the orchestrator dispatches `voice-rewrite.md` and merges rewritten asks back by `(folder_id, index)` tuple, plus `provided_summaries` keyed by `folder_id`. The tuple-merge logic has no fixture-level test. A regression that silently switched to positional merge (e.g., assumed the sub-agent preserves source order) would not be caught by the existing schema and coverage tests.
- **Expected:** Add a unit-level test fixture that exercises the tuple-merge path: a synthetic input (pre-rewrite asks + simulated sub-agent JSON response) and an assertion that each rewritten `text` lands at the correct `(folder_id, index)` slot, including when the sub-agent reorders or omits entries.
- **Why out of scope:** Plan task 16 scoped the template file and the orchestrator step, not a test harness for sub-agent response merging. Building this test requires either a mocked sub-agent invocation or a pure-Python reimplementation of the merge logic — design work not in the original plan.
- **Severity:** MEDIUM
- **Created:** 2026-05-18
