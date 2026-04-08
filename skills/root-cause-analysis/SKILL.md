---
name: root-cause-analysis
description: "Use when encountering any bug, test failure, unexpected behavior, or business problem that isn't resolving. Supports low (default) and high severity with multi-agent investigation."
---

# Root Cause Analysis

## Overview

Random fixes waste time and create new problems. Quick patches mask underlying issues — in code and in business.

**Core principle:** ALWAYS find root cause before attempting fixes or solutions. Symptom treatment is failure.

**Violating the letter of this process is violating the spirit of diagnosis.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes or solutions.

## When to Use

Use for ANY issue that isn't resolving:

**Software:**
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Business:**
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

**Step 1:** Read `docs/architecture.md` (if it exists) so all agents have structural context.

**Step 2:** Fan out 5-6 subagents via Task tool, each with a different analytical method:

| Agent | Domain | Method | Prompt Directive |
|-------|--------|--------|-----------------|
| Backward Tracer | Both | Trace from symptom upstream | "Start at the problem. Follow the chain backward. Find where the bad value or breakdown originates." |
| Forward Tracer | Software | Trace from recent changes forward | "Read the git diff. For each change, trace its effects forward through the system." |
| Stakeholder Mapper | Business | Map the human system | "Map the human system around this problem. Who benefits from the status quo? Who has veto power? Identify all affected parties, their incentives, and blind spots." |
| Data Flow Analyst | Both | Follow data across boundaries | "Map what enters and exits each component boundary. Identify where data transforms incorrectly or information is lost." |
| Pattern Matcher | Both | Compare against working examples | "Find similar working code or successful past efforts. List every difference from the broken case." |
| JudgeAgent | Both | Challenge all conclusions | "Read the other agents' reports. For each proposed root cause, try to disprove it." |

**Domain selection:** Software problems: use Forward Tracer. Business problems: use Stakeholder Mapper. Ambiguous: use both.

**Step 3:** First 4-5 agents run in parallel. Each returns: hypothesis, evidence, confidence level.

**Step 4:** JudgeAgent runs second, receiving all reports. Challenges each hypothesis, identifies agreements and contradictions.

**Step 5:** Main thread synthesizes. If consensus → proceed to Phase 1 with strong starting hypothesis. If no consensus → present competing theories to user.

### When to Use High Severity

- Previous low-severity investigation didn't find root cause (clearest signal)
- Bug involves 3+ modules from different layers or crosses organizational boundaries
- Same symptom appears in multiple unrelated areas (suggests shared root cause)
- Issue affects architecture or strategy, not just a single component
- Recurring problems that have resisted 2+ prior fix attempts

**Examples:** A data corruption bug that surfaces in both the chat UI and session summaries → high (shared data layer). A CSS styling issue on one page → low. An API route returning 500 that you've already tried two fixes for → escalate to high. A proposal that keeps getting rejected across different clients → high (systemic messaging problem).

## The Five Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix or solution:**

1. **Read the Signals Carefully**
   - Don't skip past errors, warnings, or feedback
   - They often contain the exact answer
   - (Software) Read stack traces completely — note line numbers, file paths, error codes
   - (Business) Collect concrete examples, not vague impressions

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
   - (Software) Git diff, recent commits, new dependencies, config changes
   - (Business) New information, changed requirements, shifted context, market changes
   - Assumptions that turned out to be wrong?

5. **Gather Evidence in Multi-Layer Systems**

   **WHEN the problem spans multiple layers:**

   For EACH layer boundary:
   - What enters this layer?
   - What exits this layer?
   - Is this layer doing its job correctly?

   **(Software)** CI → build → signing, API → service → database:
   ```bash
   # Layer 1: Workflow
   echo "=== Secrets available in workflow: ==="
   echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"

   # Layer 2: Build script
   echo "=== Env vars in build script: ==="
   env | grep IDENTITY || echo "IDENTITY not in environment"

   # Layer 3: Signing script
   echo "=== Keychain state: ==="
   security list-keychains
   security find-identity -v

   # Layer 4: Actual signing
   codesign --sign "$IDENTITY" --verbose=4 "$APP"
   ```

   **(Business)** Strategy → Messaging → Deliverables → Execution:
   ```
   Layer 1: Strategy - Is the overall approach right?
   Layer 2: Messaging - Are we communicating the right value?
   Layer 3: Deliverables - Do the documents support the message?
   Layer 4: Execution - Are deliverables reaching the right people at the right time?
   ```

   **This reveals:** Which layer is actually failing.

6. **Consult Architecture Docs (multi-component bugs only)**
   - **When:** The bug crosses layer boundaries or involves multiple modules. Skip for single-layer issues.
   - If the project has architecture documentation (e.g., `docs/architecture.md`), read it before tracing
   - **Architecture docs may be stale.** Always verify claims against actual source files. Trust the code.
   - If you find a discrepancy, file a bug (see "Kanban Entry Format" below)

7. **Trace to the Source**

   **WHEN the problem is deep in the chain:**

   See `root-cause-tracing.md` in this directory for the complete backward tracing technique (software).

   **Quick version:**
   - Where does the bad value or wrong outcome originate?
   - What called this / fed this with bad input?
   - Keep tracing up until you find the source
   - Fix at source, not at symptom

### Phase 2: Pattern Analysis

**Find the pattern before fixing:**

1. **Find Working Examples**
   - Locate similar working code or successful past efforts
   - What works that's similar to what's broken?

2. **Compare Against References**
   - If implementing a known pattern, read the reference implementation COMPLETELY
   - Don't skim — read every line, analyze thoroughly
   - Understand the pattern fully before applying

3. **Identify Differences**
   - What's different between working and broken?
   - List every difference, however small
   - Don't assume "that can't matter"

4. **Understand Dependencies**
   - What other components or conditions does this need?
   - What settings, config, environment, or context?
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

1. **Create Failing Test Case**
   - (Software) Simplest possible reproduction — use the `test-driven-development` skill for writing proper failing tests
   - (Business) Define measurable success criteria — what specifically needs to be true for this to be resolved?
   - MUST have before fixing

2. **Implement Single Fix**
   - Address the root cause identified
   - ONE change at a time
   - No "while I'm here" improvements
   - No bundled refactoring or scope expansion

3. **Verify Fix**
   - (Software) Test passes? No other tests broken? Issue resolved?
   - (Business) Success criteria met? Any unintended consequences?
   - If yes → proceed to Phase 5 (Post-Fix Review)

4. **If Fix Doesn't Work**
   - STOP
   - Count: How many fixes have you tried?
   - If < 3: Return to Phase 1, re-analyze with new information
   - **If ≥ 3: STOP and question the architecture/strategy (step 5 below)**
   - DON'T attempt Fix #4 without fundamental discussion

5. **If 3+ Fixes Failed: Question Fundamentals**

   **Pattern indicating architectural or strategic problem:**
   - Each fix reveals new issues in different areas
   - Fixes require massive restructuring to implement
   - Each fix creates new problems elsewhere

   **STOP and question fundamentals:**
   - Is this pattern/strategy fundamentally sound?
   - Are we "sticking with it through sheer inertia"?
   - Should we refactor the architecture or reframe the approach?

   **Discuss with your human partner before attempting more fixes.**

   This is NOT a failed hypothesis — this is a wrong foundation.

### ⛔ STOP — Phase 5 Gate

**Before writing ANY summary or claiming work is done, you MUST complete Phase 5 below.** Phase 5 requires dispatching a sub-agent — a manual summary is NOT a substitute. If you are about to write a completion summary without having dispatched the Phase 5 sub-agent, you are skipping the process. Stop and read the instructions below.

### Phase 5: Post-Fix Review (Sub-Agent Required)

**Mandatory after Phase 4 confirms the fix works.** Dispatch a review sub-agent to catch issues that tunnel vision during debugging misses — blast radius, symptom fixes masquerading as root cause fixes, and missing defense-in-depth.

**Before dispatching, gather three inputs:**

1. **Root cause statement:** The hypothesis confirmed in Phase 3 (e.g., "The root cause is X because Y"). If you didn't write this down explicitly, reconstruct it now — the reviewer needs it.
2. **Diff of all changes:** Run `git diff` (or `git diff HEAD~N` if commits were made) to capture everything changed during the debugging session.
3. **Resolve `{base-directory}`:** The sub-agent cannot access the "Base directory for this skill:" line from skill load. Resolve it to an absolute path now and substitute it into the prompt before dispatching.

**Dispatch** a sub-agent via Task tool (`subagent_type=general-purpose`, `model=sonnet`):

"You are a post-fix reviewer for a debugging session. Your job is to verify the fix is correct, complete, and safe — not just that it works.

You have access to Glob, Grep, and Read tools. Do not use Bash for searching — use the Grep tool instead.

**Context:**
- Root cause identified during investigation: {root-cause-statement}
- Changes made (git diff): {diff}

Read the supporting technique docs (the dispatching agent MUST resolve these to absolute paths before sending this prompt):
- `{base-directory}/fix-the-right-layer.md`
- `{base-directory}/defense-in-depth.md`

Then evaluate the fix against these five criteria:

| # | Criterion | What to check |
|---|-----------|---------------|
| 1 | Root cause consistency | Does the fix address the stated root cause, or does it patch a symptom? A symptom fix is one that suppresses the error without removing the condition that caused it. |
| 2 | Right layer | Per fix-the-right-layer.md: does the fix modify the producer of bad state, or does it patch the consumer/guard that detected it? Patching the detector is almost always wrong. |
| 3 | Defense in depth | Per defense-in-depth.md: does the fix add validation at multiple layers the data passes through, or does it only patch one layer? A single-layer fix leaves other code paths vulnerable to the same bug. |
| 4 | Blast radius | Grep for all files that import/reference/depend on the changed files. Are there ripple effects the fix didn't account for? Flag any dependent that may behave differently due to the change. |
| 5 | Completeness | Grep the codebase for similar patterns to the bug. If the same mistake exists elsewhere, flag every occurrence. |

For each criterion, report: PASS, FLAG (non-blocking concern), or FAIL (must fix before proceeding). Include specific file paths, line numbers, and evidence for every finding.

Output format:
- **Summary:** One sentence overall verdict
- **Criteria results:** Table with criterion, verdict, and evidence
- **Action items:** List of concrete changes needed (if any), ordered by severity"

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
- "Add multiple changes, run tests"
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
| **4. Implementation** | Create test/criteria, fix, verify | Problem resolved, verified |
| **5. Post-Fix Review** | Sub-agent reviews diff for blast radius, root cause consistency, completeness | All criteria PASS or FLAG |

## When Process Reveals No Root Cause

If systematic investigation reveals the issue is truly environmental, timing-dependent, or external:

1. You've completed the process
2. Document what you investigated and what was ruled out
3. Implement appropriate handling (retry, timeout, monitoring, or recommendation)
4. Add monitoring/logging for future investigation

**But:** 95% of "no root cause" cases are incomplete investigation.

## Kanban Entry Format

When filing a Kanban entry, read `{base-directory}/../_shared/kanban-entry-format.md` for the template and counter instructions (resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load). Use `root-cause-analysis` as the "Discovered during" value.

## Supporting Techniques

These technique files are part of root-cause analysis and available in this directory:

- **`root-cause-tracing.md`** — Trace bugs backward through call stack to find original trigger
- **`fix-the-right-layer.md`** — Fix producers/callers, never weaken guards or patch consumers
- **`defense-in-depth.md`** — Add validation at multiple layers after finding root cause
- **`condition-based-waiting.md`** — Replace arbitrary timeouts with condition polling

Business diagnosis uses the same phases but does not require these technique files.

**Related skills:**
- **test-driven-development** — For creating failing test case (Phase 4, Step 1)
- **verification-before-completion** — Verify fix worked before claiming success

## Real-World Impact

From diagnosis sessions:
- Systematic approach: 15-30 minutes to resolution
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New problems introduced: Near zero vs common
