# Phase B: Mechanical Tasks (Ralph Loop)

Run this SECOND, after Phase A is complete and committed.

## Command

```bash
cd ~/software/aligned_cc_skills && rm -f .ralph-done && while :; do claude -p "$(cat <<'PROMPT'
You are executing Phase B of the Aligned Plugin Parity Migration.

Read the plan at /Users/ericpage/software/epch-projects/docs/plans/2026-02-17-aligned-plugin-parity.md in full.

Phase A (Tasks 1, 13, 14, 15, 16, 17) is ALREADY COMPLETE. Do NOT re-execute those tasks.

Execute the remaining tasks in this order. Commit after each task as specified in the plan.

## Group 1: Port Hook Scripts and Infrastructure
- Task 2: Port All 5 Hook Scripts to Plugin
- Task 19: Fix Eval-Audit Hook Threshold Logic (create check-eval-audit.sh — needed by Task 3)
- Task 3: Update hooks.json with All Event Types
- Task 4: Delete Sync Infrastructure

## Group 2: Convert Kanban Format
- Task 5: Convert Kanban Format to Folder-Based System (all 6 skills)

## Group 3: Port Agents
- Task 6: Port Code-Reviewer Agent
- Task 7: Port Code-Simplifier Agent
- Task 8: Port Test-Auditor System (7 Files)
- Task 9: Port Kanban-Triage Agent

## Group 4: Restore Missing Features
- Task 10: Restore Step 1d and Step 6 in Finishing-a-Development-Branch

## Group 5: Port Skills
- Task 11: Port Kanban-Resolve Skill
- Task 12: Port Create-New-Skill (+ Supporting Files)

## Group 6: Content Fixes
- Task 18: Remove Ghost References and Fix Content Issues

## Group 7: Documentation and Verification
- Task 20: Update README with Permission Model and Complete Inventory
- Task 21: Update plugin.json Version
- Task 22: Final Verification

Working directory: ~/software/aligned_cc_skills/

When ALL tasks are complete and Task 22 verification passes, write the file .ralph-done with contents "done" and stop.
If Task 22 verification finds issues, fix them before writing .ralph-done.
PROMPT
" && [ -f .ralph-done ] && rm .ralph-done && break; done
```
