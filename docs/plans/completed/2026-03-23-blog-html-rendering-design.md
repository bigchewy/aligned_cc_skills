# Blog Post HTML Rendering & MDX Output

**Date:** 2026-03-23
**Status:** Draft
**Scope:** Upgrade `generate-blog-post` skill from markdown-only to MDX + HTML preview output
**Brainstorm lead:** The Designer (visual craft lens)
**Mockups:** docs/mockups/blog-html-rendering.html
**ewp-site integration:** See `docs/plans/2026-03-23-ewp-site-blog-integration.md` (separate plan)

## Problem

The generate-blog-post skill outputs plain markdown to `output/blog-{slug}-{date}.md`. When rendered, posts have no visual hierarchy — title, meta description, hook, and body text all appear in the same font with no brand presence. The meta description and hook often repeat each other's phrasing, creating a jarring double-read at the top of every post. There are no images, no iconography, no branded elements. The output doesn't match the visual ambition of a marketing blog.

## Solution

Upgrade the skill to produce:
1. **MDX** as the primary deliverable — drops into `src/content/blog/` in Next.js projects
2. **HTML preview** as a secondary artifact — for the skill user to review and share before publishing

The MDX body stays as close to pure markdown as possible. Page layout (hero image, title, byline, metadata) is driven by frontmatter and owned by the consuming site's page template. Two MDX components (`<Callout>`, `<CTA>`) handle the only elements that need styling beyond standard markdown.

## Architecture

### Workflow Changes

The 4-step workflow (Input → Generate → Review → Deliver) is preserved. Changes:

- **Step 2 (Generate):** Produces richer content with enhanced frontmatter (`heroImage`, `readingTime`) and two MDX components. Two new quality gates enforce hook/Problem differentiation and meta description isolation.
- **Step 4 (Deliver):** Adds context-aware output:

| Context | Detection Signal | Output |
|---------|-----------------|--------|
| A: Next.js/MDX | `src/content/blog/*.mdx` exists | MDX to `src/content/blog/` + HTML preview to `output/` |
| Fallback | No MDX blog infrastructure detected | Markdown to `output/` (current behavior) |

Detection checks: `src/content/blog/*.mdx` exists AND `next.config.ts` or `next.config.js` exists. If either is absent, fall back to markdown. Do not probe further — a wrong detection is worse than a conservative fallback.

Steps 1 (Input) and 3 (Review) are unchanged.

### MDX Output Format

```mdx
---
title: "Mindset Without Systems Is Meditation in a Burning Building"
date: "2026-03-23"
description: "Why coaching without operational infrastructure keeps founders stuck..."
category: "mindset"
featured: true
heroImage: "/images/blog/mindset-without-systems/hero.webp"
readingTime: "6 min"
---

A CEO I work with was drowning. Twelve-hour days. Hundreds of unread emails...

## The Coaching Trap

{Problem section — no brand mentions}

> The issue isn't mindset. It's that there's no system to apply the mindset to.

## Why Coaching Alone Fails

{Insight section}

> "Pull quote woven into evidence."

## The Evidence

{Evidence section with proof points}

## What Changes When You Build the System First

{Implication section — 80/20 brand ratio}

<Callout>
Key takeaway or insight summary.
</Callout>

<CTA>

### Ready to build the system?

Book a strategy call to diagnose what's actually broken.

[Book a Call](/contact)

</CTA>
```

**Key principles:**
- No title, header, meta, or byline markup in MDX body — all driven by frontmatter, rendered by page template
- Body starts with hook paragraph — matches existing ewp-site blog post pattern
- Pull quotes use standard `>` blockquote syntax — already styled by mdxComponents
- Only 2 MDX components: `<Callout>` and `<CTA>` — registered in consuming project's mdx-components.tsx
- `description` stays in frontmatter only (SEO/social cards) — not rendered visually
- `author` field omitted (single-author site, YAGNI)

**Unregistered component handling:** If the skill detects that `<Callout>` or `<CTA>` are not registered in the consuming project's `mdx-components.tsx`, the skill strips them from the MDX output:
- `<Callout>` content becomes a standard `> blockquote`
- `<CTA>` content becomes a standard `## heading` + paragraph + link

This prevents `next-mdx-remote` v6 from throwing on unrecognized capitalized components. The setup notice informs the user that richer rendering is available with the components registered.

### Asset Manifest

Each generated blog post includes a manifest of required images:

```
Required images:
- /images/blog/{slug}/hero.webp — Hero image (recommended 1360x800)
```

The user places actual image files before publishing. The HTML preview shows placeholder boxes with alt text and dimensions for images that don't exist yet.

The asset manifest is included in the Step 4 delivery output alongside the file paths (see Delivery Output below).

### HTML Preview

**Purpose:** The skill user reviews the preview to verify visual hierarchy, content flow, and brand alignment before publishing. The preview can also be shared with stakeholders for approval. It is generated automatically alongside the MDX — no separate step required.

**Rendering approach:** Read the project's `globals.css`, extract the `@theme inline` block (CSS custom properties), and inject into a Tailwind CDN-powered standalone HTML file. This is a new rendering pattern specific to published content previews — it differs from the mockup-generator (which reads `docs/design/design-principles.md`) in both its token source and extraction mechanism.

**What the preview renders:**
- Full page layout the site template would produce (hero image area, title, category badge, reading time, date)
- Article body (hook, PIEI sections, blockquotes, callout, CTA)
- Placeholder boxes for images not yet placed (gray box with alt text and recommended dimensions)
- Footer note: *"Preview — approximate rendering. Final output uses your site's Tailwind build and MDX pipeline."*

**MDX component rendering in preview:**
- `<Callout>` renders as a `<div>` with accent-colored left border, subtle background, and padding
- `<CTA>` renders as a `<div>` with background color, centered text, and prominent link styling
- These are standalone CSS/HTML implementations in the preview template — they do not reference the consuming project's React components

**What the preview does NOT render:**
- Site navigation/header/footer
- Interactive elements (social share buttons are visual-only)

**Token extraction and failure handling:**

Simple string scan of `@theme inline { }` block from the project's `globals.css`. Minimum required tokens: `--color-background`, `--color-foreground`, `--color-accent`, `--font-sans`. If the `@theme inline` block is missing, malformed, or contains fewer than the 4 minimum tokens:

1. Log a warning: "Could not extract sufficient tokens from globals.css. Falling back to visual-identity.md."
2. Fall back to `brand/guidelines/visual-identity.md` tokens
3. If that also fails, fall back to a neutral palette (`#faf9f7`, `#1a1a1a`, `#ff6900`)

Partial extraction is not attempted — the skill uses the full token set from whichever tier succeeds first.

**Output path:** `output/blog-{slug}-preview.html`

**Testing:** The HTML preview artifact should be validated with:
- Structural check: required HTML elements present (title, article body, callout, CTA)
- CDN script tag present for Tailwind
- Token extraction produces valid CSS custom property declarations
- Placeholder boxes render for missing images

### Quality Gate Updates

Two new gates added to the existing 14:

**Gate 15 — Hook/Problem differentiation:**
The Hook and the Problem section's first paragraph must not share sentence openers, character introductions, or scene descriptions. If the Hook opens with a character ("A CEO I work with..."), the Problem section must open with a different angle — a statistic, a trend, a contrasting scene. The LLM should evaluate: could a reader mistake the Hook and Problem opening for the same paragraph? If yes, fail.

**Gate 16 — Meta description isolation:**
The `description` frontmatter field must be a standalone summary of the post's core insight — not an excerpt from the Hook or Problem section. It must not appear verbatim anywhere in the article body.

**Modification to gate 1:** Updated structural elements to include Callout (the `<Callout>` component surfaces the post's key takeaway as a scannable element).

### Delivery Output (Step 4)

When Context A is detected, the delivery summary includes:

```
Blog post generated:
  MDX: src/content/blog/{slug}.mdx
  Preview: output/blog-{slug}-preview.html
  Critique log: learnings/blog-posts/{slug}-{date}.md

Required images (place before publishing):
  - public/images/blog/{slug}/hero.webp (1360x800)

{count} review findings applied ({accepted} accepted, {rejected} rejected).
```

When fallback is used:

```
Blog post generated: output/blog-{slug}-{date}.md
Critique log: learnings/blog-posts/{slug}-{date}.md

{count} review findings applied ({accepted} accepted, {rejected} rejected).

For MDX output with HTML preview, set up a Next.js blog with src/content/blog/.
```

### Setup Detection

The skill checks for two things when Context A is detected:

1. **MDX components:** Whether `Callout` appears in `src/lib/mdx-components.tsx`. If not found, the skill strips `<Callout>` and `<CTA>` to markdown equivalents (see Unregistered component handling above) and emits:
   > "Callout and CTA components not found in mdx-components.tsx. Using markdown equivalents. For richer rendering, see the setup guide at `skills/generate-blog-post/references/ewp-site-setup.md`."

2. **Frontmatter support:** Whether `heroImage` appears in `src/lib/blog.ts`. If not found, the skill still includes `heroImage` and `readingTime` in frontmatter (they're harmlessly ignored) and emits:
   > "Your site's blog infrastructure doesn't yet support heroImage or readingTime fields. The MDX includes them in frontmatter, but they won't render until you update `blog.ts` and `[slug]/page.tsx`. See the setup guide."

## Decision Log

| # | Decision | Source | Rationale |
|---|----------|--------|-----------|
| 1 | MDX primary + HTML preview output | User | Published directly into ewp-site (Next.js/MDX) with preview for skill user review |
| 2 | Marketing blog visual ambition | User | Hero section, pull quotes, CTA, reading time |
| 3 | CSS from project's existing stylesheet | User | Consuming projects already have CSS (e.g., globals.css); don't duplicate in brand/ |
| 4 | MDX body stays pure markdown + 2 components | Architect | Matches ewp-site's existing pattern; all 6 current posts are pure markdown |
| 5 | Page layout owned by site template, not MDX | Architect | [slug]/page.tsx already renders title, category, date; skill shouldn't duplicate |
| 6 | 2-tier output detection (MDX + fallback) | Architect, PM, QA | 3-tier YAGNI — only one consuming project exists; Context B removed |
| 7 | HTML preview via Tailwind CDN + globals.css token extraction | Architect | New pattern for published content previews; differs from mockup-generator approach |
| 8 | Asset paths: /images/blog/{slug}/ | Architect | Enforced ewp-site convention (test validates all srcs start with /images/) |
| 9 | Remove meta description from rendered output | Designer | SEO artifact, not reading artifact; eliminates first repetition layer |
| 10 | Quality gate for hook/Problem differentiation | Designer | Addresses observed repetition in generated blog posts |
| 11 | MDX components (Callout, CTA) not CSS classes | Architect | mdx-components.tsx is the existing pattern for styled elements in ewp-site |
| 12 | Drop author from frontmatter | Architect | Single-author site; every post is Eric Page; YAGNI |
| 13 | Hero images NOT on listing cards in v1 | Architect | BlogPostCard stays unchanged; listing images are separate enhancement |
| 14 | ewp-site changes split to separate plan | PM | Different codebase and deploy cycle; skill doc specifies output contract only |
| 15 | Section icons deferred | PM critique | User requested but not addressed; revisit when icon integration pattern is established |
| 16 | Social share deferred | PM critique | User requested; requires interactive implementation beyond skill scope; revisit separately |
| 17 | Strip unregistered components to markdown | QA Engineer | next-mdx-remote v6 may throw on unrecognized capitalized components |
