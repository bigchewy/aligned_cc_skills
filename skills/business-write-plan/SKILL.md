---
name: business-write-plan
description: "Use when you have a business objective or deliverable to plan out, before starting the work"
---

# Writing Business Plans

## Overview

You are a business plan writer. Your job is to produce detailed work plans that an executor with zero context can follow step by step.

Write comprehensive work plans assuming the executor has zero context for the business situation. Document everything needed: which sections to draft, what evidence to gather, what format to use, how to validate quality. Give the whole plan as bite-sized tasks.

Assume the executor is capable but knows nothing about this client, project, or objective.

**Announce at start:** "I'm using the business-write-plan skill to create the work plan."

**Context:** This should follow a design created by /aligned:business-brainstorming, or a clear objective from the user.

**Autonomous execution:** Run to completion without pausing for user feedback.
Pre-approved actions (do not ask):
- Read any file in the project
- Search the project for context
- Write plan sections to the plan file
- Launch critique sub-agents
- Commit the plan to git

Only stop for: unresolvable ambiguity in the design document.

**Save plans to:** Relevant project directory with naming: `YYYY-MM-DD-<topic>-plan.md`

## Bite-Sized Task Granularity

**Each step is one focused action:**
- "Draft the executive summary" - step
- "Review against success criteria" - step
- "Gather evidence for recommendation #1" - step
- "Write recommendation #1 with supporting data" - step
- "Review section with the user" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Deliverable/Objective] Work Plan

> **For Claude:** REQUIRED SUB-SKILL: Use /aligned:business-executing to implement this plan task-by-task.

**Goal:** [One sentence describing the desired outcome]

**Audience:** [Who will receive/use this]

**Format:** [Document type, structure, tone]

**Success Criteria:** [How we know this worked]

---
```

## Task Structure

```markdown
### Task N: [Section or Action]

**Output:**
- Create: `exact-filename.md` (or section within existing doc)
- Reference: `existing-doc.md` (materials to draw from)
- Review: Criteria for this section being "done"

**Step 1: Gather inputs**

Review [specific documents/notes]. Extract [specific information needed].

**Step 2: Draft section**

Write [specific section] covering:
- [Key point 1]
- [Key point 2]
- [Key point 3]

Target: [word count or scope guidance]
Tone: [formal/conversational/direct/etc.]

**Step 3: Review against criteria**

Check:
- [ ] Addresses the audience's actual concern
- [ ] Supported by evidence, not assertion
- [ ] Concise - no filler or buzzwords
- [ ] Passes the "so what?" test

**Step 4: Checkpoint with the user**

Present section. Wait for feedback before continuing.
```

## Task Types

Plans will contain a mix of these task types depending on the objective:

**Document sections** - Draft, review, refine a piece of writing
**Research tasks** - Gather evidence, find examples, synthesize information
**Analysis tasks** - Evaluate data, compare options, assess trade-offs
**Action items** - Concrete next steps with owner and context (emails, meetings, decisions)
**Review gates** - Checkpoints where the user validates direction before continuing

## Quality Checks for Plans

Before completing any plan, verify:

| Check | Question |
|-------|----------|
| Audience clarity | Does every task know who it's writing for? |
| Evidence required | Are claims backed by data, not just assertion? |
| "So what?" test | Does each section answer why the reader should care? |
| Scope discipline | Is anything included that doesn't serve the goal? |
| Review points | Are there enough checkpoints to catch drift early? |

## Sub-Agent Critique (mandatory)

After writing the plan, run two rounds of critique using fresh sub-agents. Sub-agents provide independent evaluation — they haven't seen the planning conversation, so they won't anchor on the author's assumptions.

**Round 1:**
1. Launch a fresh sub-agent (Task tool, `subagent_type=general-purpose`, `model=opus`). Replace `{plan-file-path}` below with the absolute path of the plan document you wrote in the previous step. Prompt:
   - "You are a skeptical, evidence-driven business plan reviewer. You have access to Glob, Grep, and Read tools for verifying claims. Read `skills/business-write-plan/plan-critique-checklist.md` in full, then read `{plan-file-path}` in full. Follow every instruction in the checklist to critique the plan using its output format. Verify all claims against referenced documents in the project directory — check that cited files exist and contain the data the plan references. Flag any claims you cannot verify as [UNVERIFIABLE]. Only report issues you can prove with evidence — do not speculate. Do not suggest expanding the plan's scope. Output a critique only — do not modify the plan file. If you cannot locate the checklist or plan file, report the error and stop."
2. Present the sub-agent's findings to the user
3. Incorporate approved fixes into the plan

**Round 2 (conditional):**
Only run if Round 1 found medium or high severity issues. Use fresh sub-agents (do NOT resume Round 1 agents).
1. Launch another fresh sub-agent (same config)
2. Same prompt, same checklist, but against the updated plan
3. Present Round 2 findings to the user
4. Incorporate any final fixes

## Plan Critique

When critiquing an existing plan (instead of writing one), use the checklist in `plan-critique-checklist.md`. Launch fresh sub-agents for critique rounds to ensure independent evaluation. Verify every claim against actual source materials — don't trust that referenced documents exist, contain the cited data, or support the conclusions drawn from them without checking.

## Remember
- Specific deliverable descriptions, not vague ("write the pricing section" not "add content")
- Include what evidence/sources to reference for each section
- Include acceptance criteria for each task
- Reference `elements-of-style:writing-clearly-and-concisely` for all writing tasks (if unavailable, apply standard plain-English principles: active voice, short sentences, no jargon)
- Cut scope ruthlessly - if it doesn't serve the goal, remove it

## Execution Handoff

After saving the plan, offer execution:

**"Plan complete and saved to `<filename>.md`. Ready to start executing?"**

**If yes:**
- **REQUIRED SUB-SKILL:** Use /aligned:business-executing
- Work through tasks in batches with review checkpoints
