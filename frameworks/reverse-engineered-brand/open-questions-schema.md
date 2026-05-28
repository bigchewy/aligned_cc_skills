# Review Data Schema (Marley model)

Reference for the `review-data.json` envelope produced at PHASE 3 of `reverse-engineered-brand` and consumed by `render_review.py`.

---

## Top-level structure

```jsonc
{
  "org": "The Knot",
  "generated_at": "2026-05-27",
  "brand_folder": "/abs/path/to/brand",
  "source_counts": {
    "total_sources": 0,
    "usable_sources": 0,
    "canonical_markdown_files": 0,
    "review_sections": 8,
    "open_questions": 0
  },
  "grade_scale": {
    "5": "Ready to use with minor edits",
    "4": "Solid draft — one or two gaps",
    "3": "Partial — usable but missing key signal",
    "2": "Thin — mostly speculative",
    "1": "Missing or too speculative"
  },
  "theme": {
    "palette": { /* 17 hex vars */ },
    "fonts": {
      "heading": { "family": "...", "faces": [...], "cdn": "...", "fallback": "..." },
      "body":    { "family": "...", "faces": [...], "cdn": "...", "fallback": "..." }
    },
    "logo": { "src": "<rel-path|null>", "wordmark_text": "The Knot" }
  },
  "sections": [ /* overview + 7 area sections — see below */ ],
  "open_questions": [ /* thin curated shape, 5–15 entries — see below */ ]
}
```

| Field | Type | Notes |
|---|---|---|
| `org` | string | Client/brand name |
| `generated_at` | string | ISO 8601 date (`YYYY-MM-DD`) |
| `brand_folder` | string | Absolute path to the brand folder scanned |
| `source_counts` | object | See §source_counts |
| `grade_scale` | object | String-keyed 1–5 rubric; rendered in the review legend |
| `theme` | object | See §theme |
| `sections` | array | overview + 7 area sections; see §sections |
| `open_questions` | array | Thin curated shape; see §open_questions (thin) |

---

## `source_counts`

| Field | Type | Notes |
|---|---|---|
| `total_sources` | integer | All source files found in the brand folder |
| `usable_sources` | integer | Sources with enough content to inform the build |
| `canonical_markdown_files` | integer | `.md` files written into `.build/` as canonical slices |
| `review_sections` | integer | Always `8` (overview + 7 area sections) |
| `open_questions` | integer | Count of entries in `open_questions[]` |

---

## `grade_scale`

String-keyed object `"1"`–`"5"`. The rubric labels are authored at PHASE 3 and stored verbatim for rendering. Default values:

| Key | Label |
|---|---|
| `"5"` | Ready to use with minor edits |
| `"4"` | Solid draft — one or two gaps |
| `"3"` | Partial — usable but missing key signal |
| `"2"` | Thin — mostly speculative |
| `"1"` | Missing or too speculative |

---

## `theme`

Extracted at PHASE 2.3b from brand design assets.

### `theme.palette`

17 hex-color variables:

`primary`, `primary_dark`, `primary_light`, `secondary`, `secondary_dark`, `secondary_light`, `accent`, `background`, `surface`, `surface_alt`, `text_primary`, `text_secondary`, `text_muted`, `border`, `divider`, `success`, `error`

Each value is a hex string (e.g., `"#1a1a2e"`).

### `theme.fonts`

Two font objects: `heading` and `body`. Each has:

| Field | Type | Notes |
|---|---|---|
| `family` | string | CSS font-family name |
| `faces` | array | Font face objects (see below) |
| `cdn` | string\|null | CDN import URL (Google Fonts, Adobe, etc.) |
| `fallback` | string | CSS fallback stack |

Each face object:

| Field | Type | Notes |
|---|---|---|
| `weight` | integer | e.g., `400`, `700` |
| `style` | string | `"normal"` or `"italic"` |
| `src_woff2` | string\|null | WOFF2 URL or rel path |
| `src_woff` | string\|null | WOFF URL or rel path |

### `theme.logo`

| Field | Type | Notes |
|---|---|---|
| `src` | string\|null | Relative path to logo file inside brand folder; null if not found |
| `wordmark_text` | string | Brand name as text fallback when `src` is null |

---

## `sections`

One overview section plus exactly 7 area sections. Total: 8 entries.

### Area section schema

| Field | Type | Notes |
|---|---|---|
| `id` | string | **Bare folder token** — MUST be one of: `overview`, `strategy`, `language`, `personas`, `audiences`, `market`, `proof`, `design`. The renderer routes open questions to section panels by `oq["slice"].startswith(section_id + "/")` — any other value silently drops all OQs for that section. |
| `label` | string | Human-readable tab label (e.g., `"Strategy"`) |
| `grade` | integer | `1`–`5`; see `grade_scale` for rubric |
| `confidence` | string | **Freeform string** at section level — e.g., `"medium-high"`, `"high"`. Derived: modal per-slice enum; compound string only on an even split (see R4 in design doc). NOT the strict per-slice enum. |
| `status` | string | Short eyebrow string shown in the tab header (e.g., `"Strong"`, `"Partial"`, `"GAP"`) |
| `summary` | string | 1–3 sentences of brand-specific learnings. What the build discovered, where confidence is high, where it's thin. NOT a generic definition of the area. |
| `provided` | string[] | What source material was available for this section |
| `needed` | string[] | What additional input would strengthen this section |
| `files` | string[] | Relative paths to canonical files that back this section |

### `overview` section — additional fields

The `overview` section carries two extra fields that no area section has:

| Field | Type | Notes |
|---|---|---|
| `readout` | object | `{ brand_system, main_risk, decisions_needed }` — executive summary narrative strings authored at PHASE 3 |
| `recent_update` | string\|null | ISO 8601 date of most recent update; `null` on first build |

`readout` sub-fields:

| Field | Type | Notes |
|---|---|---|
| `brand_system` | string | 1–2 sentences: what the build found about the brand as a system |
| `main_risk` | string | 1 sentence: the highest-stakes gap or inconsistency |
| `decisions_needed` | string | 1–2 sentences: what the client needs to decide before the next build |

---

## Open-question shapes

Two distinct shapes exist for open questions. They are never interchanged.

---

### Rich internal emission shape

**Status:** UNCHANGED from v0.4.1. Validated at PHASE 2.4. Lives only in `.build/slices/*.oq.json`. Never written to `review-data.json`.

#### Required at emission (validated at PHASE 2.4)

`id`, `file`, `framework_slot`, `confidence`, `impact`, `evidence`, `deepen_with`, `summary`, `why_it_matters`, `rationale`, AND at least one of `question` or `inferred_value`.

For GAP slices, `framework_slot` and `deepen_with` MAY be literal `null`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Local ID, e.g., `"Q-strategy-positioning-1"` |
| `global_id` | string | yes | Sequential `"OQ-N"` across entire output |
| `file` | string | yes | Relative path to the brand file this OQ addresses |
| `slice` | string | yes | Human label for the content slice (empty string OK for GAP) |
| `framework_slot` | string\|null | yes | Must match slot vocabulary table below; null for GAP |
| `summary` | string | yes | **One sentence, ≤25 words.** The line an executive sees at a glance. Must stand alone without needing the rationale. |
| `question` | string | conditional | Required if `inferred_value` absent. Phrase as a complete question. |
| `inferred_value` | string\|null | conditional | Required if `question` absent; null OK. Write a complete declarative sentence — not a fragment. **Atomicity:** if the sentence contains two coordinated predicates each with its own subject + verb, split into two OQs. |
| `draft_excerpt` | string\|null | no | Quote from source file that prompted this OQ |
| `confidence` | enum | yes | `high \| medium \| low` |
| `impact` | enum | yes | `P0 \| P1 \| P2` |
| `evidence` | array | yes | `["source:#N"]` refs; empty array OK for GAP |
| `alternatives` | array | no | When confidence is low, plausible alternative answers |
| `deepen_with` | string\|null | yes | Framework id to dispatch; null for GAP |
| `why_it_matters` | string | yes | **2-3 sentences, ≤60 words total.** Downstream stakes if this inference is wrong: (a) what breaks, (b) which surfaces propagate the error, (c) cost of being wrong vs. confirming. |
| `rationale` | string | yes | **2-3 sentences, ≤60 words total.** HOW the inference was derived: (a) what sources say, (b) where evidence converges/diverges, (c) what was assumed to bridge gaps. |
| `emitted_at` | string | no | ISO 8601 timestamp |

#### Derived (not persisted)

`type` is computed at render time: `confidence === "low" ? "question" : "assumption"`. Do not store `type` in the JSON.

---

### Thin persisted curated shape

**Status:** NEW (Marley model). Written into `review-data.json` by `curate_open_questions.py` at PHASE 3. Exactly 5 fields — no others persist.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Zero-padded sequential ID: `"OQ-001"`, `"OQ-002"`, … |
| `slice` | string | yes | Brand file path — e.g., `"strategy/positioning.md"`. Used by renderer to route OQ to the correct section panel via `oq["slice"].startswith(section_id + "/")`. |
| `impact` | enum | yes | `P0 \| P1 \| P2` |
| `question` | string | yes | The open question text |
| `why_it_matters` | string | yes | Why this question matters |

---

## `framework_slot` slot-validator rule

`framework_slot` must match `phase-{N}-{kebab(heading)}` exactly against the dispatched framework's PHASE headings.

**No slot merging across phases.** Example: for `5-components-positioning`, `"unique-value"` is NOT a valid slot. Valid slots are `"phase-2-unique-attributes"` and `"phase-3-value"` — separate phases, not merged.

### Authoritative kebab algorithm

Given a framework PHASE heading:

1. Identify the numbered prefix. Patterns:
   - `### PHASE N:` (most frameworks) → prefix `phase-N-`
   - `### ELEMENT N:` (strategic-narrative) → prefix `element-N-`
   - `## Phase N:` (design-principles — h2, lowercase "Phase") → prefix `phase-N-`
2. Take the text after the prefix's colon and space.
3. Lowercase it.
4. Strip leading/trailing whitespace.
5. Replace runs of `[^a-z0-9]+` with a single `-`.
6. Strip a leading or trailing `-`.

**Examples:**

| Raw heading | slot_id |
|---|---|
| `### PHASE 1: Competitive Alternatives` | `phase-1-competitive-alternatives` |
| `### PHASE 5: Market Category` | `phase-5-market-category` |
| `### ELEMENT 1: Name the Undeniable Change (The Old Game)` | `element-1-name-the-undeniable-change-the-old-game` |
| `## Phase 2: Design Direction` | `phase-2-design-direction` |
| `### PHASE 4: Dos and don'ts` | `phase-4-dos-and-don-ts` |

---

## Authoritative slot vocabulary

Source of truth for the slot validator at PHASE 2.4. Derived from reading each framework's `prompt.md`.

| framework_id | phase_number | heading | slot_id |
|---|---|---|---|
| buyer-persona | 1 | PHASE 1: Role anchoring | `phase-1-role-anchoring` |
| buyer-persona | 2 | PHASE 2: Evaluation criteria | `phase-2-evaluation-criteria` |
| buyer-persona | 3 | PHASE 3: Skepticism triggers | `phase-3-skepticism-triggers` |
| buyer-persona | 4 | PHASE 4: Language resonance | `phase-4-language-resonance` |
| buyer-persona | 5 | PHASE 5: Common objections | `phase-5-common-objections` |
| buyer-persona | 6 | PHASE 6: File assembly | `phase-6-file-assembly` |
| brand-voice | 1 | PHASE 1: Sample intake | `phase-1-sample-intake` |
| brand-voice | 2 | PHASE 2: Tone principles | `phase-2-tone-principles` |
| brand-voice | 3 | PHASE 3: Register table | `phase-3-register-table` |
| brand-voice | 4 | PHASE 4: Dos and don'ts | `phase-4-dos-and-don-ts` |
| brand-voice | 5 | PHASE 5: Banned phrases | `phase-5-banned-phrases` |
| messaging-distillation | 1 | PHASE 1: Anchor in positioning | `phase-1-anchor-in-positioning` |
| messaging-distillation | 2 | PHASE 2: Category name string | `phase-2-category-name-string` |
| messaging-distillation | 3 | PHASE 3: Tagline | `phase-3-tagline` |
| messaging-distillation | 4 | PHASE 4: Elevator pitch variants (per audience) | `phase-4-elevator-pitch-variants-per-audience` |
| messaging-distillation | 5 | PHASE 5: Value-prop phrasings | `phase-5-value-prop-phrasings` |
| competitive-battle-card | 1 | PHASE 1: Load canonical alternatives | `phase-1-load-canonical-alternatives` |
| competitive-battle-card | 2 | PHASE 2: Competitive landscape narrative | `phase-2-competitive-landscape-narrative` |
| competitive-battle-card | 3 | PHASE 3: Differentiators per alternative | `phase-3-differentiators-per-alternative` |
| competitive-battle-card | 4 | PHASE 4: Common objections + responses | `phase-4-common-objections-responses` |
| competitive-battle-card | 5 | PHASE 5: File assembly | `phase-5-file-assembly` |
| competitive-battle-card | 6 | PHASE 6: Sync check | `phase-6-sync-check` |
| proof-points-audit | 1 | PHASE 1: Claim extraction | `phase-1-claim-extraction` |
| proof-points-audit | 2 | PHASE 2: Source identification | `phase-2-source-identification` |
| proof-points-audit | 3 | PHASE 3: Date verification | `phase-3-date-verification` |
| proof-points-audit | 4 | PHASE 4: Confidence labeling | `phase-4-confidence-labeling` |
| proof-points-audit | 5 | PHASE 5: Gap report | `phase-5-gap-report` |
| proof-points-audit | 6 | PHASE 6: Digital-health proof split (optional) | `phase-6-digital-health-proof-split-optional` |
| proof-points-audit | 7 | PHASE 7: File assembly | `phase-7-file-assembly` |
| 5-components-positioning | 1 | PHASE 1: Competitive Alternatives | `phase-1-competitive-alternatives` |
| 5-components-positioning | 2 | PHASE 2: Unique Attributes | `phase-2-unique-attributes` |
| 5-components-positioning | 3 | PHASE 3: Value | `phase-3-value` |
| 5-components-positioning | 4 | PHASE 4: Target Customers | `phase-4-target-customers` |
| 5-components-positioning | 5 | PHASE 5: Market Category | `phase-5-market-category` |
| strategic-narrative | 1 | ELEMENT 1: Name the Undeniable Change (The Old Game) | `element-1-name-the-undeniable-change-the-old-game` |
| strategic-narrative | 2 | ELEMENT 2: Name the Stakes (Winners and Losers) | `element-2-name-the-stakes-winners-and-losers` |
| strategic-narrative | 3 | ELEMENT 3: Name the Promised Land (The Buyer's Mission) | `element-3-name-the-promised-land-the-buyer-s-mission` |
| strategic-narrative | 4 | ELEMENT 4: Name the Obstacles | `element-4-name-the-obstacles` |
| strategic-narrative | 5 | ELEMENT 5: Magic Gifts (Your Solution) | `element-5-magic-gifts-your-solution` |
| design-principles | 1 | Phase 1: Review Context | `phase-1-review-context` |
| design-principles | 2 | Phase 2: Design Direction | `phase-2-design-direction` |
| design-principles | 3 | Phase 3: Produce Design Principles Document | `phase-3-produce-design-principles-document` |

---

## Compound-question regex

PHASE 2.4 emits a warning (not a block) when a question field matches:

```
/\b(and|or)\b.*\?|\?.*\?/
```

**Does NOT match** (acceptable atomic question with alternatives):
> `"Is pricing per-member, per-transport, or hybrid?"`

**DOES match** (compound — split into two OQs):
> `"Is spreadsheets the real alternative and is DispatchTrack worth calling out?"`

The regex detects AND/OR between clauses with question marks, or two question marks in one string. Listing atomic alternatives within a single question is fine.

---

## Compound-declarative heuristic (warning)

PHASE 2.4 Check 6 inspects `inferred_value` for compound declaratives — two coordinated predicates joined by `" and "`, `" while "`, `" but "`, or `" — "` where each side has its own subject + verb.

Suggested implementation: split `inferred_value` at each connector; if both halves contain a capitalized noun AND a verb, warn. The intent is to catch run-on inferences like:

> "Chronic disease has become the dominant cost driver in US healthcare **while** the primary care system has been rendered structurally unable to manage it."

Two independent claims. They should be two OQs.

**Does NOT match** (single claim with a subordinate clause):
> "The brand's primary competitor is manual spreadsheet dispatch, not a named SaaS product."

A warning is non-blocking.

---

## Test fixtures

Curation input fixtures (rich-shape `.oq.json` sets fed to `curate_open_questions.py`) live in `test-fixtures/curation/`.

Render fixtures (`review-data.json`-shaped inputs fed to `render_review.py`) live in `test-fixtures/render/`.

| Directory | Purpose |
|---|---|
| `test-fixtures/curation/` | Rich-shape OQ inputs for `curate_open_questions.py` tests |
| `test-fixtures/render/` | `review-data.json`-shaped inputs for `render_review.py` tests |

See Tasks 2 and 5 in the implementation plan for fixture details.
