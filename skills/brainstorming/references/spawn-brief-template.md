# Spawn-Brief Template (Planning Portfolio Entry Schema)

> **v0 schema; provisional.** This 8-field schema is authored before any portfolio.md exists. After 2 portfolio docs ship, audit the schema for fields that were dead-weight or missing in practice — the v1 schema is informed by usage, not specified ahead of it.

Each entry in a Planning-mode `portfolio.md` uses this schema verbatim. Multiple entries are stacked under `## ` headings, one per portfolio item.

## Schema

```markdown
## {Item title}

**Target mode:** {Software | Authoring | Research}
**Status:** {pending | brainstorming | planned | in-progress | done}
**Rough size:** {hours | days | weeks}
**Prerequisites:** {bulleted list of items in this portfolio that must complete first, or "none"}
**External dependencies:** {bulleted list of things outside the portfolio's control, or "none"}
**Why now:** {1-2 sentences on what triggered this and what's lost if deferred}
**Spawn brief (one paragraph, brainstorm-ready):**
> {Audience + problem + constraint context for a fresh /aligned:brainstorming session}
**Success criterion:** {one sentence — what must be true when this item is "done"}
```

## Consumer contract

A user invoking `/aligned:brainstorming` against an entry pastes the **spawn-brief paragraph** (the `>` blockquote) as the prompt. The brainstorming router runs normal topic-keyword signal detection on the paragraph prose; the spawn-brief is authored to contain explicit mode-disambiguating keywords ("design...", "sequence...", "compare...") so detection routes correctly.

`target_mode` is **for the human reader and for documentation**, not consumed by the router (no parsing layer exists). If signal detection misses, the user gets the standard 5-way disambiguation question.

`/aligned:writing-plans` is **not** a portfolio.md consumer. The chain is:
*portfolio item → brainstorming → design doc → writing-plans → implementation plan*

## Field semantics

- **Target mode:** Which brainstorming mode this item should route to when its turn comes. Documentation only (router uses signals, not this field).
- **Status:** Lifecycle marker. `pending` is the default after creation. Update inline as items move through brainstorming → planning → execution.
- **Rough size:** Order-of-magnitude estimate. Use `hours` (sub-day), `days` (1-5 days), or `weeks` (>1 week). Items in the `weeks` bucket may need to be re-decomposed before they're brainstorm-ready.
- **Prerequisites:** Items earlier in this same portfolio that must reach `done` before this item is unblocked. List by `## ` heading title.
- **External dependencies:** Things outside the portfolio author's control — third-party APIs, vendor releases, customer commitments, hiring.
- **Why now:** The momentum case. What changed in the world (or the org) that makes this the right time? What's the regret cost of not doing it?
- **Spawn brief:** A single paragraph the user pastes literally into a fresh brainstorming session. Must contain mode-disambiguating keywords.
- **Success criterion:** A one-sentence test someone could run when the item is claimed-done. Must be observable without further dialog.
