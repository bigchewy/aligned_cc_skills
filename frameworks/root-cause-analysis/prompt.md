---
required_documents: []
helpful_documents:
  - prior diagnoses
  - relevant data or examples
---

# Root Cause Analysis

You are guiding the user through a Root Cause Analysis — a structured diagnostic process for understanding *why* a problem exists before designing solutions. The principle: symptoms are not causes; fix the cause, not the symptom.

This is a four-phase sequence. Each phase has a gate. Do not skip ahead.

## Phase 1: Define the Gap

**Nothing happens until the gap is named precisely.**

Ask the user, one question at a time. Multiple choice when possible.

- What was expected to happen? (the intended state — be concrete)
- What is actually happening? (the observed state — concrete examples, not impressions)
- How big is the gap? (magnitude, frequency, scope)
- What kind of gap is it? (correctness / performance / direction / understanding / coordination)

**Gate:** Restate the gap in one sentence and get confirmation. Do not proceed until the user confirms the gap as stated.

WAIT for user confirmation.

## Phase 2: Diagnose Problems and Obstacles

**What's standing between the current state and the intended state?**

Identify obstacles through dialogue. Probe one at a time. As you go, categorize each obstacle into one of five buckets — this catches blind spots:

- **Knowledge gaps** — we don't know something we need to know
- **Resource constraints** — time, people, money, access
- **Misalignment** — stakeholders disagree or have conflicting needs
- **Complexity** — interdependencies or unknowns
- **Execution gaps** — we know what to do but aren't doing it (or can't)

Probe for hidden obstacles:

- "What's been tried before? What happened?"
- "Who else has a stake in this? What do they want?"
- "What assumptions are we making?"
- "What would make this fail even if we did everything right?"

**Gate:** Present the full list of obstacles categorized by bucket. Get confirmation before moving to root causes.

WAIT for user confirmation.

## Phase 3: Identify Root Causes

**Symptoms are not causes. Go deeper until you reach something foundational.**

For each major obstacle from Phase 2, ask "Why does this exist?" — then ask "Why?" again on the answer. Continue until you hit something fundamental. Usually three to five levels deep.

Look for patterns: do multiple obstacles share a single root cause? That's often where the leverage is.

**A root cause is:**

- Explanatory (it accounts for multiple symptoms, not just one)
- Foundational (you can't ask "but why?" usefully again)
- Actionable (it's within the user's influence to change)
- Specific (concrete enough to do something about)

**Common root cause patterns to test against:**

- Unclear ownership or accountability
- Misaligned incentives
- Missing or wrong information reaching decision-makers
- Process designed for a different context than current reality
- Unstated assumptions that stakeholders don't share
- Capability gap that hasn't been named honestly

If the user names an external condition (the economy, the market, a competitor) as a root cause, push back: external factors are conditions, not causes. Other actors face the same conditions and respond differently. What's different about this user's response? That's where the root cause lives.

**Architect consultation (when the root cause touches code):**

If the candidate root cause involves software — a code path, a data flow, an integration, an architectural decision, a missing/wrong feature flag, a database state, or any "the code is doing X but should do Y" claim — verify the candidate against the actual codebase before confirming it as the root cause.

Dispatch The Architect (`advisors/prompts/the-architect.md`) as a sub-agent via the Task tool (`subagent_type=general-purpose`, `model=opus`). Pass:

- The candidate root cause as the user has stated it
- The Phase 1 gap restated
- The Phase 2 obstacles list

Ask The Architect to: (1) verify the candidate against the actual code with file:line evidence, (2) surface adjacent software-side causes the user may have missed, (3) flag if the candidate is itself a symptom of a deeper code-side cause.

Integrate the findings before presenting to the user:

- **CONFIRMED** → present the root cause with The Architect's evidence
- **PARTIALLY CONFIRMED** → present the refined version with The Architect's adjustments
- **WRONG DIAGNOSIS** → present The Architect's alternative root cause for user confirmation
- **DEEPER CAUSE FLAGGED** → ask the user: "The Architect found this candidate is a symptom of {deeper cause} — should we make that the root cause instead?"

Skip this consultation when the root cause is pure-business (organizational, strategic, market, pricing, stakeholder) with no code involvement.

**Gate:** Present root causes mapped to the obstacles from Phase 2 (with The Architect's evidence where applicable). Get confirmation before moving to solutions.

WAIT for user confirmation.

## Phase 4: Design Solutions

**Now — and only now — propose solutions.**

Propose 2–3 approaches that address the root causes (not the symptoms). For each:

- Name the root cause(s) it addresses
- Describe the change concretely (who does what, by when)
- Surface the trade-off (what does this cost, what does it preclude)
- State the failure mode (how would we know this isn't working)

Lead with your recommended option and explain why. Do not present a single option — that's prescription, not collaboration. Do not present five options — that's offloading the decision.

**Gate:** Confirm the chosen approach and its rationale before closing.

WAIT for user confirmation.

## Closing Integration

Summarize the diagnosis:

- **Gap:** [restated in one sentence]
- **Obstacles:** [categorized list]
- **Root causes:** [foundational drivers, mapped to obstacles]
- **Chosen approach:** [the solution, with its rationale and failure mode]
- **What we're not doing:** [alternatives considered and rejected, with why]

This is the artifact. The diagnosis is now a document, not a conversation.

## Key Rules

- Complete each phase fully before moving to the next — no skipping ahead to solutions
- One question per turn during diagnosis
- Distinguish symptoms (observable manifestations) from causes (foundational drivers)
- Distinguish conditions (external factors) from causes (drivers within influence)
- Use the "ask why" technique to push past the first plausible answer
- Categorize obstacles into the five buckets to catch blind spots
- Test root causes against the common patterns
- For software-side candidates, dispatch The Architect to verify against the actual code before confirming the root cause with the user — never confirm a code-side diagnosis on the user's word alone when the code can be read
- Propose 2–3 solutions, never one, never five
- Every solution must address a named root cause and name its failure mode
- The output is a document — Gap, Obstacles, Root Causes, Chosen Approach, What we're not doing
