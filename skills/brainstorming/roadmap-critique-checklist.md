# Roadmap Spawn-List Critique Checklist

You are reviewing a spawn-list produced by Roadmap mode — a paste-ready queue of 3–6 brainstorming prompts that decompose a larger outcome into single-session brainstorms.

This checklist is **inline self-review**, not a sub-agent critique panel. The Roadmap mode reads this file at the end of its process and answers the two questions below against the spawn-list it just authored. No advisor panel, no fact-checking pipeline, no aggregation step.

## Instructions

1. Read the spawn-list document and the schema at `references/spawn-brief-template.md`.
2. For each criterion below, evaluate the spawn-list. Report each issue with severity (high / medium / low) and evidence (quoted line, missing field, or specific gap).
3. If an issue is found, fix it inline (re-confirming with the user as needed) before committing.

**Severity guide:**
- **high** — will break the next brainstorm's routing OR omit a required step toward the outcome
- **medium** — will cause rework or confusion when the next brainstorm runs
- **low** — cosmetic

## Critique Criteria

### 1. Spawn-brief paste-readiness

For each component:

- Are all 5 schema fields present and substantive (no `TBD`, no one-word placeholders)?
- Does the spawn-brief paragraph contain mode-disambiguating verbs ("design...", "compare...", "write...", "synthesize...") so the next brainstorm auto-routes to the declared target mode?
- Could the paragraph be pasted verbatim into a fresh `/aligned:brainstorming` session and produce a useful brainstorm without further clarification? It must carry the population, constraints, prior art, and deliverable shape.
- Are prerequisites cited by component title, not vague pointers?

- BAD: "Prerequisites: after research is done. Spawn brief: build the dashboard thing." — no component reference, no population, no constraints, no mode-disambiguating verb.
- GOOD: "Prerequisites: Component #2 (Research synthesis). Spawn brief: Design a dashboard for SMB sales reps that surfaces the top three insights from the Research synthesis design doc at `docs/plans/YYYY-MM-DD-foo-research.md`. Must work for screen sizes ≥1024px and integrate with the existing CRM data layer. Deliverable: design doc with component sketches and data flow."

### 2. Decomposition fit

- Do the 3–6 components, run in declared order, plausibly compose the stated outcome?
- Are any components themselves too large for a single brainstorm? (If a spawn brief implies multiple sub-projects, the component needs further decomposition before this spawn-list is shippable.)
- Are there obvious missing steps that would block the outcome? (e.g., outcome is "ship a research-grounded blog post" but the spawn-list has no research step, jumping straight to authoring.)
- Is the count in the 3–6 range? Fewer suggests the work didn't need decomposition (route to a single brainstorm instead); more suggests the orchestration is becoming a bottleneck and components should be combined or the outcome scoped down.

- BAD: Outcome is "ship a prospect-specific sales deck" — spawn-list has one component titled "write the deck" with no research, no insights, no review step.
- GOOD: Components flow Research synthesis → Insights authoring → Deck authoring, each brainstorm-sized, prerequisites cited by component title.

## Critique Output Format

If issues are found:

```markdown
# Spawn-List Self-Review: {topic}

**File:** `docs/plans/YYYY-MM-DD-<topic>-spawn-list.md`

## Issues

### 1. {Issue title} (high/medium/low)
**Criterion:** {1 or 2}
**Problem:** {What's wrong}
**Evidence:** {Quoted line / missing field / specific gap}
**Fix:** {What to change}

### 2. ...
```

If no issues:

```markdown
# Spawn-List Self-Review: {topic}

**File:** `docs/plans/YYYY-MM-DD-<topic>-spawn-list.md`

Pass — both criteria satisfied.
```

## Important

- This is inline self-review, not a sub-agent critique. Do not dispatch sub-agents from here.
- Report what IS wrong, not what MIGHT be wrong. Evidence required for every issue.
- Do NOT propose new components the user didn't decompose to. Flag missing steps that would block the outcome, but don't author them yourself — re-engage the user on Phase 2.
- Do NOT rewrite the spawn-list silently. Fix issues with the user in the loop.
