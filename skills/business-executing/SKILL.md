---
name: business-executing
description: "Use when you have a business plan to execute with deliverables and action items"
---

# Executing Business Plans

## Overview

Load plan, review critically, execute tasks in batches, report for review between batches.

**Core principle:** Batch execution with checkpoints for review. Never go too far without validation.

**Announce at start:** "I'm using the business-executing skill to implement this plan."

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns
3. If concerns: Raise them before starting
4. If no concerns: Create task list and proceed

### Step 2: Execute Batch
**Default: First 3 tasks**

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
- Say: "Ready for feedback."

### Step 4: Continue
Based on feedback:
- Apply changes if needed
- Execute next batch
- Repeat until complete

### Step 5: Complete

After all tasks complete and validated:
- Compile final deliverable if tasks produced sections of a larger document
- Present summary of all outputs (documents created, action items identified, decisions made)
- Ask: "Anything to adjust before we call this done?"

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

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip review checkpoints
- Apply writing quality standards to all output
- Between batches: report and wait
- Stop when blocked, don't guess
