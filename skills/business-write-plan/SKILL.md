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

## Before Writing

Gather context before writing any plan:
1. Read the source design document (if one exists — path typically provided by the user or in a prior brainstorming session)
2. Check for prior plans on the same topic in the project's `docs/plans/` directory (if it exists)
3. Review any relevant business documents in the project directory
4. Identify stakeholders, dependencies, and constraints mentioned in project docs

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

**Source Design Doc:** [path to design doc, e.g. `docs/plans/2026-01-15-topic-design.md`, or `N/A` if none]

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

## Fact-Check + Critique Panel (mandatory, 2 parallel critics)

**MANDATORY: You MUST use the Task tool to launch fresh sub-agents** for every critique round. NEVER run the critique in the main context window. The sub-agents provide independent evaluation — they haven't seen the planning conversation, so they won't anchor on the author's assumptions. Running critique inline defeats the purpose and is a skill violation.

**Critic selection:** Default critics are listed below. If the plan's domain clearly warrants different critics (e.g., a technical plan that needs The Architect instead of Rumelt), select from `advisors/registry.md` instead. State which critics you selected and why.

**Round 1:**
1. Launch 2 sub-agents **in parallel** (both in a single message with 2 Task tool calls). Each uses `subagent_type=general-purpose`, `model=sonnet`. Replace `{plan-file-path}` below with the absolute path of the plan document you wrote in the previous step.

   **Critic 1 — Richard Rumelt (Strategic Alignment lens):**
   - Read Richard Rumelt's full prompt file (path listed in `advisors/registry.md`). Then:

   "[Full contents of Rumelt's prompt file]

   You have access to Glob, Grep, and Read tools for verifying claims. Read `skills/business-write-plan/plan-critique-checklist.md` in full, then read `{plan-file-path}` in full.

   Evaluate the plan through your strategic lens. Focus on: Does the plan identify and attack the crux? Are priorities correctly ordered? Does the guiding policy cohere? Do the tasks form a coordinated set of actions?

   You own checklist criteria 1 (Task sizing — are tasks focused on the crux?), 2 (Audience clarity), 5 (Scope discipline), and 9 (Decision quality). Skip criteria 3, 4, 6, 7, 8 (The PM covers those). You do NOT fact-check individual claims — The PM handles that.

   Also evaluate Decision Log entries if present. Tag every finding with [Rumelt].
   Output a critique in the checklist output format."

   **Critic 2 — The PM (Operability lens):**
   - Read The PM's full prompt file (path listed in `advisors/registry.md`). Then:

   "[Full contents of The PM's prompt file]

   You have access to Glob, Grep, and Read tools for verifying claims. Read `skills/business-write-plan/plan-critique-checklist.md` in full, then read `{plan-file-path}` in full. Your job has two phases:

   **Phase 1 (Fact-check):** Extract every factual claim (referenced documents, data points, stakeholder names, deliverable descriptions). Verify each using Glob/Grep/Read. Mark claims as [CONFIRMED], [INCORRECT] with correction, or [UNVERIFIABLE]. Report accuracy percentage.

   **Phase 2 (Critique):** Using the verification data you already gathered (do not re-verify), evaluate the plan against checklist criteria 3 (Evidence requirements), 4 ('So what?' test), 6 (Review gates), 7 (Acceptance criteria), and 8 (Dependencies and ordering). Focus on: Are tasks correctly sized? Are acceptance criteria measurable? Is the plan executable by someone with zero context? Are review gates at the right points?

   Also evaluate Decision Log entries if present. Tag every finding with [The PM].
   Output a single combined report: fact-check summary at the top, then critique in the checklist output format."

2. **Aggregate the two reports:**
   - **Fact-checks:** Take The PM's fact-check report as the authoritative source. If Rumelt flagged a factual issue The PM missed, include it with a [Rumelt] tag.
   - **Critique findings:** Merge both, preserving persona tags (`[Rumelt]`, `[The PM]`). De-duplicate — when both flag the same issue, keep the higher-severity version and note both sources.
   - Present the unified report to the user.

3. Apply corrections for any INCORRECT fact-check claims. Apply fixes for medium/high critique issues.

**Round 2 (conditional):**
Only run if Round 1 found medium or high severity issues. Use fresh sub-agents (do NOT resume Round 1 agents).

Round 2 is **scoped to changes only** — not a full re-review. Before launching agents, prepare a brief summary of what changed since Round 1.

Launch 2 sub-agents **in parallel**, both using `subagent_type=general-purpose`, `model=haiku`. Same critic identities (Rumelt + The PM), scoped prompts focusing only on changed sections with the summary of changes provided. Tag findings with persona names. Apply any remaining fixes.

## Plan Critique

When critiquing an existing plan (instead of writing one), use the checklist in `plan-critique-checklist.md`. Launch fresh sub-agents for critique rounds to ensure independent evaluation. Verify every claim against actual source materials — don't trust that referenced documents exist, contain the cited data, or support the conclusions drawn from them without checking.

## Decision Log (mandatory)

Every non-obvious choice in the plan gets logged. Append this section after completing the plan.

### Format

```markdown
## Decision Log

### Summary
| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | [topic]  | [choice] | [brief rationale] |

### Appendix: Decision Details

#### Decision 1: [topic]
**Chose:** [choice]
**Why:** [reasoning, trade-offs]
**Alternatives rejected:**
- [Alt A]: [why not]
- [Alt B]: [why not]
```

The summary table should fit on one page. Supporting detail goes in the appendix.

## Verification Gate

Before including any claim in the plan:
- Confirm referenced data points against the source design document
- Check that cited deliverables, documents, or artifacts actually exist (use Glob/Read)
- Verify stakeholder names and roles are accurate per project docs
- If a referenced file or document cannot be found, flag it as `[NOT FOUND]` in the plan rather than guessing

## Remember
- Specific deliverable descriptions, not vague ("write the pricing section" not "add content")
- Include what evidence/sources to reference for each section
- Include acceptance criteria for each task
- Reference `elements-of-style:writing-clearly-and-concisely` for all writing tasks (if unavailable, apply standard plain-English principles: active voice, short sentences, no jargon)
- Cut scope ruthlessly - if it doesn't serve the goal, remove it

## Execution Handoff

After saving the plan, commit it to git and output:

```
Plan complete and saved to `<filename>.md` (committed to git).
```

Then output a ready-to-paste prompt:

> Use `/aligned:business-executing` to execute the plan at `<plan-file-path>`.
