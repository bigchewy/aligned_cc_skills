# Phase B: Mechanical Tasks (Ralph Loop)

Run this SECOND, after Phase A is complete and committed.

## Command

```bash
cd ~/software/aligned_cc_skills && rm -f .ralph-done && while :; do claude -p "$(cat docs/ralph_loops/EXECUTE-PLAN.md)

Plan: <path-to-plan-file>
Worktree: ~/software/aligned_cc_skills

NOTE: Phase A (Tasks 1, 13, 14, 15, 16, 17) is ALREADY COMPLETE. Skip any task already marked ✅." && [ -f .ralph-done ] && rm .ralph-done && break; done
```
