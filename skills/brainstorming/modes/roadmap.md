<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->

# Brainstorming Decomposition into a Spawn List

## Contents

- Overview
- Disambiguation rules
- The Process
- After Decomposition
- Out of scope
- Key Principles

## Overview

Roadmap mode is **pure orchestration scaffolding**. The user has an outcome that's too big for one `/aligned:brainstorming` session — a software overhaul with multiple components, a deck that needs research → insights → authoring, a multi-step build. Your job: produce a paste-ready queue of 3–6 brainstorming prompts that, run in order, compose the outcome.

The single deliverable is `docs/plans/YYYY-MM-DD-<topic>-spawn-list.md`. Each entry conforms to the 5-field schema in `{base-directory}/references/spawn-brief-template.md`. The spawn-brief paragraph from each entry is what the user pastes verbatim into a fresh `/aligned:brainstorming` session to start the next brainstorm.

Roadmap mode does **not** produce a strategic roadmap document, do quarterly planning, reconcile team capacity, or consult strategy advisors. It is decomposition + a paste-ready queue. Nothing more.

## Disambiguation rules

- **Roadmap vs Software:** Software is one brainstorm → one design doc → one plan. Roadmap is "this is too big for one brainstorm" → a list of 3–6 brainstorming prompts to run in order. If the user can describe what they want as a single design doc, route to Software.
- **Roadmap vs Authoring:** Authoring produces a single named document — including any *roadmap-shaped document* (quarterly plan, prioritization memo, portfolio doc for stakeholders). Roadmap mode produces a spawn-list, not a document. If the user wants a roadmap document for humans to read, that's Authoring with a roadmap-shaped framework. If the user wants a queue of brainstorms to run, that's Roadmap.
- **Mixed signals:** Look at what the user expects to do with the artifact. "I'll paste each entry into a new brainstorming session" = Roadmap. "I'll share this with my team / stakeholders" = Authoring.

## The Process

You MUST complete each phase before proceeding to the next. Ask one question at a time, multiple choice preferred where it fits.

### Phase 1: Outcome and why it needs decomposition

Establish two things:

- **Outcome:** What's the end-state, in one sentence? ("Ship a prospect-specific sales deck for Dispatch Track." "Land a multi-component refactor of the autopilot pipeline." "Produce a research-grounded blog post on RCA frameworks.")
- **Why too big for one brainstorm:** What makes this multi-step? Common shapes: research → synthesis → authoring; multi-component build with internal dependencies; design then validate then build.

That's the entire scoping pass. No advisor panels, no capacity envelope, no person-week math.

**Gate:** Restate the outcome and the reason it needs decomposition. Confirm.

### Phase 2: Decompose into 3–6 components

Propose a decomposition. For each component, list:

- **Title** — short, descriptive (e.g., "Research synthesis", "Schema redesign", "Migration plan")
- **Target brainstorming mode** — Software / Authoring / Research
- **One-sentence outcome** — what artifact comes out of that brainstorm

Aim for 3–6 components. Fewer and decomposition isn't earning its keep; more and the orchestration becomes the bottleneck. If a proposed component itself looks like multiple brainstorms wearing one name, decompose it further — every component must fit comfortably in a single brainstorming session.

Walk through the list with the user. Adjust, add, remove.

**Gate:** Present the component list (titles + target modes + one-sentence outcomes). Confirm.

### Phase 3: Dependencies and run order

For each component, identify prerequisites — other components in this list that must complete before this one is brainstorm-ready. Cite by component title, not vague pointers ("After Component #2 (Research synthesis)", not "after the research is done").

Most decompositions are mostly linear; not all are. If two components are independent, say so — that's useful when the user has time to run brainstorms in parallel.

**Gate:** Present the ordered list with dependencies. Confirm.

### Phase 4: Spawn briefs

For each component, write the spawn-brief block using the 5-field schema in `{base-directory}/references/spawn-brief-template.md`. **Reference the template; do not duplicate the schema here.** Every field must be substantive — no `TBD`, no one-word placeholders.

The spawn-brief paragraph (the `>` blockquote) is what gets pasted verbatim into a fresh `/aligned:brainstorming` invocation. It MUST contain mode-disambiguating verbs ("design...", "compare...", "write...", "synthesize...") so the brainstorming router auto-routes to the correct mode. A generic brief falls through to the always-ask 4-mode confirmation — not a failure, but a friction the spawn-list should be authored to avoid.

Quality bar: could a reader who has never seen this conversation paste the spawn-brief paragraph into a fresh `/aligned:brainstorming` and get a useful brainstorm started? If not, re-author it with the missing population, constraints, or deliverable shape.

Walk the user through each component. For each, present the populated 5-field block, ask if anything's missing, then move to the next.

**Gate:** Present the full spawn-list (all components with all 5 fields populated). Confirm ready to commit. Move to After Decomposition.

## After Decomposition

**Documentation (single artifact):**

Write `docs/plans/YYYY-MM-DD-<topic>-spawn-list.md`. Structure:

- Header: `**Outcome:**` (one sentence) and `**Why decomposed:**` (one sentence on what makes it multi-step)
- Body: one `## ` heading per component, in run order, each using the 5-field schema

No `roadmap.md` companion artifact. No mockups. No dependency-graph HTML. Markdown only.

**Lightweight critique pass:**

Read `{base-directory}/roadmap-critique-checklist.md` and answer its two questions against the spawn-list you just wrote. This is an inline self-review in the main context — no sub-agents, no advisor panels, no fact-checking pipeline. If the checklist surfaces issues, fix them and re-confirm with the user.

**Commit:**

Commit `docs/plans/YYYY-MM-DD-<topic>-spawn-list.md` to git.

**Next-step affordance:**

Output exactly one affordance:

> **Next:** Pick the first component with no remaining prerequisites and run `/aligned:brainstorming` against its spawn-brief paragraph. That brainstorm produces a design doc, which `/aligned:writing-plans` can turn into an implementation plan if the component is build-shaped. Repeat per component until the spawn list is exhausted.

## Out of scope

Roadmap mode is **not** for:

- **Stakeholder-facing roadmap documents** — those are Authoring with a roadmap-shaped framework
- **Quarterly planning, capacity reconciliation, portfolio governance** — this plugin doesn't do those; use the team's planning tool
- **Status / WIP tracking** — the spawn-list is a queue at authoring time, not a live tracker; `docs/kanban/` holds agent-found work, not user-strategized work
- **Strategic advisor consultation** — too heavy for "break this into pieces"; if a component itself needs strategic framing, that surfaces inside its own brainstorm

## Key Principles

- **Pure orchestration scaffolding** — Roadmap mode produces a queue, not a strategy artifact
- **Single deliverable** — `spawn-list.md`. No companion roadmap document, no mockups, no dependency-graph HTML
- **3–6 components** — Fewer and decomposition isn't earning its keep; more and the orchestration becomes the bottleneck
- **Each component fits one brainstorm session** — If a component would itself need decomposition, decompose it now, not later
- **Spawn briefs are paste-ready** — The paragraph is what gets pasted into the next `/aligned:brainstorming`; mode-disambiguating verbs required
- **Dependencies cite component titles** — "After Component #2 (Research synthesis)", not "after the research is done"
- **No advisor panel, no capacity math, no critique panel** — These are deliberately excluded; they belong in the downstream brainstorms, not in the decomposition pass

(Process-wide interaction principles — one question at a time, multiple choice preferred, gates mandatory — live in `references/shared-rules.md` and apply here.)
