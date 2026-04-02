---
name: generate-blog-post
description: Generate an on-brand thought leadership blog post using the PIEI narrative arc with a 3-reviewer panel
---

# Generate Blog Post

## Overview

You generate branded thought leadership blog posts. Each post follows the PIEI narrative arc (Problem → Insight → Evidence → Implication) and is reviewed by a 3-reviewer panel before delivery. Posts are educational, not promotional — the brand appears only in the final section.

**Announce at start:** "I'm using the generate-blog-post skill to create a branded thought leadership blog post."

**Workflow:** 4 gated steps — Input → Generate → Review → Deliver. Each step completes before the next begins.

## Step 1: Input

The requestor provides a topic: "Write a blog post about [topic]." Optionally, they specify a target vertical.

### 1a. Parse the request

Extract topic (required) and vertical (optional — read available verticals from `brand/CLAUDE.md` or `brand/guidelines/audiences/`).

**If no topic provided:** Ask for one.

**If topic is too broad** (e.g., "delivery", "logistics"): Ask to narrow it.

Then ask: **"Any particular angle or point you want to make sure this covers?"**

Store any optional context provided.

### 1b. Load brand context

Read these files from the project root.

**Halt guard:** First, check if `brand/CLAUDE.md` exists at the project root. If not, halt with:
> No brand context found. This skill requires a `brand/` directory with a `CLAUDE.md` manifest at the project root. See the brand context contract in the Aligned plugin README.

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

## Step 2: Generate

Produce a structured blog post as markdown following the 8-element framework from `brand/templates/blog-post/framework.md`.

### Generation process

For each framework element, the skill:
1. Reads the framework element's **Content Sources** (from `framework.md`)
2. Loads the specified brand context files
3. Personalizes using the vertical audience profile (if provided) and requestor's optional context
4. Writes content following the element's **Rules**

### Output format

When generating content, produce it in this MDX structure. The frontmatter drives page layout in the consuming site's template — no title, header, meta, or byline markup appears in the MDX body.

```mdx
---
title: "{Title — under 70 chars, no brand name}"
date: "{YYYY-MM-DD}"
description: "{Meta description — under 160 chars, standalone summary of core insight}"
category: "{topic category}"
featured: {true or false}
heroImage: "/images/blog/{slug}/hero.webp"
readingTime: "{N} min"
---

{Hook — 2-3 sentences, ends with tension or question}

## {Problem section heading}
{2-3 paragraphs — names the shift, describes failing status quo}

> {Pull quote — uses standard blockquote syntax}

## {Insight section heading}
{2-3 paragraphs — names root cause, offers new lens}

## {Evidence section heading}
{2-3 paragraphs — proof points woven into narrative}

## {Implication section heading}
{2-3 paragraphs — New Reality + 80/20 brand mention}

<Callout>
{Key takeaway or insight summary — 1-2 sentences}
</Callout>

<CTA>

### {CTA heading}

{1 paragraph — single call to action}

[{Link text}]({link path})

</CTA>
```

Target length: 1,000–1,500 words.

**Key principles:**
- Body starts with hook paragraph — no title or meta in body
- Pull quotes use standard `>` blockquote syntax
- Only 2 MDX components: `<Callout>` (key takeaway) and `<CTA>` (call to action)
- `description` stays in frontmatter only (SEO/social cards) — not rendered visually
- `author` field omitted (single-author site, YAGNI)
- `heroImage` uses `/images/blog/{slug}/` path convention
- `readingTime` is calculated from word count (roughly 250 words/minute)

### Generation status

Display a brief status update to the requestor:

```
Generating blog post on "{topic}" using {vertical or 'cross-vertical'} positioning...
```

The requestor does not interact during generation.

### Quality gates (all 16 must pass before presenting draft)

1. All 9 structural elements present: Title (frontmatter), Meta Description (frontmatter `description`), Hook, Problem, Insight, Evidence, Implication, Callout (`<Callout>` component), CTA (`<CTA>` component)
2. Title under 70 characters, no brand name in title
3. Uses correct terminology per terminology.md (if loaded)
4. All statistics match proof-points.md exactly — no invented numbers (if proof-points.md loaded)
5. Tone matches blog register (educational, thought-leadership, longer form)
6. Problem section leads with a named change in the reader's industry, not a product claim
7. Insight section names a root cause or systemic flaw — not a product capability or restated positioning (test: remove all brand references and the Insight should still be a valid industry observation)
8. Brand not mentioned in Problem, Insight, or Evidence sections
9. Implication section maintains 80/20 ratio (sentence count: ≤1 in 5 sentences references the brand by name or describes a product capability)
10. Implication section paints a concrete New Reality — what the reader's world looks like when they operate from the Insight
11. At least 2 proof points from proof-points.md, woven into narrative (not bullet-listed)
12. No generic enterprise jargon (per terminology.md)
13. Reference example used as style guide (if available)
14. Meta description under 160 characters, contains core insight
15. Hook/Problem differentiation: The Hook and the Problem section's first paragraph must not share sentence openers, character introductions, or scene descriptions. If the Hook opens with a character ("A CEO I work with..."), the Problem section must open with a different angle — a statistic, a trend, a contrasting scene. Test: could a reader mistake the Hook and Problem opening for the same paragraph? If yes, fail. (Note: the mockup suggests a ">50% significant word overlap" threshold; the design doc uses this qualitative judgment test instead — follow the design doc.)
16. Meta description isolation: The `description` frontmatter field must be a standalone summary of the post's core insight — not an excerpt from the Hook or Problem section. It must not appear verbatim anywhere in the article body.

## Step 3: Review

Three reviewers evaluate the draft **in parallel**. Each reviewer is a Claude sub-agent with a specific lens.

### Reviewer 1: Positioning Expert

Evaluates framework adherence and positioning quality:

- Does the Problem section name a real shift in the reader's industry, grounded in competitive alternatives from `competitive.md`?
- Does the Insight section name a root cause or systemic flaw, not a product capability? (Apply the removal test: strip all brand references — does the Insight still stand as a valid industry observation?)
- Does the arc follow Problem → Insight → Evidence → Implication in logical sequence?
- Are proof points used accurately and woven into narrative (not listed)?
- Does the positioning chain trace correctly through the arc?
- Is the post thought leadership or thinly veiled product marketing?

**Insight collapse patterns to flag:**
1. Insight restates the Problem in different words (no new information)
2. Insight leads with a product capability ("Companies need AI-powered...")
3. Insight is a truism everyone already knows ("Customer experience matters")
4. Insight jumps directly to the solution without naming the underlying flaw

### Reviewer 2: Editorial / Brand Voice

Evaluates tone, register, and brand compliance:

- Does the tone match the blog register (educational, thought-leadership)?
- Is terminology correct throughout ("right-time" not "on-time", no banned jargon)?
- Is the writing accessible without being dumbed down?
- Does the Hook create genuine tension or curiosity anchored in a named change?
- Is the brand absent from sections before Implication?
- Does the 80/20 ratio hold in the Implication section? (Count sentences: ≤1 in 5 should reference the brand by name or describe a product capability.)
- Does the Implication section paint a concrete New Reality?
- Arc effectiveness: is the Insight a genuine editorial perspective or restated positioning?

### Reviewer 3: Audience Personas

**If a vertical was specified:**
- Do pain points match what this vertical actually experiences?
- Is the language calibrated to this audience's terminology preferences?
- Does the buying trigger connect to the Problem section's named change?
- Does the New Reality in the Implication section feel achievable for this vertical?
- What resonates, what feels generic, what triggers skepticism?

**If no vertical was specified:** Evaluate for a general logistics decision-maker audience — check that the content isn't so generic it fails to connect with anyone.

### Finding severity definitions

- **HIGH:** Issue will undermine the post's effectiveness (collapsed Insight, wrong tone, invented statistics, no named change in Problem)
- **MEDIUM:** Issue weakens the post but doesn't undermine it (generic language, suboptimal section transitions, weak New Reality)
- **LOW:** Cosmetic or minor (slightly off tone in one paragraph, meta description could be sharper)

### Finding presentation format

```
Review findings:

HIGH
1. [{source}] {finding description — references specific section}

MEDIUM
2. [{source}] {finding description}
3. [{source}] {finding description}

LOW
4. [{source}] {finding description}

Accept all, or tell me which to skip (by number)?
```

Sources tagged: `[positioning]`, `[editorial]`, `[audience:{vertical}]`

### Requestor triage

The requestor can:
- **Accept all:** All findings applied
- **Cherry-pick:** "Accept all except #3" — requestor can explain why (reasoning is captured)
- **Add context:** Requestor-provided context is captured as human feedback

The accepted finding numbers are passed as the explicit input to the revision step. Only findings in the accepted set are applied; rejected findings are logged but not acted on.

**Conflict resolution:** When two reviewers make contradictory suggestions about the same section, present both with reasoning. The requestor decides.

**Edge case:** If all three reviewers produce no findings, note this and proceed directly to Step 4.

### Sub-agent failure handling

- **Single reviewer failure** (timeout, malformed output, context exhaustion): Log the failure, proceed with the remaining 2 reviewers. Note in the findings presentation: "Reviewer X did not complete — {reason}. Findings are from {remaining reviewers} only."
- **Two or more reviewer failures:** Halt and surface the error to the requestor. Do not proceed with a single reviewer.
- **All reviewers produce empty/malformed output:** Treat as total failure — halt and surface.

## Step 4: Deliver

### Context detection

Before delivering, detect the project's blog infrastructure to determine output format.

**Detection logic (ordered, stop at first match):**

| Context | Detection Signal | Output |
|---------|-----------------|--------|
| A: Next.js/MDX | `src/content/blog/*.mdx` exists AND (`next.config.ts` or `next.config.js` exists) | MDX to `src/content/blog/` + HTML preview to `output/` |
| Fallback | Neither condition met | Markdown to `output/` (current behavior) |

Use Glob to check for `src/content/blog/*.mdx` and `next.config.*`. If either is absent, use the fallback. Do not probe further — a wrong detection is worse than a conservative fallback.

Store the detected context (A or Fallback) for use in steps 4b and 4d.

### Unregistered component handling

When Context A is detected, check whether `Callout` appears in `src/lib/mdx-components.tsx` using Grep. If not found, strip `<Callout>` and `<CTA>` from the MDX output to prevent `next-mdx-remote` from throwing on unrecognized capitalized components:

- `<Callout>` content becomes a standard `> blockquote`
- `<CTA>` content becomes a standard `## heading` + paragraph + link

Emit a setup notice:
> "Callout and CTA components not found in mdx-components.tsx. Using markdown equivalents. For richer rendering, add Callout and CTA components to your mdx-components.tsx."

Also check whether `heroImage` appears in `src/lib/blog.ts`. If not found, still include `heroImage` and `readingTime` in frontmatter (they're harmlessly ignored by the MDX parser) and emit:
> "Your site's blog infrastructure doesn't yet support heroImage or readingTime fields. The MDX includes them in frontmatter, but they won't render until you update `blog.ts` and `[slug]/page.tsx`. See the setup guide."

### 4a. Apply findings

Apply all accepted findings (by number from Step 3 triage) to the markdown draft. Re-run the Step 2 quality gates on the revised post. **Maximum 2 revision attempts.** If the quality gates still fail after 2 attempts, present the current draft to the requestor with the failing gates noted — do not loop indefinitely.

### 4b. Save output

**Context A (Next.js/MDX detected):**

1. Save the MDX file to `src/content/blog/{slug}.mdx`
2. Generate the HTML preview (see "HTML preview generation" below) and save to `output/blog-{slug}-preview.html`

**Fallback (no MDX infrastructure):**

Save the finalized blog post as markdown to `output/blog-{slug}-{date}.md` (current behavior — no MDX frontmatter, no components, plain markdown format).

### HTML preview generation

**Purpose:** The skill user reviews the preview to verify visual hierarchy, content flow, and brand alignment before publishing. The preview can also be shared with stakeholders for approval. It is generated automatically alongside the MDX when Context A is detected.

**Token extraction from `globals.css`:**

Use Glob to locate `globals.css` (try `src/app/globals.css`, then `app/globals.css`). Once found, perform a simple string scan of the `@theme inline { }` block. Extract CSS custom properties for use in the preview's inline styles.

Minimum required tokens: `--color-background`, `--color-foreground`, `--color-accent`, `--font-sans`.

**Fallback chain (use first tier that succeeds — no partial extraction):**
1. `globals.css` `@theme inline` block — primary source
2. `brand/guidelines/visual-identity.md` tokens — fallback if globals.css missing or malformed
3. Neutral palette (`#faf9f7` background, `#1a1a1a` foreground, `#ff6900` accent) — final fallback

If the `@theme inline` block is missing, malformed, or contains fewer than the 4 minimum tokens, log a warning: "Could not extract sufficient tokens from globals.css. Falling back to visual-identity.md." Then try the next tier.

**HTML preview structure:**

Generate a standalone HTML file with:
- Tailwind CDN script tag (`<script src="https://cdn.tailwindcss.com"></script>`)
- Extracted CSS custom properties as inline `<style>` block
- Full page layout: hero image area (placeholder box if image not placed), title, category badge, reading time, date
- Article body: hook, PIEI sections, blockquotes
- `<Callout>` rendered as a `<div>` with accent-colored left border, subtle background, and padding
- `<CTA>` rendered as a `<div>` with background color, centered text, and prominent link styling
- Placeholder boxes for images not yet placed (gray box with alt text and recommended dimensions)
- Footer note: *"Preview — approximate rendering. Final output uses your site's Tailwind build and MDX pipeline."*

**What the preview does NOT render:** site navigation, header, footer, or functional interactive elements.

**Output path:** `output/blog-{slug}-preview.html`

**Preview validation:** After generating the HTML preview, verify:
- Required HTML elements present (title, article body, callout div, CTA div)
- Tailwind CDN script tag present
- Token extraction produced valid CSS custom property declarations in the `<style>` block

### Asset manifest

When Context A is detected, include a manifest of required images in the delivery output. The user places actual image files before publishing. The HTML preview shows placeholder boxes for images that don't exist yet.

```
Required images:
- public/images/blog/{slug}/hero.webp — Hero image (recommended 1360×800)
```

Note: The `heroImage` frontmatter field uses `/images/blog/{slug}/hero.webp` (web path), while the asset manifest uses `public/images/blog/{slug}/hero.webp` (filesystem path). Both refer to the same file.

### 4c. Write critique log

Save to `learnings/blog-posts/{slug}-{date}.md`:

```markdown
---
topic: "{blog post title}"
date: YYYY-MM-DD
vertical: "{vertical or 'cross-vertical'}"
author: "{requestor name if known}"
---

## Review Findings
- [{severity}] [{source}] {finding} → {ACCEPTED|REJECTED} {— "reason" if rejected}

## Requestor Feedback
- Requestor override: {any overrides with reasoning}
- Requestor added context: {any new context provided}
- Requestor friction: {any friction points noted, or "(none)"}

## Arc Effectiveness
- Problem clarity: {did the Problem name a real shift the reader recognizes?}
- Insight originality: {did the Insight name a root cause, or did it collapse into positioning?}
- Evidence integration: {were proof points woven into narrative or listed?}
- Implication balance: {was 80/20 sentence ratio maintained? Did the New Reality land?}
```

### 4d. Present final output

**Context A (Next.js/MDX detected):**

```
Blog post generated:
  MDX: src/content/blog/{slug}.mdx
  Preview: output/blog-{slug}-preview.html
  Critique log: learnings/blog-posts/{slug}-{date}.md

Required images (place before publishing):
  - public/images/blog/{slug}/hero.webp (1360×800)

{count} review findings applied ({accepted} accepted, {rejected} rejected).
```

**Fallback:**

```
Blog post generated: output/blog-{slug}-{date}.md
Critique log: learnings/blog-posts/{slug}-{date}.md

{count} review findings applied ({accepted} accepted, {rejected} rejected).

For MDX output with HTML preview, set up a Next.js blog with src/content/blog/.
```
