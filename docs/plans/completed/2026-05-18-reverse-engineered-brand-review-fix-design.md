# reverse-engineered-brand `review.html` fix — design

**Date:** 2026-05-18
**Topic:** `reverse-engineered-brand-review-fix`
**Owning framework:** `frameworks/reverse-engineered-brand/`
**Schema bump:** v0.4.0 → v0.4.1
**Prior plan:** `docs/plans/completed/2026-05-17-reverse-engineered-brand-input-asks-design.md` (v0.4.0 input-asks feature — this design supersedes its review.html surfaces)
**Mockups:** `docs/mockups/2026-05-18-reverse-engineered-brand-review-fix.html`
**Critique:** `docs/mockups/2026-05-18-reverse-engineered-brand-review-fix-critique.html` (Round 1, 3 critics, 28 findings)

## Goal

Turn the `review.html` deliverable into a document a CEO/COO can validate in 5 minutes and then engage with for ~1 hour by sending additional documents. Three offending shapes go away:

1. The 4–6 sentence paragraphs in **Sections at a Glance** (the `folders[].summary` field rendered at `review-template.html:1717` and `:1823`).
2. The methodology-textbook **Inputs Needed** asks ("Source-attributed metrics with date and method. A number without a date and a method is a guess.") sourced from owning-framework `input_asks` frontmatters + 4 inline blocks in `reverse-engineered-brand/prompt.md` and `audience-taxonomy.md`.
3. The per-ask **folder-name "chip"** at `review-template.html:2054` (`iaEl('span', { className: 'ask-tab-tag', ... })`).

The fourth offender — unrealistic asks like "compliance attestation letters from named customers" — is fixed by the voice-rewrite sub-agent transforming asks on read (not by rewriting the framework frontmatters, which would regress standalone framework UX).

A bigger blind spot, raised by Kristen Berman and accepted by the user, also gets fixed in the same change: **the top nav uses build-time taxonomy** (`Strategy / Language / Audiences / Personas / Market / Proof / Design`) **rather than CEO vocabulary**. The 7 folder tabs + Competitive Context tab collapse to 4 CEO-language group tabs.

## Success criteria

- A reader who has never seen the document opens it, reads only the first tab, and can answer two questions in <5 min: "is the picture roughly right?" and "what document would help us refine it?"
- Every visible ask is a doc category, not a methodology prescription. Word count ≤12 per ask, noun-form, zero conditional clauses.
- No `folders[].summary` rendered. No dense paragraph anywhere in Overview.
- Every Sections-at-a-Glance row reads in <5 seconds. Bullets cap at 14 words.
- The tab bar names what the CEO sees about her own company, not what we built.
- Standalone `/aligned:use-framework <name>` runs are unchanged — methodology guidance in framework frontmatters stays intact for that audience.

## What's NOT in scope

- Renaming the underlying brand folder structure (the `brand/strategy/`, `brand/language/`, etc. directory layout stays as-is).
- Rewriting framework `prompt.md` frontmatters (deferred per critique M3 — see Decision 10).
- Changing the OQ card approve/reject/answer UX or per-folder paste-back format.
- Instrumentation (Kristen's "files received per review.html shipped" suggestion) — file separately as a KB.
- The auto-mode preamble, slice-mapping table, framework-dispatch flow at PHASE 2.
- The `behavioral_alternatives[]` and `competitors[]` arrays (their content authoring is fine; they re-render under a renamed tab).

## Decision Log

| # | Decision | Rationale |
|---|---|---|
| 1 | Schema bump v0.4.0 → v0.4.1 (additive, with fallback) | Pattern matches v0.3.0→v0.4.0 (additive + shape-warning fallback in `render-review-html.md:35`). |
| 2 | Drop `folders[].summary` from rendering. Add `display_groups[].headline_claim` + `display_groups[].thinnest_gap` (≤14 words each). NO folder-level `headline_claim`/`thinnest_gap` — group-level only. | Critique H1: dual-authoring violated "collapse before adding." Folder-level new fields had no rendered consumer. The renderer falls back to `folders[].summary` when `display_groups[]` is absent (legacy path). |
| 3 | Adopt Kristen's label pair: `What we see:` / `What we're missing:` | User accepted Kristen's pushback. Validation-job framing puts the CEO in recognition posture, not grader posture. |
| 4 | Introduce `display_groups[]` array — render-time grouping into 4 CEO-vocabulary tabs (`How you show up` / `Who you sell to` / `Who you sell against` / `What you can prove`). | User accepted Kristen's blind-spot flag. `folders[]` structure unchanged; only the tab nav re-organizes. |
| 5 | `display_groups[]` synthesis: sub-agent dispatched per group at PHASE 3.2 (4 parallel sub-agents). Each reads its constituent folders' slice drafts and writes group-level `headline_claim` + `thinnest_gap`. | Critique M5: orchestrator-side synthesis violates the context-bloat guard (`prompt.md:22-25`). Sub-agent dispatch parallelizes and honors the guard. |
| 6 | Tab content per group: grade pill + label + assumption/question counts ONLY (no bullet repetition in banner). Then group callout ("What we have / What would help"). Then OQ cards from constituent folders, intermixed, sorted P0→P1→P2 then by file order. Each OQ card carries a renderer-added "area" chip showing CEO-vocabulary folder name (e.g., `Strategy`, not `strategy/positioning.md`). Per-folder paste-back textareas nest inside the group panel (one per constituent framework). | Critique M4 (drop banner repetition), M13 (OQ sort), L9 (CEO-vocabulary chip), H2 (per-folder paste-backs, not group paste-back). Per-folder paste-back keeps existing `buildPasteBack(folder)` working — no multi-framework rewrite. |
| 7 | Sections at a Glance renders 4 group rows. Each row uses `display_groups[i].headline_claim` + `thinnest_gap`. Rows show grade as `N/5`. | Group level is the user-facing layer for skim. |
| 8 | Overview Inputs Needed flattens to single doc-category checklist. No tier headings, no folder chips, no introductory paragraph. Bullet glyph is a hyphen (copy-paste survives). Tab heading reads "Send us any of these." | Critique L5, L6, L7 — collapse callout headings, kill happy talk, hyphen for copy-paste. |
| 9 | PHASE 3.2c gate extended: Check 2 (banned-phrase regex) covers new fields. New Check 4 enforces word caps (`headline_claim` ≤14, `thinnest_gap` ≤14, `provided_summary` ≤25, `input_asks[].ask` ≤12 — KB-136 closed). New Check 5 rejects verb-form asks (regex on `^\s*(if\|ideally\|when\|where the buyer)\b` or starts with imperative verb). Required-non-empty check on `headline_claim`/`thinnest_gap`. Word-count split = `trim().split(/\s+/).filter(Boolean).length`. | Critique H3, M6, M11. Caps tighter than first pass (was 20 words). Whitespace-robust split. |
| 10 | DO NOT rewrite framework `input_asks` frontmatters at source. Keep them intact for standalone `/aligned:use-framework <name>` UX. The voice-rewrite sub-agent transforms asks into doc-category form on read for review.html only. Add shape rule to `voice-rewrite.md`: noun-form, doc-category, zero conditional clauses. | Critique M3: source-level rewrites would strip methodology guidance from standalone framework runs. Decouple the two consumers. Also fixes F15 fact correction (only 7 framework frontmatters carry `input_asks`, not 8). |
| 11 | KB-141 (em-dash in callout success copy at `review-template.html:2126`) fixed in same change. | Same render path; one-line edit. |
| 12 | Drop Design tab from the new nav. Design folder data is still synthesized; if the orchestrator instantiates a Design slice, its OQs land under `How you show up`. | User accepted Kristen's 4-tab mapping. Visual identity is part of how the brand shows up. |
| 13 | Competitive Context tab (currently top-level at `:997`) folds into `Who you sell against`. Behavioral alternatives + competitor cards render at the top of that group panel. | Same tab vocabulary as the rest of the rename. |
| 14 | Grade pill renders as `N/5` (e.g., `3/5`), not bare `N`. Applies everywhere the grade is shown. | User input 2026-05-18: bare integer doesn't communicate the 5-point scale. CSS `.grade` `min-width: 36px` accommodates the 2 extra characters (mockup verified). |
| 15 | Drop Overview Executive Summary sub-tab. Sections at a Glance is the Overview default surface; "Inputs Needed" is the second sub-tab. The exec-summary narrative + source-counts cards become an expandable detail strip below Sections at a Glance. | Critique M10. Executive summary was unrendered in mockup and added a click of friction for the primary skim path. |
| 16 | `legacyFolderAsGroup()` fully specified: synthetic `id = "legacy-{folder-id}"`, `headline_claim = first 14 words of folder.summary` (truncate with ellipsis if longer; strip em-dashes), `thinnest_gap = ""`. Renderer always builds tab nav from `display_groups[]` — if absent, derive synthetic groups from `folders[]` 1:1 (each folder is its own group). v0.4.0 fixtures render under the new 5-button nav layout (collapse-mapping for legacy `folders[]` requires v0.4.1). | Critique M2 / L1. Spec is complete; renderer has one decision tree. |
| 17 | Sub-tab label changes: `Sections at a Glance` → `Your brand at a glance`. `Inputs Needed` → `Send us any of these`. | Critique L4, L6 — labels describe content not format. |

## Architecture

### Schema additions (`.open-questions.json` v0.4.1)

```jsonc
{
  "schema_version": "0.4.1",
  "source_counts": { ... },           // v0.4.0, unchanged
  "source_narratives": { ... },       // v0.4.0, unchanged
  "folders": [
    {
      "id": "strategy",
      "label": "Strategy",            // unchanged — still the CEO-vocabulary label for chips
      "grade": 3,
      "status": "Partial",
      "p0_count": 2, "p1_count": 3, "p2_count": 1,
      "summary": "...",               // DEPRECATED but still authored at PHASE 3.2 by orchestrator instructions (NOT rendered when display_groups[] present; renderer falls back to it when display_groups[] absent — see Decision 16)
      "provided_summary": "...",      // v0.4.0, unchanged — feeds group-level provided_summary aggregation
      "input_asks": [ ... ],          // v0.4.0, unchanged — feeds group-level input_asks aggregation
      "framework_dispatches": [ ... ] // unchanged
    }
  ],
  "display_groups": [                 // NEW v0.4.1
    {
      "id": "how-you-show-up",
      "label": "How you show up",
      "folder_ids": ["strategy", "language", "design"],
      "grade": 3,                     // aggregate of constituent folder grades (rounded mean, capped at 5)
      "headline_claim": "...",        // ≤14 words, authored by per-group sub-agent at PHASE 3.2
      "thinnest_gap": "...",          // ≤14 words, authored by per-group sub-agent at PHASE 3.2
      "provided_summary": "...",      // ≤25 words, aggregated by voice-rewrite sub-agent at PHASE 3.2b across constituent provided_summaries
      "input_asks": [ ... ]           // union of constituents' input_asks, deduped by trim+lowercase, higher-tier wins; voice-rewrite sub-agent transforms each ask on read (noun-form, doc-category, ≤12 words)
    },
    { "id": "who-you-sell-to",        "label": "Who you sell to",        "folder_ids": ["audiences", "personas"],  ... },
    { "id": "who-you-sell-against",   "label": "Who you sell against",   "folder_ids": ["market", "competitive"],  ... },
    { "id": "what-you-can-prove",     "label": "What you can prove",     "folder_ids": ["proof"],                   ... }
  ],
  "behavioral_alternatives": [ ... ], // unchanged; render top of who-you-sell-against
  "competitors": [ ... ],             // unchanged; render top of who-you-sell-against
  "open_questions": [ ... ]           // unchanged shape; renderer filters by display-group's folder_ids[] set
}
```

### `frameworks/reverse-engineered-brand/prompt.md` PHASE 3.2 changes

**Step 3.2 (existing) — folder-level summary:** orchestrator still authors `folders[].summary` for backward compat. The hard-fail gate is replaced by the new group-level gate (see Step 3.2-NEW). Soft guidance: "1-2 sentences, brand-specific" — no new validator at this layer.

**Step 3.2-NEW — group-level synthesis via sub-agent dispatch:**

For each `display_groups[i]`, dispatch a Task (`subagent_type: general-purpose`) using a new prompt template at `frameworks/reverse-engineered-brand/group-bullets.md`. The 4 sub-agents run in parallel (single assistant message, 4 Task calls). Each sub-agent receives:
- `{group-id}` and `{group-label}`
- `{constituent-folder-ids}` — JSON array of folder ids in this group
- `{slice-draft-paths}` — JSON array of absolute paths to constituent folders' `.draft.md` files (read by sub-agent, never by orchestrator)
- `{constituent-oq-paths}` — JSON array of absolute paths to constituent folders' `.oq.json` files
- `{canonical-pre-synthesis-blob-path}` — same blob used in PHASE 2
- `{output-json-path}` — `{brand-folder-path}/.build/groups/{group-id}.json`

Sub-agent reads its inputs, writes:
```json
{ "headline_claim": "...", "thinnest_gap": "..." }
```

Each string ≤14 words, banned-phrase clean, declarative (no questions, no conditionals). Sub-agent must self-check the word count before write — but PHASE 3.2c also enforces hard-fail.

Orchestrator then aggregates `display_groups[].input_asks` deterministically:
- Collect `folders[i].input_asks` for each constituent folder.
- Dedupe by case-insensitive whitespace-trimmed `ask` text. Higher tier wins on collision. Within tier, preserve first-seen order.
- Pass to PHASE 3.2b for voice-rewrite shape transformation.

**Step 3.2b (extended) — voice-rewrite with shape transformation:**

Sub-agent prompt at `voice-rewrite.md` gains a Step 0 (runs before existing Step 1):

> **Shape transformation rule.** Before applying brand-voice rewriting, transform each incoming ask string to the doc-category shape. Three rules: (a) starts with a noun, (b) names a document category (not a methodology or interview prescription), (c) zero conditional clauses ("if you have," "ideally," "where the buyer named X"). If the input ask uses verb-form ("Customer interviews answering one question: what phrase do you use when you describe us to a colleague?"), rewrite to noun-form ("Recorded customer or prospect conversations"). Preserve digit tokens and typed nouns. The output must satisfy the 12-word cap and the verb-form regex in Step 1 below.

Sub-agent also authors group-level `provided_summary` per group (aggregating constituent folders' source counts into one ≤25-word inventory).

Output contract unchanged in shape; field set expands:
```json
{
  "asks": [
    {"group_id": "how-you-show-up", "index": 0, "tier": "critical", "ask": "<voice-revised, shape-transformed>"}
  ],
  "provided_summaries": {
    "how-you-show-up": "3 marketing decks, 1 founder essay; no recorded sales calls."
  }
}
```

Orchestrator merges back by `(group_id, index)` tuple.

### `frameworks/reverse-engineered-brand/prompt.md` PHASE 3.2c gate changes

**Check 2 (banned-phrase regex):** field set expands from `{ask, provided_summary}` to `{ask, provided_summary, headline_claim, thinnest_gap}` — applied to BOTH folder-level (for `provided_summary` / `input_asks`) and group-level (for all four).

**Check 4 (NEW — word-count cap):** word-count split is `trim().split(/\s+/).filter(Boolean).length`. Hard-fail if count exceeds cap. Field table:

| Field | Cap |
|---|---|
| `folders[].provided_summary` | 25 |
| `folders[].input_asks[].ask` | 12 (post-voice-rewrite) |
| `display_groups[].headline_claim` | 14 |
| `display_groups[].thinnest_gap` | 14 |
| `display_groups[].provided_summary` | 25 |
| `display_groups[].input_asks[].ask` | 12 (post-voice-rewrite) |

`folders[].headline_claim` / `thinnest_gap` are NOT capped because they DO NOT EXIST.

**Check 5 (NEW — shape compliance):**
- Verb-form rejection regex on each `input_asks[].ask`: `^\s*(if\|ideally\|when|where the buyer)\b` — hard-fail on match.
- Required-non-empty for every `display_groups[i].headline_claim` and `thinnest_gap` (length > 0 after trim). Sub-agent omission = hard-fail.
- Field-presence: every `display_groups[i]` must have `id`, `label`, `folder_ids[]`, `headline_claim`, `thinnest_gap`. Missing key = hard-fail.

**Check 1 (array length parity):** updated to apply per group (`display_groups[i].input_asks` length before/after voice-rewrite must match).

**Check 3 (tier preservation):** unchanged scope but operates on group-level asks.

### `.build/` resume semantics

If a PHASE 3.2-NEW sub-agent or PHASE 3.2b voice-rewrite fails (timeout, malformed JSON), the orchestrator's hard-fail message names the failed sub-agent + group id. On rerun, the orchestrator checks `.build/groups/{group-id}.json` (and `.build/voice-rewrite.json` for PHASE 3.2b's output) — if present and parses, skip re-dispatch. This avoids re-paying PHASE 1+1.5+2 costs on a single-sub-agent failure. Resume rule documented in `prompt.md` PHASE 2.4 outcomes section.

### Renderer changes (`frameworks/reverse-engineered-brand/review-template.html`)

**Tab nav (lines 995-1005):** replace the 9-button tab bar with 5 buttons:

```html
<button class="tab-btn active" onclick="switchTab('overview')">Overview</button>
<button class="tab-btn" onclick="switchTab('how-you-show-up')">How you show up</button>
<button class="tab-btn" onclick="switchTab('who-you-sell-to')">Who you sell to</button>
<button class="tab-btn" onclick="switchTab('who-you-sell-against')">Who you sell against</button>
<button class="tab-btn" onclick="switchTab('what-you-can-prove')">What you can prove</button>
```

For legacy v0.4.0 fixtures (no `display_groups[]`), the renderer builds buttons from `folders[]` 1:1 — each folder is its own synthetic group. The tab nav becomes data-driven (single source of truth: whichever array is present).

**Folder→group re-keying (critique M1).** The following JS data structures and selectors are folder-keyed today and need explicit re-keying:

| Site | Today | New |
|---|---|---|
| `FRAMEWORK_BY_FOLDER` (`:1316`) | maps folder id → framework id | Stays folder-keyed. Per-folder paste-backs use it as-is. |
| `FRAMEWORK_TARGET` (`:1328`) | maps folder id → target path | Stays folder-keyed. |
| `[data-folder="strategy"]` filter (`:1368`) | OQ filter by folder | Stays folder-keyed for OQ filtering. OQ cards carry `data-folder` regardless of group rendering. |
| `rebuildAllPastebacks` (`:1937`) | iterates folder ids | Iterates `display_groups[].folder_ids` for which paste-back boxes exist; each box is per-folder. |
| `renderAll` loop (`:1920`) | per-folder rendering | Per-group rendering loop; nested per-folder paste-back rendering inside each group. |
| `FOLDER_LABEL_TO_TAB` (`:2016`) | maps folder label → tab id | Repurposed: `FOLDER_TO_GROUP_TAB` maps folder id → containing group id. Used to route any folder-keyed click into the right group panel. |
| `panel-{folder-id}` divs (`:1059-1192`) | 8 folder panels | 4 group panels. Each group panel has nested per-folder sections (paste-back boxes labeled with framework name). |
| `chip-file` content | `strategy/positioning.md` | Renderer maps via `FOLDER_LABEL_BY_ID` (already exists per folder label): chip text = "Strategy" not "strategy/positioning.md". |

**Tab panels:** each of the 4 group panels has:

```html
<div id="panel-{group-id}" class="tab-panel">
  <div class="folder-banner" id="banner-{group-id}"></div>      <!-- grade + label + counts only; NO bullets -->
  <div class="input-callout" id="callout-{group-id}"></div>     <!-- "What we have" + "What would strengthen this" -->
  <!-- For who-you-sell-against only: behavioral-alternatives + competitor-cards render here, unchanged -->
  <div id="panel-{group-id}-oqs"></div>                          <!-- OQ cards intermixed, sorted P0→P1→P2 then file order -->
  <div id="panel-{group-id}-pastebacks">                         <!-- nested per-folder paste-back boxes -->
    <!-- one .paste-back per constituent folder, each labeled with its framework name -->
  </div>
</div>
```

**`renderSectionsAtAGlance()` (`:1687`):** iterate `OPEN_QUESTIONS.display_groups`. Per row: grade pill (`N/5`) + group label + bullets cell with `What we see:` / `What we're missing:` labels. Row click navigates to group tab. Add a faint `›` right-aligned in the bullets cell to signal clickability (critique L10).

**`legacyFolderAsGroup()` (NEW):** invoked when `display_groups[]` is absent. For each `folder` in `OPEN_QUESTIONS.folders`, produce:
```js
{
  id: 'legacy-' + folder.id,
  label: folder.label || folder.id,
  folder_ids: [folder.id],
  grade: folder.grade || gradeFromStatus(folder.status),
  headline_claim: truncateAndStripDashes(folder.summary || '', 14),
  thinnest_gap: '',
  provided_summary: folder.provided_summary || '',
  input_asks: folder.input_asks || []
}
```
`truncateAndStripDashes(s, n)`: replace `[—–]` with comma + space, split on whitespace, take first n words, append ellipsis if truncated. Empty `thinnest_gap` renders as a single `What we see:` line (no second bullet).

**`renderGroupBanner()` (refactored from `renderFolderBanner` at `:1810`):** reads `display_groups[i]`. Renders grade pill (`N/5`) + label + counts. **No bullets in banner** (critique M4).

**`renderPerTabCallouts()` (refactored at `:2090`):** iterate `display_groups[]`. One callout per group. Collapse two `<h3>` headings ("What you provided" + "What would strengthen this") into a single short heading "What we have, what would help" with inline structure. Use hyphen bullets (`-`) instead of middle-dots for copy-paste survival.

**`renderInputAsks()` (rewrite at `:2064`):** flatten `display_groups[i].input_asks[].ask` across all groups. Dedupe by case-insensitive trim. Single flat `<ul>` with hyphen-prefixed list items. Heading: "Send us any of these." (replaces happy-talk intro paragraph at line 1050). Drop `iaMakeTierGroup`, `.ask-tab-tag` CSS at lines 914-923, `.ask-tab-tag` span construction at line 2054.

**OQ card sort + rendering (`:1845` filter + `renderOQCard` at `:1741`):** filter by `display_groups[i].folder_ids.some(...)`. Sort: P0 → P1 → P2, then by `file` lexically. Each card carries a NEW `chip-area` (not "preserve" — net-new render code) with text = `FOLDER_LABEL_BY_ID[folder_id]` (e.g., "Strategy"). Strip the `.md` suffix and the folder slash.

**Empty-group state (NEW):** when a group has zero OQs across all constituent folders, render under the callout: `<p class="empty-group">Coverage is sufficient across this area.</p>`. When constituent folders are partially empty, no special copy — the group simply shows fewer OQs.

**Overview sub-tabs:** drop the Executive Summary sub-tab. The Overview's sub-tab bar now has 2 buttons: `Your brand at a glance` (default active) + `Send us any of these`. The previous exec-summary narrative + source-counts cards become a small `<details>` expandable strip below `Your brand at a glance` (label: "About the source material we received").

**Empty-state copy at `:2126` (KB-141 fix):** replace `"This area has no outstanding asks — coverage is sufficient."` with `"Coverage is sufficient here."` (drops em-dash).

### Voice-rewrite sub-agent changes (`frameworks/reverse-engineered-brand/voice-rewrite.md`)

Two changes:
1. Add Step 0 (shape transformation rule — verbatim block in PHASE 3.2b spec above).
2. Aggregate `provided_summaries` per `display_groups[i]` (group-level) instead of per-folder.

NO changes to framework `prompt.md` frontmatters. NO changes to `audience-taxonomy.md` `## Ideal inputs`. NO changes to inline blocks in `reverse-engineered-brand/prompt.md` (`competitive_context_input_asks`, etc.). The transformation happens on read.

### Test fixture updates

Three render fixtures need v0.4.1 fields added:
- `frameworks/reverse-engineered-brand/test-fixtures/render/fixture-tiny.json`
- `frameworks/reverse-engineered-brand/test-fixtures/render/fixture-realistic.json`
- `frameworks/reverse-engineered-brand/test-fixtures/render/fixture-stress.json`

Add `display_groups[]` to each. Folder-level `headline_claim` and `thinnest_gap` are NOT added (they don't exist).

**Per-field negative fixtures for Check 4** (critique M7) — 4 new fixtures:
- `invalid-headline-too-long.json` — 15-word `headline_claim` hard-fails.
- `invalid-thinnest-gap-too-long.json` — 15-word `thinnest_gap` hard-fails.
- `invalid-provided-summary-too-long.json` — 26-word `provided_summary` hard-fails.
- `invalid-ask-too-long.json` — 13-word `input_asks[].ask` hard-fails.

**Edge-case fixture for word-count split** (critique M6): `valid-leading-whitespace.json` — a 14-word `headline_claim` preceded by a leading space PASSES (`trim().split(/\s+/).filter(Boolean).length` = 14).

**Dedupe-collision fixture** (critique M7): `valid-dedupe-collision.json` — two constituent folders with overlapping `input_asks` text, different tiers. Result: one ask in `display_groups[i].input_asks`, higher tier wins.

**Legacy-fallback fixture** (critique M7): `valid-legacy-v0.4.0.json` — has `folders[].summary` populated, no `display_groups[]`. Renderer invokes `legacyFolderAsGroup()`. Each synthetic group renders with truncated `headline_claim` and empty `thinnest_gap`.

**Verb-form rejection fixture** (critique H3 / M8): `invalid-ask-verb-form.json` — `input_asks[].ask` starts with `If` — hard-fails Check 5.

The OQ-schema fixture at `test-fixtures/oq-schema/valid-minimal.json` stays at v0.4.0 — verifies the renderer's fallback path.

## Data flow (one user action, end-to-end)

User runs `/aligned:use-framework reverse-engineered-brand` → PHASE 0 intake → PHASE 1 extract → PHASE 1.5 competitor research → PHASE 2 framework dispatch + AUTO_MODE → PHASE 2.4 verification gate (extended with Check 4/5) → **PHASE 3.2 (extended): orchestrator authors per-folder summary (unchanged); dispatches 4 parallel sub-agents to author group-level `headline_claim`/`thinnest_gap` from constituent slice drafts; aggregates group-level `input_asks` deterministically from folder-level asks** → **PHASE 3.2b (extended): voice-rewrite sub-agent runs shape transformation (Step 0) + voice rewrite (Step 1) on every ask; authors group-level `provided_summary` from registry metadata** → PHASE 3.2c (extended Check 2, new Check 4 + 5) → PHASE 3.3-3.6 (unchanged) → write `.open-questions.json` at schema v0.4.1 → PHASE 3.7 dispatches renderer → render-review-html.md substitutes 3 tokens, the v0.4.1 template renders 5 tabs (Overview + 4 groups), Sections at a Glance shows 4 rows with `N/5` grades, Overview Inputs Needed is a flat hyphen-bulleted checklist, each group panel shows grade banner (no bullets) + callout + sorted OQ cards + nested per-folder paste-backs.

CEO opens `review.html`. First 30 seconds: Overview tab → `Your brand at a glance` → 4 group rows in Sections at a Glance, each with 2 bullets and a `N/5` grade. Decides which group warrants engagement. Clicks group tab. Reads group-level banner (grade + label + counts) + callout. Sees per-OQ chips for area origin (CEO vocabulary). Decides to send docs from the Overview's `Send us any of these` checklist. 1-hour engagement happens through OQ card answers + doc forwarding. Per-folder paste-backs feed `/aligned:use-framework <name>` sessions for deeper sharpening.

## Testing strategy

**Unit tests** (where existing unit tests live):
- Word-count cap function — positive + negative pair for each capped field. Edge cases: leading whitespace, trailing whitespace, hyphenated compounds, exactly-at-cap.
- Banned-phrase regex against new fields, including the new shape-rule regex from Check 5.
- Display-group `input_asks` union+dedupe (case-insensitive trim, higher-tier wins). Dedupe-collision fixture exercises this.
- `legacyFolderAsGroup()` truncation + em-dash stripping. Fixture: `valid-legacy-v0.4.0.json`.
- `FOLDER_LABEL_BY_ID` mapping — every folder id maps to a CEO-vocabulary label.

**Renderer smoke tests:**
- Open each fixture in headless browser, assert: tab bar has 5 buttons (or N buttons from legacy fallback), Sections at a Glance has 4 rows (or N rows for legacy), no `<p>` in Sections at a Glance exceeds 1 line height, Overview Inputs Needed has no tier headings, OQ cards within a group are sorted P0→P1→P2.
- Empty-group state: assert "Coverage is sufficient across this area." renders when group has zero OQs.

**End-to-end tests:**
- Re-run the framework against the existing test corpus → assert `.open-questions.json` schema v0.4.1, all `display_groups[].headline_claim`/`thinnest_gap` ≤14 words, all `input_asks[].ask` ≤12 words, no em-dashes anywhere, no verb-form asks slipping through.

**Error-path tests for mocks (CLAUDE.md mandate):**
- Voice-rewrite sub-agent rejection: malformed JSON, missing keys, mismatched `(group_id, index)` tuples, missing `provided_summaries` key.
- Group-bullets sub-agent rejection: malformed JSON, missing `headline_claim` or `thinnest_gap`, group-bullets file written but content fails Check 5 required-non-empty.
- PHASE 3.2c gate hard-failure paths: word-count overflow at every capped field, banned-phrase match at every covered field, verb-form ask at Check 5.
- `.build/` resume: simulate one group-bullets sub-agent fail-after-write, verify orchestrator resumes from `.build/groups/{group-id}.json` on rerun.

**Visual regression:**
- Compare new `review.html` against committed `docs/mockups/2026-05-18-reverse-engineered-brand-review-fix.html` snapshot.

## Open questions

1. **CEO-vocabulary chip wording.** Each OQ card carries a chip showing area origin in CEO vocabulary (`Strategy`, not `strategy/positioning.md`). For folders under a merged group (e.g., `Strategy` and `Language` both inside `How you show up`), the chips help engaged readers route. But is "Strategy" the right CEO word? Or "Positioning"? Or something else? **Trigger to resolve:** first real CEO test or kristen-berman pass on the chip vocabulary.

2. **Test against the marley corpus.** The first real validation is re-running the framework on the existing marley source folder and reading the resulting `review.html` end-to-end as a CEO would. **Trigger to resolve:** implementation lands, run framework, manually skim.

3. **A/B `Who you sell against` vs `Your competition`.** Krug flagged "sell against" as sales-team vocabulary. Worth testing both with two CEOs before locking the label. **Trigger to resolve:** first user-test with a CEO outside the team.

## Implementation order (revised after critique)

1. **Renderer-only, no schema impact:** drop `ask-tab-tag` chip (Q4), drop `.ask-tab-tag` CSS, KB-141 em-dash fix at `:2126`. Single commit.
2. **Validator spec (pure spec text in `prompt.md` PHASE 3.2c):** Check 4 word caps with corrected split, Check 5 verb-form + required-non-empty + field-presence, extended Check 2 field set. No code yet.
3. **Schema v0.4.1 + renderer field-binding:** add `display_groups[]` (additive); update renderer to read group-level first, fall back to `legacyFolderAsGroup()`. Rewrite `renderInputAsks` to flat list, `renderSectionsAtAGlance` to 4 group rows with `N/5` grades and 2-bullet cells. Rewrite tab nav data-driven. 3 fixture rewrites + 4 negative + 1 dedupe + 1 legacy + 1 verb-form fixture.
4. **Tab rename + group panels:** restructure HTML — 4 group panels with grade banner (no bullets) + callout + sorted OQ cards + nested per-folder paste-backs. Update `renderAll`, `rebuildAllPastebacks`, OQ filter, `chip-area` rendering. Drop Executive Summary sub-tab; merge to expandable `<details>`.
5. **PHASE 3.2 group-bullets sub-agent dispatch:** new `group-bullets.md` prompt template. Orchestrator dispatches 4 in parallel. Output writes to `.build/groups/{group-id}.json`. Resume semantics.
6. **PHASE 3.2b voice-rewrite shape transformation:** Step 0 added to `voice-rewrite.md`. Sub-agent now operates on group-level asks and authors group-level `provided_summary`.
7. **End-to-end smoke test:** re-run against marley corpus, manually verify `review.html` looks like the mockup.

Each step is independently shippable. TDD discipline: fixture updates land in the same commit as the renderer/schema change they exercise.
