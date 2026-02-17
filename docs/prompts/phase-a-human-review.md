# Phase A: Architectural Tasks (Human Review)

Run this FIRST in an interactive Claude Code session.

## Prompt

```
cd ~/software/aligned_cc_skills

Read the plan at <path-to-plan-file> in full.

Execute ONLY these 5 tasks from the plan, in order. STOP after each task and show me what you changed so I can review before you proceed:

1. **Task 1: Update Plugin CLAUDE.md with Behavioral Guardrails**
2. **Task 13: Create Advisors Directory and Copy All Advisor Files** (including registry.md — needed by Task 16)
3. **Task 14: Port Use-Advisor Skill (Update for Plugin Paths)**
4. **Task 16: Upgrade Brainstorming to Multi-Critic Architecture**
5. **Task 17: Upgrade Writing-Plans to Dual-Critic Architecture**

After completing all 5, also do Task 15 (Port Use-Framework Skill) — it follows the same pattern as Task 14.

IMPORTANT:
- STOP after each task. Show me a summary of changes and wait for my "proceed" before moving to the next.
- For Tasks 16 and 17, show me the full replacement critique section before writing it — I want to review the architecture.
- Working directory is ~/software/aligned_cc_skills/ for ALL tasks.
- Commit after each task as specified in the plan.
```
