# Global Content Skills Migration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Move 3 content generation skills (`generate-deck`, `generate-blog-post`, `generate-one-pager`) from `dispatch-tracker/skills/` to `aligned_cc_skills/skills/`, generalizing them so any project with a `brand/CLAUDE.md` manifest can use them.

**Source Design Doc:** `docs/plans/2026-03-23-global-content-skills-design.md`

**Architecture:** Each skill is a single SKILL.md file. Copy from dispatch-tracker, apply systematic generalization transforms (strip DispatchTrack references, replace `brand/INDEX.md` → `brand/CLAUDE.md`, add halt guards, restructure required/optional file matrix per design doc, strip hardcoded colors/fonts from slide design brief, make verticals dynamic). Then update aligned_cc_skills README.md and plugin.json. Cross-repo changes (dispatch-tracker cleanup, ewp-site skeleton update) are post-automation manual steps since they target different repositories.

**Tech Stack:** Markdown skill files, JSON (plugin.json)

---

## Manual Steps (Post-Automation)

> Complete these steps manually after all automated tasks finish.

- [ ] **In dispatch-tracker:** Verify `brand/CLAUDE.md` exists and contains a valid brand asset manifest. If the file is instead named `brand/Claude.md`, rename it via `git mv brand/Claude.md brand/CLAUDE.md` (macOS is case-insensitive — `git mv` is required). If already `brand/CLAUDE.md`, no action needed.
- [ ] **In dispatch-tracker:** Update `e2e/scenarios/generate-blog-post-happy-path.md` line 14: change `brand/INDEX.md` to `brand/CLAUDE.md`
- [ ] **In dispatch-tracker:** Search all SKILL.md files and other scenarios for remaining `brand/INDEX.md` references and update to `brand/CLAUDE.md` (skills themselves will be removed, but verify scenarios first)
- [ ] **In ewp-site:** Update `brand/templates/blog-post/skeleton.md` to align with PIEI methodology — add Problem/Insight/Evidence/Implication section structure alongside the existing Setup/Principle/Mechanism/Application structure, or replace it per user preference
- [ ] **Verification:** Invoke `/aligned:generate-deck` from dispatch-tracker with a test prospect — verify it reads `brand/CLAUDE.md`, loads brand context, and generates a deck
- [ ] **Verification:** Invoke `/aligned:generate-blog-post` from ewp-site with a test topic — verify it reads `brand/CLAUDE.md`, loads ewp-site brand context, and generates PIEI-structured output
- [ ] **Verification:** Invoke any skill from a project WITHOUT `brand/CLAUDE.md` — verify it halts with setup instructions
- [ ] **In dispatch-tracker:** Only after ALL verifications above pass, remove `skills/generate-deck/`, `skills/generate-blog-post/`, and `skills/generate-one-pager/` directories. Do not proceed with removal if any verification step failed.

---

### ✅ Task 1: Create generalized generate-deck SKILL.md

**Files:**
- Create: `skills/generate-deck/SKILL.md`

**Step 1: Read source file**

Read `/Users/ericpage/software/dispatch-tracker/skills/generate-deck/SKILL.md` (338 lines). This is the source to generalize.

**Step 2: Write the generalized file**

Create `skills/generate-deck/SKILL.md` with the source content, applying ALL of the following transforms. Every transform is mandatory — do not skip any.

**Transform A — Frontmatter (no change needed):**
The frontmatter `name` and `description` are already brand-agnostic. Keep as-is.

**Transform B — Overview paragraph (line 10):**
```
BEFORE: You generate branded B2B sales decks for DispatchTrack. Each deck is personalized
AFTER:  You generate branded B2B sales decks. Each deck is personalized
```
Remove "for DispatchTrack" — the rest of the sentence stays.

**Transform C — Remove Phase 1 scope note (lines 45-46):**
Delete the entire blockquote:
```
> **Phase 1 scope:** Only the `furniture-appliance` audience profile exists. Prospects in other verticals (food/beverage, consumer services) will trigger the missing-context halt until those audience files are created.
```

**Transform D — Add halt guard before required files list:**
Insert after the line "Read these files from the project root." and before the required files list:

```markdown
**Halt guard:** First, check if `brand/CLAUDE.md` exists at the project root. If not, halt with:
> No brand context found. This skill requires a `brand/` directory with a `CLAUDE.md` manifest at the project root. See the brand context contract in the Aligned plugin README.
```

> **Behavior change:** The halt guard is new. Projects invoking this skill without `brand/CLAUDE.md` will now receive a hard halt instead of proceeding with whatever context is available.

**Transform E — Restructure required files list (lines 48-61):**

> **Behavior change:** Files 4-13 in the list below are downgraded from Required/halt-on-missing (original) to Recommended or Standard/graceful-skip. Projects that previously relied on the halt guard to catch misconfigured brand directories (e.g., missing `competitive.md`) will no longer receive a halt — the skill will silently proceed without those files. This is intentional per the design doc to enable adoption by projects with minimal brand context.
Replace the current numbered list (items 1-12) with this tiered structure:

```markdown
**Required files (skill halts if missing):**
1. `brand/CLAUDE.md` — brand asset manifest
2. `brand/guidelines/brand-voice.md` — tone and style rules
3. `brand/guidelines/messaging-framework.md` — market category and value props

**Recommended files (skill adapts if missing):**
4. `brand/guidelines/visual-identity.md` — colors, fonts, spacing. If missing: skip slide design brief in Step 4b-ii, output markdown only.

**Standard context files (loaded if available, gracefully skipped if absent):**
5. `brand/guidelines/positioning.md` — 5-component positioning chain
6. `brand/guidelines/competitive.md` — competitive positioning and differentiators
7. `brand/guidelines/proof-points.md` — statistics, metrics, customer logos
8. `brand/guidelines/terminology.md` — approved terms and glossary
9. `brand/guidelines/audiences/{vertical}.md` — vertical-specific messaging (vertical from prospect file). If missing: generate without vertical-specific tuning.
10. `brand/templates/deck/framework.md` — narrative arc template. If missing: use skill-embedded Dunford 8-step as default.
11. `brand/templates/deck/skeleton.md` — slide structure template
12. `brand/templates/examples/deck-example-1.md` — reference output for style

**Persona files (one per stakeholder, skipped if unavailable):**
13. `brand/personas/{role}.md` — base buyer persona for each stakeholder role
```

Note: `prospects/{slug}.md` is intentionally omitted from this list — prospect loading is handled in Step 1a (unchanged), not the brand context loading section.

**Transform F — Quality gates (lines 99-108):**
Apply these specific changes to individual quality gate items:

| Original gate | Generalized gate |
|---|---|
| `Uses "right-time delivery" (not "on-time delivery") per terminology.md` | `Uses correct terminology per terminology.md (if loaded)` |
| `All statistics match proof-points.md exactly — no invented numbers` | `All statistics match proof-points.md exactly — no invented numbers (if proof-points.md loaded)` |
| `Deck example (deck-example-1.md) was used as style reference` | `Reference example used as style guide (if available)` |

All other quality gates are already brand-agnostic — keep them unchanged.

**Transform G — Slide design brief brand constraints (lines 213-222):**
Replace the hardcoded color/font block:

```
BEFORE:
## Brand design constraints
- Primary: #1779ba (DispatchTrack Blue)
- Dark text: #0a0a0a
- Accent: #0d4f7e
- Background: #ffffff, section fills #f4f4f4
- Font family: Lora (serif) — fallback to Georgia if web-safe fonts required
- Style: Clean, professional, high-contrast, generous whitespace
- See brand/guidelines/visual-identity.md for full palette and typography rules

AFTER:
## Brand design constraints
Read color palette, typography, and styling from `brand/guidelines/visual-identity.md`. Apply the brand's primary, accent, background, and text colors. Use the specified font family with appropriate web-safe fallbacks for PPTX rendering.

If `brand/guidelines/visual-identity.md` is not available, skip the slide design brief entirely — the markdown deck is the deliverable.
```

**Transform H — CLI rendering font reference (in Context B — Claude Code CLI section, the line starting with "Web-safe fonts only"):**
```
BEFORE: Web-safe fonts only — use Georgia as the Lora fallback (see `brand/guidelines/visual-identity.md` PPTX Rendering Notes)
AFTER:  Web-safe fonts only — use the fallback font specified in `brand/guidelines/visual-identity.md`, or a serif web-safe default if no fallback is specified
```

**Transform I — Fallback rendering message (lines 275-276):**
Already brand-agnostic. No change needed.

**Step 3: Verify no brand-specific references remain**

Run: `grep -c "DispatchTrack" skills/generate-deck/SKILL.md`
Expected: 0 matches

Run: `grep -c "brand/INDEX.md" skills/generate-deck/SKILL.md`
Expected: 0 matches

Run: `grep -c "#1779ba\|DispatchTrack Blue\|Lora (serif)" skills/generate-deck/SKILL.md`
Expected: 0 matches

Verify frontmatter `name: generate-deck` matches directory name.

**Step 4: Commit**

```bash
git add skills/generate-deck/SKILL.md
git commit -m "feat: add generalized generate-deck skill"
```

---

### ✅ Task 2: Create generalized generate-blog-post SKILL.md

**Files:**
- Create: `skills/generate-blog-post/SKILL.md`

**Step 1: Read source file**

Read `/Users/ericpage/software/dispatch-tracker/skills/generate-blog-post/SKILL.md` (254 lines). This is the source to generalize.

**Step 2: Write the generalized file**

Create `skills/generate-blog-post/SKILL.md` with the source content, applying ALL of the following transforms.

**Transform A — Overview paragraph (line 10):**
```
BEFORE: You generate branded thought leadership blog posts for DispatchTrack. Each post follows the PIEI narrative arc (Problem → Insight → Evidence → Implication) and is reviewed by a 3-reviewer panel before delivery. Posts are educational, not promotional — DispatchTrack appears only in the final section.
AFTER:  You generate branded thought leadership blog posts. Each post follows the PIEI narrative arc (Problem → Insight → Evidence → Implication) and is reviewed by a 3-reviewer panel before delivery. Posts are educational, not promotional — the brand appears only in the final section.
```

**Transform B — Vertical parsing (line 22):**
```
BEFORE: Extract topic (required) and vertical (optional: furniture-appliance, food-beverage, consumer-services).
AFTER:  Extract topic (required) and vertical (optional — read available verticals from `brand/CLAUDE.md` or `brand/guidelines/audiences/`).
```

**Transform C — Add halt guard before required files list:**
Insert after "Read these files from the project root." (line 34):

```markdown
**Halt guard:** First, check if `brand/CLAUDE.md` exists at the project root. If not, halt with:
> No brand context found. This skill requires a `brand/` directory with a `CLAUDE.md` manifest at the project root. See the brand context contract in the Aligned plugin README.
```

> **Behavior change:** The halt guard is new. Projects invoking this skill without `brand/CLAUDE.md` will now receive a hard halt instead of proceeding with whatever context is available.

**Transform D — Restructure required files list (lines 37-49):**

> **Behavior change:** `messaging-framework.md` is downgraded from Required/halt to Recommended/notify-and-proceed. Files 4-9 are downgraded from Required/halt to Standard/graceful-skip. Projects relying on halt guards to catch missing brand files will no longer receive halts for these files.

Replace the current numbered list with this tiered structure:

```markdown
**Required files (skill halts if missing):**
1. `brand/CLAUDE.md` — brand asset manifest
2. `brand/guidelines/brand-voice.md` — tone and style rules

**Recommended files (skill notifies user if missing, then proceeds with degraded output):**
3. `brand/guidelines/messaging-framework.md` — market category and value props. If missing: notify user "Messaging framework not found — generating without value-prop integration. Output quality will be reduced." Then proceed.

**Standard context files (loaded if available, gracefully skipped if absent):**
4. `brand/guidelines/positioning.md` — 5-component positioning chain
5. `brand/guidelines/competitive.md` — competitive positioning and differentiators
6. `brand/guidelines/proof-points.md` — statistics, metrics, customer logos
7. `brand/guidelines/terminology.md` — approved terms and glossary
8. `brand/templates/blog-post/framework.md` — PIEI narrative arc template. If missing: use skill-embedded PIEI as default.
9. `brand/templates/examples/blog-example-1.md` — reference output for style

**Conditional (loaded if vertical specified):**
- `brand/guidelines/audiences/{vertical}.md` — vertical-specific messaging. If missing: notify requestor and offer to proceed cross-vertical.
```

**Transform E — Output format section heading (line 85):**
```
BEFORE: {2-3 paragraphs — New Reality + 80/20 DispatchTrack mention}
AFTER:  {2-3 paragraphs — New Reality + 80/20 brand mention}
```

**Transform F — Quality gates (lines 103-118):**
Apply these specific changes:

| Original gate | Generalized gate |
|---|---|
| `Uses "right-time delivery" (not "on-time delivery") per terminology.md` | `Uses correct terminology per terminology.md (if loaded)` |
| `All statistics match proof-points.md exactly — no invented numbers` | `All statistics match proof-points.md exactly — no invented numbers (if proof-points.md loaded)` |
| `DispatchTrack not mentioned before the Implication section` | `Brand not mentioned by name before the Implication section` |
| `Implication section maintains 80/20 ratio (sentence count: ≤1 in 5 sentences references DispatchTrack by name or describes a product capability)` | `Implication section maintains 80/20 ratio (sentence count: ≤1 in 5 sentences references the brand by name or describes a product capability)` |
| `Blog example (blog-example-1.md) was used as style reference` | `Reference example used as style guide (if available)` |

All other quality gates are already brand-agnostic.

**Transform G — Reviewer 1 instructions (lines 128-133):**
No changes needed — already references generic `competitive.md`, not DispatchTrack specifically.

**Transform H — Reviewer 2 instructions (lines 149-150):**
```
BEFORE: Is DispatchTrack absent from sections before Implication?
AFTER:  Is the brand absent from sections before Implication?
```
```
BEFORE: Does the 80/20 ratio hold in the Implication section? (Count sentences: ≤1 in 5 should reference DispatchTrack by name or describe a product capability.)
AFTER:  Does the 80/20 ratio hold in the Implication section? (Count sentences: ≤1 in 5 should reference the brand by name or describe a product capability.)
```

**Transform I — Finding severity definitions (line 167):**
```
BEFORE: (collapsed Insight, wrong tone, invented statistics, no named change in Problem)
AFTER:  (collapsed Insight, wrong tone, invented statistics, no named change in Problem)
```
No change — already brand-agnostic.

**Transform J — Failure indicators in eval-relevant language (line 61 area):**
```
BEFORE: DispatchTrack not mentioned in Problem, Insight, or Evidence sections
AFTER:  Brand not mentioned in Problem, Insight, or Evidence sections
```
(This text appears in the quality gates, already covered by Transform F.)

**Step 3: Verify no brand-specific references remain**

Run: `grep -c "DispatchTrack" skills/generate-blog-post/SKILL.md`
Expected: 0 matches

Run: `grep -c "brand/INDEX.md" skills/generate-blog-post/SKILL.md`
Expected: 0 matches

Run: `grep -c "furniture-appliance\|food-beverage\|consumer-services" skills/generate-blog-post/SKILL.md`
Expected: 0 matches (hardcoded verticals removed)

Verify frontmatter `name: generate-blog-post` matches directory name.

**Step 4: Commit**

```bash
git add skills/generate-blog-post/SKILL.md
git commit -m "feat: add generalized generate-blog-post skill"
```

---

### ✅ Task 3: Create generalized generate-one-pager SKILL.md

> **Note:** The design doc states "One-pager is being completed in parallel; plan assumes it's done before execution." However, the source at dispatch-tracker is currently a 16-line placeholder with a STOP guard. This task migrates the placeholder as-is. The skill will not be usable until the source skill is built in dispatch-tracker and this file is updated with the full implementation. This is acceptable — the skill's own STOP guard prevents accidental invocation.

**Files:**
- Create: `skills/generate-one-pager/SKILL.md`

**Step 1: Write the file**

The source at `/Users/ericpage/software/dispatch-tracker/skills/generate-one-pager/SKILL.md` is a placeholder (16 lines). Create the generalized version with proper frontmatter and halt guard:

```markdown
---
name: generate-one-pager
description: Generate a branded one-pager or battle card for a specified audience using brand context
---

# Generate One-Pager

> **Status:** Placeholder — not yet implemented. **STOP.** Do not execute the steps below. Tell the user this skill is under construction.

Generate a branded one-pager or battle card for a specified audience.

## Planned Behavior

**Halt guard:** First, check if `brand/CLAUDE.md` exists at the project root. If not, halt with:
> No brand context found. This skill requires a `brand/` directory with a `CLAUDE.md` manifest at the project root. See the brand context contract in the Aligned plugin README.

1. Read `brand/CLAUDE.md` to find available assets
2. Load the audience profile matching the user's target
3. Load `brand-voice.md`, `competitive.md`, and `proof-points.md`
4. Load the one-pager template from `brand/templates/one-pager/`
5. Generate content using brand context
6. Output a markdown one-pager draft for review
7. Render output via context-aware delegation (same pattern as generate-deck Step 4b): produce a design brief, then delegate to the PowerPoint add-in (if available), Claude Code `pptx` skill (if in CLI), or fall back to markdown
```

**Step 2: Verify**

Run: `grep -c "DispatchTrack\|brand/INDEX.md" skills/generate-one-pager/SKILL.md`
Expected: 0 matches

Verify frontmatter `name: generate-one-pager` matches directory name.

**Step 3: Commit**

```bash
git add skills/generate-one-pager/SKILL.md
git commit -m "feat: add generalized generate-one-pager skill (placeholder)"
```

---

### Task 4: Update README.md skill reference table

**Files:**
- Modify: `README.md` (the skill reference table starting at line 75)

**Step 1: Add 3 new skills to the reference table**

Find the skill reference table in README.md. Add these 3 rows in the **Content** layer (new layer — insert after the existing "Business" layer rows and before "Pipeline"):

```markdown
| generate-deck | Content | `/aligned:generate-deck` | Generate branded sales decks with April Dunford framework and expert review panel |
| generate-blog-post | Content | `/aligned:generate-blog-post` | Generate thought leadership blog posts with PIEI narrative arc and 3-reviewer panel |
| generate-one-pager | Content | `/aligned:generate-one-pager` | Generate branded one-pagers and battle cards (placeholder) |
```

**Step 2: Add skill permissions**

Find the permissions JSON block in README.md. Add these 3 entries to the `"allow"` array:

```json
"Skill(aligned:generate-deck)",
"Skill(aligned:generate-blog-post)",
"Skill(aligned:generate-one-pager)"
```

**Step 3: Update skill count in header**

Read the README.md header line (line 3) to find the current skill count. Count the actual rows in the skill reference table to validate the baseline. Then add 3 to that count and update the header. (Current header says "25 skills" — verify this matches the actual table row count before adding 3.)

**Step 4: Verify**

Read README.md and confirm:
- 3 new rows present in skill reference table
- 3 new permissions present in allow list
- Header says "28 skills"

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add 3 content generation skills to README reference table"
```

---

### Task 5: Bump version in plugin.json

**Files:**
- Modify: `.claude-plugin/plugin.json`

**Step 1: Update version and description**

In `.claude-plugin/plugin.json`:
- Bump `version` from `"0.9.0"` to `"0.10.0"` (new feature: content generation skills)
- Add "3 content generation skills" to the `description` string (insert before "automated quality gates"). Do not change any other counts in the description — leave advisor and framework counts as-is.

**Step 2: Verify**

Read `.claude-plugin/plugin.json` and confirm version is `"0.10.0"`.

**Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: bump version to 0.10.0 for content generation skills"
```

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Cross-repo changes | Post-automation manual steps | Include as automated tasks with absolute paths |
| 2 | Required file tiers | 3-tier (Required/Recommended/Standard) per design doc | Keep original all-required approach |
| 3 | Quality gate generalization | Replace brand name with "the brand" | Remove brand-specific gates entirely |
| 4 | Version bump | 0.9.0 → 0.10.0 | 0.9.1 (patch) |
| 5 | Skill layer name | "Content" | "Generation", "Marketing" |
| 6 | Notification policy for missing Recommended files | Per-skill policy (notify for messaging-framework in blog, silent skip for visual-identity in deck) | Uniform notify-all or silent-skip-all |

### Appendix: Decision Details

#### Decision 1: Cross-repo changes as post-automation manual steps
**Chose:** Post-automation manual steps for dispatch-tracker and ewp-site changes
**Why:** The plan executes within the aligned_cc_skills repo context. The executor (Ralph loop or interactive session) operates within a single repo's worktree. Changes to dispatch-tracker (manifest rename, eval scenario updates, skill removal) and ewp-site (blog skeleton update) require separate sessions in those repos. The verification steps (invoking skills from consuming projects) are inherently interactive — they require running Claude Code in each project and testing the skill invocation. Attempting to automate these via absolute-path edits would be fragile and skip the crucial "does the skill actually work from this project?" verification.
**Alternatives rejected:**
- Include as automated tasks with `git -C` commands: Fragile — executor may not have write permissions to other repos from the aligned_cc_skills worktree context. Also skips interactive verification.

#### Decision 2: Required file tiers matching design doc matrix
**Chose:** 3-tier system (Required/Recommended/Standard) from the design doc's "Required vs Optional Brand Files per Skill" tables
**Why:** The original dispatch-tracker skills treated 11+ files as required-with-halt. This made sense for a single-brand context where all files were expected to exist. For a global skill, many of those files are optional — a project might not have competitive positioning docs, proof points, or audience profiles, and the skill should still generate useful output with graceful degradation. The design doc's tiered approach (only CLAUDE.md + brand-voice + messaging-framework are truly required for generate-deck) enables broader adoption while maintaining quality for the core generation.
**Alternatives rejected:**
- Keep all-required approach: Would prevent adoption by projects with minimal brand context, defeating the purpose of globalization.

#### Decision 3: Quality gate generalization approach
**Chose:** Replace "DispatchTrack" with "the brand" or "brand" in quality gates, keep the gates themselves
**Why:** The quality gates encode the PIEI/Dunford methodology, which is the opinionated value the skills provide. "Brand not mentioned before Implication section" and "80/20 sentence ratio" are framework rules, not brand-specific rules. Generalizing the noun while keeping the rule preserves the methodology. The design doc explicitly states "Skills retain their opinionated narrative frameworks."
**Alternatives rejected:**
- Remove brand-specific gates entirely: Would weaken the methodology enforcement that makes these skills valuable. The 80/20 ratio and brand-placement rules are core to PIEI quality.

#### Decision 4: Version bump to 0.10.0
**Chose:** 0.10.0 (minor version bump)
**Why:** Adding 3 new skills is a feature addition, not a patch. Semver convention: minor version for new features. The previous version was 0.9.0.
**Alternatives rejected:**
- 0.9.1 (patch): Adding new skills is a feature, not a bug fix.

#### Decision 5: Skill layer name "Content"
**Chose:** "Content" as the layer name in the README skill reference table
**Why:** These skills generate content (decks, blog posts, one-pagers). "Content" is descriptive and consistent with the existing layer naming convention (Foundation, Pipeline, Business, Methodology, etc.). It's the most accurate single word for what these skills do.
**Alternatives rejected:**
- "Generation": Too generic — all skills "generate" something.
- "Marketing": Too narrow — the skills generate educational thought leadership, not just marketing material.

#### Decision 6: Per-skill notification policy for missing Recommended files
**Chose:** Per-skill policy — `generate-blog-post` notifies user when `messaging-framework.md` is missing; `generate-deck` silently skips when `visual-identity.md` is missing
**Why:** The impact of the missing file differs by skill. For blog posts, the messaging framework drives the entire value-prop integration — without it, the post loses a significant quality dimension, so the user should know. For decks, the visual identity only affects the slide design brief (an optional rendering step) — the markdown deck is still fully functional without it, so silent skip is appropriate. The design doc's Required vs Optional tables encode this asymmetry explicitly.
**Alternatives rejected:**
- Uniform notify-all: Would create unnecessary noise for generate-deck users who intentionally run without visual identity (e.g., markdown-only workflows).
- Uniform silent-skip-all: Would hide a meaningful quality degradation from blog post users.
