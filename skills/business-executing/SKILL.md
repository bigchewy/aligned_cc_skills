---
name: business-executing
description: "Use when you have a business plan to execute with deliverables and action items"
---

# Executing Business Plans

## Overview

Load plan, review critically, execute tasks in batches, report for review between batches.

**Core principle:** Batch execution with checkpoints for review. Never go too far without validation.

**Announce at start:** "I'm using the business-executing skill to implement this plan."

**Autonomous mode:** Execute all tasks without pausing for review between batches. Only stop if a task hits a blocker or the user intervenes.

Pre-approved actions (do not ask):
- Read any file in the project
- Search for context in project files
- Write deliverable content
- Run verification checks

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns
3. If concerns: Raise them before starting
4. If no concerns: Create task list and proceed

### Step 2: Execute Batch
**Default: First 5 tasks**

For each task:
1. Mark as in_progress
2. Follow each step exactly as planned
3. Apply `elements-of-style:writing-clearly-and-concisely` to all written output
4. Review against the task's acceptance criteria
5. Mark as completed

**For document sections:**
- Draft the section per the plan's specifications
- Check against acceptance criteria before presenting
- Present the completed section for review

**For action items:**
- List each action with: what, who, context, next step
- Flag any actions that need the user's input or decision
- Distinguish between "Claude can do now" and "the user needs to do"

**For research/analysis tasks:**
- Gather evidence from specified sources
- Synthesize findings concisely
- Present with confidence levels where appropriate

### Step 3: Report
When batch complete:
- Show what was produced
- Show how it meets acceptance criteria
- Flag any concerns or decisions needed

### Step 4: Continue
- Execute next batch
- Repeat until complete

### Step 5: Archive Plan Files

When all tasks are complete, move the plan file (and associated design doc if one exists) to a `completed/` subfolder within the plans directory. If the `completed/` subfolder doesn't exist, create it.

1. Parse the plan's `**Source Design Doc:**` field (if present) to get the design doc path.
2. Move the plan file to `completed/`.
3. If the source design doc is not `N/A` and exists, move it too.
4. Commit the moves.

If either move fails (file doesn't exist or already moved), skip and continue.

### Step 6: Report Completion

After all tasks complete and validated, output a structured summary:

**"Execution Complete"**

- **Deliverables Produced:** List each deliverable with acceptance criteria status
- **Discovered Issues:** List any issues surfaced during execution, or "None"
- **Suggested Next Steps:** Based on the deliverables and any issues

## When to Stop and Ask

**STOP executing immediately when:**
- Plan assumes context you don't have
- A section isn't landing and you're not sure why (use /aligned:business-diagnosis)
- You need a decision that isn't covered in the plan
- Feedback contradicts the plan's direction
- You realize the plan's scope needs adjustment

**Ask for clarification rather than guessing.**

## When to Use Business-Diagnosis

If during execution:
- A deliverable section isn't working despite multiple attempts
- The approach from the plan doesn't seem to fit the actual situation
- Feedback suggests the underlying strategy is off, not just the writing

**REQUIRED SUB-SKILL:** Use /aligned:business-diagnosis to find root cause before continuing.

## Issue Discovery During Execution

When unexpected business issues surface during execution (scope gaps not covered by the plan, stakeholder conflicts, assumption failures):

1. **Don't fix inline** — stay focused on the current task
2. **Raise immediately** — flag the issue in the conversation thread so the user is aware
3. **If it's a blocker** (dependency that prevents the current task from completing) — route to "When to Stop and Ask" above. Don't push through.
4. **Collect all issues** — include all raised issues in the Step 6 completion summary under "Discovered Issues" for user triage

**What qualifies as an issue to raise:**
- Scope gaps the plan doesn't cover but the deliverable needs
- Assumptions in the plan that turned out to be wrong
- Stakeholder conflicts or missing approvals that affect deliverable quality
- Evidence or data that contradicts the plan's direction

**What does NOT qualify:**
- Things that are part of a later task in the current plan (the plan handles it)
- Minor wording or formatting preferences (just handle them)
- Improvements beyond the plan's stated goal (not your job right now)

## Remember
- Review plan critically first
- Follow plan steps exactly
- Apply writing quality standards to all output
- Stop when blocked, don't guess
- Raise issues in-thread, don't fix inline
- Archive plan files when done
