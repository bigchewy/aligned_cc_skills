**Date:** 2026-04-13
**Status:** Draft
**Mockups:** docs/mockups/registry-unification.html

# Registry Unification Design

## Goal

Unify advisor and framework metadata into machine-readable YAML registries that serve as the single source of truth for discovery, skill routing, and reference. Migrate the existing advisor registry from structured markdown to YAML, create a new framework registry for 138 frameworks, and generate derived artifacts (READMEs, searchable HTML catalogs) from the registries.

**Problems solved:**
1. **No framework registry exists.** Skills discover frameworks by globbing 138 `prompt.md` files and parsing first lines at runtime. No centralized metadata for domains, categories, or use-when triggers.
2. **Advisor registry format limits consumers.** The markdown format works for LLM reading but can't serve programmatic consumers (auto-router build script) without fragile regex parsing.
3. **No intent-based selection.** `use-advisor` and `use-framework` do exact name matching only — if the user doesn't name a specific entry, they get a raw list of 65 advisors or 138 frameworks with no recommendation. (Contextual recommendation is a follow-up design — see "Deferred: Contextual Recommendation" below.)
4. **Duplicated count-update logic.** `add-advisor` and `add-framework` maintain counts in multiple places (KB-032). A registry centralizes this.

**Success criteria:**
- Both registries parse as valid YAML with all required fields populated
- All consuming skill files updated and functional (12 files modified — see Impact Summary)
- Auto-generated READMEs match registry state
- Searchable HTML catalogs render correctly with search/filter/expand

## Decision Log

| # | Decision | Rationale | Architect-validated |
|---|----------|-----------|---------------------|
| D1 | YAML over JSON or markdown | YAML serves both LLM context windows and programmatic consumers. Native list/multiline support. Already used in codebase (frontmatter, trigger-map.yaml, promptfooconfig.yaml). ~3x more token-efficient than advisor registry's prose markdown. | Yes |
| D2 | Centralized single file per registry | Discovery requires reading one file, not 138. `add-framework` already has conditional registry step. Consistent with advisor registry pattern. | Yes |
| D3 | Flat list, no nesting by category | Easier to append, sort, and query. Grouping done at query time by consumers. | Yes |
| D4 | `advisor` field stays singular on frameworks | Every `prompt.md` opens with "You are {Single Advisor}" — one voice per framework. `use-framework` parses exactly one advisor name. | Yes |
| D5 | `triggers`/`intent_phrases` not in registry | Auto-router build script generates these via LLM from registry `domains` + `use_when` + prompt content. Registry is source; `skill-router.json` is derivative. | Yes |
| D6 | Selection guidelines stay in registry YAML | Only consumer is critique-panel-orchestration, but no other consumer needs them moved. `use-advisor`/`use-framework` do name matching, not guideline-based selection. Auto-router builds its own index. | Yes |
| D7 | READMEs generated as LLM skill steps, not shell scripts | Plugin runtime pipeline has no executable scripts (though `docs/ralph_loops/` contains shell scripts and the auto-router worktree has `build-router-index.js`). Adding a YAML-parsing script introduces system dependencies (`yq`) that violate the portability rule. Trade-off: LLM generation is non-deterministic across runs. Acceptable since READMEs are reference docs, not build artifacts. If determinism matters later, a Node.js script matching `build-router-index.js` patterns is the path. | Yes |
| D8 | All derived artifacts on-demand, not coupled to add-advisor/add-framework | READMEs and HTML catalogs are reference documents with no active skill consumer. Coupling generation to every add invocation adds latency and failure modes. Generate on-demand when registry changes warrant it. | Yes |
| D9 | `category` is free-form, not enum | No consumer filters by category today. Adding a controlled vocabulary now creates maintenance overhead with no payoff. | Yes |
| D10 | Don't consolidate add-advisor Steps 3 and 8b | Step 3 writes to project-local registries (conditional, format-agnostic — remains unchanged by this migration). Step 8b writes to plugin's own registry (unconditional, migrated to YAML). Different targets, different audiences. | Yes |

---

## Section 1: Registry Schemas

### Advisor Registry (`advisors/registry.yaml`)

```yaml
# Advisor Registry — source of truth for all advisor personas
# Skills and project runtimes derive their formats from this registry.

selection_guidelines:
  narrow_scope: "1-2 critics"
  typical_scope: "2-3 critics"
  complex_scope: "3-4 critics"
  rules:
    - "Hard-exclude any critic whose not_for matches the work's primary domain"
    - "Prefer diversity of lens — avoid overlapping domains"
    - "When in doubt, prefer fewer focused critics over more redundant ones"
  calibration_examples:
    - scope: "A single utility with no integrations"
      critics: [the-architect]
    - scope: "An API route with database writes and RLS"
      critics: [the-architect, the-security-reviewer]
    - scope: "A user-facing feature with backend + UI + auth"
      critics: [steve-jobs, the-architect, the-qa-engineer]
    - scope: "A product launch plan spanning positioning, UI, backend, integrations"
      critics: [april-dunford, steve-jobs, the-architect, the-security-reviewer]

advisors:
  # Fully profiled entry
  - id: steve-jobs
    name: Steve Jobs
    summary: "Co-founder of Apple who demanded insanely great products"
    prompt: advisors/prompts/steve-jobs.md
    domains: [product design, simplicity, UX, focus, user experience]
    evaluation_expertise: >
      Evaluates whether the work achieves simplicity and focus. Does every
      element earn its place? Is the experience intuitive without explanation?
      Catches complexity creep, feature bloat, and loss of focus.
    best_for: >
      Designs with user-facing components where simplicity and focus matter.
      Product vision decisions. Feature prioritization.
    not_for: >
      Pure infrastructure, backend plumbing, CI/CD pipelines, developer tooling,
      data migrations, test architecture.

  # Unprofiled entry (minimum viable)
  - id: seth-godin
    name: Seth Godin
    summary: "Author of Purple Cow, The Dip, and This Is Marketing"
    prompt: advisors/prompts/seth-godin.md
    domains: [marketing, permission-marketing, remarkable-products, tribes]
    note: "Not yet profiled with evaluation expertise."
```

**Required fields:** `id`, `name`, `summary`, `prompt`, `domains`

**Optional fields:** `evaluation_expertise`, `best_for`, `not_for`, `note`

### Framework Registry (`frameworks/registry.yaml`)

```yaml
# Framework Registry — source of truth for all decision frameworks
# Skills use this for discovery, routing, and selection.
# Category is free-form (no controlled vocabulary until a consumer needs filtering).

frameworks:
  - id: 5-components-positioning
    name: 5 Components of Positioning
    advisor: april-dunford
    purpose: "a sequential process that builds differentiated positioning from the ground up"
    category: positioning
    domains: [positioning, differentiation, competitive-analysis]
    use_when: "Needs to build or rebuild product positioning from scratch"
    required_documents: [positioning statement]
    helpful_documents: [competitive landscape, customer research]

  - id: fear-setting
    name: Fear Setting
    advisor: tim-ferriss
    purpose: "a structured exercise for making decisions when paralyzed by fear"
    category: decision-making
    domains: [decision-making, risk-assessment, anxiety]
    use_when: "Paralyzed by a big decision or avoiding something due to fear"
```

**Required fields:** `id`, `name`, `advisor`, `purpose`, `category`, `domains`, `use_when`

**Optional fields:** `required_documents`, `helpful_documents`

**Token budget:** ~50 tokens per framework entry. 138 entries ≈ 7,000 tokens. Fits comfortably in LLM context windows.

---

## Section 2: Migration Strategy

### Phase 1: Create new files (additive, nothing breaks)

- Generate `advisors/registry.yaml` from current `advisors/registry.md` data (deterministic conversion)
- Generate `frameworks/registry.yaml` via two-pass batch processing (see Section 3)
- Add disambiguation comment to YAML files: `# This file will replace advisors/registry.md — do not manually edit registry.md`
- Both files coexist safely — no consumer globs for `registry.*`; all hardcode `registry.md`

### Consumer error handling

YAML introduces a new failure mode: file exists but fails to parse (bad indent, corrupted append). Current markdown parsing is forgiving; YAML is strict. One corrupted registry file breaks all 8 consuming skills simultaneously.

**Required behavior for all consumers:** When YAML parsing fails (file exists but is unparseable), fall back to glob-based discovery (`advisors/prompts/*.md` or `frameworks/*/prompt.md`). Log a warning noting the parse failure. This matches the existing fallback pattern in `use-advisor` and `use-framework`.

### Phase 2: Update consumers (12 files, ordered by dependency)

**Batch A (sequential, dependency-ordered):**

1. **`skills/_shared/critique-panel-orchestration.md`** — Change Read path from `.md` to `.yaml`. Update parsing instructions:
   > Read `advisors/registry.yaml`. Parse the `advisors` list — each entry has: `id`, `name`, `prompt`, `domains` (list), `evaluation_expertise`, `best_for`, `not_for`. Read the `selection_guidelines` section for count rules, hard-exclude logic, and diversity preferences. If the YAML fails to parse, fall back to globbing `advisors/prompts/*.md`.

2. **`skills/use-advisor/SKILL.md`** — Change Read path. Replace "Parse the Quick Reference table" with YAML list reading. Keep glob fallback (also covers YAML parse failures).

3. **`skills/add-advisor/SKILL.md`** — Rewrite Step 8b only (not Step 3 — see D10). Change from "append markdown table row" to "append YAML entry to `advisors/registry.yaml`" with schema template. **Post-append validation:** After appending, re-parse the full registry file. If parsing fails, revert the append and report the error — one bad entry must not corrupt the registry for all consumers. Step 8c (count updates in `README.md`, `plugin.json`, `marketplace.json`) is preserved as-is; counts can be derived from the YAML registry in a future simplification.

4. **`skills/add-framework/SKILL.md`** — Update Step 5 to reference `frameworks/registry.yaml` with YAML entry template. Update fallback format to match schema. **Same post-append validation as item 3.** Step 7b (count updates) preserved as-is.

5. **`skills/use-framework/SKILL.md`** — Read `frameworks/registry.yaml` as primary discovery source. Keep filesystem glob as fallback (also covers YAML parse failures).

**Batch B (parallel, no dependencies):**

6. `skills/brainstorming/critic-registry.md` — path update
7. `skills/find-potential-advisors/SKILL.md` — keep generic "advisor registry" wording (don't hardcode `.yaml` path — preserves portability rule). Add `registry.yaml` as an additional resolution target alongside existing generic detection.
8. `README.md` + `skills/kickstart/SKILL.md` — documentation references
9. `docs/mockups/plugin-split.html` — architecture diagram node references (5 occurrences)

**Not changed (documented):**
- `e2e/eval-surface.yaml` — references `frameworks/*/prompt.md` glob which still matches real files. No change needed unless file layout changes.
- `docs/plans/2026-04-08-plugin-split-design.md` + `docs/plans/2026-04-08-plugin-split-plan.md` — historical plan documents. Path references are dated artifacts, not runtime consumers. Left as-is to preserve historical accuracy.

### Phase 3: Remove old file (separate commit)

- Delete `advisors/registry.md` after all consumers verified
- Separate commit for revert safety and worktree compatibility

### Phase 4: Generate derived artifacts

- Auto-generate `advisors/README.md` from `advisors/registry.yaml`
- Auto-generate `frameworks/README.md` from `frameworks/registry.yaml`
- Generate searchable HTML catalog pages (see Section 6)

---

## Section 3: Framework Registry Population

### Deterministic extraction (no LLM)

| Field | Method | Coverage |
|-------|--------|----------|
| `id` | Directory name | 138/138 |
| `name` | Regex on prompt.md first line | 127/138 (92%) |
| `advisor` | Same regex, group 1 | 127/138 (92%) |
| `purpose` | Text after dash in first line | 127/138 (92%) |
| `required_documents` | YAML frontmatter | 136/138 (98.5%) |
| `helpful_documents` | YAML frontmatter | 136/138 (98.5%) |

**Regex:** `/^You are (.+?),\s*guiding someone through (.+?)\s*[-–—.]/`

**11 outlier frameworks** that don't match the standard format: `landing-page-assembly`, `design-principles`, `do-things-that-dont-scale`, `earnestness-filter`, `enneagram-typing`, `focus-through-saying-no`, `personal-context-intake`, `professional-context-intake`, `quadrinity`, `the-story-so-far`, `6-step-process`. These get a hardcoded fallback map in the generation script — they're a known, closed set since `add-framework` enforces the standard format for new entries.

### LLM classification (3 fields only)

Only `category`, `domains`, and `use_when` need LLM classification. Everything else is deterministic.

### Three-pass approach

Modeled on existing `build-router-index.js` in the auto-router worktree, which already implements this pattern at this scale.

**Pass 1 (deterministic):** Parse all 138 `prompt.md` files. Extract `id`, `name`, `advisor`, `purpose`, `required_documents`, `helpful_documents` via regex + frontmatter parsing. Handle 11 outliers with hardcoded fallback map.

**Pass 2 (LLM, batched):** Send batches of 10 frameworks to Claude Haiku with extracted metadata (name, advisor, purpose, first 300 chars of content). Classify:
- `category` — constrained to starter set (see below)
- `domains` — 2-5 freeform tags per framework
- `use_when` — natural language trigger phrase

Total: ~14 API calls.

**Pass 3 (merge + write):** Combine into `frameworks/registry.draft.yaml` for human review before committing.

### Starter categories (16)

| Category | Description | Example frameworks |
|----------|-------------|-------------------|
| `positioning` | Positioning, messaging, differentiation | 5-components-positioning, positioning-canvas |
| `startup` | Validation, lean methodology, PMF | build-measure-learn, earlyvangelists, product-market-fit-test |
| `content-strategy` | Content creation, audience building | content-inc-model, jk5-content-pillars, batched-content-system |
| `social-media` | Platform-specific tactics | the-algorithm, the-carousel, first-seven-reels |
| `pricing` | Monetization, packaging, subscriptions | value-metric, forever-promise |
| `growth` | Growth marketing, experimentation | growth-hacking-process, creator-flywheel |
| `podcasting` | Podcast strategy and marketing | podcast-brand-strategy, podcast-marketing-systems |
| `negotiation` | Communication, negotiation | calibrated-questions, tactical-empathy-labeling |
| `leadership` | Management, leadership transitions | leadership-pipeline-passages, management-level-progression |
| `strategy` | Decision-making, strategic thinking | first-principles-thinking, finding-the-crux, working-backwards |
| `psychology` | Self-development, inner work | fear-setting, ifs-parts-work, the-work, radical-acceptance |
| `health-autonomic` | Dysautonomia, POTS, autonomic NS | multi-system-approach-pots, pots-subtype-recognition |
| `health-movement` | Spine, movement, physical therapy | flexion-intolerance-assessment, mcgill-big-3 |
| `health-fitness` | Exercise, recovery, training | heart-rate-reserve-training-zones, load-velocity-relationship |
| `conversion` | Landing pages, UX, conversion | landing-page-assembly, cognitive-friction-audit |
| `onboarding` | Intake, context-setting | personal-context-intake, professional-context-intake |

Categories are free-form strings — this starter set guides the LLM classification but is not enforced as an enum. Some frameworks straddle categories; the `domains` field handles cross-cutting concerns.

### Advisor registry generation

The advisor migration is a pure deterministic format conversion — no LLM needed. A script parses the Quick Reference table + detailed entries from `advisors/registry.md` and writes `advisors/registry.yaml`. ~30 unprofiled advisors get entries with empty optional fields (`evaluation_expertise`, `best_for`, `not_for` omitted; `note` populated).

---

## Section 4: Auto-generated READMEs

Both `advisors/README.md` and `frameworks/README.md` are generated from their respective YAML registries. Generation is an LLM skill step — no shell scripts, no system dependencies. This matches the existing pattern of "LLM reads structured data, writes derived artifact."

### `advisors/README.md` contents

- Count: total advisors, profiled count, unprofiled count
- Quick reference table: id, name, domains, summary
- Grouped sections: profiled advisors (with evaluation_expertise summary), unprofiled advisors
- Selection guidelines summary

### `frameworks/README.md` contents

- Count: total frameworks, count per category
- Quick reference table: id, name, advisor, category, use_when
- Grouped sections by category

### Generation

On-demand only — not coupled to add-advisor/add-framework skills. Same reasoning as D8 for HTML catalogs: adding generation steps to every add invocation introduces latency and failure modes when no skill currently reads these READMEs as input. Generate READMEs manually or as a standalone invocation when the registry changes warrant it.

Neither README exists today — clean slate.

---

## Section 5: Deferred — Contextual Recommendation

Contextual recommendation for `use-advisor` and `use-framework` (recommend best match + alternatives when invoked without a specific name) is **deferred to a follow-up design.** The registry migration enables this feature by providing the metadata (`domains`, `use_when`, `best_for`) needed for scoring, but the recommendation behavior itself has its own edge cases, interaction design, and testing surface that warrant separate treatment.

The follow-up design should address:
- Three-path behavior: named (fuzzy match), contextual (intent scoring), bare (listing)
- Scoring heuristic and which fields to weight
- How to distinguish contextual from bare invocations (detection heuristic)
- Handling unprofiled advisors (~55% of catalog lack `best_for`/`evaluation_expertise`)
- Fallback when scoring returns zero or weak matches
- Acceptance criteria for recommendation quality

---

## Section 6: Searchable HTML Catalogs

Two standalone HTML files for browsing advisors and frameworks.

### Files

- `docs/advisor-catalog.html`
- `docs/framework-catalog.html`

Placed in `docs/` consistent with existing `docs/skill-orchestration.html`.

### Design conventions

- Tailwind CDN with project design tokens (accent `#ff6900`, surface `#f5f3ef`)
- Same `tailwind.config` block used across existing mockup files
- Self-contained single HTML files
- Generated from YAML registries

### Features

- **Search box** — filters by name, domain, category, advisor
- **Card or table layout** — key metadata visible per entry
- **Expandable details** — click to reveal full fields (evaluation_expertise, best_for, not_for for advisors; use_when, required/helpful documents for frameworks)
- **Category grouping** with counts
- **Cross-links** — advisor cards link to their frameworks, framework cards link to their advisor
- **Responsive** — usable on mobile

### Generation

On-demand only — not coupled to add-advisor/add-framework skills. HTML generation is heavier than README markdown generation and would add failure modes blocking advisor/framework creation. Generate catalogs manually or as a standalone invocation when needed.

---

## Section 7: Testing & Verification

### Automated tests (new)

- YAML schema validation test in `e2e/tests/` — validates both `advisors/registry.yaml` and `frameworks/registry.yaml` parse as valid YAML with required fields per entry (`id`, `name`, `summary`, `prompt`, `domains` for advisors; `id`, `name`, `advisor`, `purpose`, `category`, `domains`, `use_when` for frameworks)
- Update `e2e/trigger-map.yaml` to include registry files as trigger paths mapping to affected eval scenarios

### Manual verification (per-skill)

**Happy path scenarios:**

| Skill | Test scenario |
|-------|--------------|
| Critique panel | Run brainstorming session → verify critic selection reads YAML, respects `not_for` exclusion |
| use-advisor (named) | `/aligned:use-advisor steve-jobs` → verify fuzzy match from YAML |
| use-advisor (bare) | `/aligned:use-advisor` with no context → verify listing from YAML |
| use-framework (named) | `/aligned:use-framework fear-setting` → verify match from YAML |
| use-framework (bare) | `/aligned:use-framework` with no context → verify listing from YAML |
| add-advisor | Add test advisor → verify YAML entry appended correctly |
| add-framework | Add test framework → verify YAML entry appended correctly |

**Error path scenarios:**

| Scenario | Expected behavior |
|----------|-------------------|
| Malformed `registry.yaml` (bad indent) | Consumer skills fall back to glob-based discovery, log warning |
| `add-advisor` appends bad YAML | Post-append validation catches parse failure, reverts append, reports error |
| `add-framework` appends bad YAML | Same as above |
| `registry.yaml` missing entirely | Fallback to glob-based discovery (existing behavior preserved) |
| Grep for `registry.md` after Phase 3 | Zero matches in skill files (regression check) |

### Migration verification

After Phase 2 consumer updates, before Phase 3 deletion:
- Grep for `registry.md` across all skill files — should return zero matches (except documentation noting the migration)
- Verify `advisors/registry.yaml` entry count matches original `registry.md` advisor count
- Verify `frameworks/registry.yaml` has 138 entries

---

## Implementation Order

| Phase | What | Depends on |
|-------|------|------------|
| 1a | Generate `advisors/registry.yaml` (deterministic conversion) | — |
| 1b | Generate `frameworks/registry.yaml` (three-pass batch) | — |
| 2a | Update critique-panel-orchestration.md | 1a |
| 2b | Update use-advisor (path + YAML reading + glob fallback) | 1a |
| 2c | Update add-advisor Step 8b (YAML append + post-append validation) | 1a |
| 2d | Update add-framework Step 5 (YAML append + post-append validation) | 1b |
| 2e | Update use-framework (path + YAML reading + glob fallback) | 1b |
| 2f | Update Batch B files (4 files, parallel) | 1a |
| 3 | Delete `advisors/registry.md` | 2a-2f verified |
| 4a | Generate `advisors/README.md` (on-demand) | 1a |
| 4b | Generate `frameworks/README.md` (on-demand) | 1b |
| 4c | Generate HTML catalogs (on-demand) | 1a, 1b |
| 5 | Add e2e schema validation tests | 1a, 1b |

**Follow-up (separate design):** Contextual recommendation for use-advisor and use-framework.

---

## Impact Summary

### Files created (new)

| File | Purpose |
|------|---------|
| `advisors/registry.yaml` | Advisor registry (source of truth) |
| `frameworks/registry.yaml` | Framework registry (source of truth) |
| `advisors/README.md` | Auto-generated advisor reference |
| `frameworks/README.md` | Auto-generated framework reference |
| `docs/advisor-catalog.html` | Searchable advisor catalog |
| `docs/framework-catalog.html` | Searchable framework catalog |

### Files modified

| File | Change |
|------|--------|
| `skills/_shared/critique-panel-orchestration.md` | Read path + YAML parsing instructions |
| `skills/use-advisor/SKILL.md` | Read path + YAML parsing + glob fallback |
| `skills/add-advisor/SKILL.md` | Step 8b YAML append + post-append validation |
| `skills/add-framework/SKILL.md` | Step 5 YAML append + post-append validation |
| `skills/use-framework/SKILL.md` | Read path + YAML parsing + glob fallback |
| `skills/brainstorming/critic-registry.md` | Path reference |
| `skills/find-potential-advisors/SKILL.md` | Add YAML as resolution target (keep generic wording) |
| `README.md` | Documentation reference |
| `skills/kickstart/SKILL.md` | Documentation reference |
| `docs/mockups/plugin-split.html` | Architecture diagram references |

### Files deleted

| File | Reason |
|------|--------|
| `advisors/registry.md` | Replaced by `advisors/registry.yaml` |
