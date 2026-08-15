# Spawn-Brief Template (Roadmap Spawn-List Entry Schema)

Each entry in a Roadmap-mode `spawn-list.md` uses this schema. Multiple entries are stacked under `## ` headings, one per component, in run order.

## Schema

```markdown
## {Component title}

**Target mode:** {Software | Authoring | Research}
**Prerequisites:** {bulleted list of components in this spawn-list that must complete first, or "none"}
**Spawn brief (paste-ready):**
> {One paragraph the user pastes verbatim into a fresh /aligned:brainstorming session. Must include: what gets produced from this brainstorm, the population/audience it serves, the constraints, and any prior-art the next brainstorm should read. Must contain mode-disambiguating verbs ("design...", "compare...", "write...", "synthesize...") so the brainstorming router auto-routes to the correct mode.}
**Success criterion:** {one sentence — what artifact exists when this component is "done"}
```

## Consumer contract

A user invoking `/aligned:brainstorming` against a component pastes the **spawn-brief paragraph** (the `>` blockquote) as the prompt. The brainstorming router runs topic-keyword signal detection on the paragraph prose; the spawn-brief is authored to contain explicit mode-disambiguating verbs so detection routes correctly.

`Target mode` is for the human reader and documentation, not consumed by the router (no parsing layer exists). If signal detection misses, the always-ask 3-mode confirmation question presents with no pre-selected mode — friction, not failure.

Plan-writing is **not** a spawn-list consumer. The chain is:

*spawn-list component → /aligned:brainstorming → design doc → (build-shaped components only, when the superpowers plugin is installed) superpowers:writing-plans → implementation plan*

(Components targeting Research or Authoring terminate at the design-doc-equivalent step and don't continue to plan-writing.)

## Field semantics

- **Target mode:** Which brainstorming mode this component should route to when its turn comes. Software for build/refactor/integration (runs in a dev-workflow plugin such as superpowers, not in this plugin); Authoring for any named document; Research for evidence synthesis. Documentation only — the router still detects from the paragraph.
- **Prerequisites:** Components earlier in this same spawn-list that must reach "done" before this component is brainstorm-ready. List by `## ` heading title. Use "none" when independent.
- **Spawn brief:** A single paragraph pasted literally into a fresh brainstorming session. Mode-disambiguating verbs required. Must carry enough context (population, constraints, prior art, deliverable shape) that the next brainstorm can start cold.
- **Success criterion:** A one-sentence test someone could run when the component is claimed done. Must be observable without further dialog (e.g., "design doc committed at `docs/plans/YYYY-MM-DD-foo-design.md` with all sections populated").
