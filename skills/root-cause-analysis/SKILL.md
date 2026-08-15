---
name: root-cause-analysis
description: "Use when a business or process problem isn't resolving — a deliverable that isn't landing, a strategy not producing results, a process breakdown. Supports low (default) and high severity with multi-agent investigation. Code bugs and test failures are out of scope; use a dev-workflow plugin such as superpowers (systematic-debugging)."
---

# Root Cause Analysis

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/root-cause-analysis/`. See `skills/_shared/resolve-skill-path.md` for rationale.

## Overview

Random fixes waste time and create new problems. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes or solutions. Symptom treatment is failure.

**Violating the letter of this process is violating the spirit of diagnosis.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes or solutions.

## When to Use

Use for ANY business or process issue that isn't resolving:

**Code bugs, test failures, and build breakage are out of scope.** If the
superpowers plugin is installed, use `superpowers:systematic-debugging`
for those; otherwise install a dev-workflow plugin.

- Deliverable isn't landing with the audience
- Strategy not producing results
- Process inefficiency or breakdown
- Client relationship friction
- Revenue/pipeline problems
- A document or proposal that keeps getting rejected

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple problems have root causes too)
- You're in a hurry (rushing guarantees rework)
- Someone wants it fixed NOW (systematic is faster than thrashing)

## Severity Levels

Default severity is **low** (current single-agent behavior). Pass `high` as an argument for multi-agent fan-out investigation.

- `/aligned:root-cause-analysis` — low severity (default)
- `/aligned:root-cause-analysis high` — high severity, multi-agent

### High Severity — Phase 0: Multi-Agent Investigation

Added before the existing four phases. Use when low-severity investigation is insufficient.

**Step 1:** Read the project's context documents (e.g., positioning, strategy, or process docs) if they exist, so all agents share structural context.

**Step 2:** Fan out 5-6 subagents via Task tool, each with a different analytical method:

| Agent | Method | Prompt Directive |
|-------|--------|-----------------|
| Backward Tracer | Trace from symptom upstream | "Start at the problem. Follow the chain backward. Find where the breakdown originates." |
| Change Tracer | Trace from recent changes forward | "List what changed recently — messaging, process, people, pricing, market conditions. For each change, trace its effects forward through the system." |
| Stakeholder Mapper | Map the human system | "Map the human system around this problem. Who benefits from the status quo? Who has veto power? Identify all affected parties, their incentives, and blind spots." |
| Information Flow Analyst | Follow information across boundaries | "Map what enters and exits each stage boundary — strategy, messaging, deliverables, execution. Identify where information gets distorted or lost in a handoff." |
| Pattern Matcher | Compare against successes | "Find similar past efforts that succeeded. List every difference from the failing case." |
| JudgeAgent | Challenge all conclusions | "Read the other agents' reports. For each proposed root cause, try to disprove it." |

**Step 3:** First 4-5 agents run in parallel. Each returns: hypothesis, evidence, confidence level.

**Step 4:** JudgeAgent runs second, receiving all reports. Challenges each hypothesis, identifies agreements and contradictions.

**Step 5:** Main thread synthesizes. If consensus → proceed to Phase 1 with strong starting hypothesis. If no consensus → present competing theories to user.

### When to Use High Severity

- Previous low-severity investigation didn't find root cause (clearest signal)
- Problem crosses organizational boundaries or involves 3+ teams, functions, or process stages
- Same symptom appears in multiple unrelated areas (suggests shared root cause)
- Issue affects strategy, not just a single deliverable
- Recurring problems that have resisted 2+ prior fix attempts

**Examples:** A proposal that keeps getting rejected across different clients → high (systemic messaging problem). One email that got no replies → low. Churn rising in two unrelated customer segments at once → high (shared root cause). A demo that fell flat once → low; falling flat three times after two script rewrites → escalate to high.

## The Five Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix or solution:**

1. **Read the Signals Carefully**
   - Don't skip past complaints, objections, or feedback
   - They often contain the exact answer
   - Collect concrete examples — the actual rejection email, the exact meeting moment, the specific metric — not vague impressions

2. **Define the Gap**
   - What was expected to happen?
   - What is actually happening?
   - How big is the gap?
   - Is this a gap in correctness, performance, reliability, direction, scope, or understanding?

3. **Reproduce Consistently**
   - Can you trigger it reliably?
   - What are the exact conditions?
   - If not reproducible → gather more data, don't guess

4. **Check What Changed**
   - What changed that could cause this?
   - New information, changed requirements, shifted context, market changes, new people, revised messaging
   - Assumptions that turned out to be wrong?

5. **Gather Evidence in Multi-Layer Systems**

   **WHEN the problem spans multiple layers:**

   For EACH layer boundary:
   - What enters this layer?
   - What exits this layer?
   - Is this layer doing its job correctly?

   Example — Strategy → Messaging → Deliverables → Execution:
   ```
   Layer 1: Strategy - Is the overall approach right?
   Layer 2: Messaging - Are we communicating the right value?
   Layer 3: Deliverables - Do the documents support the message?
   Layer 4: Execution - Are deliverables reaching the right people at the right time?
   ```

   **This reveals:** Which layer is actually failing.

6. **Consult Context Docs (cross-boundary problems only)**
   - **When:** The problem crosses layer or organizational boundaries. Skip for single-layer issues.
   - If the project has context documentation (e.g., strategy, positioning, or process docs), read it before tracing
   - **Docs may be stale.** Always verify claims against current reality — the actual deliverables, the actual process as practiced.
   - If you find a discrepancy, file a Kanban entry (see "Kanban Entry Format" below)

7. **Trace to the Source**

   **WHEN the problem is deep in the chain:**

   - Where does the wrong outcome originate?
   - What decision, handoff, or input upstream fed this?
   - Keep tracing up until you find the source
   - Fix at source, not at symptom

### Phase 2: Pattern Analysis

**Find the pattern before fixing:**

1. **Find Working Examples**
   - Locate successful past efforts similar to what's failing
   - The proposal that won, the launch that landed, the process that ran smoothly

2. **Compare Against References**
   - If following a known playbook or framework, read the reference COMPLETELY
   - Don't skim — read every step, analyze thoroughly
   - Understand the pattern fully before applying

3. **Identify Differences**
   - What's different between the success and the failure?
   - List every difference, however small — audience, timing, channel, messenger, format
   - Don't assume "that can't matter"

4. **Understand Dependencies**
   - What other people, resources, or conditions does this need?
   - What context, timing, or buy-in?
   - What assumptions does it make?

### Phase 3: Hypothesis and Testing

**Scientific method:**

1. **Form Single Hypothesis**
   - State clearly: "I think X is the root cause because Y"
   - Write it down
   - Be specific, not vague

2. **Test Minimally**
   - Make the SMALLEST possible change to test hypothesis
   - One variable at a time
   - Don't fix multiple things at once

3. **Verify Before Continuing**
   - Did it work? Yes → Phase 4
   - Didn't work? Form NEW hypothesis
   - DON'T add more fixes on top

4. **When You Don't Know**
   - Say "I don't understand X"
   - Don't pretend to know
   - Ask for help
   - Research more

### Phase 4: Implementation

**Fix the root cause, not the symptom:**

1. **Define Success Criteria**
   - What specifically needs to be true for this to be resolved?
   - Make it measurable — a reply rate, a signed contract, a process step that stops slipping
   - MUST have before fixing

2. **Implement Single Fix**
   - Address the root cause identified
   - ONE change at a time
   - No "while I'm here" improvements
   - No bundled restructuring or scope expansion

3. **Verify Fix**
   - Success criteria met? Any unintended consequences?
   - If yes → proceed to Phase 5 (Post-Fix Review)

4. **If Fix Doesn't Work**
   - STOP
   - Count: How many fixes have you tried?
   - If < 3: Return to Phase 1, re-analyze with new information
   - **If ≥ 3: STOP and question the strategy (step 5 below)**
   - DON'T attempt Fix #4 without fundamental discussion

5. **If 3+ Fixes Failed: Question Fundamentals**

   **Pattern indicating a strategic or structural problem:**
   - Each fix reveals new issues in different areas
   - Fixes require massive restructuring to implement
   - Each fix creates new problems elsewhere

   **STOP and question fundamentals:**
   - Is this strategy or process fundamentally sound?
   - Are we "sticking with it through sheer inertia"?
   - Should we reframe the strategy or redesign the process?

   **Discuss with your human partner before attempting more fixes.**

   This is NOT a failed hypothesis — this is a wrong foundation.

### ⛔ STOP — Phase 5 Gate

**Before writing ANY summary or claiming work is done, you MUST complete Phase 5 below.** Phase 5 requires dispatching a sub-agent — a manual summary is NOT a substitute. If you are about to write a completion summary without having dispatched the Phase 5 sub-agent, you are skipping the process. Stop and read the instructions below.

### Phase 5: Post-Fix Review (Sub-Agent Required)

**Mandatory after Phase 4 confirms the fix works.** Dispatch a review sub-agent to catch issues that tunnel vision during investigation misses — blast radius, symptom fixes masquerading as root cause fixes, and missing safeguards.

**Before dispatching, gather two inputs:**

1. **Root cause statement:** The hypothesis confirmed in Phase 3 (e.g., "The root cause is X because Y"). If you didn't write this down explicitly, reconstruct it now — the reviewer needs it.
2. **Record of all changes:** If the fix changed files, run `git diff` (or `git diff HEAD~N` if commits were made) to capture everything changed during the session. If the fix is a process or strategy change not captured in files, write a concrete summary of what changed.

**Dispatch** a sub-agent via Task tool (`subagent_type=general-purpose`, `model=sonnet`) using the prompt template in `{base-directory}/post-fix-review-prompt.md`. Read the template, substitute `{root-cause-statement}` and `{changes}`, and pass the result as the sub-agent's prompt.

**Gate:**
- If any criterion is FAIL → address the findings, then re-run Phase 5
- If all PASS or FLAG → note any FLAGs, then proceed to the Lessons-Learned Gate

## Lessons-Learned Gate

BEFORE completing this skill's process:
  IF 3+ fixes failed and fundamental questioning was triggered:
    Write a lesson to docs/lessons-learned/YYYY-MM-DD-short-description.md
    using the lesson template (see kickstart scaffold docs).

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Change several things at once, see what sticks"
- "Skip the evidence, I know what's wrong"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing the cause
- **Each fix reveals new problem in different place**
- **"One more attempt" (when already tried 2+)**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the fundamentals (see Phase 4, step 5)

## Your Human Partner's Signals You're Doing It Wrong

**Watch for these redirections:**
- "Is that not happening?" — You assumed without verifying
- "Will it show us...?" — You should have added evidence gathering
- "Stop guessing" — You're proposing fixes without understanding
- "Ultrathink this" — Question fundamentals, not just symptoms
- "We're stuck?" (frustrated) — Your approach isn't working
- They keep saying "but why?" — You haven't gone deep enough
- "We tried that already" — You didn't check history

**When you see these:** STOP. Return to Phase 1.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple problems. |
| "Emergency, no time for process" | Systematic diagnosis is FASTER than guess-and-check thrashing. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = fundamental problem. Question the approach, don't fix again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **0. Multi-Agent** (high only) | Fan out subagents, synthesize | Consensus hypothesis or competing theories |
| **1. Root Cause** | Read signals, define gap, check changes, gather evidence | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare | Identify differences |
| **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
| **4. Implementation** | Define success criteria, fix, verify | Problem resolved, verified |
| **5. Post-Fix Review** | Sub-agent reviews changes for blast radius, root cause consistency, completeness | All criteria PASS or FLAG |

## When Process Reveals No Root Cause

If systematic investigation reveals the issue is truly external, timing-dependent, or outside your control:

1. You've completed the process
2. Document what you investigated and what was ruled out
3. Implement appropriate handling (a contingency, a follow-up cadence, or a recommendation)
4. Set up tracking so future occurrences produce better evidence

**But:** 95% of "no root cause" cases are incomplete investigation.

## Kanban Entry Format

When filing a Kanban entry, read `{base-directory}/../_shared/kanban-entry-format.md` for the template and counter instructions. Use `root-cause-analysis` as the "Discovered during" value.

## Related References

**Read when relevant:**
- Read **`skills/_shared/verification-checklist.md`** — Verify fix worked before claiming success

## Real-World Impact

From diagnosis sessions:
- Systematic approach: 15-30 minutes to resolution
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New problems introduced: Near zero vs common
