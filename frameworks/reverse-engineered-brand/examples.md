# Reverse-Engineered Brand Examples

Running example: **Fieldline** — a B2B SaaS company that helps mid-market field-service organizations dispatch, track, and invoice without spreadsheets.

---

## PHASE 0: Intake (the only WAIT in the build pass)

### User giving a clear URL, source folder, write target, and org name

**User:** "URL is fieldline.io. Source folder is ~/Documents/fieldline-research with customer interview transcripts and our last sales deck. Write the brand folder into ~/Documents/fieldline-research/brand. Org name: Fieldline."

**Advisor:** "Got it. Sources: fieldline.io (public) plus ~/Documents/fieldline-research (local). Write target: ~/Documents/fieldline-research/brand. Org name: Fieldline. Running Extract → Transform → Load now. No further interruptions until the HTML review opens in your browser."

> The advisor restates the inputs once and proceeds to a fully automated build. No mid-flow questions.

### User giving a vague description without a URL

**User:** "We help field-service companies manage their operations. I don't have a public URL — we're kind of pre-launch."

**Advisor:** "Understood — pre-launch, no public URL. For Extract, I'll work from local material only. Point me at a folder with anything written down: deck, one-pager, email template, founder essay, Loom transcript. If you have nothing in writing yet, this framework isn't the right starting point — you'd need to do an intake conversation first and dump that into a file."

> Offers a concrete substitute for the URL. Does not stall.

---

## PHASE 1: Extract (silent — no advisor narration to the user)

The Extract phase is fully silent. No user interaction. The advisor reads every URL page and local file, classifies them, and holds the Source Registry in memory until the Load phase writes it into `brand/CLAUDE.md § Source Registry`.

### Entity extraction with role field (new schema)

Each entity in the flat `entities` array carries a `role` field that classifies its strategic position:

```json
{
  "entities": [
    {
      "name": "Fieldline",
      "role": "subject",
      "type": "company",
      "sources": [1, 2, 4]
    },
    {
      "name": "DispatchTrack",
      "role": "competitor",
      "type": "company",
      "slug": "dispatchtrack",
      "sources": [3, 6]
    },
    {
      "name": "spreadsheets + manual dispatch",
      "role": "alternative",
      "type": "behavior",
      "sources": [5, 7]
    },
    {
      "name": "VP of Operations",
      "role": "persona",
      "type": "person",
      "sources": [2, 4]
    }
  ]
}
```

> PHASE 1.5a runs next, aggregating competitor entities and extracting behavioral alternatives.

---

## PHASE 1.5: Competitor research and behavioral alternatives (silent)

### PHASE 1.5 example — competitor research

After Extract completes, the orchestrator writes `behavioral-alternatives.json` and dispatches competitor-dossier sub-agents in a single parallel batch.

**Behavioral alternatives write (compact 3-entry array):**

```json
[
  {
    "id": "alt-1",
    "label": "spreadsheets + manual dispatch",
    "type": "behavior",
    "evidence": "5 of 8 interview transcripts reference prior state"
  },
  {
    "id": "alt-2",
    "label": "DispatchTrack (legacy incumbent)",
    "type": "competitor",
    "evidence": "3 win/loss mentions; pricing comparison in sales deck"
  },
  {
    "id": "alt-3",
    "label": "custom Airtable build",
    "type": "behavior",
    "evidence": "2 transcripts; one prospect still mid-migration"
  }
]
```

**Competitor dossier dispatch (single batch — 2 sub-agents in parallel):**

Each competitor entity with `role: "competitor"` triggers a sub-agent call to the `competitor-dossier` prompt template. Dispatched together in one message:

- Sub-agent A: slug `dispatchtrack` → reads fieldline.io competitive page, DispatchTrack public pricing, 3 win/loss excerpts → writes `brand/competitors/dispatchtrack.md`
- Sub-agent B: slug `routemaster` → reads public site + 1 transcript mention → writes `brand/competitors/routemaster.md`

**Resulting dossier files (one per slug):**

```
brand/competitors/
  dispatchtrack.md   ← full dossier: positioning, pricing, strengths, gaps, Fieldline wedge
  routemaster.md     ← partial dossier: limited evidence; confidence tagged low
```

---

## PHASE 2: Transform — auto-framework dispatch (silent)

The Transform phase dispatches all owning frameworks as parallel sub-agents. No slice-by-slice narration. The orchestrator builds a canonical pre-synthesis blob, attaches the AUTO_MODE preamble, and fires all frameworks in a single batch.

### Auto-framework dispatch narrative

**Orchestrator builds pre-synthesis blob:**

```json
{
  "org": "Fieldline",
  "sources": ["fieldline.io", "~/Documents/fieldline-research"],
  "entities": [...],
  "behavioral_alternatives": [...],
  "raw_evidence": {...}
}
```

The AUTO_MODE preamble (see `auto-mode-preamble.md`) is prepended to every sub-agent prompt. It instructs each framework to skip all WAIT points, fill all slots from evidence, and emit `draft.md` + `oq.json` without user interaction.

**Parallel batch dispatch (single message, 4 sub-agents):**

- Sub-agent A: `5-components-positioning` with AUTO_MODE preamble → writes `brand/strategy/positioning.md` + `brand/.oq/positioning.json`
- Sub-agent B: `strategic-narrative` with AUTO_MODE preamble → writes `brand/strategy/narrative.md` + `brand/.oq/narrative.json`
- Sub-agent C: `messaging-distillation` with AUTO_MODE preamble → writes `brand/language/messaging.md` + `brand/.oq/messaging.json`
- Sub-agent D: `buyer-persona` with AUTO_MODE preamble → writes `brand/personas/vp-ops.md` + `brand/.oq/buyer-persona.json`

Each sub-agent emits a `draft.md` (the slice content) and an `oq.json` (open questions found during that framework's work).

**PHASE 2.4 ready-to-load gate (success path — no validation failures):**

Orchestrator runs schema validation and slot validator after all sub-agents complete:
- All 4 `oq.json` files pass schema (required fields present, no compound OQs flagged)
- All required slots in each slice are populated (confidence tagged, sources cited)
- AUTO_MODE heuristics confirm sufficient evidence density for all frameworks
- Result: gate passes, proceed to PHASE 3

---

## PHASE 3: Load and final report

### Aggregation and render

PHASE 3 aggregates sub-agent outputs, deduplicates open questions, inlines competitor dossiers, and dispatches the renderer.

**Aggregation produces:**

```json
{
  "folders": [
    {"path": "brand/strategy/positioning.md", "framework": "5-components-positioning", "confidence": "high"},
    {"path": "brand/strategy/narrative.md", "framework": "strategic-narrative", "confidence": "medium"},
    {"path": "brand/language/messaging.md", "framework": "messaging-distillation", "confidence": "medium"},
    {"path": "brand/personas/vp-ops.md", "framework": "buyer-persona", "confidence": "high"},
    {"path": "brand/market/competitive.md", "framework": "competitive-battle-card", "confidence": "medium"},
    {"path": "brand/market/alternatives.md", "framework": "5-components-positioning", "confidence": "medium"},
    {"path": "brand/audiences/channels/employer.md", "framework": null, "confidence": "low", "gap": true}
  ],
  "global_oq_ids": ["oq-1", "oq-2", "oq-3", "oq-4", "oq-5", "oq-6", "oq-7"],
  "deduped_gap_entries": [
    {"id": "gap-1", "description": "employer channel strategy", "owning_framework": null}
  ],
  "competitor_dossiers": ["brand/competitors/dispatchtrack.md", "brand/competitors/routemaster.md"]
}
```

Global OQ ids are deduplicated across all `oq.json` files — an OQ surfaced by two frameworks appears once in the merged queue.

GAP entries (slices with no owning framework) are collected once regardless of how many frameworks flagged the gap.

**Renderer dispatch:**

Orchestrator passes the aggregated blob to the `render-review-html` schema-reader, which reads `review-template.html` and writes `brand/review.html`.

### Advisor's end-of-run report

**Advisor:** "Done. Wrote `~/Documents/fieldline-research/brand` with 11 slice files plus `CLAUDE.md`, `version.yaml`, `contracts.yaml`.

Confidence distribution: 3 high, 5 medium, 3 low.

Logged 14 Open Questions covering: primary competitive alternative, owner-operator persona depth, voice register, pricing language, four unverified proof claims, three tagline candidates. The interactive review document is open in your browser at `~/Documents/fieldline-research/brand/review.html` — type answers in the browser, click 'Copy all answers,' then paste the resulting prompt back into Claude Code (this session or a new one) to apply the answers to the folder.

The canonical Open Questions queue lives in `brand/CLAUDE.md § Open Questions`. The HTML is a view of it — paste-back keeps them in sync."

> The final report is single-shot. The advisor reports the manifest, confidence distribution, Open Questions count + topic summary, and the HTML path. No mid-flow updates.

---

## Open Question shape (what sub-agents write during Transform)

Every Open Question in the queue (both in `brand/CLAUDE.md § Open Questions` and `brand/.oq/<framework>.json`) has the same shape:

```markdown
### OQ-1: Primary competitive alternative

**File:** `strategy/positioning.md`#competitive-alternatives
**Confidence:** low
**What I wrote:** Best customers were previously cobbling together spreadsheets and manual dispatch.
**Question for you:** Was the real alternative for your best customers the spreadsheet state, or were they limping along on a competitor product they hated?
**Why it matters:** If it's the spreadsheet state, positioning frames against operational chaos. If it's incumbent software, positioning frames against migration pain. Two different messaging arcs.
**Deepen with:** `/aligned:use-framework 5-components-positioning` for a full interactive pass on this slice
**Sources:** #4, #6
```

> The Open Question is a self-contained card: file/anchor, current draft, the calibration question, the downstream consequence, the owning framework for deeper work, and source provenance. The HTML renders each one as an answer-textarea card; the markdown form is the canonical record.

---

## Atomic vs compound open questions

The PHASE 2.4 validator flags compound OQs (two predicates joined by `and` or `or` in a way that creates two independent questions). Examples:

**❌ Bad — compound (flagged by validator):**

```
"Is the alternative spreadsheets and is the segment mid-market?"
```

Two predicates joined by `and`. The validator's compound regex matches. A warning is surfaced and the OQ is split before Load.

**✅ Good — split into two atomic OQs:**

```
"Is the alternative spreadsheets-plus-manual-dispatch?"
"Is the primary segment mid-market retail?"
```

Each question has exactly one predicate. Validator passes.

**✅ Also good — `or` inside alternatives list, not joining predicates:**

```
"Is the pricing model per-member, per-transport, or hybrid?"
```

The `or` enumerates options for a single predicate (pricing model). The compound regex does NOT match. Validator passes.

---

## Slice → owning framework mapping (in CLAUDE.md)

After the build, `brand/CLAUDE.md § Next Steps to Deepen` lists every slice with its owning framework. Example:

```markdown
## Next Steps to Deepen

- `strategy/positioning.md` → run `/aligned:use-framework 5-components-positioning` for a deeper, interactive pass
- `strategy/narrative.md` → run `/aligned:use-framework strategic-narrative` for a deeper, interactive pass
- `language/messaging.md` → run `/aligned:use-framework messaging-distillation` for a deeper, interactive pass
- `language/voice.md` → run `/aligned:use-framework brand-voice` for a deeper, interactive pass
- `personas/vp-ops.md` → run `/aligned:use-framework buyer-persona` for a deeper, interactive pass
- `market/competitive.md` → run `/aligned:use-framework competitive-battle-card` for a deeper, interactive pass
- `market/alternatives.md` → run `/aligned:use-framework 5-components-positioning` (Component 1 is the canonical source)
- `proof/proof-points.md` → run `/aligned:use-framework proof-points-audit` for a deeper, interactive pass
- `audiences/channels/employer.md` → GAP — no framework owns this slice; synthesis is ad-hoc. Consider commissioning a `channel-strategy` framework.
```

> Every slice in the folder appears here. The user never has to guess which framework to run; the mapping is explicit and authoritative.

---

## HTML review (offline from this session)

After the framework ends, the user reviews `brand/review.html` in the browser. The HTML has:

- One card per Open Question, with file, confidence, draft, question, why-it-matters, and source provenance
- A textarea on each card for the user's answer
- A "Skip for now" checkbox on each card
- Per-card "Copy this question's prompt" button — copies a one-question paste-back prompt
- Bottom-of-page "Copy all answers" button — copies a batch paste-back prompt

The paste-back prompt is plain Claude Code instructions to apply the answers to the slice files and mark Open Questions resolved in `brand/CLAUDE.md`. The user can paste it into this session, a new session, or any session — the prompt is self-contained and identifies the brand folder path.

> The framework's job ends when the HTML opens. The HTML is the review surface. The paste-back is the apply mechanism. The brand folder is the canonical store.
