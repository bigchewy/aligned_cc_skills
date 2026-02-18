# Business Skills Sync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Synchronize the 4 business-oriented skills with structural improvements from their software counterparts, preserving all business domain content.

**Source Design Doc:** `docs/plans/2026-02-18-business-skills-sync-design.md`

**Architecture:** Each business skill is a standalone Markdown file (`skills/<name>/SKILL.md`) with optional supporting files (checklists, registries). Changes are prompt engineering — no code, no tests, no builds. The 4 skills form a pipeline: brainstorming > write-plan > diagnosis (lateral) > executing.

**Tech Stack:** Markdown prompt files, Claude Code plugin system

---

## Prerequisites

None. All work happens in Markdown files within the repo.

---

### Task 1: Add MANDATORY sub-agent enforcement language to business-brainstorming

**Files:**
- Modify: `skills/business-brainstorming/SKILL.md:104-106`

**Step 1: Add enforcement language**

In `skills/business-brainstorming/SKILL.md`, replace lines 104-106:

```markdown
**Fact-Check + Critique Panel (mandatory, dynamic selection):**

After writing the design, run critique using fresh sub-agents. Sub-agents provide independent evaluation — they haven't seen the brainstorming conversation, so they won't anchor on the author's assumptions.
```

with:

```markdown
**Fact-Check + Critique Panel (mandatory, dynamic selection):**

**MANDATORY: You MUST use the Task tool to launch fresh sub-agents** for every critique round. NEVER run the critique in the main context window. The sub-agents provide independent evaluation — they haven't seen the brainstorming conversation, so they won't anchor on the author's assumptions. Running critique inline defeats the purpose and is a skill violation.
```

**Step 2: Verify the change**

Read `skills/business-brainstorming/SKILL.md` and confirm lines ~104-106 contain the MANDATORY warning matching `skills/brainstorming/SKILL.md:53`.

**Step 3: Commit**

```
git add skills/business-brainstorming/SKILL.md
git commit -m "feat(business-brainstorming): add MANDATORY sub-agent enforcement language"
```

---

### Task 2: Restructure fact-check into explicit two-phase format in business-brainstorming

**Files:**
- Modify: `skills/business-brainstorming/SKILL.md:117-119` (the critic prompt block)

**Step 1: Replace the single-phase critic prompt with two-phase structure**

In `skills/business-brainstorming/SKILL.md`, find the critic prompt text (inside the "Each critic's prompt:" block, approximately lines 116-119). Replace:

```markdown
   "[Full contents of the critic's prompt file]

   You have access to Glob, Grep, and Read tools for verifying claims. Read `skills/business-brainstorming/design-critique-checklist.md` in full, then read `{design-file-path}` in full. Follow every instruction in the checklist to critique the design using its output format. Verify all claims against referenced documents in the domain folder. Flag any claims you cannot verify as [UNVERIFIABLE]. Only report issues you can prove with evidence — do not speculate. Do not suggest expanding scope or adding sections. Tag every finding with your name (e.g., [Dalio], [The PM]).
   Output a critique report in the checklist output format."
```

with:

```markdown
   "[Full contents of the critic's prompt file]

   You have access to Glob, Grep, Read, WebSearch, and WebFetch tools for verifying claims. Read `skills/business-brainstorming/design-critique-checklist.md` in full, then read `{design-file-path}` in full. Your job has two phases:
   **Phase 1 (Fact-check):** Extract every factual claim (market data, competitor assertions, financial assumptions, stakeholder claims, timeline assertions). Verify against evidence provided in the document and referenced domain materials. Use WebSearch/WebFetch to check external claims where possible. Mark claims as [CONFIRMED], [INCORRECT] with correction, or [UNVERIFIABLE]. Report accuracy percentage. Include source URLs for verified external claims.
   **Phase 2 (Critique):** Using the verification data you already gathered (do not re-verify), evaluate the design against each criterion in the checklist through your lens. Also evaluate Decision Log entries if present. Tag every finding with your name (e.g., [Dalio], [The PM]).
   Output a single combined report: fact-check summary at the top, then critique in the checklist output format."
```

**Step 2: Verify the change**

Read `skills/business-brainstorming/SKILL.md` and confirm the critic prompt block now has Phase 1 (Fact-check) and Phase 2 (Critique) matching the structure in `skills/brainstorming/SKILL.md:65-68`.

**Step 3: Commit**

```
git add skills/business-brainstorming/SKILL.md
git commit -m "feat(business-brainstorming): restructure critic prompt into two-phase fact-check format"
```

---

### Task 3: Add escalation protocol for Round 2 in business-brainstorming

**Files:**
- Modify: `skills/business-brainstorming/SKILL.md:128-129`

**Step 1: Add escalation mechanic to Round 2**

In `skills/business-brainstorming/SKILL.md`, find the Round 2 section (approximately lines 128-129):

```markdown
**Round 2 (conditional):**
Only run if Round 1 found medium or high severity issues. Same critics (not re-selected), fresh sub-agents (do NOT resume Round 1 agents), against the updated document. Incorporate any final fixes. Present final results to the user.
```

Replace with:

```markdown
**Round 2 (conditional):**
Only run if Round 1 found medium or high severity issues. Same critics (not re-selected), fresh sub-agents (do NOT resume Round 1 agents), against the updated document.

**Escalation:** If Round 1 revealed concerns in a domain not covered by the selected critics, add one specialist critic for Round 2. For example, if a financial critic flagged a legal compliance concern but no legal advisor was in Round 1, add one for Round 2. State the escalation reason. Maximum one additional critic per round.

Apply any remaining fixes. Present final results to the user.
```

**Step 2: Verify the change**

Read `skills/business-brainstorming/SKILL.md` and confirm the Round 2 section now includes the Escalation paragraph matching `skills/brainstorming/SKILL.md:80`.

**Step 3: Commit**

```
git add skills/business-brainstorming/SKILL.md
git commit -m "feat(business-brainstorming): add escalation protocol for Round 2 critique"
```

---

### Task 4: Add git commit and handoff prompt to business-brainstorming

**Files:**
- Modify: `skills/business-brainstorming/SKILL.md:131-133`

**Step 1: Replace the existing execution handoff**

In `skills/business-brainstorming/SKILL.md`, find the execution section (approximately lines 131-133):

```markdown
**Execution (if continuing):**
- Ask: "Ready to plan out the work?"
- **REQUIRED SUB-SKILL:** Use /aligned:business-write-plan to create detailed work plan
```

Note: The software counterpart (`brainstorming`) has a "Create worktree + next step prompt" section that invokes `/aligned:using-git-worktrees`. Business skills have no feature branch workflow, so the worktree step is intentionally omitted.

Replace with:

```markdown
**Post-design steps:**

- Commit the design document to git after critique rounds are complete

**Next step prompt (mandatory):**

After committing the design document, output a ready-to-paste prompt for the next session:

> Use `/aligned:business-write-plan` to write an execution plan based on the design document at `docs/plans/YYYY-MM-DD-<topic>-design.md`.
```

**Step 2: Verify the change**

Read `skills/business-brainstorming/SKILL.md` and confirm:
1. The `**Post-design steps:**` header is present
2. The git commit instruction is present
3. The handoff prompt references `/aligned:business-write-plan` with the correct path pattern

**Step 3: Commit**

```
git add skills/business-brainstorming/SKILL.md
git commit -m "feat(business-brainstorming): add git commit step and next-step handoff prompt"
```

---

### Task 5: Create critic-registry.md pointer file for business-brainstorming

**Files:**
- Create: `skills/business-brainstorming/critic-registry.md`

**Step 1: Create the pointer file**

Create `skills/business-brainstorming/critic-registry.md` with this content (matching `skills/brainstorming/critic-registry.md`):

```markdown
Critic selection uses `advisors/registry.md`. See that file for per-advisor domain metadata, selection guidelines, and diversity rules.
```

**Step 2: Verify the file**

Read `skills/business-brainstorming/critic-registry.md` and confirm it matches `skills/brainstorming/critic-registry.md` exactly.

**Step 3: Commit**

```
git add skills/business-brainstorming/critic-registry.md
git commit -m "feat(business-brainstorming): add critic-registry.md pointer file"
```

---

### Task 6: Add applicability assessment directive to business design-critique-checklist.md

**Files:**
- Modify: `skills/business-brainstorming/design-critique-checklist.md:7-9`

**Step 1: Add applicability assessment after the instructions preamble**

In `skills/business-brainstorming/design-critique-checklist.md`, find:

```markdown
## Instructions

1. Read the design document at the path provided. If the file cannot be read or is empty, report the error and stop.
```

(Note: line 7 = `## Instructions`, line 8 = blank, line 9 = `1. Read the design document...`)

Replace with:

with:

```markdown
## Instructions

**Applicability assessment:** After reading the design document, quickly assess which of the 8 criteria below are relevant to its scope. If a criterion clearly doesn't apply (e.g., "Missing stakeholders" when the design is a solo deliverable with no external dependencies; "Feasibility and constraints" when the design is a pure analysis with no resource requirements), mark it **N/A** with a one-line reason in the Checklist Results table and skip verification for that criterion.

1. Read the design document at the path provided. If the file cannot be read or is empty, report the error and stop.
```

**Step 2: Verify the change**

Read `skills/business-brainstorming/design-critique-checklist.md` and confirm the applicability assessment directive appears between `## Instructions` and the numbered list.

**Step 3: Commit**

```
git add skills/business-brainstorming/design-critique-checklist.md
git commit -m "feat(business-brainstorming): add applicability assessment directive to design critique checklist"
```

---

### Task 7: Add autonomous execution mode to business-write-plan

**Files:**
- Modify: `skills/business-write-plan/SKILL.md:18-20`

**Step 1: Add autonomy block after the context line**

In `skills/business-write-plan/SKILL.md`, find (lines 18-20):

```markdown
**Context:** This should follow a design created by /aligned:business-brainstorming, or a clear objective from the user.

**Save plans to:** Relevant project directory with naming: `YYYY-MM-DD-<topic>-plan.md`
```

Replace with:

```markdown
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
```

**Step 2: Verify the change**

Read `skills/business-write-plan/SKILL.md` and confirm the autonomous execution block appears between the Context and Save lines.

**Step 3: Commit**

```
git add skills/business-write-plan/SKILL.md
git commit -m "feat(business-write-plan): add autonomous execution mode"
```

---

### Task 8: Add research/exploration phase to business-write-plan

**Files:**
- Modify: `skills/business-write-plan/SKILL.md` (after the Save plans line, before `## Bite-Sized Task Granularity`)

**Step 1: Add the "Before Writing" section**

In `skills/business-write-plan/SKILL.md`, find:

```markdown
**Save plans to:** Relevant project directory with naming: `YYYY-MM-DD-<topic>-plan.md`

## Bite-Sized Task Granularity
```

Insert a new section between them:

```markdown
**Save plans to:** Relevant project directory with naming: `YYYY-MM-DD-<topic>-plan.md`

## Before Writing

Gather context before writing any plan:
1. Read the source design document (if one exists — path typically provided by the user or in a prior brainstorming session)
2. Check for prior plans on the same topic in the project's `docs/plans/` directory (if it exists)
3. Review any relevant business documents in the project directory
4. Identify stakeholders, dependencies, and constraints mentioned in project docs

## Bite-Sized Task Granularity
```

**Step 2: Verify the change**

Read `skills/business-write-plan/SKILL.md` and confirm the `## Before Writing` section appears before `## Bite-Sized Task Granularity`.

**Step 3: Commit**

```
git add skills/business-write-plan/SKILL.md
git commit -m "feat(business-write-plan): add research/exploration phase before writing"
```

---

### Task 9: Add verification gate and Source Design Doc header field to business-write-plan

**Files:**
- Modify: `skills/business-write-plan/SKILL.md` (plan header template + new section)

**Step 1: Add Source Design Doc to the plan header template**

In `skills/business-write-plan/SKILL.md`, find the plan header template:

```markdown
**Goal:** [One sentence describing the desired outcome]

**Audience:** [Who will receive/use this]
```

Replace with:

```markdown
**Goal:** [One sentence describing the desired outcome]

**Source Design Doc:** [path to design doc, e.g. `docs/plans/2026-01-15-topic-design.md`, or `N/A` if none]

**Audience:** [Who will receive/use this]
```

**Step 2: Add verification gate section**

Find:

```markdown
## Remember
```

Insert before it:

```markdown
## Verification Gate

Before including any claim in the plan:
- Confirm referenced data points against the source design document
- Check that cited deliverables, documents, or artifacts actually exist (use Glob/Read)
- Verify stakeholder names and roles are accurate per project docs
- If a referenced file or document cannot be found, flag it as `[NOT FOUND]` in the plan rather than guessing

## Remember
```

**Step 3: Verify the change**

Read `skills/business-write-plan/SKILL.md` and confirm:
1. The plan header template includes `**Source Design Doc:**`
2. The `## Verification Gate` section appears before `## Remember`

**Step 4: Commit**

```
git add skills/business-write-plan/SKILL.md
git commit -m "feat(business-write-plan): add verification gate and Source Design Doc header field"
```

---

### Task 10: Add mandatory Decision Log section to business-write-plan

**Ordering dependency:** Complete Task 9 before Task 10 — Task 10 inserts before `## Verification Gate`, which Task 9 creates.

**Files:**
- Modify: `skills/business-write-plan/SKILL.md` (insert before Verification Gate)

**Step 1: Add Decision Log section**

In `skills/business-write-plan/SKILL.md`, find:

```markdown
## Verification Gate
```

Insert before it:

```markdown
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
```

**Step 2: Verify the change**

Read `skills/business-write-plan/SKILL.md` and confirm the `## Decision Log (mandatory)` section appears before `## Verification Gate`.

**Step 3: Commit**

```
git add skills/business-write-plan/SKILL.md
git commit -m "feat(business-write-plan): add mandatory Decision Log section"
```

---

### Task 11: Replace single-critic with dual-critic architecture in business-write-plan

**Files:**
- Modify: `skills/business-write-plan/SKILL.md` (the `## Sub-Agent Critique (mandatory)` section)

**Step 1: Replace the entire Sub-Agent Critique section**

In `skills/business-write-plan/SKILL.md`, find the entire `## Sub-Agent Critique (mandatory)` section (from the header through the Round 2 conditional block). Replace it with:

```markdown
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
```

**Step 2: Verify the change**

Read `skills/business-write-plan/SKILL.md` and confirm:
1. Section header is now `## Fact-Check + Critique Panel (mandatory, 2 parallel critics)`
2. Two named critics: Rumelt (criteria 1, 2, 5, 9) and The PM (criteria 3, 4, 6, 7, 8 + fact-checking)
3. Round 1 uses `model=sonnet`, Round 2 uses `model=haiku`
4. MANDATORY enforcement language is present

**Step 3: Commit**

```
git add skills/business-write-plan/SKILL.md
git commit -m "feat(business-write-plan): replace single critic with dual-critic architecture (Rumelt + The PM)"
```

---

### Task 12: Update handoff prompt in business-write-plan

**Files:**
- Modify: `skills/business-write-plan/SKILL.md` (the `## Execution Handoff` section)

**Step 1: Replace the execution handoff**

In `skills/business-write-plan/SKILL.md`, find the entire `## Execution Handoff` section:

```markdown
## Execution Handoff

After saving the plan, offer execution:

**"Plan complete and saved to `<filename>.md`. Ready to start executing?"**

**If yes:**
- **REQUIRED SUB-SKILL:** Use /aligned:business-executing
- Work through tasks in batches with review checkpoints
```

Replace with:

```markdown
## Execution Handoff

After saving the plan, commit it to git and output:

```
Plan complete and saved to `<filename>.md` (committed to git).
```

Then output a ready-to-paste prompt:

> Use `/aligned:business-executing` to execute the plan at `<plan-file-path>`.
```

**Step 2: Verify the change**

Read `skills/business-write-plan/SKILL.md` and confirm the handoff section outputs a ready-to-paste prompt referencing `/aligned:business-executing`.

**Step 3: Commit**

```
git add skills/business-write-plan/SKILL.md
git commit -m "feat(business-write-plan): update handoff to commit + ready-to-paste prompt"
```

---

### Task 13: Update business plan-critique-checklist.md with new directives and 9th criterion

**Files:**
- Modify: `skills/business-write-plan/plan-critique-checklist.md`

**Step 1: Add applicability assessment directive**

In `skills/business-write-plan/plan-critique-checklist.md`, find:

```markdown
## Instructions

1. Read the plan file at the path provided. If the file cannot be read or is empty, report the error and stop.
```

(Note: line 7 = `## Instructions`, line 8 = blank, line 9 = `1. Read the plan file...`)

Insert the applicability assessment after `## Instructions` and before the numbered list:

```markdown
## Instructions

**Applicability assessment:** After reading the plan, quickly assess which of the 9 criteria below are relevant to its scope. If a criterion clearly doesn't apply (e.g., "Dependencies and ordering" when the plan has only 1-2 tasks; "Review gates" when the plan is a solo deliverable with no stakeholder checkpoints), mark it **N/A** with a one-line reason in the Checklist Results table and skip verification for that criterion.

**Never suggest merging, combining, or consolidating tasks** — granular tasks are intentional. Document ordering dependencies instead.

1. Read the plan file at the path provided. If the file cannot be read or is empty, report the error and stop.
```

**Step 2: Add 9th criterion — Decision quality**

After criterion 8 (Dependencies and ordering), add:

```markdown
### 9. Decision quality

Every non-obvious choice in the plan should be captured in the Decision Log with sufficient rationale.

- Does the plan include a Decision Log section?
- For each decision, are alternatives listed with reasons for rejection?
- Are there non-obvious choices in the plan that are NOT logged? (Flag as missing)
- Is the rationale sufficient to understand why the choice was made without additional context?

- BAD: Decision Log missing entirely, or decisions listed without alternatives
- GOOD: Every non-trivial choice documented with rationale and rejected alternatives
```

**Step 3: Update the Checklist Results table in the output format**

In the Critique Output Format section, add row 9 to the table:

```markdown
| 9 | Decision quality | {Pass / N issues found} |
```

**Step 4: Verify the change**

Read `skills/business-write-plan/plan-critique-checklist.md` and confirm:
1. Applicability assessment directive is present after `## Instructions`
2. "Never suggest merging" directive is present
3. Criterion 9 (Decision quality) exists after criterion 8
4. Checklist Results table has 9 rows

**Step 5: Commit**

```
git add skills/business-write-plan/plan-critique-checklist.md
git commit -m "feat(business-write-plan): add applicability assessment, anti-merge directive, and 9th criterion to checklist"
```

---

### Task 14: Add severity levels and Phase 0 header to business-diagnosis

**Files:**
- Modify: `skills/business-diagnosis/SKILL.md`

**Step 1: Add severity levels section after "When to Use"**

In `skills/business-diagnosis/SKILL.md`, find:

```markdown
- You don't fully understand why something isn't working

## The Four Phases
```

Insert between them:

```markdown
- You don't fully understand why something isn't working

## Severity Levels

Default severity is **low** (single investigator, standard 4-phase process). Pass `high` as an argument for multi-agent fan-out investigation.

- `/aligned:business-diagnosis` — low severity (default)
- `/aligned:business-diagnosis high` — high severity, multi-agent

### High Severity — Phase 0: Multi-Agent Investigation

Added before the existing four phases. Use when low-severity investigation is insufficient.

Fan out 5 subagents via Task tool, each with a different analytical method:

| Agent | Method | Prompt Directive |
|-------|--------|-----------------|
| Backward Tracer | Trace from symptoms to origin | "Start at the problem symptoms. Trace backward: when did this start? What changed? What was working before? Follow the chain to find the origin point." |
| Stakeholder Mapper | Map human system around the problem | "Identify all affected parties, their perspectives, incentives, and potential blind spots. Map the human system around this problem. Who benefits from the status quo? Who has veto power?" |
| Data Analyst | Analyze quantitative evidence | "Gather and analyze relevant metrics, timelines, and quantitative evidence. Look for correlations, trends, and anomalies. What does the data say vs. what people believe?" |
| Pattern Matcher | Search for similar past problems | "Search project history for similar past problems and how they were resolved. Check if this is a recurring pattern. What was tried before? What worked and what didn't?" |
| JudgeAgent | Synthesize and resolve contradictions | "Read the other agents' reports. For each proposed root cause, try to disprove it. Identify agreements and contradictions. Produce a unified hypothesis ranked by evidence strength." |

First 4 agents run in parallel. Each returns: hypothesis, evidence, confidence level.

JudgeAgent runs second, receiving all 4 reports. Challenges each hypothesis, resolves contradictions.

Main thread synthesizes. If consensus → proceed to Phase 1 with strong starting hypothesis. If no consensus → present competing theories to user.

### When to Use High Severity

- Previous low-severity investigation didn't find root cause (clearest signal)
- Cross-functional issues affecting multiple teams or stakeholders
- Multi-stakeholder impact with conflicting perspectives
- Recurring problems that have resisted 2+ prior fix attempts
- Time-critical situations (deadline pressure, escalation risk)
- User explicitly requests high severity

## The Four Phases
```

**Step 2: Verify the change**

Read `skills/business-diagnosis/SKILL.md` and confirm:
1. `## Severity Levels` section exists after "When to Use"
2. Phase 0 has 5 agents in the table (Backward Tracer, Stakeholder Mapper, Data Analyst, Pattern Matcher, JudgeAgent)
3. `## The Four Phases` still exists after the severity section

**Step 3: Commit**

```
git add skills/business-diagnosis/SKILL.md
git commit -m "feat(business-diagnosis): add severity levels and Phase 0 multi-agent investigation"
```

---

### Task 15: Add "When Process Reveals No Root Cause" section to business-diagnosis

**Files:**
- Modify: `skills/business-diagnosis/SKILL.md` (insert after Quick Reference, before end of file)

**Step 1: Add the new section**

In `skills/business-diagnosis/SKILL.md`, find the end of the Quick Reference table. After it, append:

```markdown

## When Process Reveals No Root Cause

If systematic investigation surfaces no clear root cause, consider these possibilities:

- **External/environmental factors:** Market shifts, competitor actions, regulatory changes that are outside the team's control
- **Timing issues:** The problem is intermittent or context-dependent — it only manifests under specific conditions (certain clients, certain times, certain workloads)
- **Third-party dependencies:** The root cause lies in a partner, vendor, or platform the team doesn't control

**Action:** Document what was investigated, what was ruled out, and what external factors are suspected. Recommend monitoring rather than fixing.

**But:** 95% of "no root cause" cases are incomplete investigation. Before concluding the cause is external, verify you have genuinely exhausted the 4-phase process.
```

**Step 2: Verify the change**

Read `skills/business-diagnosis/SKILL.md` and confirm the `## When Process Reveals No Root Cause` section exists after `## Quick Reference`.

**Step 3: Commit**

```
git add skills/business-diagnosis/SKILL.md
git commit -m "feat(business-diagnosis): add 'When Process Reveals No Root Cause' section"
```

---

### Task 16: Add User Signals section to business-diagnosis

**Files:**
- Modify: `skills/business-diagnosis/SKILL.md` (insert after Red Flags, before Common Rationalizations)

**Step 1: Add the User Signals section**

In `skills/business-diagnosis/SKILL.md`, find:

```markdown
**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ approaches failed:** Question the strategy (see Phase 4.5)

## Common Rationalizations
```

Insert between the "If 3+ approaches" line and `## Common Rationalizations`:

```markdown
**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ approaches failed:** Question the strategy (see Phase 4.5)

## Your Human Partner's Signals You're Doing It Wrong

**Watch for these redirections:**
- They keep saying "but why?" after your explanations → you haven't gone deep enough
- They're getting frustrated because you keep proposing solutions → you skipped root cause investigation
- They say "we tried that already" → you didn't check history
- They redirect you to talk to someone else → you're missing a stakeholder perspective
- They ask you to "just fix it" → the process feels too slow, but don't skip steps — explain what you're doing and why

**When you see these:** STOP. Return to Phase 1.

## Common Rationalizations
```

**Step 2: Verify the change**

Read `skills/business-diagnosis/SKILL.md` and confirm the User Signals section exists between Red Flags and Common Rationalizations.

**Step 3: Commit**

```
git add skills/business-diagnosis/SKILL.md
git commit -m "feat(business-diagnosis): add User Signals section"
```

---

### Task 17: Trim rationalizations table in business-diagnosis

**Files:**
- Modify: `skills/business-diagnosis/SKILL.md`

**Step 1: Remove 2 rows from the rationalizations table**

In `skills/business-diagnosis/SKILL.md`, find the Common Rationalizations table:

```markdown
| Excuse | Reality |
|--------|---------|
| "Issue is obvious, don't need process" | Obvious issues have root causes too. Process is fast for simple problems. |
| "Urgent, no time for process" | Systematic diagnosis is FASTER than solution-hopping. |
| "Just try this first, then investigate" | First solution sets the direction. Do it right from the start. |
| "Multiple changes at once saves effort" | Can't isolate what worked. Causes new issues. |
| "I see the problem, let me fix it" | Seeing symptoms does not equal understanding root cause. |
| "One more attempt" (after 2+ failures) | 3+ failures = strategic problem. Question the approach, don't try again. |
```

Replace with (removing rows 3 and 4):

```markdown
| Excuse | Reality |
|--------|---------|
| "Issue is obvious, don't need process" | Obvious issues have root causes too. Process is fast for simple problems. |
| "Urgent, no time for process" | Systematic diagnosis is FASTER than solution-hopping. |
| "I see the problem, let me fix it" | Seeing symptoms does not equal understanding root cause. |
| "One more attempt" (after 2+ failures) | 3+ failures = strategic problem. Question the approach, don't try again. |
```

**Step 2: Verify the change**

Read `skills/business-diagnosis/SKILL.md` and confirm the rationalizations table has exactly 4 rows (not 6).

**Step 3: Commit**

```
git add skills/business-diagnosis/SKILL.md
git commit -m "feat(business-diagnosis): trim rationalizations table from 6 to 4 rows"
```

---

### Task 18: Update Quick Reference table in business-diagnosis

**Files:**
- Modify: `skills/business-diagnosis/SKILL.md`

**Step 1: Expand Quick Reference table to include Phase 0**

In `skills/business-diagnosis/SKILL.md`, find the Quick Reference table:

```markdown
| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Gather evidence, define gap, check changes, trace cause | Understand WHAT and WHY |
| **2. Pattern** | Find successes, compare, identify differences | Know what works and why this doesn't |
| **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
| **4. Implementation** | Define criteria, single change, verify | Problem resolved, criteria met |
```

Replace with:

```markdown
| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **0. Multi-Agent** (high only) | Fan out subagents, synthesize | Consensus hypothesis or competing theories |
| **1. Root Cause** | Gather evidence, define gap, check changes, trace cause | Understand WHAT and WHY |
| **2. Pattern** | Find successes, compare, identify differences | Know what works and why this doesn't |
| **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
| **4. Implementation** | Define criteria, single change, verify | Problem resolved, criteria met |
```

**Step 2: Verify the change**

Read `skills/business-diagnosis/SKILL.md` and confirm the Quick Reference table has 5 rows (Phase 0 through Phase 4).

**Step 3: Commit**

```
git add skills/business-diagnosis/SKILL.md
git commit -m "feat(business-diagnosis): expand Quick Reference table to include Phase 0"
```

---

### Task 19: Add autonomous mode and increase batch size in business-executing

**Files:**
- Modify: `skills/business-executing/SKILL.md:14-16`

**Behavioral change:** business-executing's core principle shifts from checkpoint-gated execution to autonomous batch execution. This removes the user review loop between batches. The "When to Stop and Ask" section remains as the only interruption path.

**Step 1: Add autonomous mode after the announce line**

In `skills/business-executing/SKILL.md`, find (lines 14-16):

```markdown
**Announce at start:** "I'm using the business-executing skill to implement this plan."

## The Process
```

Replace with:

```markdown
**Announce at start:** "I'm using the business-executing skill to implement this plan."

**Autonomous mode:** Execute all tasks without pausing for review between batches. Only stop if a task hits a blocker or the user intervenes.

Pre-approved actions (do not ask):
- Read any file in the project
- Search for context in project files
- Write deliverable content
- Run verification checks

## The Process
```

**Step 2: Update batch size from 3 to 5**

In `skills/business-executing/SKILL.md`, find:

```markdown
**Default: First 3 tasks**
```

Replace with:

```markdown
**Default: First 5 tasks**
```

**Step 3: Remove "Ready for feedback" from Step 3 and "feedback" loop from Step 4**

In `skills/business-executing/SKILL.md`, find Step 3:

```markdown
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
```

Replace with:

```markdown
### Step 3: Report
When batch complete:
- Show what was produced
- Show how it meets acceptance criteria
- Flag any concerns or decisions needed

### Step 4: Continue
- Execute next batch
- Repeat until complete
```

**Step 4: Verify the changes**

Read `skills/business-executing/SKILL.md` and confirm:
1. Autonomous mode block appears after the announce line
2. Batch size is 5
3. "Ready for feedback" and feedback-based Step 4 are removed

**Step 5: Commit**

```
git add skills/business-executing/SKILL.md
git commit -m "feat(business-executing): add autonomous mode and increase batch size to 5"
```

---

### Task 20: Add plan archival step to business-executing

**Files:**
- Modify: `skills/business-executing/SKILL.md` (replace Step 5 section)

**Step 1: Replace the Complete step with archival + structured completion**

In `skills/business-executing/SKILL.md`, find the entire Step 5:

```markdown
### Step 5: Complete

After all tasks complete and validated:
- Compile final deliverable if tasks produced sections of a larger document
- Present summary of all outputs (documents created, action items identified, decisions made)
- Ask: "Anything to adjust before we call this done?"
```

Replace with:

```markdown
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
```

**Step 2: Verify the change**

Read `skills/business-executing/SKILL.md` and confirm:
1. Step 5 is now "Archive Plan Files" with archival instructions
2. Step 6 is "Report Completion" with the structured format
3. The informal "Anything to adjust?" is gone

**Step 3: Commit**

```
git add skills/business-executing/SKILL.md
git commit -m "feat(business-executing): add plan archival step and structured completion handoff"
```

---

### Task 21: Add issue discovery protocol to business-executing

**Files:**
- Modify: `skills/business-executing/SKILL.md` (insert after "When to Use Business-Diagnosis", before "Remember")

**Step 1: Add the issue discovery section**

In `skills/business-executing/SKILL.md`, find:

```markdown
**REQUIRED SUB-SKILL:** Use /aligned:business-diagnosis to find root cause before continuing.

## Remember
```

Insert between them:

```markdown
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
```

**Step 2: Verify the change**

Read `skills/business-executing/SKILL.md` and confirm the `## Issue Discovery During Execution` section exists between the business-diagnosis section and `## Remember`.

**Step 3: Commit**

```
git add skills/business-executing/SKILL.md
git commit -m "feat(business-executing): add issue discovery protocol"
```

---

### Task 22: Update Remember section in business-executing

**Files:**
- Modify: `skills/business-executing/SKILL.md`

**Step 1: Update the Remember section for autonomous mode**

In `skills/business-executing/SKILL.md`, find:

```markdown
## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip review checkpoints
- Apply writing quality standards to all output
- Between batches: report and wait
- Stop when blocked, don't guess
```

Replace with:

```markdown
## Remember
- Review plan critically first
- Follow plan steps exactly
- Apply writing quality standards to all output
- Stop when blocked, don't guess
- Raise issues in-thread, don't fix inline
- Archive plan files when done
```

**Step 2: Verify the change**

Read `skills/business-executing/SKILL.md` and confirm the Remember section reflects autonomous mode (no "report and wait" or "review checkpoints").

**Step 3: Commit**

```
git add skills/business-executing/SKILL.md
git commit -m "feat(business-executing): update Remember section for autonomous mode"
```

---

### Task 23: Final verification — cross-reference check

**Files:**
- Read: all 4 modified SKILL.md files + 2 checklists + 1 new file

**Step 1: Verify all cross-references are valid**

For each modified file, confirm:
1. `skills/business-brainstorming/SKILL.md` references:
   - `advisors/registry.md` — exists
   - `skills/business-brainstorming/design-critique-checklist.md` — exists
   - `/aligned:business-write-plan` — skill exists
2. `skills/business-write-plan/SKILL.md` references:
   - `advisors/registry.md` — exists
   - `skills/business-write-plan/plan-critique-checklist.md` — exists
   - `/aligned:business-executing` — skill exists
3. `skills/business-diagnosis/SKILL.md` — self-contained, no new external refs
4. `skills/business-executing/SKILL.md` references:
   - `/aligned:business-diagnosis` — skill exists
5. `skills/business-brainstorming/critic-registry.md` references:
   - `advisors/registry.md` — exists
6. Advisor prompt files used by business-write-plan dual-critic (Task 11):
   - `advisors/va-web-app/richard-rumelt.md` — exists
   - `advisors/.claude/the-pm.md` — exists

**Step 2: Verify all preserved content is intact**

Spot-check that these business-domain sections still exist unchanged:
- business-brainstorming: 4-phase gates, obstacle taxonomy (5 categories), root cause indicators
- business-write-plan: task types catalog, quality checks table
- business-diagnosis: Iron Law block, 4-layer tracing model, red flags list
- business-executing: task type guidance (document sections, action items, research/analysis)

**Step 3: Verify new content from checklist updates**

Confirm:
- `skills/business-brainstorming/design-critique-checklist.md` contains the applicability assessment directive between `## Instructions` and the numbered list (added by Task 6)
- `skills/business-write-plan/plan-critique-checklist.md` contains the applicability assessment directive, anti-merge directive, and criterion 9 (added by Task 13)

**Step 4: Commit (if any fixes needed)**

If any cross-references are broken or preserved content is missing, fix and commit. Otherwise, no commit needed.

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Task ordering | Follow design doc's execution order (brainstorm > write-plan > diagnosis > executing) | Parallel by skill, alphabetical |
| 2 | Commit granularity | One commit per logical feature addition | One commit per skill, single mega-commit |
| 3 | Round 2 model for business-write-plan | `model=haiku` (matching writing-plans) | `model=sonnet` (matching Round 1) |
| 4 | business-executing Step 3/4 rewrite | Remove "Ready for feedback" and feedback loop | Keep feedback loop alongside autonomous mode |
| 5 | business-diagnosis description field | Keep existing description unchanged | Update to mention severity support |
| 6 | Critic model: business-write-plan vs business-brainstorming | `model=sonnet` for write-plan (matching writing-plans counterpart) | `model=opus` (matching business-brainstorming) |

### Appendix: Decision Details

#### Decision 1: Task ordering
**Chose:** Follow design doc's execution order (brainstorming first, executing last)
**Why:** The design doc explicitly specifies this order with rationale: brainstorming sets the pattern for critic architecture upgrades, write-plan benefits from brainstorming being done first for handoff coherence, and executing benefits from write-plan being done first. The pipeline dependencies make this the natural order.
**Alternatives rejected:**
- Parallel by skill: Each skill is independent at the file level, but the design patterns established in skill 1 inform skill 2's implementation. Sequential ensures consistency.
- Alphabetical: No logical basis.

#### Decision 2: Commit granularity
**Chose:** One commit per logical feature addition (e.g., "add MANDATORY language" is separate from "add escalation protocol")
**Why:** The design doc lists 4-6 distinct features per skill. Each feature is independently revertable and independently reviewable. This matches the writing-plans skill's bite-sized granularity principle and makes git blame useful.
**Alternatives rejected:**
- One commit per skill: Bundles unrelated changes (e.g., critic prompt restructuring + git commit step). Harder to revert individual features.
- Single mega-commit: Defeats the purpose of version control for a 4-skill change.

#### Decision 3: Round 2 model for business-write-plan
**Chose:** `model=haiku` for Round 2
**Why:** Design doc explicitly specifies this. It matches writing-plans' efficiency optimization — Round 2 is scoped to changes only, so a lighter model suffices. Saves cost without quality loss for a focused re-review.
**Alternatives rejected:**
- `model=sonnet` for Round 2: More expensive with no clear benefit for a scoped re-review of changes.

#### Decision 4: business-executing Step 3/4 rewrite
**Chose:** Remove "Ready for feedback" and simplify the feedback loop
**Why:** The autonomous mode explicitly says "execute all tasks without pausing for review between batches." Keeping "Ready for feedback" contradicts the autonomous mode. The executing-plans counterpart has the same pattern: autonomous mode with no inter-batch pauses.
**Alternatives rejected:**
- Keep feedback loop alongside autonomous mode: Contradictory instructions. The agent would either follow autonomous mode (skip feedback) or follow the feedback prompt (pause). Ambiguity leads to inconsistent behavior.

#### Decision 5: business-diagnosis description field
**Chose:** Keep the existing frontmatter description unchanged
**Why:** The description focuses on when to use the skill ("when a business problem isn't resolving"), which remains accurate. The systematic-debugging counterpart includes "Supports low (default) and high severity" in its description, but that's implementation detail that makes the description less scannable. Users learn about severity from the skill content itself. This is an intentional divergence from the software counterpart's description pattern — the trade-off favors scannability over counterpart consistency.
**Alternatives rejected:**
- Add severity mention: Would make the description longer without improving discoverability. The `/aligned:business-diagnosis high` syntax is documented inside the skill.

#### Decision 6: Critic model — business-write-plan vs business-brainstorming
**Chose:** `model=sonnet` for business-write-plan critics (Round 1)
**Why:** Each business skill aligns with its own software counterpart. `writing-plans` uses `model=sonnet` for both critics; `brainstorming` uses `model=opus`. business-write-plan follows writing-plans → sonnet. business-brainstorming follows brainstorming → opus. The cross-skill asymmetry (sonnet vs opus) mirrors the asymmetry in the software counterparts. Aligning to opus for both would diverge from the writing-plans counterpart pattern, and critique quality at sonnet is sufficient for plan review (plans contain fewer codebase-specific facts than designs).
**Alternatives rejected:**
- `model=opus` to match business-brainstorming: Would diverge from the writing-plans counterpart. The sync goal is to align each business skill with its own software counterpart, not to harmonize across business skills.
