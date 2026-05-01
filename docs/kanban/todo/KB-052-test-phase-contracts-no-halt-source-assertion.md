# KB-052: test_phase_contracts.py does not assert phases source lib/halt.sh when they emit halts

- **Type:** test gap
- **Discovered during:** finishing-a-development-branch (code-reviewer)
- **Location:** `e2e/tests/test_phase_contracts.py:144-160`
- **Observed:** `test_phase_worktree_exists_and_conforms` only checks `"uncommitted_main" in text`. This assertion is satisfied by an inline `cat > $HALT_PATH <<HALT_EOF\nreason: uncommitted_main\n...` block — it does not verify that the phase actually uses `write_halt` (which provides the schema-required `log:`, `next-action:`, and centralized `fix-instructions:` via `format_halt`). A real bug (C1 in the original review on this branch) where `worktree.sh` was emitting a malformed halt sentinel passed this test.
- **Expected:** For every phase that the halt taxonomy maps to (per `skills/_shared/autopilot-halt-format.md`), assert the phase script either (a) sources `lib/halt.sh` and contains a `write_halt` call, or (b) is the orchestrator (which has its own halt-write path for `phase_crashed`). Equivalent rule: any `phases/*.sh` whose halt-taxonomy entry is not `phase_crashed` must contain `lib/halt.sh` in its source list.
- **Why out of scope:** The C1 fix on this branch updates `worktree.sh` to use `write_halt`; tightening the contract test is a follow-up that prevents the next phase author from making the same mistake.
- **Severity:** MEDIUM
- **Created:** 2026-04-30
