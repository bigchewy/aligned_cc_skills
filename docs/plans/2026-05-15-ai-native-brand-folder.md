---
mcp-tools-required: []
---

# AI-Native Brand Folder Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Ship the canonical AI-native brand folder architecture inside the aligned plugin by (1) authoring the brand-folder spec as a reference doc, (2) shipping the shared `load-brand-slices` skill, and (3) registering six new frameworks (one orchestrator + five per-section frameworks) with their `prompt.md` / `examples.md` / `anti-examples.md` triplets and registry entries.

**Source Design Doc:** `docs/plans/2026-05-15-ai-native-brand-folder-design.md`

**Mockups:** `docs/mockups/2026-05-15-ai-native-brand-folder.html`

**Architecture:** The plugin gains one new shared loader skill (`skills/_shared/load-brand-slices.md`) that every brand-consuming generator delegates to, one reference document (`docs/brand-folder-spec.md`) describing the canonical folder schema, and six new framework directories under `frameworks/` (each with the standard `prompt.md` + `examples.md` + `anti-examples.md` triplet). The registry (`frameworks/registry.yaml`) gains six new entries. The folder schema itself is documentation that downstream repos (e.g., dispatch-tracker) and downstream generators (e.g., `~/.claude/skills/generate-deck/`) will adopt — those repo migrations are tracked separately and are NOT modified by this plan.

**Tech Stack:** Markdown content (skill prompts, framework prompts, reference docs); YAML registry edits; bash/Glob/Grep verification commands. No code execution. No external dependencies.

---

## Prerequisites

> Complete these steps manually before starting Task 1.

(none — every task is automatable)

---

## Out of scope (handled in separate plans)

The design references work that lives in *other* repos and is **explicitly out of scope** for this plan:

- **`~/.claude/skills/generate-deck/`, `generate-blog-post/`, `generate-one-pager/`** — these personal skills currently hardcode `brand/guidelines/*` paths. They will be updated in a follow-up session that targets the personal skills repo (`~/.claude/skills/`). This plan does NOT modify them.
- **`dispatch-tracker/brand/` migration** — the design's "single-PR migration" applies to the dispatch-tracker repo, not this plugin repo. That repo's plan will be authored separately.
- **`brand/eval/*.md` scenarios** — those eval files ship inside each *consumer's* brand folder, not inside this plugin. They will be authored as part of each downstream brand folder's first build.

This plan ships only the canonical schema spec, the shared loader, and the six new frameworks — the artifacts that downstream consumers depend on.

---

### ✅ Task 1: Reference doc — `docs/brand-folder-spec.md`

**Files:**
- Create: `docs/brand-folder-spec.md`

**Step 1: Write the failing existence check**

This task is documentation, not code; the "test" is that the file exists, contains the canonical sections, and references the right downstream consumers. Treat the verification steps as the test.

Run: `ls /Users/ericpage/software/aligned_cc_skills/docs/brand-folder-spec.md`
Expected: FAIL with "No such file or directory".

**Step 2: Write the spec file**

Author `docs/brand-folder-spec.md` as a single self-contained reference. The downstream consumers (the shared loader, every generator, the `reverse-engineered-brand` orchestrator) will reference this file by path. Required H2 sections, in order:

1. `## Purpose` — one paragraph: this file is the canonical schema reference for the AI-native `brand/` folder; ships in the aligned plugin; consumed by generators and the brand-authoring frameworks. Note: schema is v0.1 — the loader and frameworks reference these contracts, but downstream generators have not yet validated all fields end-to-end. Minor field additions/renames may occur in v0.2 before the schema stabilizes.
2. `## Directory tree (canonical)` — copy the tree block from the design doc's Section 1, verbatim. Includes `strategy/`, `language/`, `proof/` (including `clinical-evidence.md` + `compliance.md`), `market/`, `audiences/channels/`, `audiences/segments/`, `personas/`, `design/`, `templates/`, `assets/`, `contracts.yaml`, `eval/`.
3. `## Per-file purpose table` — copy the "what it owns / what it does NOT own" table from the design doc.
4. `## Frontmatter schema` — copy the YAML block from the design doc's Section 2. Required fields: `id, type, slices, status, confidence, updated, summary`. Optional: `validated_at, validated_by, sources, depends_on, consumers, tags`.
5. `## Provenance & confidence model` — copy from design doc's Section 3. Three states (`draft | validated | retired`), three labels (`low | medium | high`), per-section pragma block syntax.
6. `## Slice-loading mechanics` — slice path syntax (`{folder}/{file-stem}#{slice-slug}`), slug derivation rule, collision rule, fallback rule (missing slice → `status: missing`, generator degrades gracefully — Decision 29). Distinguish the two missing-slice cases per the design (Section 4): (a) "slug declared in frontmatter, H2 absent from body" = build-failing lint failure, loader returns `status: missing-in-body`; (b) "H2 present in body, not declared in `slices:`" = warning only, loader does NOT expose the slice.
7. `## Composition contract (`contracts.yaml` schema)` — show the YAML schema with `generators:` map, each entry having `requires`, `optional`, `min_confidence`, optional `compose:` block. Include the persona × channel × segment × prospect overlay rule (Decision 22).
8. `## CLAUDE.md manifest template` — paste the manifest template from design doc's Section 5. Document the file's role: front-door manifest for human + LLM readers; lists every file, every slice, every status, and the "Next Steps to Deepen This Brand Folder" framework queue.
9. `## Versioning` — file-level `updated:` + folder-level `version.yaml` schema. Document the `version.yaml` schema explicitly:
   ```yaml
   version: <semver string, e.g. "0.4.0">
   generated_at: <ISO date>
   generated_by: <framework-id, e.g. "reverse-engineered-brand", or "manual">
   git_sha: <git SHA at generation time, optional>
   sources:                      # OPTIONAL
     - { kind: url | interview | doc, value: "..." }
   notes: >
     <free-form notes>
   ```
   Generated artifacts (decks, blog posts) stamp `generated_against: { brand_version, brand_sha }` in their own frontmatter.
10. `## Subdomain reuse` — copy the design doc's Section 9 table set verbatim. The directory layout does NOT change between digital health subdomains (telehealth, RPM, behavioral health, digital therapeutics, payer-side, provider-side, condition platforms); only fills differ. This section is load-bearing for generators that need to confirm a `brand/` folder belongs to a digital-health org.
11. `## Eval scenarios (consumer-side)` — list the three baseline evals (`voice-conformance`, `positioning-trace`, `proof-points-cite`) and the optional `competitive-alternatives-sync`. Note these files ship in the consumer's `brand/eval/` directory, not in this plugin.
12. `## Hard constraints (recap)` — copy the bullet list from the design doc's "Hard constraints" section.

Do not paraphrase the design; quote the canonical wording. This file IS the schema — generators will grep its tables for fields. Use exact field names (`id`, `type`, `slices`, etc.) verbatim.

Top of file:

```markdown
# Brand Folder Spec (Canonical)

> **Status:** Canonical reference for the AI-native `brand/` folder schema. Skills that consume `brand/` (generators, audits, persona checks) and skills that produce `brand/` (the `reverse-engineered-brand` orchestrator and its sub-frameworks) MUST conform to this spec.
>
> **Source design:** `docs/plans/2026-05-15-ai-native-brand-folder-design.md` (decision log captures rationale)
>
> **Target population:** digital health companies across subdomains (telehealth, RPM, behavioral health, digital therapeutics, payer-side, provider-side, condition platforms). Structural design is general; example fills are digital-health-specific.

## Purpose
...
```

Aim for ~400–600 lines. Quoting the design doc's content verbatim is the right move — DRY says the design doc is the source, but operationally generators will look up `docs/brand-folder-spec.md` first because the design doc lives in `docs/plans/` (planning artifacts), not in the consumed reference set.

**Step 3: Verify structure**

Run:
```bash
grep -c '^## ' /Users/ericpage/software/aligned_cc_skills/docs/brand-folder-spec.md
```
Expected output: at least `12` (the twelve required H2 sections listed above; sub-headings you added count too but only top-level H2s match this grep).

Run:
```bash
grep -c 'status: draft | validated | retired' /Users/ericpage/software/aligned_cc_skills/docs/brand-folder-spec.md
```
Expected: at least 1 (the three-state model is canonical).

Run:
```bash
grep -c 'load-brand-slices' /Users/ericpage/software/aligned_cc_skills/docs/brand-folder-spec.md
```
Expected: at least 1 (the spec must mention the shared loader by name so generators can find it).

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add docs/brand-folder-spec.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(brand): add canonical brand-folder schema reference"
```

---

### ✅ Task 2: Shared loader skill — `skills/_shared/load-brand-slices.md`

**Files:**
- Create: `skills/_shared/load-brand-slices.md`

**Step 1: Verify the file does not yet exist**

Run:
```bash
ls /Users/ericpage/software/aligned_cc_skills/skills/_shared/load-brand-slices.md
```
Expected: FAIL with "No such file or directory".

**Step 2: Write the shared loader skill**

This is a *shared skill* (lives under `skills/_shared/`), not a top-level skill. Per `skills/_shared/resolve-skill-path.md`, shared files do not perform their own resolution — the caller resolves `{base-directory}`. Shared skill files are short, procedure-oriented, and called by other skills. Model the file shape on `skills/_shared/kanban-entry-format.md` (terse, numbered procedural steps with embedded YAML/markdown templates).

Required sections (H2), in order:

1. `## Purpose` — one paragraph: this skill loads brand slices from a `brand/` folder conforming to `docs/brand-folder-spec.md`. Every generator that consumes brand content delegates to it. No generator implements frontmatter or H2 parsing inline (Decision 19 — single loader, six generators, no duplication).
2. `## Inputs` — slice path list (e.g., `["strategy/positioning#category", "language/voice#tone-principles"]`), optional `min_confidence` (default `medium`), optional `brand_root` (default `./brand`).
3. `## Output shape` — YAML schema for the return: `blocks: [{path, status, confidence, body}], sources: [...], warnings: [...]`. Each block carries its slice path, the file's resolved `status` (from frontmatter or per-section pragma), the file's `confidence`, and the slice body markdown.
4. `## Procedure` — numbered steps:
   1. Resolve `brand_root` (default `./brand`).
   2. Read `brand_root/contracts.yaml` (if present) only when the caller asks for "all required slices for generator X" — direct slice-path callers skip this step.
   3. For each input slice path `{folder}/{file-stem}#{slice-slug}`:
      a. Glob `brand_root/{folder}/{file-stem}.md`. If missing, emit `{path, status: missing, body: null}` and continue (Decision 29 — graceful degradation).
      b. Read the file. Parse YAML frontmatter (lines between leading `---` and matching `---`).
      c. Validate required frontmatter fields exist (`id, type, slices, status, confidence, updated, summary`). If any missing, emit `{path, status: missing-frontmatter, body: null}` and add a warning.
      d. If file `status: retired`, emit `{path, status: retired, body: null}` and add a warning ("file is retired").
      e. If file `confidence` is below `min_confidence`, emit `{path, status: below-confidence-threshold, body: null}` and add a warning.
      f. **Two missing-slice cases (per the spec doc's slice-loading-mechanics section):**
         - **f-i. Slug declared in frontmatter `slices:` but H2 absent from body:** emit `{path, status: missing-in-body, body: null}` and add a warning ("declared slice has no matching H2 in body — lint failure"). This is the hard error case.
         - **f-ii. H2 present in body but slug not in frontmatter `slices:`:** the loader does NOT expose the slice — skip silently if the slug was not requested, or emit `{path, status: undeclared-slice, body: null}` plus a warning ("undeclared slice ignored") if the slug WAS requested.
      g. Locate the H2 matching the slice slug. Slug derivation: lowercase the H2 text, replace non-alphanumeric runs with `-`, strip leading/trailing `-`.
      h. Check for a per-section pragma block on the line immediately after the H2: `> [PROVENANCE: status=..., confidence=..., source=..., note="..."]`. If present, override file-level `status` and `confidence` for this slice.
      i. Extract the body markdown from immediately after the H2 (and pragma block if present) up to the next H2 or EOF. Emit `{path, status, confidence, body}`.
   4. Collect `sources:` arrays from every successfully-loaded file's frontmatter; dedupe by `kind` + `value`; return as `sources:`.
   5. Return the assembled output structure.
5. `## Composition rule` — when the caller's input list contains `personas/{role}` plus any of `audiences/channels/{channel}` and/or `audiences/segments/{segment}`, the loader composes them with this layering (Decision 22):
   - base = persona file (all declared slices)
   - first overlay = channel file (last-write-wins per H2 slice slug)
   - second overlay = segment file (last-write-wins)
   - optional third overlay = prospect from sibling `clients/`. The loader accepts EITHER `clients/{prospect}.md` (single-file form) OR `clients/{prospect}/{slice}.md` (folder form, one file per slice slug); the caller passes the prospect identifier and the loader probes both shapes in that order. **Precedence:** if both shapes exist for the same prospect, the single-file form wins and the loader emits a warning to surface the conflict ("prospect '{name}' exists in both single-file and folder forms; using single-file"). Missing prospect → composition continues without overlay (graceful — Decision 29).
   - Missing dimensions degrade gracefully — composition continues with whatever exists. The caller passes the prospect identifier explicitly; the loader does not auto-discover from conversation context.
6. `## Slug collisions` — if two H2 headings slug-collide, the loader appends `-2`, `-3` in document order to the second and subsequent and adds a warning per collision. Caller may treat this as a hard error if they choose.
7. `## Loader output usage` — every generator that calls this skill MUST: (a) refuse to proceed if any *required* slice is `missing` / `missing-frontmatter` / `retired` / `below-confidence-threshold`; (b) include an appendix in the generated artifact listing every missing/below-threshold slice; (c) include a `DRAFT` disclaimer in the output if any consumed slice is `status: draft`.
8. `## Caller integration checklist` — three bullets to help a generator author confirm correct delegation: (1) call this skill via the standard `_shared` invocation pattern; (2) pass `min_confidence` explicitly (do not rely on the default for production generators); (3) handle every output block's `status` — never assume `body` is non-null.
9. `## v1 contract enforcement` — one paragraph: v1 enforces the loader contract by *documentation*. Six generators internalize this procedure; drift between them is the predictable failure mode. Every generator MUST link to this skill by path (`skills/_shared/load-brand-slices.md`) in its own SKILL.md and quote the output shape verbatim from the `## Output shape` section above. v2 promotes the loader to executable code; until then, structural conformance is checked by reading both the generator's SKILL.md and this file side-by-side during code review.

Aim for ~200–280 lines. Match the terse, procedure-driven style of `skills/_shared/kanban-entry-format.md` and `skills/_shared/critique-panel-orchestration.md`. No exhortations, no philosophy — just the procedure and contract.

Top of file:

```markdown
# Load Brand Slices

> **Caller responsibility:** This shared file does NOT resolve `{base-directory}` itself. The calling skill is responsible for resolving its own `{base-directory}` before invoking this loader. See `skills/_shared/resolve-skill-path.md`.

## Purpose

Load addressable slices from a brand folder conforming to `docs/brand-folder-spec.md`. Every brand-consuming generator (`generate-deck`, `generate-blog-post`, `generate-one-pager`, `generate-email`, `generate-landing-page`, `generate-battlecard`) delegates to this skill rather than implementing frontmatter or H2 parsing inline. One loader, six generators (Decision 19).
...
```

**Step 3: Verify structural conformance**

Run:
```bash
grep -c '^## ' /Users/ericpage/software/aligned_cc_skills/skills/_shared/load-brand-slices.md
```
Expected: at least 9 (the nine required H2 sections above).

Run:
```bash
grep -c 'Decision 19\|Decision 22\|Decision 29' /Users/ericpage/software/aligned_cc_skills/skills/_shared/load-brand-slices.md
```
Expected: at least 3 (the three load-bearing design decisions must be cited so future readers can trace rationale).

Run:
```bash
grep -c 'graceful' /Users/ericpage/software/aligned_cc_skills/skills/_shared/load-brand-slices.md
```
Expected: at least 1 (graceful degradation is the v1 contract).

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add skills/_shared/load-brand-slices.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(skills): add shared load-brand-slices skill"
```

---

### ✅ Task 3: Framework `reverse-engineered-brand` — prompt.md

**Files:**
- Create: `frameworks/reverse-engineered-brand/prompt.md`

> Complete Tasks 1 and 2 before this task. The prompt references `docs/brand-folder-spec.md` (Task 1) and `skills/_shared/load-brand-slices.md` (Task 2) by name — both paths must exist when the prompt is read.

**Step 1: Verify the file does not yet exist**

Run:
```bash
ls /Users/ericpage/software/aligned_cc_skills/frameworks/reverse-engineered-brand/prompt.md
```
Expected: FAIL with "No such file or directory".

**Step 2: Author the prompt**

This is the orchestrator framework. Its job: take a public URL + optional local content folder, then run a fully interactive Q&A across the 9 sub-frameworks in canonical order (Decision 16), producing a complete `brand/` folder at version 0.1.0 with all files `status: draft, confidence: low or medium`.

Frontmatter:

```yaml
---
required_documents: ["a public URL for the org (homepage or About page)"]
helpful_documents: ["a local folder path with supplementary content (past decks, customer interviews, sample copy, internal docs)"]
---
```

Opening line (mandatory format — ASCII hyphen between framework and purpose, matching `skills/use-framework/SKILL.md` Step 2's parser and the 20+ existing prompt.md files):

```
You are April Dunford, guiding someone through a Reverse-Engineered Brand session - a fully interactive walk-through that takes a public URL plus optional supplementary content and produces a canonical brand/ folder ready for human validation.
```

Structure: one outer H2 wrapper (`## The Reverse-Engineered Brand Process`) followed by H3 phases. This matches every existing framework in the repo (sample `5-components-positioning/prompt.md`: `## The 5 Components Framework` then `### PHASE 1: Competitive Alternatives`).

Required H3 phases, in canonical run order matching the design's dependency graph (`1 → 2 → 3 → 4 → 5 → 8 → 7 → 6 → 9`):

1. `### PHASE 0: Intake` — ask for URL + optional local content folder. WAIT.
2. `### PHASE 1: Public surface review` — Dunford reads the URL, summarizes what she sees. Asks the user to validate or correct the summary. WAIT.
3. `### PHASE 2: Positioning (composes 5-components-positioning)` — runs the 5-components flow scripted in `frameworks/5-components-positioning/prompt.md`. WAIT at each Dunford-required pause.
4. `### PHASE 3: Strategic narrative (composes strategic-narrative)` — Raskin 5-element arc; consumes positioning's `category` + `target` as inputs. WAIT.
5. `### PHASE 4: Jobs-to-be-done (composes jobs-to-be-done)` — one run per priority audience. Discovers channel × segment pair(s). WAIT.
6. `### PHASE 5: Buyer-persona (composes buyer-persona — Task 6 of this plan)` — one run per role on the buying committee. WAIT.
7. `### PHASE 6: Messaging-distillation (composes messaging-distillation — Task 9)` — produces copy-ready language. WAIT.
8. `### PHASE 7: Competitive-battle-card (composes competitive-battle-card — Task 18)` — runs AFTER messaging-distillation so objection rebuttals can draw on `messaging#value-prop-phrasings`. WAIT.
9. `### PHASE 8: Proof-points-audit (composes proof-points-audit — Task 15)` — verifies claims surfaced in prior phases. WAIT.
10. `### PHASE 9: Brand-voice (composes brand-voice — Task 12)` — needs positioning's category name + messaging's tagline as anchors. WAIT.
11. `### PHASE 10: Design-principles (composes design-principles)` — optional; ask the user "does this org want a visual identity layer, or does it inherit a parent brand's design system?" WAIT.
12. `### PHASE 11: Folder write` — assemble the draft `brand/` folder. **Hand-off contract:** sub-frameworks invoked in PHASES 2–10 do NOT write files to disk themselves; they yield their assembled-but-unwritten markdown back to the orchestrator. The orchestrator writes everything in PHASE 11 as a single atomic step. Every file gets frontmatter with `status: draft, confidence: low` (or `medium` where the public URL or supplementary content provided strong signal). **Skipped sub-frameworks still produce a file** in the atomic write, with frontmatter `status: missing` and an empty body — this preserves the canonical folder shape so downstream generators can detect "this slot is expected but not yet built" instead of "this org has no positioning at all." Write `version.yaml` per the schema documented in `docs/brand-folder-spec.md` (Section "Versioning"). Write `CLAUDE.md` from the spec's template. Write `contracts.yaml` with the canonical generator contracts copied from `docs/brand-folder-spec.md`. WAIT for user to confirm before writing.
13. `### PHASE 12: Manifest + deepen-next queue` — show the user the populated `CLAUDE.md` "Next Steps to Deepen This Brand Folder" queue. Explain that each entry is `/aligned:use-framework {framework-id}` and can be run individually to sharpen one slice. WAIT for acknowledgment.

**Missing sub-framework handling:** if `frameworks/{sub-id}/prompt.md` is unreadable at runtime (e.g., a sub-framework's files weren't yet authored), the orchestrator MUST surface the failure to the user, offer to skip that PHASE (the corresponding brand file gets `status: missing` in the folder write), and continue. Never silently swallow a missing sub-framework.

For each phase that composes a sub-framework, the prompt MUST:
- State which sub-framework it composes by ID
- Direct the LLM to load `frameworks/{sub-framework-id}/prompt.md` and run its phases as scripted (WAITs included)
- Add an outer instruction: "Speak in April Dunford's voice across all phases unless the sub-framework's opening line specifies a different advisor (e.g., Raskin for narrative); in those cases adopt the sub-framework's named advisor for that phase."
- Note that the orchestrator NEVER skips a WAIT point even when running long — autopilot is not a use case for `reverse-engineered-brand` (it is an interactive brainstorm; per Decision 16, "90+ minute investment is appropriate for a foundational artifact")

WAIT-point discipline: every phase MUST end with `WAIT for user response before continuing.` on its own line. Per `skills/use-framework/SKILL.md` Step 5, a phase is not complete until the user has responded to all prompts within it.

Frontmatter style: use block-list YAML (preferred for diff readability; inline-array YAML is functionally equivalent and the registry parser accepts both). Example:

```yaml
---
required_documents:
  - a public URL for the org (homepage or About page)
helpful_documents:
  - a local folder path with supplementary content (past decks, customer interviews, sample copy, internal docs)
---
```

Aim for ~350–500 lines.

**Step 3: Verify structure**

Run:
```bash
grep -c '^### PHASE' /Users/ericpage/software/aligned_cc_skills/frameworks/reverse-engineered-brand/prompt.md
```
Expected: at least 13 (PHASE 0–12 inclusive; missing phases break orchestration).

Run:
```bash
grep -c '^WAIT for user response before continuing\.$' /Users/ericpage/software/aligned_cc_skills/frameworks/reverse-engineered-brand/prompt.md
```
Expected: at least 13 (one per phase).

Run:
```bash
grep -c '^You are April Dunford, guiding someone through' /Users/ericpage/software/aligned_cc_skills/frameworks/reverse-engineered-brand/prompt.md
```
Expected: 1 (the opening line — must use ASCII hyphen between framework and purpose to match the use-framework parser).

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/reverse-engineered-brand/prompt.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add reverse-engineered-brand prompt"
```

---

### ✅ Task 4: Framework `reverse-engineered-brand` — examples.md

**Files:**
- Create: `frameworks/reverse-engineered-brand/examples.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/reverse-engineered-brand/examples.md`
Expected: FAIL.

**Step 2: Author examples**

Model on `frameworks/5-components-positioning/examples.md` (sampled in survey). Examples.md uses H2 phase headers (`## PHASE N: ...`) at the top level — this differs from prompt.md (which uses H3 because prompt.md has an outer H2 wrapper). Examples.md has no outer wrapper. Under each H2, two or three `### {Calibration label}` blocks. Each block: a **User:** quote, an **Advisor:** response, and a `> blockquote rationale` line.

**Coverage rule (applies to every framework's examples.md in this plan):** examples.md SHOULD have a corresponding `## PHASE N:` heading for every calibration-sensitive phase — typically the phases that surface user judgment (intake, value translation, file-assembly confirmation). Pure mechanical phases (e.g., a phase that only reads a file and summarizes) may be omitted. Skip phases only when calibration would not change advisor behavior.

Required H2 sections for this orchestrator's examples (covering the calibration-sensitive phases):

1. `## PHASE 0: Intake` — example of user giving a clear URL + optional local folder; example of user giving a vague company description without a URL (advisor pushes for a URL).
2. `## PHASE 1: Public surface review` — example of advisor's URL-summary being correct; example of user correcting an inferred audience claim.
3. `## PHASE 6: Messaging-distillation handoff` — example of advisor surfacing a tagline draft from positioning + asking for user calibration.
4. `## PHASE 11: Folder write` — example of advisor previewing the folder write and asking for confirmation; example of user requesting one slice be marked `confidence: medium` instead of `low` based on prior validation.

Aim for ~120–180 lines.

**Step 3: Verify structure**

Run:
```bash
grep -c '^## PHASE' /Users/ericpage/software/aligned_cc_skills/frameworks/reverse-engineered-brand/examples.md
```
Expected: at least 4.

Run:
```bash
grep -c '^\*\*User:\*\*\|^\*\*Advisor:\*\*' /Users/ericpage/software/aligned_cc_skills/frameworks/reverse-engineered-brand/examples.md
```
Expected: at least 12 (≥4 phases × ≥3 user/advisor pairs).

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/reverse-engineered-brand/examples.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add reverse-engineered-brand examples"
```

---

### ✅ Task 5: Framework `reverse-engineered-brand` — anti-examples.md

**Files:**
- Create: `frameworks/reverse-engineered-brand/anti-examples.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/reverse-engineered-brand/anti-examples.md`
Expected: FAIL.

**Step 2: Author anti-examples**

Model on `frameworks/5-components-positioning/anti-examples.md`. Document failure modes specific to orchestration:

1. **Skipping a sub-framework's WAIT** — advisor rushes through the composed flow without honoring the inner WAIT points.
2. **Inferring missing data from the URL alone** — advisor writes confident frontmatter (e.g., `confidence: high`) for slices the URL only weakly supports. The correct move is `status: draft, confidence: low`.
3. **Writing the folder before user confirmation in PHASE 12** — advisor writes files without surfacing the PHASE 12 confirmation gate.
4. **Switching advisor voice mid-phase incorrectly** — advisor uses Raskin's voice during the Dunford-led positioning phase, or stays in Dunford during the Raskin narrative phase.
5. **Treating the orchestrator as autopilot-compatible** — advisor (or executing harness) skips WAIT points to "get through faster." Per Decision 16, this framework is interactive-only.

Each entry: `### {Title}`, then **User:**, **Wrong:**, **Right:**, blockquote rationale.

Aim for ~80–130 lines.

**Step 3: Verify structure**

Run:
```bash
grep -c '^### ' /Users/ericpage/software/aligned_cc_skills/frameworks/reverse-engineered-brand/anti-examples.md
```
Expected: at least 5.

Run:
```bash
grep -c '^\*\*Wrong:\*\*\|^\*\*Right:\*\*' /Users/ericpage/software/aligned_cc_skills/frameworks/reverse-engineered-brand/anti-examples.md
```
Expected: at least 10 (≥5 entries × Wrong + Right).

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/reverse-engineered-brand/anti-examples.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add reverse-engineered-brand anti-examples"
```

---

### ✅ Task 6: Framework `buyer-persona` — prompt.md

**Files:**
- Create: `frameworks/buyer-persona/prompt.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/buyer-persona/prompt.md`
Expected: FAIL.

**Step 2: Author the prompt**

Advisor: **matt-dixon**. Output goal: a single `personas/{role}.md` file per run (one role at a time). Per the design's `personas/{role}.md` slot, the output structure is: role-overview, evaluation-criteria, skepticism-triggers, language-resonance, common-objections.

Frontmatter (block-list YAML — valid YAML, matches the writing-plans style guide and reads cleanly in diffs; inline-array YAML is functionally equivalent but the block-list form is preferred here):

```yaml
---
required_documents:
  - the role being profiled (e.g., CMO, VP-Ops, Chief People Officer)
helpful_documents:
  - customer research
  - interview transcripts
  - competitor positioning
---
```

Opening line (ASCII hyphen between framework and purpose):

```
You are Matt Dixon, guiding someone through a Buyer-Persona framework - a structured walk-through that produces a role-specific persona file for the buying committee.
```

Structure: one outer H2 wrapper (`## The Buyer-Persona Process`) followed by H3 phases (matches the existing repo convention).

Required H3 phases:

1. `### PHASE 1: Role anchoring` — name the role, the typical title variants, where it sits in the buying committee (champion / mobilizer / blocker / approver), and what the role is *accountable for* (not what the role *cares about* — Challenger distinction). WAIT.
2. `### PHASE 2: Evaluation criteria` — what concrete signals does this role use to assess vendors? Outcomes, ROI thresholds, evidence types, peer references. Forces the user to be specific. WAIT.
3. `### PHASE 3: Skepticism triggers` — what makes this role distrust a vendor pitch? Common red flags, prior bad experiences, category baggage. WAIT.
4. `### PHASE 4: Language resonance` — what phrases ring true to this role; which jargon they accept vs. reject; what level of technical depth they expect. WAIT.
5. `### PHASE 5: Common objections` — list 5–8 specific objections this role raises during the sale. For each, the underlying concern + a response framing. WAIT.
6. `### PHASE 6: File assembly` — produce the markdown file body. Frontmatter MUST include `id: persona-{role-kebab}`, `type: persona`, `slices: [role-overview, evaluation-criteria, skepticism-triggers, language-resonance, common-objections]`, `status: draft`, `confidence: medium`, `updated: {today}`, `summary: ...`. Body uses one H2 per slice. **Hand-off contract:** when invoked as a sub-framework by `reverse-engineered-brand`, this phase yields the assembled-but-unwritten markdown back to the orchestrator (orchestrator writes the file in its own PHASE 11). When invoked standalone (`/aligned:use-framework buyer-persona`), this phase writes the file directly to `brand/personas/{role}.md`. The framework MUST detect which mode it is running in by checking for an orchestrator-set flag in conversation context, or by asking the user once at PHASE 1: "standalone or orchestrated?" WAIT for user to confirm/adjust.

Use Matt Dixon's voice from `advisors/prompts/matt-dixon.md`. Dixon's signature: insist on the *commercial insight* — the role's blind spot or hidden constraint that the vendor reframes for them. PHASE 5 should explicitly include "what's the commercial insight that disrupts this role's current thinking?"

Aim for ~280–400 lines.

**Step 3: Verify structure**

Run:
```bash
grep -c '^### PHASE' /Users/ericpage/software/aligned_cc_skills/frameworks/buyer-persona/prompt.md
```
Expected: at least 6.

Run:
```bash
grep -c '^WAIT for user response before continuing\.$' /Users/ericpage/software/aligned_cc_skills/frameworks/buyer-persona/prompt.md
```
Expected: at least 6.

Run:
```bash
grep -c '^You are Matt Dixon, guiding someone through' /Users/ericpage/software/aligned_cc_skills/frameworks/buyer-persona/prompt.md
```
Expected: 1.

Run:
```bash
grep -c 'commercial insight\|Challenger' /Users/ericpage/software/aligned_cc_skills/frameworks/buyer-persona/prompt.md
```
Expected: at least 1 (the Dixon-distinctive frame must be present).

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/buyer-persona/prompt.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add buyer-persona prompt"
```

---

### ✅ Task 7: Framework `buyer-persona` — examples.md

**Files:**
- Create: `frameworks/buyer-persona/examples.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/buyer-persona/examples.md`
Expected: FAIL.

**Step 2: Author examples**

Model on `frameworks/5-components-positioning/examples.md`. One H2 per phase (PHASE 1–6). Under each, 2–3 calibration blocks (User / Advisor / blockquote rationale). Pull a realistic digital-health buyer-committee role for the running example — recommend `Chief Medical Officer (payer-side)` because it appears in the design's "Personas populated set" table.

Aim for ~140–200 lines.

**Step 3: Verify structure**

Run:
```bash
grep -c '^## PHASE' /Users/ericpage/software/aligned_cc_skills/frameworks/buyer-persona/examples.md
```
Expected: at least 6.

Run:
```bash
grep -c '^\*\*User:\*\*\|^\*\*Advisor:\*\*' /Users/ericpage/software/aligned_cc_skills/frameworks/buyer-persona/examples.md
```
Expected: at least 12.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/buyer-persona/examples.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add buyer-persona examples"
```

---

### ✅ Task 8: Framework `buyer-persona` — anti-examples.md

**Files:**
- Create: `frameworks/buyer-persona/anti-examples.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/buyer-persona/anti-examples.md`
Expected: FAIL.

**Step 2: Author anti-examples**

Required entries:

1. **Conflating role with market** — User describes a vertical (e.g., "healthcare CIOs") and the advisor uses that as the role. Correct move: roles are role-shaped (CMO, CIO, CFO); vertical context lives in `audiences/*`.
2. **Producing a generic "buyer" persona** — output reads like a marketing-stock persona ("data-driven leader who values ROI"). Wrong because the file's whole job is role-specific evaluation signal.
3. **Skipping the commercial insight** — PHASE 5 lists generic objections without identifying the underlying commercial insight that reframes the role's thinking. Wrong per Dixon's frame.
4. **Letting the user dictate the persona** — advisor writes whatever the user says without pushing back on vague claims. Wrong because the framework's job is to extract sharpness, not to transcribe.
5. **Writing more than one role per run** — advisor tries to produce CMO + CFO + CMIO in one session. Wrong per the file contract (`personas/{role}.md` is one role per file).

Aim for ~90–140 lines.

**Step 3: Verify structure**

Run:
```bash
grep -c '^### ' /Users/ericpage/software/aligned_cc_skills/frameworks/buyer-persona/anti-examples.md
```
Expected: at least 5.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/buyer-persona/anti-examples.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add buyer-persona anti-examples"
```

---

### ✅ Task 9: Framework `messaging-distillation` — prompt.md

**Files:**
- Create: `frameworks/messaging-distillation/prompt.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/messaging-distillation/prompt.md`
Expected: FAIL.

**Step 2: Author the prompt**

Advisor: **april-dunford**. Output goal: a `language/messaging.md` file. Per design, slices: `category-name`, `tagline`, `elevator-pitch-variants`, `value-prop-phrasings`, `value-prop-to-persona-map`, `key-phrases`, `pricing-language` (optional).

Frontmatter (block-list YAML):

```yaml
---
required_documents:
  - completed strategy/positioning.md (5-components output)
helpful_documents:
  - strategy/narrative.md
  - personas/*.md
  - proof/proof-points.md
  - sample existing copy
---
```

Opening line (ASCII hyphen):

```
You are April Dunford, guiding someone through a Messaging Distillation framework - the workshop that turns a positioning chain into copy-ready language.
```

Structure: outer H2 wrapper (`## The Messaging Distillation Process`) followed by H3 phases.

Required H3 phases:

1. `### PHASE 1: Anchor in positioning` — load + paraphrase the org's 5-component chain (Component 5 = category, Component 4 = target). WAIT for user to confirm the paraphrase before continuing.
2. `### PHASE 2: Category name string` — pick the exact phrase a customer will hear for the category. Dunford: it must make differentiated value obvious, not the technology. WAIT.
3. `### PHASE 3: Tagline` — 3–7 word headline. Variants for the homepage hero, the deck cover, the email signature. WAIT.
4. `### PHASE 4: Elevator pitch variants (per audience)` — for each priority audience (channel × segment from `audiences/*`), one 2–3 sentence elevator pitch. WAIT.
5. `### PHASE 5: Value-prop phrasings` — translate each unique attribute → value claim (so what?). 3–6 value props, each in customer-language. WAIT.
6. `### PHASE 6: Value-prop-to-persona map` — for each persona in `personas/*`, which value props lead, in which order. Table format. WAIT.
7. `### PHASE 7: Key phrases & rhetorical hooks` — the 6–12 phrases the org wants to own in the market (e.g., "right-time, not on-time"). Bonus list of phrases the org explicitly does NOT use. WAIT.
8. `### PHASE 8: Pricing language (optional)` — *how* the org talks about price (e.g., "value-based pricing aligned to outcomes"), not the price itself. If the org has no public pricing posture yet, mark this slice as a placeholder. WAIT.
9. `### PHASE 9: File assembly` — produce the markdown. Frontmatter `id: messaging`, `type: messaging`, `slices: [category-name, tagline, elevator-pitch-variants, value-prop-phrasings, value-prop-to-persona-map, key-phrases, pricing-language]`, `status: draft`, `confidence: medium`, `updated: {today}`, `summary: ...`, `depends_on: [strategy/positioning, strategy/narrative]`. **Hand-off contract** (same as buyer-persona Task 6): when invoked standalone, write to `brand/language/messaging.md`; when invoked by the orchestrator, yield the assembled markdown back. WAIT.

Dunford voice: distinct from positioning — messaging is the surface, positioning is the reasoning. Cite the boundary explicitly in the opening narration (Decision 1).

Aim for ~320–450 lines.

**Step 3: Verify structure**

Run:
```bash
grep -c '^### PHASE' /Users/ericpage/software/aligned_cc_skills/frameworks/messaging-distillation/prompt.md
```
Expected: at least 9.

Run:
```bash
grep -c '^You are April Dunford, guiding someone through' /Users/ericpage/software/aligned_cc_skills/frameworks/messaging-distillation/prompt.md
```
Expected: 1.

Run:
```bash
grep -c '^WAIT for user response before continuing\.$' /Users/ericpage/software/aligned_cc_skills/frameworks/messaging-distillation/prompt.md
```
Expected: at least 9.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/messaging-distillation/prompt.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add messaging-distillation prompt"
```

---

### ✅ Task 10: Framework `messaging-distillation` — examples.md

**Files:**
- Create: `frameworks/messaging-distillation/examples.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/messaging-distillation/examples.md`
Expected: FAIL.

**Step 2: Author examples**

Model on `frameworks/5-components-positioning/examples.md`. One H2 per phase. Under each, 2–3 calibration blocks. Use a realistic digital-health running example for continuity. Aim for ~150–220 lines.

**Step 3: Verify structure**

```bash
grep -c '^## PHASE' /Users/ericpage/software/aligned_cc_skills/frameworks/messaging-distillation/examples.md
```
Expected: at least 7.

```bash
grep -c '^\*\*User:\*\*\|^\*\*Advisor:\*\*' /Users/ericpage/software/aligned_cc_skills/frameworks/messaging-distillation/examples.md
```
Expected: at least 14.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/messaging-distillation/examples.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add messaging-distillation examples"
```

---

### ✅ Task 11: Framework `messaging-distillation` — anti-examples.md

**Files:**
- Create: `frameworks/messaging-distillation/anti-examples.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/messaging-distillation/anti-examples.md`
Expected: FAIL.

**Step 2: Author anti-examples**

Required entries:

1. **Re-doing positioning under the messaging label** — advisor re-litigates Component 1–5 instead of distilling. Wrong because positioning lives in its own file (Decision 1).
2. **Tagline as feature list** — advisor accepts a tagline like "AI-powered care management" that names the technology, not the value.
3. **Single elevator pitch for all audiences** — advisor produces one elevator pitch and skips per-audience variants. Wrong because audience composition is first-class (Decision 22).
4. **Value-prop-to-persona map missing** — output skips PHASE 6 because the user "doesn't have personas yet." Correct move: produce the map as a placeholder, flag as `confidence: low`.
5. **Confusing pricing language with pricing** — advisor records the actual dollar number. PHASE 8 is about *how* the org talks about price, not the price itself.

Aim for ~90–140 lines.

**Step 3: Verify structure**

```bash
grep -c '^### ' /Users/ericpage/software/aligned_cc_skills/frameworks/messaging-distillation/anti-examples.md
```
Expected: at least 5.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/messaging-distillation/anti-examples.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add messaging-distillation anti-examples"
```

---

### ✅ Task 12: Framework `brand-voice` — prompt.md

**Files:**
- Create: `frameworks/brand-voice/prompt.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/brand-voice/prompt.md`
Expected: FAIL.

**Step 2: Author the prompt**

Advisor: **steve-krug**. Output goal: a single `language/voice.md` with slices `tone-principles, register-table, dos-and-donts, banned-phrases, banned-terms, glossary, competitor-naming`. Per Decision 26, terminology is folded into voice — no separate `terminology.md` file. The framework therefore produces seven slices in one pass.

Frontmatter (block-list YAML):

```yaml
---
required_documents:
  - 3-10 sample pieces of existing copy (homepage, blog posts, founder tweets, sales emails)
helpful_documents:
  - competitor copy samples
  - category-name and tagline from messaging.md
---
```

Opening line (ASCII hyphen):

```
You are Steve Krug, guiding someone through a Brand-Voice framework - a structured pass that extracts tone principles, register, banned phrases, terminology, and glossary into a single voice.md file.
```

Structure: outer H2 wrapper (`## The Brand-Voice Process`) followed by H3 phases.

Required H3 phases:

1. `### PHASE 1: Sample intake` — ask for 3–10 sample copy pieces (paste or path) + 2–3 competitor copy samples. WAIT.
2. `### PHASE 2: Tone principles` — extract 3–5 principles from samples ("Krug-style": principles are about *how it feels to read*, not abstract values). WAIT.
3. `### PHASE 3: Register table` — rows by content type (homepage hero / explainer / proof / objection / about / footer); columns by register dimension (formality, intensity, length, voice — first/second/third person). WAIT.
4. `### PHASE 4: Dos and don'ts` — concrete pairs. "Do: ..., Don't: ..." with rationale per pair. 5–10 pairs. WAIT.
5. `### PHASE 5: Banned phrases` — phrases the org will not use (e.g., "best-in-class", "world-class", "synergy"). Each with one-line reason. WAIT.
6. `### PHASE 6: Banned terms + glossary` — terms the org refuses (e.g., "user" if the org uses "member") plus the glossary of approved terms with definitions. WAIT.
7. `### PHASE 7: Competitor naming` — rules for when/how to name competitors in copy. (Some categories: name competitors freely; others: never name; rules depend on category maturity.) WAIT.
8. `### PHASE 8: File assembly` — produce the markdown. Frontmatter `id: voice`, `type: voice`, `slices: [tone-principles, register-table, dos-and-donts, banned-phrases, banned-terms, glossary, competitor-naming]`, `status: draft`, `confidence: medium`, `updated: {today}`, `summary: ...`. **Hand-off contract:** standalone → write to `brand/language/voice.md`; orchestrated → yield assembled markdown back. WAIT.

Krug's voice: plain, readable, anti-jargon. The brand-voice framework's job is to extract specificity from samples — never invent voice principles from nothing.

Aim for ~280–400 lines.

**Step 3: Verify structure**

Run:
```bash
grep -c '^### PHASE' /Users/ericpage/software/aligned_cc_skills/frameworks/brand-voice/prompt.md
```
Expected: at least 8.

Run:
```bash
grep -c '^You are Steve Krug, guiding someone through' /Users/ericpage/software/aligned_cc_skills/frameworks/brand-voice/prompt.md
```
Expected: 1.

Run:
```bash
grep -c '^WAIT for user response before continuing\.$' /Users/ericpage/software/aligned_cc_skills/frameworks/brand-voice/prompt.md
```
Expected: at least 8.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/brand-voice/prompt.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add brand-voice prompt"
```

---

### ✅ Task 13: Framework `brand-voice` — examples.md

**Files:**
- Create: `frameworks/brand-voice/examples.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/brand-voice/examples.md`
Expected: FAIL.

**Step 2: Author examples**

One H2 per phase, 2–3 calibration blocks each. Aim for ~140–200 lines.

**Step 3: Verify structure**

```bash
grep -c '^## PHASE' /Users/ericpage/software/aligned_cc_skills/frameworks/brand-voice/examples.md
```
Expected: at least 6.

```bash
grep -c '^\*\*User:\*\*\|^\*\*Advisor:\*\*' /Users/ericpage/software/aligned_cc_skills/frameworks/brand-voice/examples.md
```
Expected: at least 12.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/brand-voice/examples.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add brand-voice examples"
```

---

### ✅ Task 14: Framework `brand-voice` — anti-examples.md

**Files:**
- Create: `frameworks/brand-voice/anti-examples.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/brand-voice/anti-examples.md`
Expected: FAIL.

**Step 2: Author anti-examples**

Required entries:

1. **Inventing voice principles from nothing** — advisor proposes "warm, professional, approachable" without grounding in samples. Wrong because PHASE 2 derives principles from samples.
2. **Splitting voice from terminology** — advisor argues for a separate `terminology.md`. Wrong per Decision 26 — one file, seven slices.
3. **Banned phrases without reasons** — advisor lists phrases to avoid without the "why" line. Wrong because rationale survives team turnover; opinions don't.
4. **Glossary as marketing collateral** — advisor writes flowery definitions for the glossary. Wrong — glossary entries are operational definitions, not pitches.
5. **Competitor-naming policy left implicit** — advisor skips PHASE 7. Wrong because every generator that touches competitive content needs the rule.

Aim for ~80–130 lines.

**Step 3: Verify structure**

```bash
grep -c '^### ' /Users/ericpage/software/aligned_cc_skills/frameworks/brand-voice/anti-examples.md
```
Expected: at least 5.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/brand-voice/anti-examples.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add brand-voice anti-examples"
```

---

### ✅ Task 15: Framework `proof-points-audit` — prompt.md

**Files:**
- Create: `frameworks/proof-points-audit/prompt.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/proof-points-audit/prompt.md`
Expected: FAIL.

**Step 2: Author the prompt**

Advisor: **the-qa-engineer**. Output goal: `proof/proof-points.md` with structured entries. Each proof point has: claim, source (URL / interview / audit doc), date verified, confidence label.

Frontmatter (block-list YAML):

```yaml
---
required_documents:
  - existing customer-facing copy (homepage, deck, one-pager)
helpful_documents:
  - customer interview transcripts
  - case study drafts
  - third-party reports
  - regulatory filings
---
```

Opening line (ASCII hyphen):

```
You are The QA Engineer, guiding someone through a Proof-Points Audit framework - a structured pass that extracts every quantitative claim from existing copy and grounds it in source + date + confidence.
```

Structure: outer H2 wrapper (`## The Proof-Points Audit Process`) followed by H3 phases.

Required H3 phases:

1. `### PHASE 1: Claim extraction` — read existing copy, list every quantitative or proof-shaped claim verbatim (numbers, percentages, named customers, awards, certifications). WAIT.
2. `### PHASE 2: Source identification` — for each claim, what document/URL/interview substantiates it. WAIT.
3. `### PHASE 3: Date verification` — when was the source produced; when was the claim last re-verified. WAIT.
4. `### PHASE 4: Confidence labeling` — `high` (primary source), `medium` (corroborated secondary), `low` (placeholder or weak source). WAIT.
5. `### PHASE 5: Gap report` — claims with no source → flag for follow-up. Claims older than 18 months → flag for re-verification. Claims with `confidence: low` → flag. WAIT.
6. `### PHASE 6: Digital-health proof split (optional)` — if the org has clinical evidence (RCTs, peer-reviewed pubs, FDA clearances, real-world evidence) or compliance certifications (HIPAA, SOC 2, HITRUST, FDA QSR, ISO), split those into separate `proof/clinical-evidence.md` and `proof/compliance.md` files per Decision 25. The QA Engineer asks: "does this org have clinical evidence claims?" and "does this org have compliance certifications?" — if yes, the file write in PHASE 7 produces three files instead of one. WAIT.
7. `### PHASE 7: File assembly` — produce `proof/proof-points.md` (always) and conditionally `proof/clinical-evidence.md` + `proof/compliance.md`. Frontmatter for each: `id` (e.g., `proof-points`, `clinical-evidence`, `compliance`), `type: proof-points | clinical-evidence | compliance`, `slices: [...]` (one slice per category of proof), `status: draft`, `confidence: medium`, `updated: {today}`, `summary: ...`, plus `sources: [...]` listing every cited source with `kind` + `value`. **Hand-off contract:** standalone → write the file(s) to `brand/proof/`; orchestrated → yield the assembled markdown back to the orchestrator. WAIT.

The QA Engineer voice: skeptical, evidence-driven, blunt about gaps. Per advisor prompts at `advisors/prompts/the-qa-engineer.md`. No varnish — if a claim is unsubstantiated, the QA Engineer says so plainly.

Aim for ~260–380 lines.

**Step 3: Verify structure**

Run:
```bash
grep -c '^### PHASE' /Users/ericpage/software/aligned_cc_skills/frameworks/proof-points-audit/prompt.md
```
Expected: at least 7.

Run:
```bash
grep -c '^You are The QA Engineer, guiding someone through' /Users/ericpage/software/aligned_cc_skills/frameworks/proof-points-audit/prompt.md
```
Expected: 1.

Run:
```bash
grep -c 'clinical-evidence\|compliance' /Users/ericpage/software/aligned_cc_skills/frameworks/proof-points-audit/prompt.md
```
Expected: at least 2 (Decision 25 — the digital-health split must be present).

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/proof-points-audit/prompt.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add proof-points-audit prompt"
```

---

### ✅ Task 16: Framework `proof-points-audit` — examples.md

**Files:**
- Create: `frameworks/proof-points-audit/examples.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/proof-points-audit/examples.md`
Expected: FAIL.

**Step 2: Author examples**

One H2 per phase. Include calibration for the digital-health split decision (PHASE 6) — example user with no clinical evidence (single file output); example user with FDA clearance + HITRUST cert (three-file output). Aim for ~140–200 lines.

**Step 3: Verify structure**

```bash
grep -c '^## PHASE' /Users/ericpage/software/aligned_cc_skills/frameworks/proof-points-audit/examples.md
```
Expected: at least 5.

```bash
grep -c '^\*\*User:\*\*\|^\*\*Advisor:\*\*' /Users/ericpage/software/aligned_cc_skills/frameworks/proof-points-audit/examples.md
```
Expected: at least 10.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/proof-points-audit/examples.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add proof-points-audit examples"
```

---

### ✅ Task 17: Framework `proof-points-audit` — anti-examples.md

**Files:**
- Create: `frameworks/proof-points-audit/anti-examples.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/proof-points-audit/anti-examples.md`
Expected: FAIL.

**Step 2: Author anti-examples**

Required entries:

1. **Accepting "many customers" as a claim** — advisor records "trusted by many" as a proof point. Wrong — proof points are *quantitative*, sourced, dated.
2. **Skipping source identification** — advisor accepts a claim with "founder said so" and no underlying source. The QA Engineer pushes for the actual artifact (interview transcript ID, audit doc, dashboard screenshot date).
3. **Confidence inflation** — advisor labels every claim `high` because they don't want to surface gaps. Wrong — `high` is reserved for primary source / quote / audited metric / founder-validated.
4. **Single file for digital-health org with FDA clearance** — advisor writes everything into `proof-points.md` instead of splitting clinical-evidence and compliance. Wrong per Decision 25.
5. **Treating PHASE 5 gap report as optional** — advisor skips the gap report because "the user already knows what's missing." Wrong — the gap report is the artifact the org acts on between framework runs.

Aim for ~90–140 lines.

**Step 3: Verify structure**

```bash
grep -c '^### ' /Users/ericpage/software/aligned_cc_skills/frameworks/proof-points-audit/anti-examples.md
```
Expected: at least 5.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/proof-points-audit/anti-examples.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add proof-points-audit anti-examples"
```

---

### ✅ Task 18: Framework `competitive-battle-card` — prompt.md

**Files:**
- Create: `frameworks/competitive-battle-card/prompt.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/competitive-battle-card/prompt.md`
Expected: FAIL.

**Step 2: Author the prompt**

Advisor: **april-dunford**. Output goal: `market/competitive.md` with slices `competitive-landscape, differentiators, common-objections`. MUST declare `depends_on: [strategy/positioning#competitive-alternatives]` in frontmatter (Decision 21 — positioning is canonical, competitive.md is a deep view).

Frontmatter (block-list YAML):

```yaml
---
required_documents:
  - completed strategy/positioning.md (Component 1: competitive alternatives)
  - completed language/messaging.md (value-prop phrasings)
helpful_documents:
  - customer win/loss interviews
  - competitor public materials
---
```

Opening line (ASCII hyphen):

```
You are April Dunford, guiding someone through a Competitive Battle-Card framework - a deep view of the competitive terrain built on the canonical alternatives list in positioning.
```

Structure: outer H2 wrapper (`## The Competitive Battle-Card Process`) followed by H3 phases.

Required H3 phases:

1. `### PHASE 1: Load canonical alternatives` — read `strategy/positioning#competitive-alternatives`. The framework MUST NOT introduce new competitor names; if the user surfaces one, redirect them to update positioning first (Decision 21). WAIT.
2. `### PHASE 2: Competitive landscape narrative` — for each canonical alternative, 2–3 sentences on where they sit in the market, how they win, who their best customer is. WAIT.
3. `### PHASE 3: Differentiators per alternative` — for each, what does the org do that this competitor doesn't (or vice versa, honestly). WAIT.
4. `### PHASE 4: Common objections + responses` — list 5–10 objections sales hears in deals that involve each competitor. For each: the underlying concern + a response that pulls from `language/messaging#value-prop-phrasings` (Decision: runs after messaging-distillation so phrasings exist). WAIT.
5. `### PHASE 5: File assembly` — produce `market/competitive.md`. Frontmatter MUST include `depends_on: [strategy/positioning#competitive-alternatives]`. Slices: `competitive-landscape, differentiators, common-objections`. **Hand-off contract:** standalone → write to `brand/market/competitive.md`; orchestrated → yield assembled markdown back. WAIT.
6. `### PHASE 6: Sync check` — verify every competitor named in this file appears in `strategy/positioning#competitive-alternatives` (or is explicitly marked non-direct). Surface drift to the user. WAIT.

April Dunford voice: same as in positioning, but here she's drilling deeper into terrain rather than reasoning structure. The battle-card is the salesperson's working document; positioning is the strategist's.

Aim for ~280–400 lines.

**Step 3: Verify structure**

Run:
```bash
grep -c '^### PHASE' /Users/ericpage/software/aligned_cc_skills/frameworks/competitive-battle-card/prompt.md
```
Expected: at least 6.

Run:
```bash
grep -c '^You are April Dunford, guiding someone through' /Users/ericpage/software/aligned_cc_skills/frameworks/competitive-battle-card/prompt.md
```
Expected: 1.

Run:
```bash
grep -c 'depends_on.*competitive-alternatives' /Users/ericpage/software/aligned_cc_skills/frameworks/competitive-battle-card/prompt.md
```
Expected: at least 1 (the Decision 21 enforcement must appear in the file-assembly instructions).

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/competitive-battle-card/prompt.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add competitive-battle-card prompt"
```

---

### ✅ Task 19: Framework `competitive-battle-card` — examples.md

**Files:**
- Create: `frameworks/competitive-battle-card/examples.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/competitive-battle-card/examples.md`
Expected: FAIL.

**Step 2: Author examples**

One H2 per phase. Aim for ~140–200 lines. Calibration block in PHASE 1 must include an example of the advisor refusing to introduce a competitor not in positioning, and redirecting the user to update positioning first.

**Step 3: Verify structure**

```bash
grep -c '^## PHASE' /Users/ericpage/software/aligned_cc_skills/frameworks/competitive-battle-card/examples.md
```
Expected: at least 5.

```bash
grep -c '^\*\*User:\*\*\|^\*\*Advisor:\*\*' /Users/ericpage/software/aligned_cc_skills/frameworks/competitive-battle-card/examples.md
```
Expected: at least 10.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/competitive-battle-card/examples.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add competitive-battle-card examples"
```

---

### ✅ Task 20: Framework `competitive-battle-card` — anti-examples.md

**Files:**
- Create: `frameworks/competitive-battle-card/anti-examples.md`

**Step 1: Verify file does not exist**

Run: `ls /Users/ericpage/software/aligned_cc_skills/frameworks/competitive-battle-card/anti-examples.md`
Expected: FAIL.

**Step 2: Author anti-examples**

Required entries:

1. **Introducing a new competitor in this file** — advisor adds a name not in positioning. Wrong per Decision 21 — positioning is canonical; update positioning first, then re-run this framework.
2. **Objection responses divorced from messaging** — advisor writes responses without pulling from `messaging#value-prop-phrasings`. Wrong because the battle-card composes with messaging by design.
3. **Mistaking alternatives.md for competitive.md** — advisor lists "status quo" or "in-house" here. Wrong — those live in `market/alternatives.md`.
4. **Skipping the sync check** — advisor doesn't run PHASE 6. Wrong because drift between positioning and competitive.md is the failure mode this framework prevents.
5. **Per-alternative narrative as marketing fluff** — advisor writes laudatory descriptions of every competitor. Wrong — the narrative is operational ("how they win, who their best customer is"), not marketing copy.

Aim for ~90–140 lines.

**Step 3: Verify structure**

```bash
grep -c '^### ' /Users/ericpage/software/aligned_cc_skills/frameworks/competitive-battle-card/anti-examples.md
```
Expected: at least 5.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/competitive-battle-card/anti-examples.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): add competitive-battle-card anti-examples"
```

---

### ✅ Task 21: Register the six new frameworks in `frameworks/registry.yaml`

**Files:**
- Modify: `frameworks/registry.yaml` (append six new entries)

> Complete Tasks 3–20 before this task — every framework directory referenced here must exist with all three files (`prompt.md`, `examples.md`, `anti-examples.md`).

**Step 1: Verify all six framework directories have all three files**

Run:
```bash
for f in reverse-engineered-brand buyer-persona messaging-distillation brand-voice proof-points-audit competitive-battle-card; do
  ls /Users/ericpage/software/aligned_cc_skills/frameworks/$f/prompt.md \
     /Users/ericpage/software/aligned_cc_skills/frameworks/$f/examples.md \
     /Users/ericpage/software/aligned_cc_skills/frameworks/$f/anti-examples.md
done
```
Expected: 18 lines of output, all files exist.

**Step 2: Verify the registry currently lacks these entries**

Run:
```bash
grep -c '^  - id: reverse-engineered-brand\|^  - id: buyer-persona\|^  - id: messaging-distillation\|^  - id: brand-voice\|^  - id: proof-points-audit\|^  - id: competitive-battle-card' /Users/ericpage/software/aligned_cc_skills/frameworks/registry.yaml
```
Expected: `0`.

**Step 3: Append the six entries**

Append to the end of `frameworks/registry.yaml` (after the last existing entry, before EOF):

```yaml
  - id: reverse-engineered-brand
    name: "a Reverse-Engineered Brand session — a fully interactive walk-through that takes a public URL plus optional supplementary content and produces a canonical brand/ folder ready for human validation"
    advisor: april-dunford
    purpose: "the orchestrator that composes positioning, narrative, jobs-to-be-done, buyer-persona, messaging-distillation, competitive-battle-card, proof-points-audit, brand-voice, and design-principles into a single cold-start brand folder build"
    category: positioning
    domains: [brand-folder, positioning, audiences, personas, messaging, voice, competitive, proof-points, design]
    use_when: "an organization is building its first canonical brand/ folder from a public URL and optional supplementary content"
    required_documents: ["a public URL for the org (homepage or About page)"]
    helpful_documents: ["a local folder path with supplementary content (past decks, customer interviews, sample copy, internal docs)"]

  - id: buyer-persona
    name: "a Buyer-Persona framework — a structured walk-through that produces a role-specific persona file for the buying committee"
    advisor: matt-dixon
    purpose: "produces one personas/{role}.md file per run, capturing role overview, evaluation criteria, skepticism triggers, language resonance, and common objections — anchored in the Challenger commercial-insight frame"
    category: customer
    domains: [buyer-persona, buying-committee, sales-strategy, customer-research]
    use_when: "an organization needs to characterize a specific role on the buying committee (champion, mobilizer, blocker, approver)"
    required_documents: ["the role being profiled (e.g., CMO, VP-Ops, Chief People Officer)"]
    helpful_documents: ["customer research", "interview transcripts", "competitor positioning"]

  - id: messaging-distillation
    name: "a Messaging Distillation framework — the workshop that turns a positioning chain into copy-ready language"
    advisor: april-dunford
    purpose: "distills positioning and narrative into a language/messaging.md file with slices for category name, tagline, elevator-pitch variants, value-prop phrasings, value-prop-to-persona map, key phrases, and (optional) pricing language"
    category: positioning
    domains: [messaging, copywriting, positioning, value-propositions]
    use_when: "positioning and narrative are complete and the org needs copy-ready language for decks, pages, emails, and one-pagers"
    required_documents: ["completed strategy/positioning.md (5-components output)"]
    helpful_documents: ["strategy/narrative.md", "personas/*.md", "proof/proof-points.md", "sample existing copy"]

  - id: brand-voice
    name: "a Brand-Voice framework — a structured pass that extracts tone principles, register, banned phrases, terminology, and glossary into a single voice.md file"
    advisor: steve-krug
    purpose: "extracts a complete language/voice.md from 3–10 sample pieces of existing copy, with seven slices (tone-principles, register-table, dos-and-donts, banned-phrases, banned-terms, glossary, competitor-naming)"
    category: brand
    domains: [voice, tone, terminology, brand-language, copywriting]
    use_when: "an organization has existing copy and needs to extract a documented brand voice + terminology contract"
    required_documents: ["3–10 sample pieces of existing copy (homepage, blog posts, founder tweets, sales emails)"]
    helpful_documents: ["competitor copy samples", "category-name and tagline from messaging.md"]

  - id: proof-points-audit
    name: "a Proof-Points Audit framework — a structured pass that extracts every quantitative claim from existing copy and grounds it in source + date + confidence"
    advisor: the-qa-engineer
    purpose: "produces proof/proof-points.md with structured, sourced, dated claims; conditionally splits into proof/clinical-evidence.md and proof/compliance.md when the org has clinical evidence or compliance certifications"
    category: evidence
    domains: [proof-points, evidence, claims-substantiation, brand-credibility]
    use_when: "an organization needs to inventory and verify every quantitative or proof-shaped claim in its customer-facing copy"
    required_documents: ["existing customer-facing copy (homepage, deck, one-pager)"]
    helpful_documents: ["customer interview transcripts", "case study drafts", "third-party reports", "regulatory filings"]

  - id: competitive-battle-card
    name: "a Competitive Battle-Card framework — a deep view of the competitive terrain built on the canonical alternatives list in positioning"
    advisor: april-dunford
    purpose: "produces market/competitive.md with competitive-landscape, differentiators, and common-objections slices; declares depends_on against strategy/positioning#competitive-alternatives so drift is detectable"
    category: competitive-analysis
    domains: [competitive-analysis, battle-cards, sales-enablement, objection-handling]
    use_when: "positioning and messaging are complete and the org needs a salesperson's working battle card for the named competitors"
    required_documents: ["completed strategy/positioning.md (Component 1: competitive alternatives)", "completed language/messaging.md (value-prop phrasings)"]
    helpful_documents: ["customer win/loss interviews", "competitor public materials"]
```

Pre-edit verification: open the file and confirm the last existing entry ends with a blank line so YAML parsing remains clean. If not, add a blank line before appending.

**Step 4: Verify parse + entry presence**

Run:
```bash
python3 -c "import yaml; data = yaml.safe_load(open('/Users/ericpage/software/aligned_cc_skills/frameworks/registry.yaml')); ids = [e['id'] for e in data['frameworks']]; missing = [x for x in ['reverse-engineered-brand','buyer-persona','messaging-distillation','brand-voice','proof-points-audit','competitive-battle-card'] if x not in ids]; assert not missing, f'missing: {missing}'; print(f'OK — {len(ids)} entries, all 6 new IDs present')"
```
Expected: `OK — N entries, all 6 new IDs present` (where N is the previous count + 6).

Run:
```bash
python3 -c "import yaml; data = yaml.safe_load(open('/Users/ericpage/software/aligned_cc_skills/frameworks/registry.yaml')); req = {'id','name','advisor','purpose','category','domains','use_when'}; new = [e for e in data['frameworks'] if e['id'] in {'reverse-engineered-brand','buyer-persona','messaging-distillation','brand-voice','proof-points-audit','competitive-battle-card'}]; missing = [(e['id'], req - set(e.keys())) for e in new if (req - set(e.keys()))]; assert not missing, f'missing required fields: {missing}'; print('OK — all required fields present on 6 new entries')"
```
Expected: `OK — all required fields present on 6 new entries`.

**Step 5: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add frameworks/registry.yaml
git -C /Users/ericpage/software/aligned_cc_skills commit -m "feat(frameworks): register 6 new brand-folder frameworks in registry"
```

---

### Task 22: Bump plugin version and update README skill reference

**Files:**
- Modify: `.claude-plugin/plugin.json` (version bump)
- Modify: `.claude-plugin/marketplace.json` (version bump — must match)
- Modify: `README.md` (skill reference table if needed)

> Complete Task 21 before this task — the registry must reflect the six new frameworks so the README's framework count aligns with reality.

**Step 1: Read current versions and verify they match**

Run:
```bash
python3 -c "import json; p=json.load(open('/Users/ericpage/software/aligned_cc_skills/.claude-plugin/plugin.json'))['version']; m=json.load(open('/Users/ericpage/software/aligned_cc_skills/.claude-plugin/marketplace.json'))['version']; assert p==m, f'plugin={p} marketplace={m}'; print(f'current version: {p}')"
```
Expected: `current version: 0.28.0` (or whatever the current version is — both must agree).

**Step 2: Bump both to the next minor**

This release adds a new shared skill, six new frameworks, and a new reference document — a minor version bump (per repo CLAUDE.md: semver, pre-1.0). Edit `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`: increment the minor version by 1 (e.g., `0.28.0` → `0.29.0`). Read each file's current version first before writing the new one.

Also update the `description` field in each file if it mentions a framework count. Do NOT use a literal "N → N+6" arithmetic; the pre-existing description string may be stale (e.g., the description may say "147 frameworks" while the registry contains 148 entries today). Instead:

1. Get the current registry count: `python3 -c "import yaml; print(len(yaml.safe_load(open('/Users/ericpage/software/aligned_cc_skills/frameworks/registry.yaml'))['frameworks']))"` — this is the *post-Task-21* count (148 + 6 new = expected 154, but always trust the live count).
2. Edit the description fields in both `plugin.json` and `marketplace.json` to reflect that exact count.

**Step 3: Verify both files agree post-edit and the framework count is correct**

Run:
```bash
python3 -c "import json; p=json.load(open('/Users/ericpage/software/aligned_cc_skills/.claude-plugin/plugin.json'))['version']; m=json.load(open('/Users/ericpage/software/aligned_cc_skills/.claude-plugin/marketplace.json'))['version']; assert p==m, f'plugin={p} marketplace={m}'; print(f'new version: {p}')"
```
Expected: a version string that is strictly greater than the pre-edit version, and both files agree.

Run:
```bash
python3 -c "import yaml; data = yaml.safe_load(open('/Users/ericpage/software/aligned_cc_skills/frameworks/registry.yaml')); print(f'framework count: {len(data[\"frameworks\"])}')"
```
Note the count. Then grep the description field in `plugin.json` and confirm the integer it states matches.

**Step 4: Update `README.md` if it references frameworks by count**

Run:
```bash
grep -n 'framework' /Users/ericpage/software/aligned_cc_skills/README.md
```
Read the surrounding context. If the README states a framework count, update it. If the README lists frameworks individually (in a table), do NOT add the six new entries to a table that's not enumerated — read first, edit only what already follows that pattern.

If the README's skill reference table mentions any of: `_shared/load-brand-slices.md`, `brand-folder-spec.md`, or the new frameworks by name, ensure they are listed. Do not invent new sections that don't already exist; only update existing tables.

**Step 5: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add .claude-plugin/plugin.json .claude-plugin/marketplace.json README.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "chore: bump version for brand-folder framework release"
```

---

### Task 23: Smoke-test the new frameworks via `use-framework`

**Files:**
- No file changes — this is a smoke test that validates the prior tasks integrate correctly.

> Complete Tasks 1–22 before this task.

**Step 1: Confirm all six frameworks are discoverable by the use-framework skill**

The `use-framework` skill discovers frameworks via `frameworks/registry.yaml` (primary) or `frameworks/*/prompt.md` glob (fallback). Verify both:

Run:
```bash
python3 -c "import yaml; data = yaml.safe_load(open('/Users/ericpage/software/aligned_cc_skills/frameworks/registry.yaml')); ids = {e['id'] for e in data['frameworks']}; want = {'reverse-engineered-brand','buyer-persona','messaging-distillation','brand-voice','proof-points-audit','competitive-battle-card'}; missing = want - ids; print('all present in registry' if not missing else f'missing: {missing}')"
```
Expected: `all present in registry`.

Run:
```bash
for f in reverse-engineered-brand buyer-persona messaging-distillation brand-voice proof-points-audit competitive-battle-card; do
  test -f /Users/ericpage/software/aligned_cc_skills/frameworks/$f/prompt.md && echo "$f: OK" || echo "$f: MISSING"
done
```
Expected: 6 `OK` lines.

**Step 2: Verify every prompt.md has the canonical opening line format**

`use-framework` Step 2 parses the opening line via the pattern `You are {Advisor}, guiding someone through {Framework} - {purpose}.` (period, em-dash, or hyphen between framework and purpose). For each new framework, confirm the first non-frontmatter line matches.

Run:
```bash
for f in reverse-engineered-brand buyer-persona messaging-distillation brand-voice proof-points-audit competitive-battle-card; do
  path=/Users/ericpage/software/aligned_cc_skills/frameworks/$f/prompt.md
  awk '/^---$/{n++; next} n>=2 && NF{print FILENAME ":"$0; exit}' "$path"
done
```
Expected: 6 lines, each starting with `You are {Advisor}, guiding someone through `. If any framework lacks frontmatter (no leading `---`), the awk above still grabs the first non-empty line — adjust as needed.

**Step 3: Verify the advisor names in every opening line exist in `advisors/registry.yaml`**

Run:
```bash
python3 -c "
import yaml, re
ar = yaml.safe_load(open('/Users/ericpage/software/aligned_cc_skills/advisors/registry.yaml'))
advisor_ids = {a['id'] for a in ar['advisors']}
advisor_names = {a['name'] for a in ar['advisors']}
expected = {
  'reverse-engineered-brand': 'April Dunford',
  'buyer-persona': 'Matt Dixon',
  'messaging-distillation': 'April Dunford',
  'brand-voice': 'Steve Krug',
  'proof-points-audit': 'The QA Engineer',
  'competitive-battle-card': 'April Dunford',
}
missing = [n for n in expected.values() if n not in advisor_names]
print('all advisor names resolvable' if not missing else f'missing: {missing}')
"
```
Expected: `all advisor names resolvable`.

**Step 4: Verify the shared loader and spec are reachable**

Run:
```bash
test -f /Users/ericpage/software/aligned_cc_skills/skills/_shared/load-brand-slices.md && echo "loader: OK" || echo "loader: MISSING"
test -f /Users/ericpage/software/aligned_cc_skills/docs/brand-folder-spec.md && echo "spec: OK" || echo "spec: MISSING"
```
Expected: `loader: OK` and `spec: OK`.

**Step 5: Verify framework count is consistent across docs**

Run:
```bash
python3 -c "import yaml; data = yaml.safe_load(open('/Users/ericpage/software/aligned_cc_skills/frameworks/registry.yaml')); n = len(data['frameworks']); print(f'frameworks/registry.yaml entries: {n}')"
```

Compare with the description field in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` if either references a count.

If counts diverge, return to Task 22 Step 4 and reconcile.

**Step 6: No commit**

This task makes no file changes; nothing to commit. If any verification fails, return to the appropriate prior task.

---

## Manual Steps (Post-Automation)

After every automatable task in this plan is complete (Tasks 1–23), the following work is intentionally deferred to separate sessions:

1. **End-to-end smoke run.** Manually invoke `/aligned:use-framework reverse-engineered-brand` against a known public URL (e.g., dispatchtrack.com) to confirm the orchestrator runs end-to-end interactively. The smoke run is a user-facing exercise, not a Ralph-automatable task — `reverse-engineered-brand` is interactive-only (Decision 16) and requires a real conversation.
2. **Update personal generator skills.** Edit `~/.claude/skills/generate-deck/SKILL.md`, `generate-blog-post/SKILL.md`, and `generate-one-pager/SKILL.md` to delegate brand-slice reads to `skills/_shared/load-brand-slices.md` and reference `docs/brand-folder-spec.md` for the canonical schema. Out of this plan's scope (different repo); track in a follow-up plan in `~/.claude/`.
3. **Migrate `dispatch-tracker/brand/` to the new layout.** Rename `guidelines/` → layered homes (`strategy/`, `language/`, `proof/`, `market/`, etc.), add required frontmatter, and write `version.yaml` + `contracts.yaml`. Out of this plan's scope (different repo); track in a follow-up plan in the dispatch-tracker repo.

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Plan scope: which artifacts to ship in this plugin repo | Ship the spec doc + shared loader + 6 framework triplets + registry edits + version bump. Out: generator updates in `~/.claude/skills/`; dispatch-tracker brand migration. | Include personal-skills updates inline (rejected — cross-repo); include dispatch-tracker migration (rejected — cross-repo); ship only the shared loader and defer all frameworks to a later plan (rejected — leaves the orchestrator untested). |
| 2 | Granularity of framework tasks | One task per file (prompt / examples / anti-examples) = 18 framework tasks + 5 supporting = 23 total | One task per framework (3 files in one commit per framework) — rejected to keep commit history granular and reviewable. |
| 3 | Reference doc location: `docs/brand-folder-spec.md` vs embedding in the loader skill | Standalone `docs/brand-folder-spec.md` | Embed schema inside `skills/_shared/load-brand-slices.md` (rejected — schema is consumed by generators *and* by humans authoring `brand/` content; a shared skill file should not double as user-facing documentation). |
| 4 | TDD style for documentation tasks | "Test" is a structural grep check on the produced file (counts H2s, opening lines, key tokens). | Skip verification (rejected — every task needs an objective "done" signal for autopilot); add YAML/markdown validators (deferred — the existing repo has no lint infra, and adding it is out of scope). |
| 5 | Version bump magnitude | Minor bump (e.g., 0.28.0 → 0.29.0) | Patch bump (rejected — adds new public surface area: 6 frameworks + 1 shared skill + 1 spec doc); major bump (rejected — pre-1.0 semver, public API not yet stabilized). |
| 6 | How to verify advisor identity in opening lines | Python script that loads `advisors/registry.yaml` and checks names | Trust the framework author + manual review (rejected — autopilot needs deterministic verification); regex grep (acceptable fallback if Python is unavailable, but a YAML load is cleaner). |
| 7 | Whether to include a fixture brand folder for integration-testing the loader | Defer — the loader has no executable code; structural grep checks are sufficient for v1 | Build a small `e2e/fixtures/brand/` fixture and a promptfoo scenario that exercises the loader (rejected — adds promptfoo scenarios + a fixture per generator, and the loader's correctness is verifiable by reading its procedure. Plan in a follow-up if first downstream consumer surfaces a loader bug.) |
| 8 | Should the orchestrator's prompt.md inline every sub-framework's phases, or delegate by reference? | Delegate by reference — orchestrator's prompt instructs the LLM to read and run each sub-framework's `prompt.md` | Inline every phase (rejected — duplicates content; sub-framework prompts already exist; inlining would create two sources of truth and drift). |
| 9 | Manifest scope: empty (no MCP tools required) | Empty `mcp-tools-required: []` block | Omit manifest (rejected — per writing-plans, a missing manifest signals "no manifest" rather than "author confirmed no MCP requirements." Explicit empty block is the correct intent signal.) |
| 10 | What to do about the donald-miller advisor referenced by `storybrand-homepage` (situational, not in scope) | Ignore — `storybrand-homepage` is in the design's "Optional (situational)" list, not in scope for this plan. | Add donald-miller advisor as a sub-task (rejected — scope creep; the framework isn't being authored here). |
| 11 | Phase heading convention: `## PHASE` (H2) vs `### PHASE` (H3) | H3 phases under an outer H2 wrapper, matching every existing framework prompt in the repo | Round 1 critique found the original plan diverged from the established convention; H3 is the unanimous existing pattern. |
| 12 | Opening line punctuation: em-dash vs ASCII hyphen | ASCII hyphen (`-`) between framework name and purpose | Matches the dominant repo convention (~91% of existing prompts use ASCII hyphen). The `use-framework` parser accepts hyphen, em-dash, or period — this is a consistency choice, not a parser requirement. |
| 13 | Sub-framework write hand-off — who writes the file when the orchestrator runs? | Sub-frameworks YIELD assembled markdown back to the orchestrator; orchestrator writes everything atomically in PHASE 11. Standalone invocation (no orchestrator) writes directly. **Mode detection (applies to every sub-framework in Tasks 6, 9, 12, 15, 18):** at PHASE 1 the framework checks for an orchestrator-set conversation context flag (e.g., a sentinel paragraph "Orchestrated by reverse-engineered-brand" in the conversation history); if absent, the framework asks the user once "standalone or orchestrated?" and proceeds accordingly. The file-assembly phase MUST honor whichever mode was set. | Decision surfaces a mode-detection requirement on every sub-framework. Alternative (sub-framework always writes) was rejected because the orchestrator needs to validate the full folder shape before any disk write, and partial writes leave invalid `brand/` states if a phase fails. |
| 14 | Spec section count: 11 vs 12 | 12 — adds a "Subdomain reuse" H2 with the design's Section 9 table set | Round 1 critique caught the omission; subdomain reuse is load-bearing for generators that need to confirm a brand folder is digital-health-shaped. |

### Appendix: Decision Details

#### Decision 1: Plan scope — what ships in this plugin repo

**Chose:** Spec doc + shared loader + 6 framework triplets + registry edits + version bump. Three classes of work explicitly deferred to other repos: (a) `~/.claude/skills/generate-deck/`, `generate-blog-post/`, `generate-one-pager/` updates; (b) `dispatch-tracker/brand/` migration; (c) per-consumer eval scenarios in each `brand/eval/`.

**Why:** Per the project CLAUDE.md cross-repo guard, plans must live in the repo where the work happens. The shared loader and the six frameworks are the canonical infrastructure that downstream consumers depend on; they belong in the plugin. The generator updates and dispatch-tracker migration are consumer-side adoption — both are downstream of this plan completing, and each has its own context (the personal-skills repo and the dispatch-tracker repo respectively). Bundling them would have stranded a cross-repo plan in a single repo's history, and the cross-repo guard would have refused it anyway. The clean cut here is: the plugin ships the contract; consumers adopt the contract on their own timelines.

**Alternatives rejected:**
- Include personal-skills updates inline — violates the cross-repo guard; the work targets `~/.claude/skills/`, not `/Users/ericpage/software/aligned_cc_skills/`.
- Include dispatch-tracker migration — same.
- Ship only the shared loader and defer all frameworks to a later plan — leaves `reverse-engineered-brand` (the orchestrator) untested in isolation and breaks the design's promise of a complete v1.

#### Decision 2: Granularity — one task per file vs one per framework

**Chose:** One task per file (18 framework tasks total: 6 frameworks × 3 files each).

**Why:** Each commit is one logical artifact (a `prompt.md`, an `examples.md`, an `anti-examples.md`). Reviewers can audit one calibration source at a time. The autopilot's per-task verification gates fire on smaller units, which surfaces drift earlier — a malformed `prompt.md` doesn't have to wait for the `examples.md` and `anti-examples.md` commits to be flagged.

**Why not one task per framework:** A single commit that drops 1,000+ lines of advisor-voice content across three files is harder to review and harder to bisect if a framework misbehaves. The granularity also matches the existing repo's per-framework structure where each file is independently authored.

#### Decision 3: Reference doc location

**Chose:** Standalone `docs/brand-folder-spec.md`.

**Why:** The schema serves two consumers: (a) generators that read brand folders, and (b) humans authoring brand content. Generators will reference the spec by path; humans need a non-skill-file home for the reference. Embedding inside the shared loader file would couple two concerns. Keeping the spec in `docs/` matches the repo's convention for canonical references (`docs/positioning.md`, `docs/workflow.html`, etc.).

**Alternatives rejected:**
- Embed in the shared loader — couples spec to skill; harder for humans to find.
- Put the spec inside `skills/_shared/brand-folder-spec.md` — `_shared/` is for procedure-shaped skill content, not reference documentation.

#### Decision 4: TDD style for documentation tasks

**Chose:** Structural grep checks (count H2 sections, verify opening line format, verify key tokens like "Decision 21").

**Why:** These tasks produce markdown content, not executable code. The autopilot needs a deterministic "done" signal per task; grep-based structure checks are deterministic, fast, and catch the most common failure modes (skipped sections, malformed opening lines, missing decision citations). They will not catch deeper content-quality issues — those are caught at integration time (when `use-framework` actually loads the prompt) and during human review of the artifacts.

**Why not richer validation:** A YAML/markdown linter would catch more, but the repo currently has no lint infrastructure. Adding it is out of scope for this plan. The proposed grep checks are a 90% solution that ships today.

#### Decision 5: Version bump magnitude

**Chose:** Minor bump (e.g., 0.28.0 → 0.29.0).

**Why:** This release adds new public surface area: a shared skill (`load-brand-slices`), six new frameworks (publicly invocable via `/aligned:use-framework`), and a new reference document. Per the repo's pre-1.0 semver convention, additive surface area = minor bump. Patch-level would understate the change; major would overstate (no breaking changes, no API contracts removed).

**Why not bump on every commit:** The version bump is a single coordinated event at the end of the plan, not per-commit. The two version files (`plugin.json` and `marketplace.json`) must agree; bumping in the middle of the plan would risk divergence if a later task fails. Bumping last keeps the release atomic.

#### Decision 6: Advisor identity verification

**Chose:** Python script that loads `advisors/registry.yaml` and checks names against expected advisors per framework.

**Why:** The opening line of every framework prompt encodes the advisor name. If a framework's opening line names "April Dunford" but the registry has only "April Dunforde," `use-framework` will fail to load the right advisor voice. A YAML-load-based check is more robust than regex (which would miss YAML reformatting) and catches the failure mode at the lowest cost.

**Why not regex:** Acceptable fallback if Python is unavailable, but YAML loading is the cleaner check. Both would catch the same failure modes.

#### Decision 7: No fixture brand folder for the loader

**Chose:** Defer. The loader's correctness is verifiable by reading its procedure (structural grep on `skills/_shared/load-brand-slices.md` confirms the required sections exist).

**Why:** The loader has no executable code in v1 — it is a markdown procedure that the LLM follows. A fixture-driven integration test would need either (a) a promptfoo scenario that exercises the loader against a fixture brand folder, or (b) a code implementation of the loader. Both add scope this plan deliberately avoids. The first downstream consumer (a generator that delegates to the loader) will surface loader bugs naturally; v2 can promote the loader to code and add a fixture suite then. This matches Open Question #1 in the design.

**Why not build it now:** Adds 2–3 tasks (fixture brand folder, promptfoo scenario, scorer) for a check that has no concrete failure mode to test against today. YAGNI.

#### Decision 8: Orchestrator delegation vs inlining

**Chose:** Delegate by reference. The `reverse-engineered-brand` prompt.md tells the LLM to read and run each sub-framework's `prompt.md` in order, honoring WAIT points.

**Why:** Sub-framework prompts already exist (5-components-positioning, strategic-narrative, jobs-to-be-done) or are being authored as part of this plan (buyer-persona, messaging-distillation, brand-voice, proof-points-audit, competitive-battle-card). Inlining all phases would create a second source of truth that drifts the moment a sub-framework is sharpened. Delegation is the same pattern `use-framework` already uses for loading prompt + examples + anti-examples — the LLM is fluent with composing these files.

**Why not inline:** Maintenance disaster. Every sub-framework edit would require a parallel orchestrator edit. The cross-reference makes the orchestrator a thin shell, but a thin shell is the right shape for an orchestrator.

#### Decision 9: Manifest scope

**Chose:** Empty `mcp-tools-required: []` front-matter block at the top of the plan.

**Why:** The writing-plans skill distinguishes "no manifest" (skip preflight) from "empty manifest" (author confirmed no MCP requirements). This plan involves only Read/Write/Edit/Bash/Grep/Glob — no MCP tools. The empty block is the correct signal.

#### Decision 10: donald-miller advisor

**Chose:** Ignore. `storybrand-homepage` is in the design's "Optional (situational)" framework list — not part of the 6 frameworks this plan builds.

**Why:** The advisor is referenced only by a framework that already exists in the registry (per the survey, `storybrand-homepage` is EXISTING and "already registered"). The framework is generator-time (used by `generate-landing-page`), not part of the brand-folder deepen-next queue. If the framework is registered without its advisor, that is a pre-existing issue; this plan does not inherit it. The user can address the missing advisor in a separate session.
