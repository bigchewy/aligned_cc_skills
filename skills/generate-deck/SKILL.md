---
name: generate-deck
description: Generate a branded, prospect-specific sales deck using the April Dunford framework with expert review panel
---

# Generate Sales Deck

## Overview

You generate branded B2B sales decks. Each deck is personalized for a specific prospect using their company profile, stakeholder personas, and competitive context. The deck follows the April Dunford 8-step sales pitch narrative arc.

**Announce at start:** "I'm using the generate-deck skill to create a branded sales deck."

**Workflow:** 4 gated steps — Input → Generate → Review → Deliver. Each step completes before the next begins.

## Step 1: Input

The rep provides a one-liner: "Generate a deck for [Company Name]."

### 1a. Locate the prospect file

Search `prospects/` for a matching file (`prospects/{company-slug}.md`). Match on the company name in the frontmatter or filename.

**If found:** Load and display the prospect summary:
- Company name, industry, size
- Stakeholders (name, role)
- Deal stage and competitive context
- Buying trigger

Then ask: **"Anything unusual about this deal I should factor in?"**

If the rep provides additional context, store it — it will be written back to the prospect file in Step 4.

**If NOT found:** Prompt the rep for key details:
- Company name, industry/vertical
- Key stakeholders (name + role for each)
- Any competitive context or special circumstances

Offer to create the prospect file from the provided details. If the rep declines to provide details, halt gracefully — do not generate a deck without prospect context.

### 1b. Load brand context

Read these files from the project root.

**Halt guard:** First, check if `brand/CLAUDE.md` exists at the project root. If not, halt with:
> No brand context found. This skill requires a `brand/` directory with a `CLAUDE.md` manifest at the project root. See the brand context contract in the Aligned plugin README.

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

## Step 2: Generate

Produce a structured deck as markdown following the April Dunford 8-step sales pitch framework. Read `brand/templates/deck/framework.md` for the narrative arc logic and content sourcing rules for each step.

### Generation process

For each of the 8 framework steps, the skill:
1. Reads the framework step's **Content sources** (from `framework.md`)
2. Loads the specified brand context files
3. Personalizes using the prospect file and stakeholder personas
4. Writes the slide content following the framework step's **Rules**

### Slide output format

Each slide is a markdown section:

```
## Slide N: {Title}

{Content — bullet points, prose, or data as appropriate}

> **Presenter notes:** {Speaking points for the rep — what to say, what to ask, what to emphasize}
```

### Generation status

Display a brief status update to the rep:

```
Generating 9-slide deck for {Prospect Name} using {vertical} positioning, emphasizing {competitive context}...
```

The rep does not interact during generation.

### Quality gates (checked before presenting draft)

- [ ] All 9 slides present (title + 8 framework steps)
- [ ] Uses correct terminology per terminology.md (if loaded)
- [ ] All statistics match proof-points.md exactly — no invented numbers (if proof-points.md loaded)
- [ ] Tone matches brand voice deck register (punchy, outcome-focused, short sentences)
- [ ] Pain points are specific to the prospect's vertical and buying trigger, not generic
- [ ] Differentiation is sharpened against the prospect's competitive context
- [ ] Value slide translates features into stakeholder-relevant outcomes
- [ ] At least 2 proof points from proof-points.md
- [ ] No generic enterprise jargon (per terminology.md dos/don'ts)
- [ ] Reference example used as style guide (if available)

## Step 3: Review

Three reviewers evaluate the draft deck **in parallel**. Each reviewer is a Claude sub-agent with a specific lens.

### Reviewer 1: Positioning Expert (April Dunford lens)

Evaluates framework adherence and positioning quality:

- Is the differentiation sharp and specific to this prospect's competitive context?
- Does the narrative follow the 8-step framework arc?
- Does the "Value" slide translate features into prospect-relevant outcomes, not generic benefits?
- Are we leading with the right insight for this vertical/stakeholder mix?
- Does competitive positioning hold up — are claims backed by proof points?
- Does the positioning chain trace correctly: alternatives → attributes → value → target → category?

### Reviewer 2: Behavioral Scientist (Shirin Oreizy lens)

Evaluates decision architecture and narrative psychology:

- Cognitive load per slide — is there one clear point per slide?
- Decision architecture — is the deck guiding the prospect's thinking rather than overwhelming?
- Loss aversion and urgency — is the Problem slide appropriately urgent without being manipulative?
- CTA design — single clear action with minimized friction?
- Narrative flow — does the emotional arc build from problem through proof to action?

### Reviewer 3: Buyer Personas (prospect-specific)

For each stakeholder in the prospect file, construct a composite persona:

```
Base persona (brand/personas/{role}.md)
  + Vertical overlay (brand/guidelines/audiences/{vertical}.md)
  + Prospect-specific overrides (prospects/{slug}.md → stakeholder section)
= Composite persona for "{Name}, {Role} at {Company}"
```

Each persona evaluates the deck through their lens:
- Does the deck address their evaluation criteria?
- Is the language aligned with what resonates for this role?
- Are there skepticism triggers in the deck content?
- Does the buying trigger connect to what actually initiated this prospect's evaluation?
- Tag reactions per-persona: what resonates, what feels generic, what triggers skepticism

### Finding consolidation

Collect all findings from all three reviewers. Severity-rank them:

- **HIGH:** Issue will undermine the deck's effectiveness (wrong positioning, misaligned value prop, missing stakeholder concern)
- **MEDIUM:** Issue weakens the deck but doesn't undermine it (generic language where specific would be better, suboptimal slide ordering)
- **LOW:** Cosmetic or minor issue (competing visualizations on one slide, slightly off tone in one section)

Present consolidated findings to the rep:

```
Review findings:

HIGH
- [{source}] {finding description — references specific slide}

MEDIUM
- [{source}] {finding description}

LOW
- [{source}] {finding description}

Accept all, or tell me which to skip?
```

Sources are tagged: `[positioning]`, `[behavioral]`, `[buyer:{role}]`

### Rep triage

The rep can:
- **Accept all:** All findings applied
- **Cherry-pick:** "Accept all except {finding}" — rep can explain why (e.g., "Maria told us she's flexible on timeline")
- **Add context:** Rep-provided context is captured as human feedback

**Conflict resolution:** When two reviewers make contradictory suggestions about the same slide, present both with reasoning. The rep decides.

**Edge case:** If all three reviewers produce no findings, note this and proceed directly to Step 4.

## Step 4: Deliver

### 4a. Apply findings

Apply all accepted findings to the markdown deck. Re-run the Step 2 quality gates on the revised deck to ensure fixes didn't introduce new issues.

### 4b. Generate output

#### 4b-i. Save markdown deck (always)

Save the finalized markdown deck to `output/{prospect-slug}-{date}.md`. This is always produced regardless of .pptx rendering.

#### 4b-ii. Produce slide design brief

Transform the finalized markdown deck into a structured design brief. This is the universal interface between the generate-deck skill (content) and any rendering layer (file format).

```markdown
# Slide Design Brief: {Prospect Name}

## Presentation metadata
- Slides: 9 (title + 8 framework steps)
- Aspect ratio: 16:9
- Output path: output/{prospect-slug}-{date}.pptx

## Brand design constraints
Read color palette, typography, and styling from `brand/guidelines/visual-identity.md`. Apply the brand's primary, accent, background, and text colors. Use the specified font family with appropriate web-safe fallbacks for PPTX rendering.

If `brand/guidelines/visual-identity.md` is not available, skip the slide design brief entirely — the markdown deck is the deliverable.

## Slides

### Slide 1: {Title}
**Layout:** {layout direction — e.g., centered title, two-column, sidebar}
**Content:**
{Exact finalized text from the reviewed deck}
**Speaker notes:**
{Presenter notes from the deck}

### Slide 2: {Title}
... (all 9 slides)
```

Each slide in the brief includes:
- The exact finalized text (already reviewed and accepted by the rep)
- A layout direction describing the visual structure
- Speaker notes for the presenter

#### 4b-iii. Render .pptx via context-aware delegation

Detect the execution context and delegate rendering to the appropriate layer.

**Context A — Inside PowerPoint (add-in)**

Detected when: native slide creation APIs are available (creating slides, setting layouts, applying templates). The Claude for PowerPoint add-in provides these capabilities automatically.

- Use the open presentation's slide master and layouts as the template
- Create slides directly in PowerPoint using native API calls
- Apply the design brief's content, layout directions, and speaker notes
- Brand fonts render correctly because they're installed on the rep's machine
- No file export needed — slides are created in the active presentation

**Context B — Claude Code (CLI)**

Detected when: file-system tools are available but no PowerPoint API access. The `pptx` skill is available.

- Delegate the slide design brief to the `pptx` skill's html2pptx workflow
- The `pptx` skill handles HTML creation (720pt x 405pt, 16:9), rendering, and .pptx assembly
- Web-safe fonts only — use the fallback font specified in `brand/guidelines/visual-identity.md`, or a serif web-safe default if no fallback is specified
- Save to `output/{prospect-slug}-{date}.pptx`
- Reference the `pptx` skill by name, not by file path

**Context C — Neither available (fallback)**

Detected when: no PowerPoint API and no `pptx` skill / rendering dependencies available.

- The markdown deck is the deliverable
- Notify the rep:

```
Deck saved as markdown: output/{prospect-slug}-{date}.md
For .pptx output, use Claude for PowerPoint (add-in) or Claude Code with the pptx skill installed.
```

- Complete all remaining workflow steps normally (critique log, prospect update)

**Context priority:** Add-in first (best output quality — native fonts, real templates), then CLI, then fallback. Do not attempt CLI rendering if the add-in is available.

### 4c. Write critique log

Write the review findings and rep decisions to `learnings/decks/{prospect-slug}-{date}.md`:

```markdown
---
prospect: {Company Name}
date: {YYYY-MM-DD}
rep: {rep name if known}
vertical: {vertical}
---

## Review Findings
- [{severity}] [{source}] {finding} → REP {ACCEPTED|REJECTED} {— "reason" if rejected}

## Rep Feedback
- Rep override: {any overrides with reasoning}
- Rep added context: {any new context provided}
- Rep frustration: {any friction points noted, or "(none)"}
```

### 4d. Update prospect file

Write any rep-provided context back to the prospect file's Rep Notes section. This ensures future deck generations benefit from accumulated rep knowledge.

### 4e. Present final output

Adapt the summary based on which rendering path was used:

**If add-in rendering (Context A):**
```
Slides created in the active presentation (9 slides).
Markdown backup: output/{prospect-slug}-{date}.md
Critique log: learnings/decks/{prospect-slug}-{date}.md

{count} review findings applied ({accepted} accepted, {rejected} rejected by rep).
```

**If CLI rendering (Context B):**
```
Deck generated: output/{prospect-slug}-{date}.pptx
Markdown backup: output/{prospect-slug}-{date}.md
Critique log: learnings/decks/{prospect-slug}-{date}.md

{count} review findings applied ({accepted} accepted, {rejected} rejected by rep).
```

**If fallback (Context C):**
```
Deck saved as markdown: output/{prospect-slug}-{date}.md
Critique log: learnings/decks/{prospect-slug}-{date}.md

{count} review findings applied ({accepted} accepted, {rejected} rejected by rep).

For .pptx output, use Claude for PowerPoint (add-in) or Claude Code with the pptx skill installed.
```
