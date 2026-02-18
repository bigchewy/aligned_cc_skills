---
name: business-diagnosis
description: "Use when a business problem isn't resolving, a deliverable isn't landing, or a strategy isn't working - before proposing solutions"
---

# Systematic Business Diagnosis

## Overview

Random solutions waste effort and mask real problems. Quick fixes to business issues create new problems elsewhere.

**Core principle:** ALWAYS find root cause before proposing solutions. Treating symptoms is failure.

**Violating the letter of this process is violating the spirit of diagnosis.**

## The Iron Law

```
NO SOLUTIONS WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose solutions.

## When to Use

Use for ANY business issue:
- Deliverable isn't landing with the audience
- Client relationship friction
- Process inefficiency or breakdown
- Strategy not producing results
- Revenue/pipeline problems
- Team or operational issues
- A document or proposal that keeps getting rejected or revised

**Use this ESPECIALLY when:**
- Under pressure to "just fix it"
- The obvious solution seems clear
- Multiple attempts haven't resolved it
- Previous solution didn't work
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

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE proposing ANY solution:**

1. **Gather Evidence**
   - What specifically isn't working? (Not vague - concrete examples)
   - What feedback exists? (Client comments, data, meeting notes)
   - What does "working" look like? (Define the gap precisely)
   - Collect actual data, not assumptions

2. **Define the Gap**
   - What was expected to happen?
   - What is actually happening?
   - How big is the gap?
   - Is this a gap in quality, direction, scope, or understanding?

3. **Check What Changed**
   - What's different from when this was working (or from the plan)?
   - New information, changed requirements, shifted context?
   - Environmental changes (market, client situation, team)?
   - Assumptions that turned out to be wrong?

4. **Trace the Cause**

   **WHEN the problem spans multiple layers (strategy > messaging > deliverable > execution):**

   For EACH layer:
   - Is the input to this layer sound?
   - Is this layer doing its job correctly?
   - Is the output reaching the next layer intact?

   **Example (client engagement not producing results):**
   ```
   Layer 1: Strategy - Is the overall approach right for this client?
   Layer 2: Messaging - Are we communicating the right value?
   Layer 3: Deliverables - Do the documents support the message?
   Layer 4: Execution - Are deliverables reaching the right people at the right time?
   ```

   **This reveals:** Which layer is actually failing (strategy is sound, messaging is off)

5. **Identify the Real Problem**
   - Where does the breakdown actually originate?
   - What's the root cause, not the symptom?
   - Trace upstream until you find the source
   - Fix at source, not at symptom

### Phase 2: Pattern Analysis

**Find the pattern before solving:**

1. **Find Comparable Successes**
   - What similar work has succeeded? (Same client, similar client, related domain)
   - What's different about the successes?
   - Check the project directory for prior work that landed well

2. **Compare Against What Works**
   - What specifically works in the successful examples?
   - Don't skim - analyze the successful example thoroughly
   - Understand the pattern fully before applying

3. **Identify Key Differences**
   - What's different between what's working and what's broken?
   - List every difference, however small
   - Don't assume "that can't matter"

4. **Understand Context Dependencies**
   - What conditions enabled the success?
   - What audience, timing, or relationship factors matter?
   - What assumptions does the current approach make?

### Phase 3: Hypothesis and Testing

**Scientific method, applied to business:**

1. **Form Single Hypothesis**
   - State clearly: "I think X is the root cause because Y"
   - Write it down
   - Be specific, not vague
   - Example: "The proposal isn't landing because it leads with our capabilities instead of their problem"

2. **Test Minimally**
   - Make the SMALLEST possible change to test the hypothesis
   - One variable at a time
   - Don't overhaul everything at once
   - Example: Rewrite just the executive summary to lead with their problem, see if reception changes

3. **Verify Before Continuing**
   - Did it work? Yes > Phase 4
   - Didn't work? Form NEW hypothesis
   - DON'T layer more changes on top

4. **When You Don't Know**
   - Say "I don't understand X"
   - Don't pretend to know
   - Ask for more context
   - Gather more evidence

### Phase 4: Implementation

**Fix the root cause, not the symptom:**

1. **Define Success Criteria**
   - What specifically needs to be true for this to be resolved?
   - How will we measure it?
   - Make it concrete and observable

2. **Implement Single Change**
   - Address the root cause identified
   - ONE change at a time
   - No "while we're at it" scope expansion
   - No bundled improvements

3. **Verify the Fix**
   - Does it meet success criteria?
   - Any unintended consequences?
   - Issue actually resolved?

4. **If Fix Doesn't Work**
   - STOP
   - Count: How many approaches have you tried?
   - If < 3: Return to Phase 1, re-analyze with new information
   - **If >= 3: STOP and question the strategy (step 5 below)**
   - DON'T attempt Approach #4 without strategic discussion

5. **If 3+ Approaches Failed: Question the Strategy**

   **Pattern indicating strategic problem:**
   - Each approach reveals new issues in different areas
   - Fixes require fundamentally rethinking the objective
   - Each fix creates new problems elsewhere

   **STOP and question fundamentals:**
   - Is this the right objective?
   - Are we solving the right problem?
   - Should we reframe the entire approach?

   **Discuss with the user before attempting more fixes.**

   This is NOT a failed hypothesis - this is a wrong strategy.

## Red Flags - STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Make multiple changes, see what sticks"
- "Skip the evidence, I know what's wrong"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Here are the main problems: [lists solutions without investigation]"
- Proposing solutions before tracing the cause
- **"One more attempt" (when already tried 2+)**
- **Each attempt reveals new problems in different areas**

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

| Excuse | Reality |
|--------|---------|
| "Issue is obvious, don't need process" | Obvious issues have root causes too. Process is fast for simple problems. |
| "Urgent, no time for process" | Systematic diagnosis is FASTER than solution-hopping. |
| "I see the problem, let me fix it" | Seeing symptoms does not equal understanding root cause. |
| "One more attempt" (after 2+ failures) | 3+ failures = strategic problem. Question the approach, don't try again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **0. Multi-Agent** (high only) | Fan out subagents, synthesize | Consensus hypothesis or competing theories |
| **1. Root Cause** | Gather evidence, define gap, check changes, trace cause | Understand WHAT and WHY |
| **2. Pattern** | Find successes, compare, identify differences | Know what works and why this doesn't |
| **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
| **4. Implementation** | Define criteria, single change, verify | Problem resolved, criteria met |

## When Process Reveals No Root Cause

If systematic investigation surfaces no clear root cause, consider these possibilities:

- **External/environmental factors:** Market shifts, competitor actions, regulatory changes that are outside the team's control
- **Timing issues:** The problem is intermittent or context-dependent — it only manifests under specific conditions (certain clients, certain times, certain workloads)
- **Third-party dependencies:** The root cause lies in a partner, vendor, or platform the team doesn't control

**Action:** Document what was investigated, what was ruled out, and what external factors are suspected. Recommend monitoring rather than fixing.

**But:** 95% of "no root cause" cases are incomplete investigation. Before concluding the cause is external, verify you have genuinely exhausted the 4-phase process.
