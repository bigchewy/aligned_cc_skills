---
---

# Reverse-Engineered-Brand Framework Revamp Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Transform `reverse-engineered-brand` from a flat-synthesis ETL into a pure orchestrator that dispatches owning frameworks in AUTO_MODE, aggregates competitor dossiers + behavioral-alternatives, and produces a tabbed `review.html` review surface with atomic confirm/correct cards.

**Source Design Doc:** `docs/plans/2026-05-16-reverse-engineered-brand-revamp-design.md`

**Mockups:** `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html`

**Architecture:** The orchestrator (`frameworks/reverse-engineered-brand/prompt.md`) runs four phases — Intake → Extract → Competitor Research → Auto-Framework Dispatch → Load. PHASE 2 dispatches each slice's owning framework in AUTO_MODE (overriding WAIT gates) via Task sub-agents, capturing draft markdown + per-slice OQ JSON. PHASE 3 aggregates outputs, writes the brand folder, and dispatches a renderer that fills a placeholder-token `review-template.html` (built from the locked mockup) with the aggregated JSON. The renderer preserves the prior `</` sanitization + `JSON.stringify` discipline + `Read`-based verify-before-open contract.

**Tech Stack:** Markdown prompt files, JSON fixtures (schema-validated at runtime by the orchestrator's LLM), a single standalone HTML template (no framework dependencies — no Tailwind, no Mermaid, no session-restore, no live-refresh), Task tool for sub-agent dispatch.

---

## Prerequisites

None. Every task in this plan is automation-safe (file edits, content authoring, no live API calls).

---

## Task Ordering & File-Level Dependencies

The plan follows the design doc's Build Order. Several tasks modify `frameworks/reverse-engineered-brand/prompt.md` (T16–T20) — these MUST run sequentially in the order listed because each builds on the previous edit's content anchors. Cross-task file ordering:

| File | Tasks (in order) |
|---|---|
| `frameworks/reverse-engineered-brand/prompt.md` | T16 → T17 → T18 → T19 → T20 (all sequential; each anchors on content the previous task preserved) |
| `frameworks/reverse-engineered-brand/synthesize.md` (deletion) | T23 + T24 must finish first (they remove remaining references) → T22 deletes the file |
| `frameworks/reverse-engineered-brand/test-fixtures/` (creation) | T1, T4, T11, T14 (independent — different subfolders) |
| `frameworks/buyer-persona/prompt.md` | T5 only |
| `frameworks/buyer-persona/examples.md` | T10 only |

**Anchor-preservation contract for T17 → T18 → T20:**

- **T17 MUST preserve, verbatim, the existing PHASE 1.4 `signal_tags` filter table** (current prompt.md lines 91–104) AND **the existing PHASE 2.4 heading and gate body**. The PHASE 2 rewrite in T17 spans only Steps 2.1 / 2.2 / 2.3 / collect-status — NOT Step 2.4. T18 will extend Step 2.4 in place.
- **T18 assumes T17 preserved the `**Step 2.4: Ready-to-load verification gate.**` heading verbatim.** If T18's Edit cannot find this anchor in the post-T17 file state, T18 must HALT with a `🔄 BLOCKED` marker citing "Step 2.4 anchor missing — T17 may have removed it; re-run T17 with explicit preservation note." Do NOT improvise a new anchor.
- **T20 assumes the slice mapping table is preserved by T17.** If T20's grep cannot find the slice mapping table in the post-T17 file, T20 must HALT with `🔄 BLOCKED` citing "slice mapping table missing — T17 owns its preservation; re-run T17." Do NOT re-insert the table from scratch in T20 (the authoritative content lives with the PHASE 2 dispatch logic in T17).

---

### ✅ Task 1: Create open-questions schema validation fixtures

**Files:**
- Create: `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/valid-minimal.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/valid-with-alternatives.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/valid-gap-slice.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/invalid-missing-impact.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/invalid-bad-confidence.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/invalid-compound-question.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/README.md`

**Step 1: Verify directory does not already exist**

Run: `ls frameworks/reverse-engineered-brand/test-fixtures/` (via Glob `frameworks/reverse-engineered-brand/test-fixtures/**`)
Expected: no results (the directory will be created by the Write).

**Step 2: Write `valid-minimal.json`**

```json
{
  "schema_version": "0.2.0",
  "folders": [
    {
      "id": "strategy",
      "label": "Strategy",
      "status": "Strong",
      "p0_count": 1,
      "p1_count": 0,
      "p2_count": 0,
      "framework_dispatches": [
        {"framework_id": "5-components-positioning", "fills": "strategy/positioning.md"}
      ]
    }
  ],
  "behavioral_alternatives": [],
  "competitors": [],
  "open_questions": [
    {
      "id": "Q-strategy-positioning-1",
      "global_id": "OQ-1",
      "file": "strategy/positioning.md",
      "slice": "competitive-alternatives",
      "framework_slot": "phase-1-competitive-alternatives",
      "question": "Is the real alternative spreadsheets + manual dispatch?",
      "inferred_value": "spreadsheets + manual dispatch",
      "draft_excerpt": "Best customers were previously cobbling together spreadsheets.",
      "confidence": "medium",
      "impact": "P0",
      "evidence": ["source:#4"],
      "deepen_with": "5-components-positioning",
      "why_it_matters": "Component 1 anchors the positioning frame.",
      "emitted_at": "2026-05-17T14:32:00Z"
    }
  ]
}
```

**Step 3: Write `valid-with-alternatives.json`**

Same shape as Step 2, plus the question has an `alternatives` array:

```json
"alternatives": ["a legacy product (e.g., DispatchTrack)", "no system — ad-hoc phone coordination"]
```

Include one behavioral_alternative and one competitor entry to exercise those arrays:

```json
"behavioral_alternatives": [
  {
    "id": "BA-1",
    "alternative": "Excel + manual dispatch",
    "evidence_quote": "Before we found you we were just throwing it together in spreadsheets every morning.",
    "source": "source:#6",
    "confidence": "high"
  }
],
"competitors": [
  {
    "slug": "dispatchtrack",
    "name": "DispatchTrack",
    "url": "https://dispatchtrack.com",
    "positioning_one_liner": "Last-mile delivery management.",
    "icp_one_liner": "Mid-market retail and distribution.",
    "differentiated_attributes": ["Driver mobile app", "Real-time tracking"],
    "who_they_say_they_beat": ["spreadsheets", "in-house tools"],
    "pricing_signal": "per-seat",
    "voice_traits": ["operational", "metrics-driven"],
    "evidence_quotes": ["..."],
    "identity_verification": "matched",
    "sources": ["https://dispatchtrack.com/about"]
  }
]
```

**Step 4: Write `valid-gap-slice.json`**

GAP folder (no owning framework). `framework_slot: null` and `deepen_with: null` are explicitly allowed for GAP entries:

```json
{
  "schema_version": "0.2.0",
  "folders": [
    {
      "id": "audiences",
      "label": "Audiences",
      "status": "GAP",
      "p0_count": 1,
      "p1_count": 0,
      "p2_count": 0,
      "framework_dispatches": [],
      "gap_frameworks_needed": ["channel-strategy", "audience-segmentation"]
    }
  ],
  "behavioral_alternatives": [],
  "competitors": [],
  "open_questions": [
    {
      "id": "Q-audiences-channels-1",
      "global_id": "OQ-1",
      "file": "audiences/channels/employer.md",
      "slice": "",
      "framework_slot": null,
      "question": "Should channel-strategy be commissioned for this brand?",
      "inferred_value": null,
      "draft_excerpt": null,
      "confidence": "low",
      "impact": "P0",
      "evidence": [],
      "deepen_with": null,
      "why_it_matters": "No framework owns this slice; meta-OQ recommends `/aligned:add-framework channel-strategy`.",
      "emitted_at": "2026-05-17T14:32:00Z"
    }
  ]
}
```

**Step 5: Write three invalid fixtures**

- `invalid-missing-impact.json` — copy `valid-minimal.json` and delete the `impact` field from the open question. Expected validator behavior: hard-fail at PHASE 2.4 with `field: impact, slice: strategy/positioning.md`.
- `invalid-bad-confidence.json` — copy `valid-minimal.json` and change `"confidence": "medium"` → `"confidence": "kinda-sure"`. Expected: hard-fail with `field: confidence, value: kinda-sure (not in [high, medium, low])`.
- `invalid-compound-question.json` — copy `valid-minimal.json` and change the `question` field to `"Is the alternative spreadsheets and is the segment mid-market?"`. Expected: WARNING (not hard-fail) per design — compound-question regex flags but does not block.

**Step 6: Write `test-fixtures/oq-schema/README.md`**

```markdown
# OQ Schema Fixtures (Layer 1)

These JSON fixtures exercise the PHASE 2.4 ready-to-load gate's schema validator. They
are read manually during framework development — there is no automated runner.

| Fixture | Expected gate behavior |
|---|---|
| `valid-minimal.json` | Pass |
| `valid-with-alternatives.json` | Pass |
| `valid-gap-slice.json` | Pass (GAP entries allow `null` for `framework_slot` + `deepen_with`) |
| `invalid-missing-impact.json` | Hard-fail (`field: impact` missing) |
| `invalid-bad-confidence.json` | Hard-fail (`field: confidence` not in enum) |
| `invalid-compound-question.json` | WARNING — compound-question regex match; does NOT block |

Schema reference: `frameworks/reverse-engineered-brand/open-questions-schema.md`.
```

**Step 7: Verify all 7 files exist**

Run (Glob): `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/*`
Expected: 7 files listed.

**Step 8: Commit**

```bash
git add frameworks/reverse-engineered-brand/test-fixtures/oq-schema/
git commit -m "test(reverse-engineered-brand): add OQ schema validation fixtures"
```

---

### ✅ Task 2: Create open-questions-schema.md reference doc

**Files:**
- Create: `frameworks/reverse-engineered-brand/open-questions-schema.md`

**Step 1: Verify file does not exist**

Run (Glob): `frameworks/reverse-engineered-brand/open-questions-schema.md`
Expected: no results.

**Step 2: Write schema doc**

The doc MUST contain:

1. **Top-level structure** — `schema_version` (string, currently `"0.2.0"`), `folders` (array), `behavioral_alternatives` (array), `competitors` (array), `open_questions` (array).
2. **`folders` array entry schema:** `id`, `label`, `status` (enum: `Strong | Partial | Weak | GAP`), `p0_count`, `p1_count`, `p2_count`, `framework_dispatches` (array of `{framework_id, fills}`), optional `gap_frameworks_needed` (array of framework ids for GAP folders).
3. **`behavioral_alternatives` array entry schema:** `id` (e.g., `BA-1`), `alternative` (atomic phrase), `evidence_quote` (verbatim), `source` (typed-prefix: `source:#N`), `confidence` (enum).
4. **`competitors` array entry schema** (per April / OQ-1 inlining decision): `slug`, `name`, `url`, `positioning_one_liner`, `icp_one_liner`, `differentiated_attributes` (verbatim), `who_they_say_they_beat`, `pricing_signal` (enum: `per-seat | enterprise | freemium | usage-based | unknown`), optional `recent_positioning_shift`, `voice_traits` (LOW confidence by default), optional `narrative_one_liner`, `evidence_quotes`, `identity_verification` (enum: `matched | mismatch_flagged | low_confidence`), `sources`. **NOTE: no `channels` field** — unreliable from public web research per April.
5. **`open_questions` array entry schema:**
   - Fields per the design doc's Field Semantics table (lines 302–319 in the design).
   - **Required at emission (validated at PHASE 2.4):** `id`, `file`, `framework_slot`, `confidence`, `impact`, `evidence`, `deepen_with`, AND at least one of `question` or `inferred_value`. For GAP slices, `framework_slot` and `deepen_with` MAY be literal `null`.
   - **Derived (not persisted):** `type` is computed at render time as `confidence === "low" ? "question" : "assumption"`.
6. **`framework_slot` slot-validator rule:** must match `phase-{N}-{kebab(heading)}` exactly against the dispatched framework's PHASE headings. No slot merging across phases — e.g., for `5-components-positioning`, `unique-value` is NOT a valid slot; must be `phase-2-unique-attributes` OR `phase-3-value`.
6a. **Authoritative kebab algorithm** (used to derive `kebab(heading)`):
   - Identify the heading's numbered prefix. The prefix is one of `### PHASE N:` (most frameworks), `### ELEMENT N:` (strategic-narrative), or `## Phase N:` (design-principles uses h2 lower-case "Phase"). The slot-id prefix maps to `phase-N-…`, `element-N-…`, or `phase-N-…` respectively.
   - Lower-case the heading text after the numbered prefix's colon and space.
   - Strip leading/trailing whitespace.
   - Replace runs of `[^a-z0-9]+` with a single hyphen (this collapses spaces, em-dashes, en-dashes, hyphens, parentheses, colons, commas, ampersands, etc.).
   - Strip a leading or trailing hyphen, if present.
   - Examples (real headings from the owning frameworks):
     - `### PHASE 1: Competitive Alternatives` → `phase-1-competitive-alternatives`
     - `### PHASE 5: Market Category` → `phase-5-market-category`
     - `### ELEMENT 1: The World` → `element-1-the-world`
     - `## Phase 2: Design Direction` (design-principles, h2 + lowercase) → `phase-2-design-direction`
6b. **Authoritative slot vocabulary** — derive the complete slot list for each owning framework that has mode-detection deleted (T5–T9) plus the 3 frameworks without mode-detection (`5-components-positioning`, `strategic-narrative`, `design-principles`). Read each framework's `prompt.md`, find every `### PHASE N:` heading, apply the kebab algorithm in 6a, and tabulate. Embed the resulting table in `open-questions-schema.md` under a heading `## Authoritative slot vocabulary`. This table is the source of truth for the slot validator at PHASE 2.4.

   Tabulate per owning framework: `framework_id | phase_number | heading | slot_id`. Skip mode-detection lines and any synthesis-only phases that don't accept user input — those phases will not have OQs and are not addressable slots. (Note: `strategic-narrative` uses `### ELEMENT N:` headings instead of `### PHASE N:`. For that framework, substitute `element` as the prefix: `element-1-world`, `element-2-change`, etc.)

7. **Compound-question regex (PHASE 2.4 warning, not block):** `/\b(and|or)\b.*\?|\?.*\?/`. The regex must NOT match an atomic question listing alternatives like `"per-member, per-transport, or hybrid?"` but MUST match a compound `"Is X true and is Y true?"`. The doc should include both examples explicitly.
8. **Identity-verification semantics:** value semantics from competitor-dossier (matched = source and web agree; mismatch_flagged = divergence detected, OQ emitted; low_confidence = ambiguous identity, OQ recommended).
9. **Cross-link** to `test-fixtures/oq-schema/` with one-line per fixture.

Body should be ~150 lines (concise reference doc). Use the design doc's section "Open Questions Schema" (lines 234–325) as the source.

**Step 3: Verify each test fixture from Task 1 conforms to the schema**

Read each fixture and check the documented required fields are present. For GAP fixture, confirm `framework_slot: null` and `deepen_with: null` are allowed per the schema doc.

**Step 4: Commit**

```bash
git add frameworks/reverse-engineered-brand/open-questions-schema.md
git commit -m "docs(reverse-engineered-brand): add open-questions schema reference"
```

---

### ✅ Task 3: Create auto-mode-preamble.md

**Files:**
- Create: `frameworks/reverse-engineered-brand/auto-mode-preamble.md`

**Step 1: Verify file does not exist**

Run (Glob): `frameworks/reverse-engineered-brand/auto-mode-preamble.md`
Expected: no results.

**Step 2: Write preamble**

The preamble's exact prose comes from the design doc's "Auto-Mode Contract" section (lines 138–184). Use the design doc body verbatim as the preamble content. Critical contract elements that MUST appear (verify each by grep after write):

1. **AUTO_MODE marker** at the top: `AUTO_MODE — non-interactive execution.`
2. **WAIT-override directive:** "Override every \"WAIT for user response\" gate in the framework's prompt."
3. **Skip mode-detection directive:** "Skip any mode-detection question (\"are you running standalone or orchestrated?\"). You are in AUTO_MODE."
4. **Per-assumption record schema** with all 5 fields: `framework_slot`, `inferred_value`, `confidence` (with HIGH/MEDIUM/LOW definitions), `evidence` (typed-prefix array), `impact` (with P0/P1/P2 definitions).
5. **Emission contract:** "At the end of execution, emit: (1) draft markdown to `{brand}/.build/slices/{slice-id}.draft.md`, (2) OQ JSON to `{brand}/.build/slices/{slice-id}.oq.json`."
6. **Schema reference:** points to `frameworks/reverse-engineered-brand/open-questions-schema.md`.
7. **ATOMICITY rule:** "Each open question is a single variable. If you would have asked two things at one WAIT, emit two OQs."
8. **VERIFICATION-STYLE FRAMEWORKS guardrail** (proof-points-audit, competitive-battle-card): May NOT fabricate evidence. Unsupported claim → emit OQ with `confidence: low` and `impact: P0`; do NOT write a draft sentence implying verification. Atomicity rule applies: one OQ per unverified claim.
9. **Cross-framework ordering caveat** (per Architect M1): `competitive-battle-card` may run before positioning finalizes. Orchestrator provides positioning DRAFT (not final). Battle-card OQs depending on positioning being settled tagged `confidence: low`, `impact: P0`, `why_it_matters` notes the upstream dependency.
10. **Canonical pre-synthesis blob placeholder:** the orchestrator passes a `{canonical-pre-synthesis-blob}` substitution describing "what the company is" (org-name, brief positioning hypothesis, ICP hypothesis) so each AUTO_MODE framework has shared baseline context.

**Step 3: Verify by reading back**

Read the file and grep for each of the 10 required elements above. If any is missing, fix and re-verify.

**Step 4: Commit**

```bash
git add frameworks/reverse-engineered-brand/auto-mode-preamble.md
git commit -m "feat(reverse-engineered-brand): add AUTO_MODE preamble contract"
```

---

### ✅ Task 4: Create AUTO_MODE input fixtures for 5-components-positioning

**Files:**
- Create: `frameworks/reverse-engineered-brand/test-fixtures/auto-mode-inputs/5-components-positioning/source-extracts.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/auto-mode-inputs/5-components-positioning/competitor-dossiers.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/auto-mode-inputs/5-components-positioning/behavioral-alternatives.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/auto-mode-inputs/5-components-positioning/canonical-pre-synthesis-blob.md`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/auto-mode-inputs/5-components-positioning/README.md`

**Step 1: Verify directory does not exist**

Run (Glob): `frameworks/reverse-engineered-brand/test-fixtures/auto-mode-inputs/**`
Expected: no results.

**Step 2: Write source-extracts.json**

A JSON array of 2 source extracts conforming to the schema in `frameworks/reverse-engineered-brand/extract.md` (post-T15 with `role` field). Each has at least: `id`, `path`, `type`, `used`, `signal_tags`, `summary`, `key_quotes` (3+ verbatim quotes), `entities` (with `role` field on each entity), `slice_relevance`. Make the content realistic for a fictional last-mile-logistics SaaS company so the AUTO_MODE smoke test exercises positioning extraction. Quotes must contain enough signal to populate competitive alternatives, value, ICP, and category.

**Step 3: Write competitor-dossiers.json**

A JSON array of 2 named-competitor dossiers conforming to the schema in `open-questions-schema.md` (created in T2). Both have `identity_verification: "matched"`. Use realistic names — e.g., `DispatchTrack`, `Onfleet`.

**Step 4: Write behavioral-alternatives.json**

A JSON array of 2 behavioral-alternative entries conforming to the schema:

```json
[
  {"id": "BA-1", "alternative": "Excel + manual dispatch", "evidence_quote": "Before [us] we were just throwing it together in spreadsheets every morning.", "source": "source:#1", "confidence": "high"},
  {"id": "BA-2", "alternative": "Do nothing — accept late deliveries", "evidence_quote": "Half our customers had just given up on the same-day promise.", "source": "source:#2", "confidence": "medium"}
]
```

**Step 5: Write canonical-pre-synthesis-blob.md**

A 1-paragraph baseline:

```markdown
# Canonical Pre-Synthesis Blob — FixtureCo

FixtureCo is a last-mile delivery management SaaS for mid-market retail and distribution.
Best-fit customers are operations leaders coordinating 50–500 daily deliveries who currently
use spreadsheets + phone calls. Primary competitive frame is replacing manual coordination,
not displacing legacy products. (FIXTURE — not a real company.)
```

**Step 6: Write README.md**

Documents how to use the fixtures: paste auto-mode-preamble + this canonical blob + the 3 JSON fixtures into a Task dispatch with `frameworks/5-components-positioning/prompt.md` as the framework. Sub-agent should emit `{output-draft-path}` + `{output-open-questions-path}` per the AUTO_MODE preamble's emission contract. **Acceptance criteria (per OQ-4 trigger condition in the design):** the dispatched framework emits OQs for every PHASE in its prompt (PHASE 1–5; PHASE 6 is synthesis) without skipping or merging, and every OQ's `framework_slot` validates against the slot rule from Task 2.

**Step 7: Verify all 5 files exist**

Run (Glob): `frameworks/reverse-engineered-brand/test-fixtures/auto-mode-inputs/5-components-positioning/*`
Expected: 5 files listed.

**Step 8: Commit**

```bash
git add frameworks/reverse-engineered-brand/test-fixtures/auto-mode-inputs/
git commit -m "test(reverse-engineered-brand): add AUTO_MODE vertical-slice fixtures for 5-components-positioning"
```

---

### ✅ Task 5: Remove mode-detection from buyer-persona framework

**Files:**
- Modify: `frameworks/buyer-persona/prompt.md` (delete mode-detection block at lines 24 + 34; delete orphan PHASE 11 reference at line 238; simplify PHASE 6 hand-off contract)

**Step 1: Read current content**

Read `frameworks/buyer-persona/prompt.md` lines 20–40 and 230–250 to capture the current text.

**Step 2: Delete the "Mode detection" preamble line near line 24**

Using Edit, locate the unique line beginning `**Mode detection:** At PHASE 1, confirm whether you are running standalone or as a sub-framework invoked by` and delete it (replace with empty string — leave surrounding blank line spacing tidy by collapsing repeated blank lines).

**Step 3: Delete the "First — standalone or orchestrated?" question near line 34**

Locate the unique block beginning `**First — standalone or orchestrated?** Are you running this as a standalone session` and delete the entire question + the WAIT statement that follows it. If the surrounding numbering changes (e.g., "Second", "Third" follow), renumber to start from "First".

**Step 4: Simplify PHASE 6 hand-off contract**

The current hand-off contract has two branches (standalone vs. orchestrated). Delete the "Orchestrated mode" branch (the bullet near line 238 referring to PHASE 11). Collapse the contract to a single instruction: "Write the assembled file directly to `brand/personas/{role-kebab}.md`. Confirm the path to the user." Remove the "(user confirmed at PHASE 1)" qualifier since there is no longer a PHASE 1 mode prompt.

**Step 5: Verify by reading**

Read the modified file and grep for `mode detection`, `standalone or orchestrated`, `PHASE 11`. Expected: 0 matches for each.

**Step 6: Commit**

```bash
git add frameworks/buyer-persona/prompt.md
git commit -m "refactor(buyer-persona): remove mode-detection WAITs + orphan PHASE 11 reference"
```

> **Behavior change:** Standalone users no longer see a "standalone or orchestrated" question at PHASE 1. The framework always writes directly to disk. AUTO_MODE invocation overrides via the preamble (no per-framework mode awareness needed).

---

### ✅ Task 6: Remove mode-detection from brand-voice framework

**Files:**
- Modify: `frameworks/brand-voice/prompt.md` (delete mode-detection block at lines 25 + 35; simplify PHASE 8 hand-off contract)

**Step 1: Read current content**

Read `frameworks/brand-voice/prompt.md` lines 20–45 and 300–360.

**Step 2: Delete the "Mode detection" preamble**

Locate and delete the unique line beginning `**Mode detection:** At PHASE 1, confirm whether you are running standalone or as a sub-framework invoked by`.

**Step 3: Delete the "First — standalone or orchestrated?" question**

Locate and delete the unique block beginning `**First — standalone or orchestrated?**` and the WAIT statement following it.

**Step 4: Simplify PHASE 8 hand-off**

Collapse the hand-off contract to: "Write the complete file to `brand/language/voice.md`. Confirm the path to the user and note any sections that should be revisited once more copy exists." Remove the orchestrated-mode branch (the standalone-vs-orchestrated bullet block around lines 353–355).

**Step 5: Verify**

Grep `frameworks/brand-voice/prompt.md` for `mode detection`, `standalone or orchestrated`. Expected: 0 matches.

**Step 6: Commit**

```bash
git add frameworks/brand-voice/prompt.md
git commit -m "refactor(brand-voice): remove mode-detection WAITs"
```

---

### ✅ Task 7: Remove mode-detection from messaging-distillation framework

**Files:**
- Modify: `frameworks/messaging-distillation/prompt.md` (delete mode-detection block at lines 29 + 39; delete orphan PHASE 11 reference at line 411; simplify PHASE 9 hand-off contract)

**Step 1: Read current content**

Read `frameworks/messaging-distillation/prompt.md` lines 25–45 and 400–415.

**Step 2: Delete the "Mode detection" preamble**

Locate and delete the unique line beginning `**Mode detection:** At PHASE 1, confirm whether you are running standalone or as a sub-framework invoked by`.

**Step 3: Delete the "First — standalone or orchestrated?" question**

Locate and delete the block beginning `**First — standalone or orchestrated?**` and its WAIT.

**Step 4: Simplify PHASE 9 hand-off (line 411 area)**

Delete the orchestrated-mode bullet that references "the atomic write in its own PHASE 11" (orphan reference). Keep only the standalone-mode instruction: "Write the assembled file directly to `brand/language/messaging.md`. Confirm the path to the user."

**Step 5: Verify**

Grep `frameworks/messaging-distillation/prompt.md` for `mode detection`, `standalone or orchestrated`, `PHASE 11`. Expected: 0 matches for each.

**Step 6: Commit**

```bash
git add frameworks/messaging-distillation/prompt.md
git commit -m "refactor(messaging-distillation): remove mode-detection WAITs + orphan PHASE 11 reference"
```

---

### ✅ Task 8: Remove mode-detection from competitive-battle-card framework

**Files:**
- Modify: `frameworks/competitive-battle-card/prompt.md` (delete mode-detection block at lines 26 + 36; delete line 169 orchestrated-mode handback; simplify PHASE 5)

**Step 1: Read current content**

Read `frameworks/competitive-battle-card/prompt.md` lines 20–45 and 160–175.

**Step 2: Delete the "Mode detection" preamble and orchestrated-mode question**

Locate and delete the two unique mode-related blocks (the `**Mode detection:**` line and the `**First — standalone or orchestrated?**` block + its WAIT).

**Step 3: Simplify PHASE 5 hand-off (line 169 area)**

Delete the orchestrated-mode bullet ("Yield the assembled markdown back to the `reverse-engineered-brand` orchestrator — do not write a file."). Keep only the standalone-mode instruction.

**Step 4: Verify**

Grep `frameworks/competitive-battle-card/prompt.md` for `mode detection`, `standalone or orchestrated`. Expected: 0 matches.

**Step 5: Commit**

```bash
git add frameworks/competitive-battle-card/prompt.md
git commit -m "refactor(competitive-battle-card): remove mode-detection WAITs + orchestrated-mode handback"
```

---

### ✅ Task 9: Remove mode-detection from proof-points-audit framework

**Files:**
- Modify: `frameworks/proof-points-audit/prompt.md` (delete mode-detection block at lines 27 + 37; simplify PHASE 7 hand-off contract)

**Step 1: Read current content**

Read `frameworks/proof-points-audit/prompt.md` lines 20–45 and 220–240.

**Step 2: Delete the "Mode detection" preamble and orchestrated-mode question**

Locate and delete both unique mode-related blocks.

**Step 3: Simplify PHASE 7 hand-off**

Delete the orchestrated-mode branch from the hand-off contract. Keep only the standalone branch ("Write the file(s) to `brand/proof/` in the current repo").

**Step 4: Verify**

Grep `frameworks/proof-points-audit/prompt.md` for `mode detection`, `standalone or orchestrated`. Expected: 0 matches.

**Step 5: Commit**

```bash
git add frameworks/proof-points-audit/prompt.md
git commit -m "refactor(proof-points-audit): remove mode-detection WAITs"
```

---

### ✅ Task 10: Clean up buyer-persona/examples.md mode-detection example

**Files:**
- Modify: `frameworks/buyer-persona/examples.md` (remove the "standalone or orchestrated" example dialogue around line 119)

**Step 1: Read lines 110–130 of `frameworks/buyer-persona/examples.md`**

**Step 2: Delete the example block that includes the standalone-vs-orchestrated dialogue**

Locate and delete the entire example block beginning at the example heading that precedes line 119 (likely "Confirming write mode before output" or similar) through the end of the example. The block uniquely contains the string `Before I assemble the file: standalone or orchestrated?`.

**Step 3: Verify**

Grep `frameworks/buyer-persona/examples.md` for `standalone or orchestrated`. Expected: 0 matches.

**Step 4: Commit**

```bash
git add frameworks/buyer-persona/examples.md
git commit -m "docs(buyer-persona): remove standalone-vs-orchestrated example"
```

---

### ✅ Task 11: Create render test fixtures

**Files:**
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/fixture-tiny.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/fixture-realistic.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/fixture-stress.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/README.md`

**Step 1: Verify directory does not exist**

Run (Glob): `frameworks/reverse-engineered-brand/test-fixtures/render/**`
Expected: no results.

**Step 2: Write `fixture-tiny.json`**

A schema-conformant OQ JSON file with: 1 folder (`strategy`), 6 open questions distributed across confidence × impact (1× HIGH/P0, 1× HIGH/P1, 2× MED/P0, 1× MED/P2, 1× LOW/P0), 1 behavioral_alternative, 0 competitors. Used for layout-spot-check rendering.

**Step 3: Write `fixture-realistic.json`**

A schema-conformant OQ JSON file with: 7 folders (Strong/Partial/Weak/GAP mix), ~40 open questions covering every confidence × impact combination, 2 GAP slices (`audiences/channels/` + `audiences/segments/`) each emitting one P0 meta-OQ pointing to `/aligned:add-framework`, 4 behavioral_alternatives, 3 competitors. **Includes one OQ whose `question` field contains a `</script>` substring** to exercise the sanitization contract. Includes one OQ whose `inferred_value` contains a verbatim newline + backslash + double-quote to exercise JSON stringify discipline.

**Step 4: Write `fixture-stress.json`**

A schema-conformant OQ JSON file with: 7 folders (matching the design's brand-folder subdirectory list — `strategy`, `language`, `audiences`, `personas`, `market`, `proof`, `design`; the HTML has 9 top-level tabs but `Overview` and `Competitive Context` are render-only views over the same 7-folder dataset), ~130 open questions (Marley-equivalent volume), 8 behavioral_alternatives, 5 competitors. Used to verify render time + scroll/tab performance.

**Step 5: Write `test-fixtures/render/README.md`**

```markdown
# Render Fixtures (Layer 2)

Schema-conformant JSON files used to manually verify `review-template.html` rendering.

| Fixture | Purpose | Critical checks |
|---|---|---|
| `fixture-tiny.json` | Layout spot-check (6 OQs) | Tab nav, single-page-scroll structure |
| `fixture-realistic.json` | Full envelope (~40 OQs, GAP slices, sanitization stress) | `</script>` sanitization, JSON stringify escaping, GAP meta-OQ rendering, paste-back generator copy-clean |
| `fixture-stress.json` | Volume (~130 OQs, Marley-equivalent) | Scroll/tab perf, paste-back generator on a 30-OQ folder |

Manual procedure: paste each fixture into the renderer's `{open-questions-json}` substitution
point in `review-template.html`, open the result in a browser, verify against the locked
mockup at `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html`.
```

**Step 6: Verify all 4 files exist**

Run (Glob): `frameworks/reverse-engineered-brand/test-fixtures/render/*`
Expected: 4 files.

**Step 7: Commit**

```bash
git add frameworks/reverse-engineered-brand/test-fixtures/render/
git commit -m "test(reverse-engineered-brand): add render-layer HTML test fixtures"
```

---

### ✅ Task 12: Build review-template.html from locked mockup

> MOCKUP DEVIATION: Exec summary conf-row replaced with `id="exec-confidence-cards"` placeholder for JS rendering. Strengths & Gaps static list items replaced with `id="strengths-list"` / `id="gaps-list"` placeholders. `oq-context-toggle` CSS kept alongside new `details.oq-context` styles for backward compatibility with any JS-rendered cards using the old button/div pattern.

**Files:**
- Create: `frameworks/reverse-engineered-brand/review-template.html`

**Step 1: Verify file does not exist**

Run (Glob): `frameworks/reverse-engineered-brand/review-template.html`
Expected: no results.

**Step 2: Read the locked mockup**

Read `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html` in chunks (it is 1954 lines). Capture full structure: `<head>`, CSS, all 9 panels (`panel-overview`, `panel-competitive`, `panel-strategy`, `panel-language`, `panel-audiences`, `panel-personas`, `panel-market`, `panel-proof`, `panel-design`), JS functions.

**Step 3: Copy mockup → review-template.html with placeholder tokens**

Substitute the mockup's hard-coded content with templated tokens. Specifically:

| Mockup content | Template token |
|---|---|
| `<title>Brand-folder review</title>` (line 6) | `<title>Brand-folder review — {Org Name}</title>` (strip the word "mockup" if present — H7 fix) |
| Hard-coded company name in headings | `{Org Name}` |
| Hard-coded folder list in Overview "Sections at a glance" | `<!-- TEMPLATE: folders array → rendered by JS from OPEN_QUESTIONS.folders -->` placeholder div with id `sections-at-a-glance` |
| Hard-coded "Where to focus first" rows | `<div id="where-to-focus-first"></div>` placeholder |
| Hard-coded executive summary numbers (5-tile snapshot) | `<div id="exec-snapshot"></div>` placeholder, filled by JS from OPEN_QUESTIONS counts |
| Hard-coded behavioral-alternatives list | `<div id="behavioral-alternatives"></div>` placeholder, filled by JS from `OPEN_QUESTIONS.behavioral_alternatives` |
| Hard-coded competitor cards | `<div id="competitor-cards"></div>` placeholder, filled by JS from `OPEN_QUESTIONS.competitors` |
| Hard-coded folder draft/assumption/question content per panel | `<div id="panel-strategy-content"></div>` etc., filled by JS from `OPEN_QUESTIONS.open_questions` grouped by `folders[].id` |
| Hard-coded paste-back textareas | `<textarea id="pasteback-strategy"></textarea>` etc., filled by JS via `buildPastebackFor(folderId)` |

**Step 4: Insert the page-header job statement (H7 fix)**

Above the title on every tab (in the template's `<header>` or top-of-`<main>` location), insert exactly:

```html
<p class="job-statement">Review the auto-generated brand folder. Toggle Approve/Reject on assumptions, answer questions, then copy the per-folder paste-back to Claude Code.</p>
```

The word "mockup" MUST NOT appear in the production title. (Defensive sanity check — verified the source mockup file's `<title>` does not currently contain "mockup", but the substitution `<title>Brand-folder review — {Org Name}</title>` makes a regression impossible regardless.)

**Step 5: Replace `oq-context-toggle` buttons with native `<details>` (H7 fix)**

The mockup uses 16 custom `<button class="oq-context-toggle" onclick="toggleContext(this)">Context</button>` toggles paired with sibling `<div class="oq-context">` panels. Replace each pair with native `<details>` markup:

```html
<details class="oq-context">
  <summary>Context</summary>
  <!-- previous .oq-context contents -->
</details>
```

Update the CSS to style `details.oq-context summary` and `details.oq-context[open]` instead of `.oq-context-toggle` + `.oq-context.expanded`. Delete the `toggleContext` JS function — `<details>` is native and needs no JS.

**Step 6: Insert tokens for JS-side substitutions**

Add at the top of the `<script>` block:

```html
<script>
  const OPEN_QUESTIONS = {open-questions-json};
  const BRAND_FOLDER_PATH = "{brand-folder-path}";
  const ORG_NAME = "{org-name}";
  // ...remainder of JS (tab switching, card toggles, paste-back generator) preserved from mockup
</script>
```

Authoritative substitution tokens: `{open-questions-json}`, `{brand-folder-path}`, `{org-name}`. The renderer (T21) will substitute these.

**Step 7: Preserve mockup JS functions**

Carry forward all interactivity from the mockup verbatim: tab switching, per-card Approve/Reject for assumptions, Answer/Skip/Leave toggles for questions, dirty-bit paste-back generator with `[Copy]` + `[Regenerate]` buttons, `document.execCommand('copy')` fallback for `file://`.

**Step 8: Verify mockup fidelity**

Read `docs/mockups/2026-05-16-reverse-engineered-brand-revamp/review-html-design.html` (relevant sections only — the file is 1954 lines, read in chunks of ~300 lines per Read call). Compare your template:
- Layout structure matches (sections, columns, ordering)
- All 9 top-level tabs present, in the same order (`Overview`, `Competitive Context`, `strategy`, `language`, `audiences`, `personas`, `market`, `proof`, `design`)
- Overview sub-tabs present (`Executive Summary`, `Strengths & Gaps`, `Where to Focus First`)
- Behavioral-alternatives section renders FIRST on Competitive Context tab (above named-competitor cards) per April critique
- Job-statement paragraph present on every tab (H7 fix)
- `<details>` elements replace `oq-context-toggle` buttons
- `Channels` does NOT appear as a `<dt>` row on any competitor card (M9 reconciliation — verify by grepping the template: only the existing GAP indicator at the Overview tree should reference `Channels`)
- All chip vocab visible: `[P0/P1/P2]`, `[confidence: HIGH/MED/LOW]`, `[file path]`; jargon chips (`slot:`, `deepen:`) inside `<details>` only

If you intentionally deviate from the mockup, add a note below the task heading:
> MOCKUP DEVIATION: [what changed and why]

**Step 9: Verify the template is loadable as HTML**

Read the template file from disk. Check for:
- `<!DOCTYPE html>` first line
- Both `<script>` tags present
- File ends with `</html>`
- All placeholder tokens (`{open-questions-json}`, `{brand-folder-path}`, `{org-name}`) appear at least once each

**Commit cadence — Task 12 produces THREE commits, not one.** The template is ~1200 LOC derived from a 1954-line mockup; a single commit obscures regressions. Commit at the three checkpoint boundaries below; the final commit completes the task.

**Commit A — after Steps 1-3 (scaffold + token placeholders):**

```bash
git add frameworks/reverse-engineered-brand/review-template.html
git commit -m "feat(reverse-engineered-brand): scaffold review-template.html with substitution tokens"
```

**Commit B — after Steps 4-5 (job-statement header + `<details>` replacement):**

```bash
git add frameworks/reverse-engineered-brand/review-template.html
git commit -m "feat(reverse-engineered-brand): add job-statement header, replace oq-context-toggle with native details"
```

**Commit C — after Steps 6-9 (JS substitutions + mockup fidelity verify + loadable HTML verify):**

```bash
git add frameworks/reverse-engineered-brand/review-template.html
git commit -m "feat(reverse-engineered-brand): wire JS substitutions, preserve mockup interactivity, verify template loadable"
```

---

### ✅ Task 13: Create competitor-dossier.md prompt template

**Files:**
- Create: `frameworks/reverse-engineered-brand/competitor-dossier.md`

**Step 1: Verify file does not exist**

Run (Glob): `frameworks/reverse-engineered-brand/competitor-dossier.md`
Expected: no results.

**Step 2: Write the sub-agent prompt template**

Modeled on the existing `extract.md` / `synthesize.md` patterns. Sections:

1. **Role:** Competitor-dossier researcher, dispatched by `reverse-engineered-brand` PHASE 1.5b.
2. **Inputs (placeholders):**
   - `{competitor-name}` — the competitor's display name
   - `{competitor-slug}` — kebab-case slug
   - `{source-extracts-paths}` — JSON array of paths to source extracts that mention this competitor (filter by `entities.role: competitor`)
   - `{output-json-path}` — `{brand-folder-path}/.build/competitors/{slug}.json`
   - `{context-blurb}` — same one-paragraph baseline used by extractor
3. **Procedure:**
   - Read all source extracts. Capture every verbatim mention of this competitor.
   - Do bounded web research: fetch the competitor's homepage + up to 4 other pages (about, pricing, customers). **Cap: 5 URLs total.**
   - **Identity verification step:** verify the web-fetched company matches the source-material company (same product domain, same ICP signal). If divergence detected, set `identity_verification: mismatch_flagged` and emit an OQ recommending the user confirm the right competitor.
4. **Output schema** (must match `open-questions-schema.md` `competitors` array entry from T2): name, url, positioning_one_liner, icp_one_liner, differentiated_attributes (verbatim from competitor site), who_they_say_they_beat, pricing_signal (per-seat | enterprise | freemium | usage-based | unknown), optional recent_positioning_shift, voice_traits (LOW confidence by default), optional narrative_one_liner, evidence_quotes (verbatim from web research), identity_verification (matched | mismatch_flagged | low_confidence), sources (URL list, ≤5).
5. **NO `channels` field** (per April — unreliable from public research). If channel signal IS strong, surface as a free-form observation in `evidence_quotes`.
6. **Soft-fail rule — full failure-mode enumeration.** If bounded web research returns zero usable information for any of the following reasons, set `identity_verification: low_confidence`, emit an OQ recommending the user provide source material, and write a minimal dossier with what's available from extracts only. Do NOT abort — the orchestrator's PHASE 1.5b is bounded soft-fail.

   Enumerated failure modes (the sub-agent MUST handle each):
   - `404 / 410 / 451` — page not found, gone, or unavailable for legal reasons
   - `403 / 401` — blocked (Cloudflare, paywall, login wall)
   - `429` — rate-limited; do NOT retry within this dispatch
   - `5xx` — server error; do NOT retry within this dispatch
   - `timeout` — request exceeded the WebFetch default timeout
   - `network-unreachable` — DNS resolution failure or no route to host
   - `tls-error` — certificate expired/invalid; treat as untrustworthy
   - `navigation-chrome-only` — fetched page returns only nav/footer chrome with no substantive content (heuristic: < 500 chars of extractable text)
   - `parse-failure` — HTML parser returns no readable structure (e.g., heavy JS-only page)
   - `no-public-site` — extracts mention the competitor but no URL was discoverable

   **Cumulative latency cap:** if the cumulative wall time for this competitor's research exceeds 60 seconds, abort the remaining fetches and proceed with whatever was captured so far. Record `partial_research: true` on the dossier.

   **Determinism note for testing:** The fixtures in Task 14 (`test-fixtures/competitor-identity/`) contain pre-prepared URL excerpts that the sub-agent reads INSTEAD of issuing live fetches during smoke testing. Reference these from the prompt under a `## Test mode` section: "When dispatched with `{test-fixtures-path}` non-empty, read prepared excerpts from that path instead of issuing WebFetch calls. This makes Layer 5 verification deterministic."

7. **Return contract:** compact ≤200-word status block (`COMPETITOR`, `IDENTITY_VERIFICATION`, `URLS_FETCHED` count, `URLS_FAILED` array of {url, reason}, `EVIDENCE_QUOTE_COUNT`, `CUMULATIVE_LATENCY_SECONDS`, `PARTIAL_RESEARCH` boolean, `NOTES`). No body returned to orchestrator.

**Step 3: Verify file is ~120 lines and contains all sections**

Read the file. Grep for: `competitor-name`, `identity_verification`, `pricing_signal`, `Cap: 5 URLs`, `cumulative latency`, `partial_research`, `Test mode`. Expected: each appears at least once.

**Step 4: Commit**

```bash
git add frameworks/reverse-engineered-brand/competitor-dossier.md
git commit -m "feat(reverse-engineered-brand): add competitor-dossier sub-agent prompt"
```

---

### ✅ Task 14: Create Layer 5 identity verification fixtures

**Files:**
- Create: `frameworks/reverse-engineered-brand/test-fixtures/competitor-identity/ambiguous-name.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/competitor-identity/rebranded-recent.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/competitor-identity/clean-match.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/competitor-identity/README.md`

**Step 1: Verify directory does not exist**

Run (Glob): `frameworks/reverse-engineered-brand/test-fixtures/competitor-identity/**`
Expected: no results.

**Step 2: Write `ambiguous-name.json`**

A fixture simulating two real "Apex" companies (one in logistics, one in HR). Source extract mentions "Apex" in a logistics context. Web fetch (simulated input — the fixture contains the prepared URL excerpts the dossier sub-agent would see) returns one logistics-Apex and one HR-Apex. **Expected dossier output:** `identity_verification: mismatch_flagged`, one OQ in `open_questions` with `confidence: low`, `impact: P0`, recommending the user disambiguate.

**Step 3: Write `rebranded-recent.json`**

Source extract names "OldCorp". Web fetch returns the rebranded site "NewCorp (formerly OldCorp)". **Expected:** `identity_verification: matched`, dossier captures both names, evidence_quote cites the rebrand notice. No OQ emitted (clean detection).

**Step 4: Write `clean-match.json`**

Source extract names "DispatchTrack". Web fetch returns the canonical DispatchTrack site with matching product domain. **Expected:** `identity_verification: matched`, no OQ.

**Step 5: Write `README.md`**

Documents each fixture's expected `identity_verification` value and OQ-emission behavior.

**Step 6: Verify all 4 files exist**

Run (Glob): `frameworks/reverse-engineered-brand/test-fixtures/competitor-identity/*`
Expected: 4 files.

**Step 7: Commit**

```bash
git add frameworks/reverse-engineered-brand/test-fixtures/competitor-identity/
git commit -m "test(reverse-engineered-brand): add competitor-identity verification fixtures"
```

---

### ✅ Task 15: Extend extract.md with entities.role field

**Files:**
- Modify: `frameworks/reverse-engineered-brand/extract.md` (entities schema; the existing schema uses separate sub-arrays for `people`/`competitors`/`audiences`/`claims`)

**Step 1: Read current extract.md**

Read the full file (82 lines).

**Step 2: Decide schema-restructure approach**

Two options per the design's D7 correction:
- **Option A:** Unified `entities` array where each entity has a `role` field (one of `competitor | customer | partner | person | audience | claim | other`).
- **Option B:** Keep separate `people`/`competitors`/`audiences`/`claims` sub-arrays AND aggregate across them in PHASE 1.5a.

**Chosen approach: Option A** — unified `entities` array with `role` field. Rationale: PHASE 1.5a's competitor aggregation needs `role` filtering; embedding it as a first-class field is simpler than maintaining four sub-array aggregations. Per the design's "Schema-restructure note": old `.build/extracts/*.json` only live across one build, so no migration is needed.

**Step 3: Modify the entities schema (extract.md lines ~45–49)**

Edit the file to replace:

```
- `entities` — structured lists of named things mentioned in the source:
  - `people` — names + roles if given
  - `competitors` — explicitly named competing products/services
  - `audiences` — segments, personas, channels mentioned
  - `claims` — quantitative or specific factual claims (e.g., "75% of HTN patients not at goal", "RCT showed 10mmHg reduction")
```

…with:

```
- `entities` — flat array of named things mentioned in the source. Each entry has:
  - `name` — the entity's name (e.g., "DispatchTrack", "VP of Operations", "75% of HTN patients not at goal")
  - `role` — one of: `competitor` | `customer` | `partner` | `person` | `audience` | `claim` | `other`
  - `verbatim_quote` — optional 1-line verbatim quote from the source that supports this entity
  - `notes` — optional context (e.g., "named alongside legacy systems", "mentioned as a target persona")
```

**Step 4: Optionally extend `signal_tags`**

The design notes this is optional. If extending: add `competitor-named` to the valid signal_tag list so PHASE 1.5a's filter can locate sources that mention competitors quickly. This is a soft optimization; skip if the current `signal_tags` set already covers it.

Decision for this plan: **skip** the signal_tags extension. PHASE 1.5a can filter on `entities.role: competitor` directly without a separate tag. (Adding a tag duplicates information.)

**Step 5: Update any example JSON inside extract.md to use the new schema**

If extract.md has example JSON blocks showing the old sub-arrays, update them to use the flat `entities` array with `role`.

**Step 6: Verify by reading**

Read the modified `extract.md`. Grep for `entities`, `role`, the four old sub-array names (`people:`, `competitors:`, `audiences:`, `claims:`). Expected: `entities` and `role` present; the four sub-array names should appear only as `role` enum values (or not at all if old example blocks were rewritten).

**Step 7: Commit**

```bash
git add frameworks/reverse-engineered-brand/extract.md
git commit -m "refactor(reverse-engineered-brand): flatten entities schema with role field"
```

> **Behavior change:** `.build/extracts/*.json` written by the OLD extractor will not parse with the new PHASE 1.5a — but extracts only live across one build, so no migration is needed.

---

### ✅ Task 16: Add PHASE 1.5 (behavioral alternatives + competitor dossier dispatch) to prompt.md

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (insert a new `### PHASE 1.5: Competitor Research` section between current PHASE 1 and PHASE 2)

**Step 1: Read prompt.md around the PHASE 1 → PHASE 2 boundary**

Read `frameworks/reverse-engineered-brand/prompt.md` lines 100–115 to locate the seam.

**Step 2: Insert PHASE 1.5 section**

Use Edit to add the new section. The `old_string` is the current `### PHASE 2: Transform — Sub-agent synthesis per slice (silent)` heading; the `new_string` is the new PHASE 1.5 section followed by that same heading. PHASE 1.5 contains:

**Step 1.5a — Orchestrator-side aggregation (cheap, no sub-agents):**

- Read all source extracts produced in PHASE 1.
- **Behavioral-alternatives extraction:** scan each extract's `key_quotes` for non-product alternative phrases ("spreadsheets," "manual coordination," "do nothing," "hiring temps," ad-hoc phone calls). For each match, record: `id` (BA-N), `alternative` (atomic phrase), `evidence_quote` (verbatim), `source` (typed-prefix), `confidence` (HIGH if multiple sources, MEDIUM if one, LOW if inferred).
- **Competitor aggregation:** filter every extract's `entities` array for `role: competitor`. Aggregate by `name` (case-insensitive). Count mentions across all extracts. Combine with user-supplied competitor names from PHASE 0 (user-supplied take priority — never dropped, always make the final list).
- **Rank and cap:** sort competitors by `mention_count` descending. Tie-break by alphabetical order of slug for determinism. Cap at 5 competitors total (or 3 minimum if fewer surfaced). The extract schema (after T15) carries `name` + `role` + optional `verbatim_quote` per entity but does NOT carry per-mention provenance (e.g., "customer quote" vs. "product page"), so signal-strength weighting is not possible at this layer — mention-count ranking is the deterministic proxy. If finer ranking is needed in the future, extend `extract.md` to record per-mention provenance.
- Write `{brand-folder-path}/.build/behavioral-alternatives.json` (the array of behavioral-alternative entries).
- Write `{brand-folder-path}/.build/competitor-list.json` (the array of `{slug, name, mention_count, source_ids}` records to dispatch).

**Step 1.5b — Sub-agent dossier dispatch (parallel):**

- Read `frameworks/reverse-engineered-brand/competitor-dossier.md` once (the prompt template).
- For each competitor in the competitor-list (≤5), dispatch a Task with `subagent_type: general-purpose` and substituted placeholders: `{competitor-name}`, `{competitor-slug}`, `{source-extracts-paths}` (filtered to extracts that mention this competitor — JSON array of absolute paths), `{output-json-path}` = `{brand-folder-path}/.build/competitors/{slug}.json`, `{context-blurb}`.
- Dispatch all dossier sub-agents in a single message (multiple Task tool calls in one assistant message — parallel execution). Competitor count is bounded (≤5) so a single batch is fine.
- **Soft-fail on zero competitors:** if PHASE 0 yielded no user-supplied names AND PHASE 1.5a aggregated zero competitor entities, emit a single meta-OQ at PHASE 3 aggregation time (`why_it_matters: "No competitor signal in source material — recommend manual addition"`) and continue. Do NOT hard-fail.

**Step 3: Verify**

Read the modified prompt.md and grep for `PHASE 1.5`, `behavioral-alternatives.json`, `competitor-dossier.md`. Expected: each appears.

**Step 4: Commit**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reverse-engineered-brand): add PHASE 1.5 competitor research (behavioral + dossier)"
```

---

### ✅ Task 17: Replace PHASE 2 with auto-framework dispatch in prompt.md

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (replace the existing PHASE 2 Steps 2.1 / 2.2 / 2.3 / status-collection — preserve Step 2.4 verbatim and preserve the PHASE 1.4 signal_tags filter table)

**Preservation contract (READ BEFORE EDITING):**

This task rewrites only the PHASE 2 dispatch logic (existing Steps 2.1 / 2.2 / 2.3 and the status-collection block). It MUST NOT touch:

- **PHASE 1.4 `signal_tags` filter table** (current lines ~91–104) — the slice→signal_tags lookup table the orchestrator uses to filter source extracts per slice. PHASE 2 references it; PHASE 1.5 references it. Removing it breaks both.
- **Step 2.4 heading + gate body** (current lines ~170–178) — T18 extends Step 2.4 in place. Removing it forces T18 to re-create from scratch, losing the anchor contract.
- **Slice mapping table** (current lines ~120–132) — preserved as part of the rewrite (re-included verbatim in the new PHASE 2 body — see Step 2 below).

**Step 1: Read the current PHASE 2 body in full**

Read `frameworks/reverse-engineered-brand/prompt.md` lines 88–180 to capture PHASE 1.4 (the signal_tags filter table), the existing PHASE 2 content, AND the Step 2.4 gate. Quote the PHASE 1.4 table and Step 2.4 heading + body in working memory before editing — these must survive the rewrite verbatim.

**Step 2: Rewrite PHASE 2 (auto-framework dispatch)**

Use Edit to replace only the Steps 2.1 / 2.2 / 2.3 / collect-status content. The Edit's `old_string` must START at the `### PHASE 2: Transform — Sub-agent synthesis per slice (silent)` heading (unique) AND END at the line immediately BEFORE `**Step 2.4: Ready-to-load verification gate.**`. The Edit's `new_string` must include the slice mapping table verbatim from the read in Step 1 plus the new PHASE 2 body below.

The new body:

**Title change:** `### PHASE 2: Auto-Framework Dispatch (silent)`

**Context-bloat guard** (preserved from existing PHASE 2): The orchestrator MUST NOT read source extracts, framework prompts, or canonical pre-synthesis blob bodies into its own context. Each slice's framework runs in a sub-agent dispatched with the owning framework's full prompt + the AUTO_MODE preamble + the slice's filtered inputs.

**Step 2.1: Determine the slice list.** (Preserved — inspect Source Registry; decide which slice instances to produce; conditional slices only if domain warrants.)

**Skip slices with no signal** (preserved): if filtered extract list is empty for a slice, mark `status: missing`, `synthesis_method: skipped_no_signal`, add OQ.

**Step 2.2: Build the canonical pre-synthesis blob.**

The orchestrator authors a 1-paragraph `canonical-pre-synthesis-blob.md` in `{brand-folder-path}/.build/` from the Source Registry: org-name, brief positioning hypothesis (extracted from PHASE 1 aggregated signal), brief ICP hypothesis. This blob is identical content passed to every framework dispatch so they share a baseline view of "what the company is".

**Step 2.3: Dispatch frameworks in parallel.**

For each non-skipped slice instance:
- Look up `owning-framework-id` from the slice mapping table.
- If owning framework is `null` (GAP slice — `audiences/channels/*`, `audiences/segments/*`): do NOT dispatch a framework. Emit one P0 meta-OQ per missing framework (deduplicated at PHASE 3.1, so emit one per GAP slice instance; PHASE 3 deduplicates by `gap_frameworks_needed`).
- Otherwise, read `frameworks/{owning-framework-id}/prompt.md` and `frameworks/reverse-engineered-brand/auto-mode-preamble.md`. Concatenate: preamble + ORIGINAL framework prompt. Dispatch a Task with `subagent_type: general-purpose` and substituted placeholders:
  - `{slice-id}` — the slice path (e.g., `strategy/positioning.md`)
  - `{output-draft-path}` — `{brand-folder-path}/.build/slices/{slice-id}.draft.md`
  - `{output-open-questions-path}` — `{brand-folder-path}/.build/slices/{slice-id}.oq.json`
  - `{extract-json-paths}` — JSON array of absolute paths to source extracts (filtered by slice→signal_tags)
  - `{competitor-dossier-paths}` — JSON array of paths to `{brand-folder-path}/.build/competitors/*.json` (for competitive-adjacent slices: `strategy/positioning.md`, `market/competitive.md`, `market/alternatives.md`)
  - `{behavioral-alternatives-path}` — `{brand-folder-path}/.build/behavioral-alternatives.json` (for `market/alternatives.md` specifically; ignored by other slices)
  - `{canonical-pre-synthesis-blob-path}` — absolute path to the blob written in Step 2.2
  - `{org-name}` — org name from PHASE 0

**Dispatch contract:** Issue all framework dispatches in a SINGLE assistant message (multiple Task tool calls in one message — parallel execution). Slice count is bounded (typically 8–15). Per `auto-mode-preamble.md`, each sub-agent runs the framework's PHASES end-to-end without WAITing.

**Cross-framework ordering caveat** (per Architect M1): `competitive-battle-card`'s prompt names positioning as its canonical source. Battle-card dispatch receives the positioning DRAFT — a placeholder note in the dispatch prompt explains the upstream slice may not be finalized; the framework's AUTO_MODE behavior is to tag any positioning-dependent OQ with `confidence: low`, `impact: P0`, `why_it_matters` noting the upstream dependency.

**Step 3: Verify**

Read the modified `prompt.md` and grep for: `Auto-Framework Dispatch`, `auto-mode-preamble.md`, `canonical-pre-synthesis-blob`, `gap_frameworks_needed`. Expected: each appears.

Grep for the old `synthesize.md` references in this PHASE 2 section. Expected: 0 matches (synthesize.md is no longer dispatched).

**Step 4: Verify preservation contract held**

Grep for these distinctive anchors (each unique to its preserved block):

- `signal_tags` — PHASE 1.4 filter table marker (matches multiple lines in that table)
- `Step 2.4: Ready-to-load verification gate` — Step 2.4 heading
- `5 Dunford components` — uniquely identifies the slice mapping table's first row (more specific than `strategy/positioning.md`, which also appears in the PHASE 1.4 filter table and would falsely report success)

Expected: every term still appears at least once. If any is missing, the rewrite consumed too much — revert and redo with a tighter `old_string` anchor.

**Step 5: Commit**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reverse-engineered-brand): replace PHASE 2 with auto-framework dispatch"
```

---

### ✅ Task 18: Extend PHASE 2.4 with JSON schema validation, slot validator, AUTO_MODE heuristics, compound regex

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (replace the existing Step 2.4 "Ready-to-load verification gate" with the extended gate)

**Step 1: Read the current Step 2.4**

Read `frameworks/reverse-engineered-brand/prompt.md` and locate the `**Step 2.4: Ready-to-load verification gate.**` heading. Per T17's preservation contract, this heading + body should still exist verbatim after T17. **If the heading is missing, HALT the task with `🔄 BLOCKED` marker citing "Step 2.4 anchor missing — T17 may have removed it; re-run T17 with explicit preservation note."** Do NOT improvise a new anchor or insertion point. The autopilot's wrapper will retry; after `MAX_BLOCKED_ITERATIONS` consecutive blocks it auto-skips.

Read 20 lines around the heading to capture the existing gate body (the current PHASE 2.4 has the stat-check logic but lacks JSON parse / schema validate / slot validate / heuristics / regex).

**Step 2: Rewrite PHASE 2.4 (ready-to-load gate)**

Anchor on `**Step 2.4: Ready-to-load verification gate.**` (unique). Replace with the extended gate. Sequencing (must be in this order, hard failures abort early; warnings collect and surface at the end):

1. **Stat check.** For each non-skipped slice: verify `{output-draft-path}` exists and is non-empty AND `{output-open-questions-path}` exists (may legitimately contain an empty `open_questions` array, but the file itself must exist). Missing or zero-byte → hard-fail with `slice: {slice-id}, missing: {draft|oq}`.
2. **JSON parse.** For each `.oq.json` file, attempt to parse. Parse error → hard-fail with `slice: {slice-id}, json_error: {error message}`.
3. **Schema validate.** For each parsed OQ, validate every entry against `open-questions-schema.md` required-at-emission rules: `id, file, framework_slot, confidence, impact, evidence, deepen_with` present; literal `null` allowed for `framework_slot` + `deepen_with` only on GAP slices (i.e., the slice mapping table has no owning framework). At least one of `question` or `inferred_value` present. `confidence` in enum `{high, medium, low}`. `impact` in enum `{P0, P1, P2}`. Validation failure → hard-fail with `slice: {slice-id}, field: {field-name}, value: {bad-value}`.
4. **Slot validator.** For each OQ with non-null `framework_slot`, verify the slot matches `phase-{N}-{kebab(heading)}` literally against the dispatched framework's PHASE headings. Read the dispatched framework's prompt.md, extract all `### PHASE N: <Name>` headings, kebab-case the name part. The OQ's `framework_slot` MUST match one of these literally — no slot merging across phases. Mismatch → hard-fail with `slice: {slice-id}, slot: {bad-slot}, valid_slots: {list}`.
5. **AUTO_MODE-ignored heuristics (warnings, do NOT block):** scan each `.draft.md` for:
   - Placeholder text: any occurrence of `[USER WILL PROVIDE]`, `TBD`, `TODO`, `<answer here>`. Match → warning `slice: {slice-id}, heuristic: placeholder-text, found: {string}`.
   - Suspiciously short draft: if draft is < 200 words AND the slice mapping table indicates the framework normally produces 500+. Match → warning `slice: {slice-id}, heuristic: short-draft, word_count: {N}`.
   - Missing PHASE coverage: if OQs in `.oq.json` do not span every PHASE heading of the dispatched framework. Match → warning `slice: {slice-id}, heuristic: missing-phase-coverage, missing_phases: {list}`.
6. **Compound-question regex (warning, do NOT block):** for each OQ `question` field, apply regex `/\b(and|or)\b.*\?|\?.*\?/`. Calibration cases (verify against test-fixtures): the regex MUST NOT match `"per-member, per-transport, or hybrid?"` (single atomic question listing alternatives — `or` precedes the question mark but `or` is inside a comma-separated list of alternatives, not joining two predicates) but MUST match `"Is X true and is Y true?"`. Match → warning `slice: {slice-id}, question: {text}, heuristic: compound`.

**Outcome:**
- Any hard-fail aborts the whole build with a named list of failures. User reruns after fixing source material or framework prompt.
- Warnings collect into a single status block surfaced at the end of the gate. Build continues; warnings are passed to PHASE 3 for inclusion in `review.html`'s Strengths & Gaps tab as "auto-mode integrity concerns" entries.

**Step 3: Add PHASE 2 Failure Modes reference table**

Insert immediately below the Step 2.4 body a table summarizing failure modes (see the design doc's "PHASE 2 Failure Modes" table — copy verbatim). Failure rows: sub-agent timeout, no draft.md, no oq.json, malformed oq.json, ignored AUTO_MODE, partial crash, all sub-agents fail.

**Step 4: Verify**

Read the modified `prompt.md`. Grep for `Step 2.4`, `JSON parse`, `Slot validator`, `Compound-question regex`, `AUTO_MODE-ignored heuristics`, `placeholder-text`. Expected: each appears.

**Step 5: Commit**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reverse-engineered-brand): extend PHASE 2.4 with schema validation + slot validator + AUTO_MODE heuristics + compound regex"
```

---

### ✅ Task 19: Update PHASE 3 (GAP dedupe, new field names, render dispatch via new template)

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (replace the existing PHASE 3 body)

**Step 1: Read the current PHASE 3 body**

Read `frameworks/reverse-engineered-brand/prompt.md` lines 180–294 to capture the existing PHASE 3 content.

**Step 2: Rewrite PHASE 3 (Load)**

Anchor on `### PHASE 3: Load — Consolidate drafts, write folder, generate review HTML (silent)` (unique). The new PHASE 3 body must contain these steps:

**Step 3.1: Aggregate per-slice OQs.**

- Read every `.build/slices/{slice-id}.oq.json` file.
- Concatenate all `open_questions` arrays in slice order. Assign global `OQ-N` ids: `global_id: "OQ-{N}"` where N is 1-indexed across the concatenation.
- **GAP-dedupe rule:** For OQs from GAP slices (`framework_slot: null`, `deepen_with: null`), deduplicate by `gap_frameworks_needed` value — emit one P0 meta-OQ per *missing framework* (not per slice instance). E.g., if `audiences/channels/employer.md` and `audiences/channels/wholesale.md` both emit a meta-OQ pointing to `channel-strategy`, keep one entry recommending `/aligned:add-framework channel-strategy` and list both slice paths in `why_it_matters`.
- **Field-rename mapping** (from the v0.1 → v0.2 schema): rename any v0.1 fields the sub-agents may have emitted: `best_guess` → `inferred_value`, `what_i_wrote` → `draft_excerpt`, `sources` → `evidence` (and convert source entries to typed-prefix strings if not already). Drop any `type` field (derived at render time per D13). Verify the AUTO_MODE preamble enforces v0.2 field names directly so this step is a no-op for compliant sub-agents — log a warning if any v0.1 rename was actually applied.

**Step 3.2: Build the `folders` array.**

For each top-level brand-folder subdirectory (`strategy`, `language`, `audiences`, `personas`, `market`, `proof`, `design`):
- Determine `status`: `Strong` (≥1 slice with HIGH-confidence OQs and 0 P0 OQs), `Partial` (≥1 slice present, some P0 OQs), `Weak` (slice present but mostly LOW confidence), `GAP` (no owning framework).
- Count `p0_count`, `p1_count`, `p2_count` from the slices in this folder.
- Build `framework_dispatches`: array of `{framework_id, fills}` entries for each dispatched framework.
- For GAP folders (`audiences`): set `gap_frameworks_needed: ["channel-strategy", "audience-segmentation"]`.

**Step 3.3: Aggregate competitor dossiers.**

Read every `.build/competitors/{slug}.json` file. Concatenate into a `competitors` array on the top-level JSON object.

**Step 3.4: Read behavioral alternatives.**

Read `.build/behavioral-alternatives.json` into the top-level JSON's `behavioral_alternatives` array.

**Step 3.5: Move slice drafts to final paths.**

For each slice: `mv {brand-folder-path}/.build/slices/{slice-id}.draft.md → {brand-folder-path}/{slice-id}`. Create parent directories as needed.

**Step 3.6: Write top-level brand-folder files.**

- `{brand-folder-path}/CLAUDE.md` — brand-folder manifest with slice → owning-framework table.
- `{brand-folder-path}/version.yaml` — schema_version + build timestamp.
- `{brand-folder-path}/contracts.yaml` — per the brand-folder-spec.
- `{brand-folder-path}/.open-questions.json` — the full aggregated JSON (folders + behavioral_alternatives + competitors + open_questions). `schema_version: "0.2.0"`.

**Step 3.7: Dispatch the renderer.**

Read `frameworks/reverse-engineered-brand/render-review-html.md` once. Dispatch a Task with `subagent_type: general-purpose` and placeholders:
- `{template-path}` — absolute path to `frameworks/reverse-engineered-brand/review-template.html`
- `{open-questions-json-path}` — absolute path to `{brand-folder-path}/.open-questions.json`
- `{output-html-path}` — `{brand-folder-path}/review.html` (renamed from `open-questions.html`)
- `{brand-folder-path}` — absolute path to the brand folder
- `{org-name}` — org name from PHASE 0

The renderer reads the template, substitutes the three tokens (`{open-questions-json}` ← the JSON content, `{brand-folder-path}` ← the path, `{org-name}` ← the name), applies the sanitization + verify-before-open contract from Task 21, writes to the output path, and opens it.

**Step 3.8: Clean up `.build/`.**

Delete `{brand-folder-path}/.build/` and all its contents. Per OQ-1 resolution, dossier data has been inlined into `.open-questions.json` so the `.build/competitors/` subdirectory is no longer needed; same for `.build/slices/` (drafts have been moved) and `.build/extracts/` (one-shot).

**Step 3.9: Final report.**

Print to the user a 5–10 line summary: org name, source count, slice count, GAP slice count, competitor count, behavioral-alternatives count, total OQ count broken down by P0/P1/P2, path to `review.html`, plus a one-line invitation to run `/aligned:use-framework {framework-id}` against the highest-priority slice (chosen from the `folders[].framework_dispatches` array sorted by P0 count).

**Step 3: Verify**

Read the modified `prompt.md`. Grep for: `folders array`, `gap-dedupe`, `GAP-dedupe`, `behavioral-alternatives.json`, `review-template.html`, `review.html` (NOT `open-questions.html`), `inferred_value`, `draft_excerpt`. Expected: each appears at least once.

Grep for the old name `open-questions.html`. Expected: 0 matches in PHASE 3 (may still appear in older parts of file that haven't been rewritten yet — fine for now; will be caught by later cross-reference check).

**Step 4: Commit**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reverse-engineered-brand): rewrite PHASE 3 with folders array + GAP dedupe + dossier inline + new render dispatch"
```

---

### ✅ Task 20: Update slice mapping table, intake header, top-of-file documentation in prompt.md

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (the file's intro section, the slice mapping table reference if PHASE 2 rewrite preserved it, and any cross-references to `synthesize.md` that need replacing)

**Step 1: Read prompt.md lines 1–50**

Capture the current intro section that names the sub-agent files.

**Step 2: Update intro references**

Find the intro lines that name `extract.md`, `synthesize.md`, `render-review-html.md` (currently around line 14 per the explore output). Replace `synthesize.md` references with `auto-mode-preamble.md` + `competitor-dossier.md`. Update the "ETL summary" lines (around 16–18) to reflect the new four-phase structure: Extract / Competitor Research / Auto-Framework Dispatch / Load.

**Step 3: Update PHASE 0 Intake**

Add an optional intake question for `competitor names` (user-supplied competitor names). The existing PHASE 0 WAIT collects: public URL, source folder, brand path, org name. Add: "[optional] competitor names (comma-separated, e.g., `DispatchTrack, Onfleet`) — if known, otherwise PHASE 1.5a will infer from source material."

Update the WAIT prompt to include this optional field. The answer parser must handle the field being absent (empty list).

**Step 4: Verify slice mapping table preservation (do NOT repair)**

T17's preservation contract requires the slice mapping table to survive verbatim. Verify by greping `frameworks/reverse-engineered-brand/prompt.md` for the table's distinctive first row anchor `strategy/positioning.md | 5 Dunford components` (or `strategy/positioning.md | ... | 5-components-positioning` depending on which column anchor is unique). **If the grep returns 0 matches, HALT the task with `🔄 BLOCKED` marker citing "slice mapping table missing — T17 owns its preservation; re-run T17."** Do NOT re-insert the table from scratch — the authoritative content lives with the PHASE 2 dispatch logic in T17. A re-insert here risks drift from T17's authoritative copy.

If the grep matches: add one explanatory line immediately ABOVE the table: `Used by PHASE 2 to look up the owning framework for each slice instance.` Use Edit anchored on the unique line above the table header (typically the `Slice → owning framework mapping (authoritative):` line).

**Step 5: Remove every remaining `synthesize.md` reference**

Grep `frameworks/reverse-engineered-brand/prompt.md` for `synthesize.md`. For each match, decide:
- If it's in PHASE 2 dispatch instructions → already replaced by T17.
- If it's in the intro file list → replaced in Step 2 above.
- If it's an example or anti-pattern → check whether the reference is still accurate after the redesign; rewrite to point to the appropriate file (`auto-mode-preamble.md` for AUTO_MODE behavior, `extract.md` for extraction behavior).
- If it's a stale reference → delete.

Expected: 0 matches after this step.

**Step 6: Replace `open-questions.html` with `review.html` across the file**

Grep `frameworks/reverse-engineered-brand/prompt.md` for `open-questions.html`. Replace every occurrence with `review.html`.

**Step 7: Verify**

Final grep sweep:
- `synthesize.md` → 0 matches
- `open-questions.html` → 0 matches
- `auto-mode-preamble.md` → ≥1 match
- `competitor-dossier.md` → ≥1 match
- `review-template.html` → ≥1 match
- `review.html` → ≥1 match

**Step 8: Commit**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "refactor(reverse-engineered-brand): update prompt.md intro, intake, and cross-references for revamp"
```

---

### Task 21: Replace render-review-html.md with new schema-reader

**Files:**
- Modify: `frameworks/reverse-engineered-brand/render-review-html.md` (full replacement)

**Step 1: Read the current render-review-html.md to capture the contracts to preserve**

Read `frameworks/reverse-engineered-brand/render-review-html.md` lines 100–150 and 285–310. Capture verbatim:
- The `</` → `<\/` sanitization contract
- The `JSON.stringify` discipline
- The post-write `Read`-based verify-before-open contract
- The `OPEN_QUESTIONS = {open-questions-json};` embed pattern

**Step 2: Replace the file contents**

Use Write to fully rewrite the file. The new contents:

1. **Role:** Renderer sub-agent dispatched by `reverse-engineered-brand` PHASE 3.7.
2. **Inputs (placeholders):** `{template-path}`, `{open-questions-json-path}`, `{output-html-path}`, `{brand-folder-path}`, `{org-name}`.
3. **Procedure:**
   - **Step 1: Read the template.** Read `{template-path}` (the `review-template.html` from Task 12). Capture the full content as a string.
   - **Step 2: Read the JSON.** Read `{open-questions-json-path}` (the aggregated `.open-questions.json` from PHASE 3.6). Parse it. Validate it is well-formed JSON (no parse errors).
   - **Step 3: Sanitize string values.** For every string value in the parsed JSON, replace every `</` with `<\/`. This prevents `</script>` inside `question`, `draft_excerpt`, `inferred_value`, `why_it_matters`, `evidence_quote`, competitor `evidence_quotes`, etc. from closing the script tag.
   - **Step 4: Re-serialize with stringify discipline.** Serialize the sanitized JSON using `JSON.stringify`-equivalent escaping (no hand-built JS literals). Backslashes, double-quotes, and control characters MUST be escaped. The output is a JS-safe literal.
   - **Step 5: Substitute tokens.** In the template string, replace:
     - `{open-questions-json}` ← the serialized sanitized JSON string from Step 4
     - `{brand-folder-path}` ← the input path (escape any `"` characters for JS-safety)
     - `{org-name}` ← the org name (HTML-escape `<`, `>`, `&`, `"`)
   - **Step 6: Write the output.** Write the result to `{output-html-path}`.
   - **Step 7: Verify by reading back.** Read `{output-html-path}`. Assert:
     - First line is `<!DOCTYPE html>`
     - Both `<script>` opening tags are present
     - No occurrence of `</script>` exists anywhere in the file except the closing tag for the script block(s)
     - The file ends with `</html>`
     - No raw token literal `{open-questions-json}`, `{brand-folder-path}`, or `{org-name}` remains (verify substitution worked)
   - **Step 8: Open the file.** Only if Step 7 fully passed, run `open {output-html-path}` to open in the default browser.
   - **Abort-before-open contract:** If Step 7 fails any check, abort with `verification_failed` reason naming the failed check + the offending byte range. Do NOT open the browser to a malformed file.
4. **Return contract:** compact ≤80-word status block: `STATUS` (`success` | `verification_failed`), `OUTPUT_PATH`, `BYTES_WRITTEN`, `VERIFICATION_CHECKS_PASSED` (N/M format), `NOTES` (only on failure).

**Step 3: Cross-verify preservation + new vocabulary**

The new render-review-html.md preserves three contracts from the old version AND introduces new vocabulary specific to the template-driven rewrite. Verify both:

**Preserved (carried over verbatim from the old file's contracts at the old lines 100–150):**
- `</` and `<\/` (sanitization)
- `JSON.stringify` (stringify discipline)
- `Read` (Read-based verify step)
- `</script>` (the sanitization contract's escape target)

**New vocabulary (introduced by this rewrite):**
- `verification_failed` (the abort status name)
- `abort-before-open` (the contract name as referenced in the design)
- `{template-path}` (the template input placeholder — replaces the old inline-HTML pattern)

Grep the new file for each term. Expected: ≥1 match for every term in both lists.

Grep for the old inline HTML template (the existing file embeds the full HTML at lines 135–401 of the old version). Expected: 0 matches for the literal HTML — the new renderer reads from `{template-path}` instead of embedding.

**Step 4: Commit**

```bash
git add frameworks/reverse-engineered-brand/render-review-html.md
git commit -m "feat(reverse-engineered-brand): replace render-review-html with template-driven renderer"
```

---

### Task 22: Delete synthesize.md

**Files:**
- Delete: `frameworks/reverse-engineered-brand/synthesize.md`

**Step 1: Verify no remaining references to synthesize.md in active code paths**

Grep for `synthesize.md` with scope limited to `frameworks/` and `skills/`. Expected: 0 matches.

Exclusions (these may legitimately retain the reference and should NOT block the deletion):
- `docs/kanban/` — historical KB entries archive deleted/changed files by name; references are descriptive, not load-bearing.
- `docs/plans/` — prior design docs reference the file historically.

If any match remains in `frameworks/reverse-engineered-brand/anti-examples.md` or `examples.md`, defer the delete to T23/T24 (those tasks will rewrite/update those files and remove the references). T22 must run AFTER both T23 and T24 complete so that examples/anti-examples are already cleaned.

**Step 2: Delete the file**

Use git rm (not bare rm) so the deletion is staged in a single step:

```bash
git rm frameworks/reverse-engineered-brand/synthesize.md
```

**Step 3: Verify the framework directory's file list is consistent with the design**

Run (Glob): `frameworks/reverse-engineered-brand/*`
Expected files:
- `prompt.md`
- `extract.md`
- `examples.md`
- `anti-examples.md`
- `auto-mode-preamble.md` (new)
- `competitor-dossier.md` (new)
- `render-review-html.md` (rewritten)
- `review-template.html` (new)
- `open-questions-schema.md` (new)

Plus `test-fixtures/` subdirectory.

`synthesize.md` MUST be absent.

**Step 4: Commit**

```bash
git commit -m "refactor(reverse-engineered-brand): delete synthesize.md (replaced by AUTO_MODE dispatch)"
```

> **Note:** The `git rm` in Step 2 has already staged the deletion. No `git add` needed.

---

### Task 23: Update examples.md for new PHASE structure

**Files:**
- Modify: `frameworks/reverse-engineered-brand/examples.md` (replace PHASE 1 narrative; add PHASE 1.5 example; add atomic-vs-compound OQ example)

**Step 1: Read current examples.md**

Read the full file (110 lines).

**Step 2: Update PHASE 1 example**

Find the PHASE 1 example (currently labeled "PHASE 1 (silent)"). Update to reference the new entity schema (flat `entities` array with `role` field per T15). Add a 2–3 line note that "PHASE 1.5a runs next, aggregating competitor entities and extracting behavioral alternatives."

**Step 3: Add a PHASE 1.5 example block**

New block titled "PHASE 1.5 example — competitor research". Show: orchestrator's `behavioral-alternatives.json` write (compact 3-entry array), then a dispatch-batch of 2–3 competitor-dossier sub-agents in a single message, then the resulting dossier files (one per slug).

**Step 4: Update PHASE 2 example**

The existing PHASE 2 example is the slice-synthesize narrative. Replace with an auto-framework-dispatch narrative: orchestrator builds canonical pre-synthesis blob, dispatches `5-components-positioning` + `strategic-narrative` + `messaging-distillation` + `buyer-persona` in a single parallel batch with the AUTO_MODE preamble, each sub-agent emits `draft.md` + `oq.json`, orchestrator runs PHASE 2.4 ready-to-load gate (success path — no validation failures).

**Step 5: Update PHASE 3 example**

Show: aggregation produces `folders` array + global OQ ids + dedup'd GAP entries + inlined competitor dossiers. Renderer dispatches with `review-template.html`. Final report 5–10 lines.

**Step 6: Add atomic-vs-compound OQ example**

A short example block titled "Atomic vs compound open questions". Show:
- ❌ Bad: `"Is the alternative spreadsheets and is the segment mid-market?"` (two predicates joined by `and`) — Compound regex matches; warning surfaced.
- ✅ Good: split into two OQs: `"Is the alternative spreadsheets-plus-manual-dispatch?"` and `"Is the primary segment mid-market retail?"`.
- ✅ Also good: `"Is the pricing model per-member, per-transport, or hybrid?"` — `or` is inside a comma-separated list of alternatives, not joining predicates. Regex does NOT match.

**Step 7: Update slice→owning-framework table reference**

If examples.md has an embedded slice mapping table, update it to match prompt.md's authoritative table (per T20).

**Step 8: Remove any references to `synthesize.md`**

Grep for `synthesize.md`. Replace each reference with `auto-mode-preamble.md` (for AUTO_MODE behavior) or delete if the reference is no longer accurate.

**Step 9: Verify**

Grep for: `PHASE 1.5`, `behavioral`, `auto-mode-preamble`, `atomic`. Expected: each appears.

Grep for `synthesize.md`. Expected: 0 matches.

**Step 10: Commit**

```bash
git add frameworks/reverse-engineered-brand/examples.md
git commit -m "docs(reverse-engineered-brand): update examples.md for AUTO_MODE dispatch + PHASE 1.5"
```

---

### Task 24: Rewrite anti-examples.md sections

**Files:**
- Modify: `frameworks/reverse-engineered-brand/anti-examples.md` (rewrite lines 67–95; update line 105 reference; add compound-question anti-example)

**Step 1: Read current anti-examples.md**

Read the full file (120 lines). Confirm the locations of the targets:
- Lines 67–95: "Synthesizing GAP slices without flagging the absence of a framework" + "Running sub-frameworks at runtime instead of synthesizing their output shape"
- Line 105: reference to `render-review-html.md`

**Step 2: Invert the "Running sub-frameworks at runtime" anti-pattern**

The old anti-pattern was: "Wrong: orchestrator loads `frameworks/5-components-positioning/prompt.md` and runs its interactive WAIT-gated phases. Right: read what the framework *produces* and synthesize that shape directly from the Source Registry."

Under the new design, the inverse is now correct: the orchestrator DOES dispatch owning frameworks in AUTO_MODE. Rewrite this entry as:

> **Wrong (old anti-pattern, now superseded):** Orchestrator synthesizes a slice's shape directly without dispatching the owning framework. Causes structural drift (the synthesizer's "5-component-like" output is structurally similar but vocabulary-inconsistent with what the framework actually produces).
>
> **Right:** Orchestrator dispatches the owning framework in AUTO_MODE with the preamble that overrides every WAIT. Sub-agent runs the framework's methodology end-to-end; emits draft + OQ JSON.

**Step 3: Update the "Synthesizing GAP slices" anti-pattern**

Keep this anti-pattern — it remains valid. Update the example to use the new field names:
- Old `synthesis_method: ad_hoc` → still correct but framed as the GAP-slice branch.
- Reference the GAP meta-OQ dedupe pattern (PHASE 3.1) — point to one P0 meta-OQ per missing framework, not per slice instance.

**Step 4: Add a compound-question anti-example**

New entry titled "Compound open questions (PHASE 2.4 warning)". Show:
- ❌ Bad OQ `question`: `"Is the alternative spreadsheets and is the segment mid-market?"` — joins two predicates. PHASE 2.4 regex flags as compound.
- ✅ Right: split into two atomic OQs.
- Edge case: `"Is the pricing model per-member, per-transport, or hybrid?"` — `or` inside a comma-separated alternatives list; not compound. Regex correctly does NOT flag.

**Step 5: Update line 105 reference**

The current line 105 is in the "Skipping the HTML review document" anti-example referencing `render-review-html.md` and `open-questions.html`. Update:
- `open-questions.html` → `review.html`
- The dispatch description: "dispatches a sub-agent using the `render-review-html.md` prompt template" remains correct (T21 preserved the file name).

**Step 6: Add a "Fabricating verification evidence" anti-example**

New entry for the AUTO_MODE preamble's VERIFICATION-STYLE FRAMEWORKS guardrail:
- ❌ Bad: `proof-points-audit` sub-agent in AUTO_MODE writes "Industry studies show 73% reduction in delivery time" without an evidence anchor — fabrication.
- ✅ Right: Same situation → emit an OQ with `confidence: low`, `impact: P0`, `inferred_value: null`, `why_it_matters` describing the unsourced claim. Do NOT write a draft sentence implying the claim was verified.

**Step 7: Remove any stale references**

Grep for `synthesize.md`. Replace each remaining reference (the anti-examples may still mention the file in inverted-anti-pattern context). Either rewrite to be design-current OR delete if no longer applicable.

**Step 8: Verify**

Grep for: `AUTO_MODE`, `compound`, `Fabricat`, `review.html`. Expected: each appears.

Grep for `open-questions.html`. Expected: 0 matches.
Grep for `synthesize.md`. Expected: 0 matches.

**Step 9: Commit**

```bash
git add frameworks/reverse-engineered-brand/anti-examples.md
git commit -m "docs(reverse-engineered-brand): rewrite anti-examples for AUTO_MODE dispatch + compound-question + fabrication guard"
```

---

### Task 25: Update README.md framework description

**Files:**
- Modify: `README.md` (line 194 — the `reverse-engineered-brand` description in the skill reference table)

**Step 1: Read README.md lines 190–200**

Verify the current line 194 contents match what the explore reported:
> `- \`reverse-engineered-brand\` — orchestrator that auto-synthesizes a draft brand folder from a URL + local content and opens an interactive HTML review for open questions`

**Step 2: Update the line**

Replace with:
> `- \`reverse-engineered-brand\` — orchestrator that auto-synthesizes a draft brand folder from a URL + local content + competitor research, dispatches owning frameworks in AUTO_MODE per slice, and opens a tabbed review.html with atomic confirm/correct cards per assumption + question`

**Step 3: Verify**

Read `README.md` around line 194 and grep for `competitor research`, `AUTO_MODE`, `review.html`. Expected: each appears in the new description.

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs(README): update reverse-engineered-brand description"
```

---

### Task 26: Update frameworks/registry.yaml entry

**Files:**
- Modify: `frameworks/registry.yaml` (the `reverse-engineered-brand` entry at lines 1258–1266)

**Step 1: Read registry.yaml lines 1255–1270**

Confirm the current entry matches the explore output. The `purpose` field currently reads:
> "the orchestrator that auto-fills positioning, narrative, jobs-to-be-done, buyer-persona, messaging-distillation, competitive-battle-card, proof-points-audit, brand-voice, and design-principles into a cold-start brand folder, logging every low-confidence inference and gap as an Open Question reviewable in an interactive HTML document with paste-back-to-Claude-Code prompts"

**Step 2: Remove `jobs-to-be-done` from the `purpose` field**

Per the design's "Modified outside framework folders" section, `jobs-to-be-done` is stale (no longer part of the orchestrator's framework set). Update the `purpose` value to remove the comma-separated `jobs-to-be-done` entry while keeping the others intact.

**Step 3: Update the `name` field to mention competitor research**

The current `name` reads "an ETL session that takes a public URL plus optional source content, automatically synthesizes a canonical brand/ folder, and produces an interactive HTML review document for every educated guess and gap". Update to:
> "an ETL session that takes a public URL plus optional source content + named competitors, dispatches owning frameworks in AUTO_MODE per brand slice, and produces a tabbed review.html with atomic confirm/correct cards for every assumption and gap"

**Step 4: Verify**

Read the modified entry. Grep for `jobs-to-be-done`. Expected: 0 matches (in this entry; matches elsewhere in registry.yaml are unrelated and acceptable).

Grep the entry for `competitor`, `AUTO_MODE`, `review.html`. Expected: each appears.

**Step 5: Commit**

```bash
git add frameworks/registry.yaml
git commit -m "docs(registry): remove stale jobs-to-be-done from reverse-engineered-brand purpose; mention AUTO_MODE + competitor research"
```

---

## Manual Steps (Post-Automation)

> Complete these steps manually after all automated tasks finish. They require running the framework against external source material and cannot be performed by the autopilot.

### Step A: Layer 3 — Per-framework AUTO_MODE smoke

For each of the 8 owning frameworks (`5-components-positioning`, `strategic-narrative`, `messaging-distillation`, `brand-voice`, `buyer-persona`, `competitive-battle-card`, `proof-points-audit`, `design-principles`), run a vertical smoke test:

1. Replicate the fixture structure from Task 4 (`test-fixtures/auto-mode-inputs/{framework-id}/`) — create minimal input fixtures for each of the remaining 7 frameworks if not already done.
2. Dispatch a Task agent with `subagent_type: general-purpose`. Prompt content: AUTO_MODE preamble (read from `auto-mode-preamble.md`) + the framework's `prompt.md` + the fixture inputs.
3. Assert (manually inspect output):
   - Sub-agent returns success without WAITing
   - `draft.md` + `oq.json` files written
   - OQ JSON validates against `open-questions-schema.md` (run mentally against the Task 1 fixtures' expected behavior)
   - Every OQ has `framework_slot` matching `phase-{N}-{kebab(heading)}` literally
   - No compound-question regex matches
4. If any framework fails, file a Kanban entry per `skills/_shared/kanban-entry-format.md` recommending per-framework `## When invoked in AUTO_MODE` escalation for that framework. Closes OQ-4 from the design doc.

### Step B: Layer 4 — Integration test (Marley regeneration)

This step requires access to the external Marley brand source folder, which lives outside this repo. **Do not skip — this is the canonical integration check.**

1. Locate the Marley source folder (the consumer brand referenced in the design doc).
2. Run `/aligned:use-framework reverse-engineered-brand` in the relevant repo.
3. Provide the Marley source folder path at the PHASE 0 intake WAIT.
4. After PHASE 3 completes, verify:
   - `brand/` folder structure matches `docs/brand-folder-spec.md`
   - All previously-populated slices are populated again
   - GAP slices are flagged with status `GAP` in the `folders` array
   - Competitor dossiers present (≥1, depending on what source material surfaced)
   - Behavioral alternatives present (≥1)
   - `review.html` opens cleanly in the browser
   - Total OQ count is dramatically reduced vs. the prior 130 (target: 30–50)
   - No verification-failure abort
5. **Comparative qualitative check (April's lens):** `market/alternatives.md` includes behavioral alternatives (not just product); executive summary leads with 1-sentence positioning; "what source supports / doesn't yet tell us" framing reads as honest assessment (not judgmental).

### Step C: Layer 5 — Identity verification spot-check

Using the fixtures from Task 14, manually exercise the `competitor-dossier.md` sub-agent with each fixture's prepared inputs. Verify the `identity_verification` field on the resulting dossier matches the fixture's documented expected value (`mismatch_flagged`, `matched`, `matched` respectively). If any divergence, file a Kanban entry.

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|---|---|---|
| 1 | Task structure for prompt-based work | TDD-adapted: write file → read back to verify → grep for expected anchors → commit | Skip TDD discipline; rely on integration test only |
| 2 | Schema-restructure for `extract.md` entities | Flat `entities` array with `role` field | Keep sub-arrays + aggregate in PHASE 1.5a |
| 3 | Where `competitors` array lives | Top-level in `.open-questions.json` (aggregated in PHASE 3.3) | Sibling `.competitors.json` file; inline in HTML only |
| 4 | Marley regeneration handling | Post-Automation manual step (Step B) | Skip Marley; add to Out of Scope |
| 5 | All framework smoke tests deferred to Post-Automation (Layer 3 for 7 frameworks + vertical-slice run for 5-components-positioning) | Fixtures created during automated tasks; actual smoke runs in Post-Automation Step A; D6/D7 demoted to in-task notes (see T12 + T15) | Smoke runs as automated tasks (requires halt-for-review — banned); eager fixture creation for all 8 frameworks (low-value inflation) |

### Appendix: Decision Details

#### Decision 1: Task structure for prompt-based work

**Chose:** TDD-adapted flow (write file → read back to verify → grep for expected anchors → commit).

**Why:** This is a prompt framework. There is no executable test runner that fails before the prompt is written. Strict TDD ("write failing test first") would force authoring of arbitrary failing assertions just to satisfy the form. Instead, every task ends with a deterministic verification step that catches the most common failure modes: missing content, incorrect substitution, stale references. Each Verify step grep targets specific design-doc requirements so it acts as a contract test for that requirement.

**Alternatives rejected:**
- *Skip verification entirely; rely on integration test:* would defer failure detection to Post-Automation Step B (Marley regeneration), where attributing a failure back to the specific prompt-edit task is hard. Per-task verification narrows the blast radius.

#### Decision 2: Schema-restructure for `extract.md` entities

**Chose:** Flat `entities` array with `role` field (Option A from the design's D7 correction).

**Why:** PHASE 1.5a's primary need is to filter entities by `role: competitor`. A flat array makes this a one-line filter. Maintaining four sub-arrays (`people`, `competitors`, `audiences`, `claims`) would require four parallel aggregation passes in PHASE 1.5a — duplicated work with no upside since extract outputs are one-shot (no migration concern). The design doc explicitly notes both options and defers the call to build order step 7; this plan picks A and documents the change in T15's behavior-change note.

**Alternatives rejected:**
- *Option B (keep sub-arrays + aggregate):* duplicates work in PHASE 1.5a; no migration benefit (extracts are one-shot).

#### Decision 3: Where the `competitors` array lives

**Chose:** Top-level on `.open-questions.json`, aggregated in PHASE 3.3.

**Why:** Per OQ-1 resolution in the design, dossier data must be inlined into `review.html` at render time so `.build/competitors/` can be deleted. The renderer needs a single input file. Storing competitors at the top level of `.open-questions.json` matches the pattern already used for `folders` and `behavioral_alternatives` — one schema, one renderer input, one verification surface.

**Alternatives rejected:**
- *Sibling `.competitors.json` file:* doubles the renderer's input surface; complicates PHASE 3 cleanup.
- *Inline directly into HTML at render time (skip aggregation):* deletes `.build/competitors/` before render; renderer would need to read all dossier files plus the OQ JSON. More complex than a single aggregation.

#### Decision 4: Marley regeneration handling

**Chose:** Post-Automation manual step (Step B).

**Why:** The autopilot/ralph loop is unattended (no human interaction mid-pipeline per `skills/writing-plans/SKILL.md`'s Anti-Pattern: Mid-Flow Human Review). Running the framework against Marley's external source material requires both (a) access to a source folder that lives outside this repo, and (b) human inspection of the rendered `review.html`. Both are explicitly Post-Automation-class work. The design itself flags Marley as "Not touched" by automated tasks and as "regenerated as integration test" — confirming this belongs in manual verification.

**Alternatives rejected:**
- *Skip Marley entirely:* loses the integration test the design explicitly calls out as canonical (Layer 4).

#### Decision 5: All framework smoke tests deferred to Post-Automation

**Chose:** Fixtures created during automated tasks (Task 4 for `5-components-positioning`); actual smoke runs (vertical-slice for `5-components-positioning` + Layer 3 sweep across the remaining 7 owning frameworks) deferred to Post-Automation Step A.

**Why:** Two related concerns collapse into a single decision.

*Smoke runs require non-deterministic LLM execution.* A framework dispatch via Task tool produces LLM-generated draft markdown + OQ JSON that requires human inspection to judge success — the "is the draft good?" question is judgment, not a deterministic check. Putting the run inside an automated task would require either a halt-for-human-review (banned by the Anti-Pattern: Mid-Flow Human Review policy) or a 🔄 BLOCKED retry pattern that can't actually verify the output. Cleaner: create the fixture inputs eagerly so they're ready, and run smokes as Step A.

*Eagerly creating all 8 fixture folders is low-value inflation.* The vertical-slice contract (build order step 3 — "end-to-end on **one** owning framework") is intentionally bounded to one framework. Building all 8 fixture folders during automated tasks would add ~7 mechanical tasks that each exercise the same AUTO_MODE preamble contract. The marginal failure detection per fixture is near zero. Defer the remaining 7 to Step A where they can be created on demand against real source material when the operator actually runs that framework's smoke.

**Demoted decisions** (folded back into in-task notes rather than separate Decision Log entries — they're scope decisions, not load-bearing architectural calls):

- **Channels mockup reconciliation (was D6):** Skipped — verified the locked mockup is already clean (no `<dt>Channels</dt>` rows on comp-cards; the only `Channels` reference is at line 947 in the Overview "Sections at a glance" GAP indicator). The design doc's M9 reconciliation note appears to predate the mockup update. T12's mockup-fidelity verification step includes an explicit grep to catch any regression. Tracked separately as a Kanban follow-up to update the design doc's M9 lines (215, 367) — see KB-115.
- **`signal_tags` extension for `competitor-named` (was D7):** Skipped — the design explicitly marks this optional. PHASE 1.5a filters on `entities.role: competitor` directly. Adding a tag duplicates information; no functional gain. T15's optional signal_tags step is documented as skipped with the rationale.

**Alternatives rejected:**
- *Smoke runs as automated tasks with 🔄 BLOCKED retry:* retries don't address that the output requires human judgment; wrong tool.
- *Halt-for-review steps mid-plan:* explicitly banned (Anti-Pattern: Mid-Flow Human Review).
- *Eagerly create all 8 fixture folders:* +7 tasks of low-value mechanical work; failure detection unchanged.

