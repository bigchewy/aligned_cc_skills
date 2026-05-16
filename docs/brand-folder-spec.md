# Brand Folder Spec (Canonical)

> **Status:** Canonical reference for the AI-native `brand/` folder schema. Skills that consume `brand/` (generators, audits, persona checks) and skills that produce `brand/` (the `reverse-engineered-brand` orchestrator and its sub-frameworks) MUST conform to this spec.
>
> **Source design:** `docs/mockups/2026-05-15-ai-native-brand-folder.html` (v0.6 — decision log captures rationale)
>
> **Target population:** digital health companies across subdomains (telehealth, RPM, behavioral health, digital therapeutics, payer-side, provider-side, condition platforms). Structural design is general; example fills are digital-health-specific.

## Purpose

This file is the canonical schema reference for the AI-native `brand/` folder. It ships inside the `aligned` plugin and is consumed by generators (generate-deck, generate-blog-post, generate-one-pager, etc.), audits, persona checks, and brand-authoring frameworks. Every generator that reads from `brand/` and every framework that writes to `brand/` must conform to the contracts defined here. The shared loader skill (`skills/_shared/load-brand-slices.md`) is the single runtime implementation of these contracts — generators delegate to it rather than parsing frontmatter inline. Note: schema is v0.1 — the loader and frameworks reference these contracts, but downstream generators have not yet validated all fields end-to-end. Minor field additions/renames may occur in v0.2 before the schema stabilizes.

## Directory tree (canonical)

The canonical folder layout. Every digital-health org installs this same shape. Generators read predictable paths regardless of subdomain. Every file is optional except `CLAUDE.md` — the loader gracefully degrades when slices are missing.

```
brand/
├── CLAUDE.md                       # manifest + slice index + "deepen next" queue
├── version.yaml                    # semver, generator provenance, git_sha
│
├── strategy/                       # the WHY — slow-moving thesis
│   ├── positioning.md              # 5-component Dunford chain
│   └── narrative.md                # Raskin 5-element arc
│
├── language/                       # the WORDS — distilled copy + audience map
│   ├── messaging.md                # category, tagline, elevator variants, vp×persona map, pricing language (optional slice)
│   ├── voice.md                    # tone, register, dos/don'ts, banned phrases/terms, glossary
│   └── voices/                     # OPTIONAL named spokespeople
│       └── {name}.md
│
├── proof/                          # the EVIDENCE — facts with sources + dates
│   ├── proof-points.md             # verifiable business metrics
│   ├── case-studies.md             # customer outcome stories
│   ├── awards-press.md             # third-party validation
│   ├── clinical-evidence.md        # RCTs, peer-reviewed pubs, RWE, FDA clearances, validation studies
│   └── compliance.md               # HIPAA, SOC 2, HITRUST, FDA QSR, ISO, accessibility, audit readiness
│
├── market/                         # the TERRAIN — who else is here
│   ├── competitive.md              # deep battle-card; depends_on strategy/positioning#competitive-alternatives
│   └── alternatives.md             # status quo, build-in-house, do-nothing
│
├── audiences/                      # MARKETS — channel × segment composition
│   ├── channels/                   # employer, payer, provider, pharma
│   │   └── {channel}.md
│   └── segments/                   # commercial, medicaid, ma, aco, ...
│       └── {segment}.md
│
├── personas/                       # ROLES — buyer/user roles
│   └── {role}.md
│
├── design/                         # the LOOK
│   ├── design-principles.md        # the WHY of the visual system
│   ├── tokens.css                  # CSS variables — the WHAT
│   └── visual-identity.md          # logo, color, typography rules
│
├── templates/                      # OUTPUT SCAFFOLDS — org-customized, per-generator
│   ├── deck/  ├── blog-post/  ├── one-pager/
│   ├── email/  ├── landing-page/  └── examples/
│
├── assets/                         # VISUAL FACTS
│   ├── logos/  ├── icons/  ├── images/  └── fonts/
│
├── contracts.yaml                  # composition contract: generator → slices
└── eval/                           # scenarios that verify on-brand output

# NOT in brand/ — sibling tree:
clients/
└── {prospect-name}.md          # per-deal prospect context, transient lifecycle
```

## Per-file purpose table

| File | What it owns | What it does NOT own |
|------|-------------|----------------------|
| `strategy/positioning.md` | 5-component Dunford chain: competitive alternatives, unique attributes, value for best-fit customers, target customers, category. Internal-facing reasoning thesis. Changes ~2× per year. | Taglines, copy strings, messaging variants — those live in `language/messaging.md` |
| `strategy/narrative.md` | Raskin 5-element arc: the world, the change, the losers/winners, the promised land, evidence/magic. Changes when strategy shifts. | Competitor analysis — that lives in `market/competitive.md` |
| `language/messaging.md` | Category name, tagline, elevator variants, value-prop-to-persona map, pricing language (optional slice). Copy-ready strings for slides and generators. | Reasoning that defends the positioning — that lives in `strategy/positioning.md` |
| `language/voice.md` | Tone principles, register rules, dos/don'ts, banned phrases, banned terms, glossary. Institutional voice. Slices: `#tone`, `#register`, `#dos-and-donts`, `#banned-phrases`, `#banned-terms`, `#glossary` | Named spokesperson voices — those live in `language/voices/{name}.md` |
| `language/voices/{name}.md` | Named spokesperson voice profile (optional). Founder-led blogs compose institutional `voice.md` + spokesperson overlay. | Brand-wide voice — that lives in `language/voice.md` |
| `proof/proof-points.md` | Verifiable business metrics with sources and dates. Quantitative claims generators can cite. | Customer narrative stories — those live in `proof/case-studies.md` |
| `proof/case-studies.md` | Customer outcome stories with context, challenge, solution, result. | Raw metrics without narrative — those live in `proof/proof-points.md` |
| `proof/awards-press.md` | Third-party validation: awards, press coverage, analyst mentions, certifications. | Self-asserted claims — those go in proof-points or positioning |
| `proof/clinical-evidence.md` | RCTs, peer-reviewed publications, real-world evidence, FDA clearances, validation studies. Digital health specific. | General proof points or press — those live in their respective files |
| `proof/compliance.md` | HIPAA, SOC 2, HITRUST, FDA QSR, ISO, accessibility, audit readiness status. | Clinical efficacy — that lives in `proof/clinical-evidence.md` |
| `market/competitive.md` | Deep battle-card view of named competitors. Must declare `depends_on: [strategy/positioning#competitive-alternatives]` — every competitor here must be in positioning Component 1. | The canonical competitor list (short, reasoning-grade) — that lives in `strategy/positioning.md#competitive-alternatives` |
| `market/alternatives.md` | Status quo, build-in-house, do-nothing alternatives. Broad "what else could they do?" | Direct named competitors — those live in `market/competitive.md` |
| `audiences/channels/{channel}.md` | Channel-specific procurement context: employer, payer, provider, pharma. | Role-specific buyer profiles — those live in `personas/` |
| `audiences/segments/{segment}.md` | Segment-specific context: commercial, medicaid, MA, ACO, dual, pediatric. | Channel context — that composes separately from `audiences/channels/` |
| `personas/{role}.md` | Buyer/user role profile: responsibilities, pain points, decision criteria, objections. Composes with audience dimensions at generation time. | Market segmentation — that lives in `audiences/` |
| `design/design-principles.md` | The WHY of the visual system: principles that explain design choices. | The design tokens (CSS variables) — those live in `design/tokens.css` |
| `design/tokens.css` | CSS custom properties: colors, type scale, spacing, radius, shadow. | Rationale for design choices — that lives in `design/design-principles.md` |
| `design/visual-identity.md` | Logo usage rules, color palette narrative, typography rules. | Raw token values — those live in `design/tokens.css` |
| `templates/{type}/` | Org-customized output scaffolds. Generators stitch org template + org content + prospect file. | Generic content — that lives in the brand files generators load |
| `contracts.yaml` | Composition contract: which generators require which slices, optional slices, min_confidence thresholds, persona × channel × segment overlay rule. | Content itself — that lives in the brand files |
| `CLAUDE.md` | Manifest: every file, every slice, every status/confidence, composition contract summary, "Next Steps to Deepen" framework queue. Auto-loaded by Claude Code — the front door every generator reads first. | Authoritative brand content — that lives in the brand files themselves |
| `version.yaml` | Semver, generator provenance (`generated_by`), `git_sha`, optional sources. | File-level provenance — that lives in each file's `updated:` frontmatter |
| `eval/` | Eval scenarios that verify on-brand output. Ship in consumer's brand folder, NOT in this plugin. | The eval framework definitions — those ship in the plugin |
| `clients/{prospect-name}.md` | Per-deal prospect context: org, deal, stakeholders, signals. Transient lifecycle. Lives in sibling `clients/` tree, NOT inside `brand/`. | Durable brand content — that lives in `brand/` |

## Frontmatter schema

Metadata every `.md` file declares at the top. Lets generators discover which slices a file exposes, gauge confidence, and reason about provenance without reading the body. Seven required fields, a handful of optionals.

Required fields: `id`, `type`, `slices`, `status`, `confidence`, `updated`, `summary`.
Optional fields: `validated_at`, `validated_by`, `sources`, `depends_on`, `consumers`, `tags`.

```yaml
---
id: guideline-positioning
type: positioning                          # positioning|narrative|messaging|voice|persona|audience|...
slices:
  - competitive-alternatives
  - unique-attributes
  - value
  - target-customers
  - category
status: draft                                # draft | validated | retired
confidence: medium                          # low | medium | high
updated: 2026-05-15
validated_at: 2026-05-15                   # OPTIONAL
validated_by: validator@example.com         # OPTIONAL — email or identifier of reviewer
sources:                                    # OPTIONAL — typed citations
  - { kind: url, value: "https://example.com" }
depends_on:                                 # OPTIONAL — slice graph edges
  - "strategy/positioning#category"
consumers: [generate-deck]
tags: [positioning, dunford]
summary: > 5-component positioning chain.
---
```

## Provenance & confidence model

How an agent knows whether a slice is trustworthy enough to use. Two axes — `status` (workflow state: is this human-validated?) and `confidence` (source quality: how solid is the underlying evidence?). Generators set thresholds; slices below the bar are excluded with a footnote.

**Status states:**

| Status | Meaning | Generator behavior |
|--------|---------|-------------------|
| `draft` | Generated/inferred; no human sign-off | Use, include "DRAFT" disclaimer in output appendix |
| `validated` | Reviewed and approved | Use without disclaimer |
| `retired` | Superseded; preserved for context | Skip entirely |

**Confidence labels:**

| Label | Meaning | Threshold behavior |
|-------|---------|-------------------|
| `high` | Primary source — quote, interview, audited metric, founder-validated | Use freely |
| `medium` | Strong inference or corroborated secondary source | Use; flag if `min_confidence=high` |
| `low` | Speculative, pattern-matched, or stub | Exclude unless explicitly opted in |

Generators MAY accept a `min_confidence` parameter (`low | medium | high`, default `medium`). Three states only: `status: draft | validated | retired`.

**Per-section pragma** — when one section of a file diverges from the file-level status/confidence, use:

```
> [PROVENANCE: status=draft, confidence=low, source=website-inference]
```

This pragma applies to the H2 section it appears in and overrides the file-level frontmatter values for that slice only.

## Slice-loading mechanics

How agents consume parts of a file instead of the whole. Every H2 in a `.md` file is a load-addressable slice; generators request only the slices they need. Saves tokens, narrows context, and keeps generators from "improving" content they shouldn't have seen in the first place.

**Slice path syntax:** `{folder}/{file-stem}#{slice-slug}`

Examples:
- `strategy/positioning#competitive-alternatives`
- `language/messaging#category-name`
- `language/voice#banned-phrases`

**Slug derivation rule:** The slug is the H2 heading text lowercased, spaces replaced with hyphens, special characters stripped. The heading `## Competitive Alternatives` → slug `competitive-alternatives`.

**Collision rule:** If two H2s in the same file produce the same slug, append `-2`, `-3` in document order. Lint warns on collision.

**Missing-slice cases — two distinct behaviors:**

| Case | Rule |
|------|------|
| Two H2s slug-collide | Append `-2`, `-3` in document order. Lint warns. |
| `slices:` declares a slug missing from body | Loader returns `status: missing-in-body`. **Lint fails (build-failing).** |
| H2 in body, not in `slices:` | Loader does NOT expose the slice. Lint warns (non-failing). |
| Non-markdown files (CSS, images, fonts) | Exempt from frontmatter. Manifest shows `status: n/a`. |

**v1 ships one loader** at `skills/_shared/load-brand-slices.md`. Every generator delegates — no inline frontmatter parsing. The loader reads the file, parses frontmatter, extracts the requested H2 sections, and returns them with their provenance metadata attached.

**Fallback rule:** When a required slice is missing, the generator degrades gracefully — it continues with whatever slices are available and notes the missing slice in the output appendix. The loader returns `status: missing` for any declared-but-absent slice; the generator is responsible for deciding whether to abort or degrade.

## Composition contract (`contracts.yaml` schema)

The wiring between generators and brand slices. Each generator declares which slices it requires and which are optional; the shared loader resolves them. Centralizing this in `contracts.yaml` means a generator can be added or removed without every other generator having to know.

```yaml
generators:
  generate-deck:
    requires:
      - strategy/positioning
      - language/messaging#category-name
      - language/messaging#value-prop-phrasings
      - language/messaging#value-prop-to-persona-map
      - language/voice#tone-principles
      - personas/{role}           # from clients/{prospect}.md
    optional:
      - audiences/channels/{channel}   # from clients/{prospect}.md; degrades gracefully
      - audiences/segments/{segment}   # from clients/{prospect}.md; degrades gracefully
      - strategy/narrative
      - proof/proof-points
      - market/competitive
      - language/messaging#pricing-language
    compose:
      brand_x_clients: "load brand slices, then clients/{prospect}.md as third overlay"
      persona_x_audience: "base=persona, overlay=audience (last-write-wins per H2)"
    min_confidence: medium

  # ... generate-blog-post, generate-one-pager, generate-email,
  #     generate-landing-page, generate-battlecard, plus 4+ future generators

# Forward-compat — third-party plugin SKILL.md brand_contract blocks merged at runtime
extends: []
```

**Persona × channel × segment × prospect overlay rule (Decision 22):**
Generators compose brand context in layers. The base layer is the brand files themselves. The second layer overlays the target persona from `personas/{role}.md`. The third layer overlays audience dimensions from `audiences/channels/{channel}.md` and `audiences/segments/{segment}.md`. The fourth layer overlays the prospect-specific context from `clients/{prospect-name}.md`. Each overlay uses last-write-wins per H2 slice — a prospect-specific messaging override replaces the brand-wide default for that generator run only. Missing dimensions degrade gracefully — composition continues with whatever exists.

## CLAUDE.md manifest template

The single front-door file every generator reads first. Lists what's in the brand folder, the status and confidence of each file, the composition contract summary, and the queue of frameworks to run next. Claude Code auto-loads `CLAUDE.md` — making it the manifest means generators always see the index before they reach for a specific slice.

The manifest template:

```markdown
# Brand Folder — {Org Name}

> **Version:** {semver from version.yaml}
> **Generated:** {date} by `{framework-id}`
> **Status:** {overall status}

## File inventory

| File | Type | Status | Confidence | Slices |
|------|------|--------|-----------|--------|
| strategy/positioning.md | positioning | draft | medium | competitive-alternatives, unique-attributes, value, target-customers, category |
| strategy/narrative.md | narrative | draft | low | world, change, losers-winners, promised-land, evidence |
| language/messaging.md | messaging | draft | medium | category-name, tagline, elevator-variants, value-prop-to-persona-map, pricing-language |
| language/voice.md | voice | validated | high | tone, register, dos-and-donts, banned-phrases, banned-terms, glossary |
| proof/proof-points.md | proof | draft | low | ... |
| market/competitive.md | competitive | draft | low | competitive-landscape, ... |
| personas/{role}.md | persona | draft | medium | ... |
| ... | | | | |

## Composition contract summary

See `contracts.yaml` for the full generator → slices wiring. Quick reference:
- `generate-deck` requires: `strategy/positioning`, `language/messaging#{category-name,value-prop-phrasings,value-prop-to-persona-map}`, `language/voice#tone-principles`, `personas/{role}`
- All generators: `min_confidence: medium` by default

## Next Steps to Deepen This Brand Folder

Run these frameworks in order. Skip if preconditions not met.

| # | Framework | Deepens | Skip if |
|---|-----------|---------|---------|
| 1 | `5-components-positioning` | `strategy/positioning.md` | already validated |
| 2 | `strategic-narrative` | `strategy/narrative.md` | requires positioning first |
| 3 | `jobs-to-be-done` | `audiences/{channels,segments}/*.md` | single-vertical org |
| 4 | `buyer-persona` | `personas/{role}.md` | single-stakeholder sale |
| 5 | `messaging-distillation` | `language/messaging.md` | requires #1 + #2 |
| 6 | `brand-voice` | `language/voice.md` (incl. terminology + glossary slices) | voice already documented |
| 7 | `proof-points-audit` | `proof/proof-points.md` | early-stage, no public proof |
| 8 | `competitive-battle-card` | `market/competitive.md` | requires positioning first |
| 9 | `design-principles` | `design/design-principles.md` | inherits parent brand |
```

## Versioning

Two layers: file-level `updated:` in frontmatter (per-file, tracks last edit), and folder-level `version.yaml` (tracks the folder as a whole, semver).

**`version.yaml` schema:**

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

Generated artifacts (decks, blog posts) stamp `generated_against: { brand_version, brand_sha }` in their own frontmatter. A v1 staleness script — grep + semver compare — flags artifacts below current.

**Example `version.yaml`:**

```yaml
version: 0.4.0
generated_at: 2026-05-15
generated_by: reverse-engineered-brand
git_sha: c306b25
sources:
  - { kind: url, value: "https://example.com" }
```

## Subdomain reuse

The directory shape does NOT change between digital health subdomains. Only the fills differ — category names, competitor lists, personas, voice principles shift per org and subdomain. This section confirms the architecture's generality and is load-bearing for generators that need to confirm a `brand/` folder belongs to a digital-health org.

**Category slot fills by subdomain:**

| Subdomain | `strategy/positioning#category` (illustrative) |
|-----------|------------------------------------------------|
| Behavioral health platform | "evidence-based digital behavioral health for [population]" |
| Remote patient monitoring | "continuous condition management for [chronic disease]" |
| Digital therapeutic | "prescription digital therapeutic for [indication]" |

**Competitive landscape fills by subdomain:**

| Subdomain | `market/competitive.md#competitive-landscape` |
|-----------|-----------------------------------------------|
| Behavioral health | Headspace Health, Lyra, Spring Health, EAP incumbents, in-network therapy networks, telephonic coaching |
| RPM | Livongo (Teladoc Health), Omada, Vida Health, in-house care-management, device-only vendors |
| Digital therapeutic | Akili, Click Therapeutics, Pear Therapeutics' legacy footprint, traditional pharma adjuncts, off-label app use |

**Personas populated by buyer type:**

| Buyer type | `personas/` populated (digital health buying committee) |
|------------|--------------------------------------------------------|
| Provider-side | CMO, CMIO, Chief Population Health Officer, Director of Care Management, CFO, IT/security |
| Payer-side | Chief Medical Officer, VP Clinical Programs, VP Network, VP Procurement, Actuarial |
| Employer-side | Chief People Officer, Benefits Director, Wellness Director, CFO, Broker/consultant |

**Audiences populated by subdomain:**

| Subdomain | `audiences/` populated (buyer-channel × condition) |
|-----------|---------------------------------------------------|
| Behavioral health | self-insured-employers, health-plans-commercial, health-plans-medicaid, providers-large-systems |
| RPM | health-plans-medicare-advantage, ACOs, large-provider-systems, employer-population-health |
| Digital therapeutic | health-plans-by-indication, prescriber-channels, specialty-pharmacy, employer-condition-specific |

**Voice tone fills by subdomain:**

| Subdomain | `language/voice.md#tone-principles` |
|-----------|-------------------------------------|
| Behavioral health | Clinical credibility + member-warmth; never "wellness app" cute; stigma-aware language |
| RPM | Clinical authority + operational realism; outcomes-language not feature-language; payer-ROI fluent |
| Digital therapeutic | Regulatory-precise (FDA cleared / De Novo / breakthrough), evidence-anchored, mechanism-explicit |

## Eval scenarios (consumer-side)

Programmatic checks that verify generated content stays on-brand. These eval scenario files ship inside each consumer's `brand/eval/` directory, NOT inside this plugin. They run at generation time, on a cadence, or manually via `/aligned:eval-audit`.

**Three baseline evals (ship with every brand folder):**

| Eval | Checks | Pass criterion |
|------|--------|----------------|
| `voice-conformance.md` | Output respects banned phrases; matches register-table | 0 banned hits; register match ≥ 0.8 |
| `positioning-trace.md` | Output traces alternatives → attributes → value → target → category | All 5 in order |
| `proof-points-cite.md` | Every quantitative claim cites proof-points | 100% citation rate |

**Optional eval (add when `market/competitive.md` is populated):**

| Eval | Checks | Pass criterion |
|------|--------|----------------|
| `competitive-alternatives-sync.md` | Every competitor in `competitive.md` is in `strategy/positioning.md` Component 1 | 0 unsynced |

The eval definitions (how to run the evals) ship in the plugin (`skills/_shared/`, framework prompts). The eval scenario files (what to check for a specific brand folder) ship in each consumer's `brand/eval/` directory.

## Hard constraints (recap)

These rules are enforceable — a generator, a lint, or a schema check fails if violated. Pass/fail.

- **Single-org per repo.** Top-level `brand/`, single-tenant. No nested `brand/{slug}/` patterns. Multi-brand orgs use separate repos.
- **One shape, every digital health company.** Directory layout identical across subdomains — telehealth, RPM, behavioral health, digital therapeutics, payer-side, provider-side, condition platforms. B2C consumer wellness, general B2B SaaS, agencies, and advisory practices are out of scope as target users.
- **AI-first design.** Primary consumer is generator agents (~95% of reads). Humans validate occasionally. Optimize for machine-parseable structure, terse summaries, dense slice tagging.
- **Frontmatter mandatory on every `.md`.** No bare markdown.
- **No content duplication.** A claim lives in exactly one file. Other files reference it by slice path.
- **Provenance encoded structurally.** Three states only: `status: draft | validated | retired`.
- **Confidence as label.** `confidence: low | medium | high`. No numeric scores.
- **Slice-loadable by H2.** `{file}#{slug}`. No nested H2-as-decoration.
- **`CLAUDE.md` is the front door.** Lists every file, every slice, every consumer, and the "deepen next" queue.
- **No symlinks outside the repo.** Source-of-truth lives in `brand/`.
- **One loader, not six.** v1 ships shared `skills/_shared/load-brand-slices.md`. Generators delegate.
- **Clean-state cutover.** No `legacy-paths.yaml`. Existing generators update to new paths in the same change. No deprecation window.
- **Brand is durable; `clients/` is transient.** Per-deal prospect context lives in a sibling `clients/{prospect-name}.md`, NOT in `brand/`.
- **Templates are org-customized.** `brand/templates/{type}/` holds the org's specific output structure. Generators stitch org template + org content + prospect file.
