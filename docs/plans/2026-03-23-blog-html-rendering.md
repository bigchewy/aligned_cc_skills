# Blog HTML Rendering & MDX Output Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the `generate-blog-post` skill from markdown-only output to MDX + HTML preview with context-aware delivery, two new quality gates, and setup detection.

**Source Design Doc:** `docs/plans/2026-03-23-blog-html-rendering-design.md`

**Mockups:** `docs/mockups/blog-html-rendering.html` (note: the mockup's "Workflow" tab shows a superseded 3-tier detection design; this plan's 2-tier detection is authoritative per design doc Decision 6)

**Architecture:** The skill's 4-step workflow (Input → Generate → Review → Deliver) is preserved. Step 2 gains MDX output format with enhanced frontmatter and two MDX components (`<Callout>`, `<CTA>`). Step 4 gains 2-tier context detection (Next.js/MDX vs fallback), HTML preview generation via Tailwind CDN with token extraction from `globals.css`, setup detection, and asset manifests. Steps 1 and 3 are unchanged.

**Tech Stack:** MDX, Tailwind CDN (HTML preview), CSS custom properties extraction, Glob/Grep for project detection

**Task ordering:** Tasks 1–8 all modify `skills/generate-blog-post/SKILL.md` and MUST be executed sequentially in order. Do not parallelize. Each task's insertion anchors depend on prior tasks having completed.

---

### ✅ Task 1: Update Step 2 output format from markdown to MDX

**Files:**
- Modify: `skills/generate-blog-post/SKILL.md` (the `### Output format` section under Step 2)

**Step 1: Verify current output format is markdown-only**

Read `skills/generate-blog-post/SKILL.md` and confirm the output format section (under `### Output format`) shows plain markdown with `# {Title}` and `*{Meta description}*` — no frontmatter, no MDX components.

**Step 2: Replace the output format section**

Replace the `### Output format` section (the prose line and the entire code block from ` ```markdown` through ` ``` `) with:

```markdown
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
```

**Step 3: Verify the change**

Read back `skills/generate-blog-post/SKILL.md` and confirm the output format section now shows MDX frontmatter with `title`, `date`, `description`, `category`, `featured`, `heroImage`, `readingTime`, plus `<Callout>` and `<CTA>` components.

**Step 4: Commit**

```bash
git add skills/generate-blog-post/SKILL.md
git commit -m "feat(generate-blog-post): update Step 2 output format from markdown to MDX"
```

---

### ✅ Task 2: Update quality gates — modify gate 1, add gates 15 and 16

**Files:**
- Modify: `skills/generate-blog-post/SKILL.md` (the `### Quality gates` section under Step 2)

**Step 1: Verify current gate count is 14**

Read `skills/generate-blog-post/SKILL.md` and confirm the quality gates header says "all 14 must pass" and gate 1 lists structural elements without Callout.

**Step 2: Update the quality gates header and gate 1**

Change the header from:

```
### Quality gates (all 14 must pass before presenting draft)
```

to:

```
### Quality gates (all 16 must pass before presenting draft)
```

Update gate 1 from:

```
1. All 8 structural elements present: Title, Meta Description, Hook, Problem, Insight, Evidence, Implication, Conclusion/CTA
```

to:

```
1. All 9 structural elements present: Title (frontmatter), Meta Description (frontmatter `description`), Hook, Problem, Insight, Evidence, Implication, Callout (`<Callout>` component), CTA (`<CTA>` component)
```

**Step 3: Add gates 15 and 16 after gate 14**

Append after line `14. Meta description under 160 characters, contains core insight`:

```
15. Hook/Problem differentiation: The Hook and the Problem section's first paragraph must not share sentence openers, character introductions, or scene descriptions. If the Hook opens with a character ("A CEO I work with..."), the Problem section must open with a different angle — a statistic, a trend, a contrasting scene. Test: could a reader mistake the Hook and Problem opening for the same paragraph? If yes, fail. (Note: the mockup suggests a ">50% significant word overlap" threshold; the design doc uses this qualitative judgment test instead — follow the design doc.)
16. Meta description isolation: The `description` frontmatter field must be a standalone summary of the post's core insight — not an excerpt from the Hook or Problem section. It must not appear verbatim anywhere in the article body.
```

**Step 4: Verify the change**

Read back the quality gates section and confirm: header says "16", gate 1 lists 9 elements including Callout and CTA, and gates 15 and 16 are present.

**Step 5: Commit**

```bash
git add skills/generate-blog-post/SKILL.md
git commit -m "feat(generate-blog-post): update gate 1 for Callout, add gates 15-16"
```

---

### ✅ Task 3: Add context detection logic to Step 4

**Files:**
- Modify: `skills/generate-blog-post/SKILL.md` (add new section at the start of Step 4, before `### 4a`)

**Step 1: Verify Step 4 currently has no context detection**

Read `skills/generate-blog-post/SKILL.md` and confirm Step 4 begins directly with `### 4a. Apply findings` with no detection logic.

**Step 2: Add context detection section before 4a**

Insert between `## Step 4: Deliver` and `### 4a. Apply findings`:

```markdown
### Context detection

Before delivering, detect the project's blog infrastructure to determine output format.

**Detection logic (ordered, stop at first match):**

| Context | Detection Signal | Output |
|---------|-----------------|--------|
| A: Next.js/MDX | `src/content/blog/*.mdx` exists AND (`next.config.ts` or `next.config.js` exists) | MDX to `src/content/blog/` + HTML preview to `output/` |
| Fallback | Neither condition met | Markdown to `output/` (current behavior) |

Use Glob to check for `src/content/blog/*.mdx` and `next.config.*`. If either is absent, use the fallback. Do not probe further — a wrong detection is worse than a conservative fallback.

Store the detected context (A or Fallback) for use in steps 4b and 4d.
```

**Step 3: Verify the change**

Read back Step 4 and confirm context detection section appears before 4a with the 2-tier detection table.

**Step 4: Commit**

```bash
git add skills/generate-blog-post/SKILL.md
git commit -m "feat(generate-blog-post): add 2-tier context detection to Step 4"
```

---

### ✅ Task 4: Add unregistered component handling section

**Files:**
- Modify: `skills/generate-blog-post/SKILL.md` (add section after context detection, before `### 4a`)

**Step 1: Add unregistered component handling**

Insert after the context detection section (before `### 4a. Apply findings`):

```markdown
### Unregistered component handling

When Context A is detected, check whether `Callout` appears in `src/lib/mdx-components.tsx` using Grep. If not found, strip `<Callout>` and `<CTA>` from the MDX output to prevent `next-mdx-remote` from throwing on unrecognized capitalized components:

- `<Callout>` content becomes a standard `> blockquote`
- `<CTA>` content becomes a standard `## heading` + paragraph + link

Emit a setup notice:
> "Callout and CTA components not found in mdx-components.tsx. Using markdown equivalents. For richer rendering, see the setup guide at `skills/generate-blog-post/references/ewp-site-setup.md`."

Also check whether `heroImage` appears in `src/lib/blog.ts`. If not found, still include `heroImage` and `readingTime` in frontmatter (they're harmlessly ignored by the MDX parser) and emit:
> "Your site's blog infrastructure doesn't yet support heroImage or readingTime fields. The MDX includes them in frontmatter, but they won't render until you update `blog.ts` and `[slug]/page.tsx`. See the setup guide."
```

**Step 2: Verify the change**

Read back and confirm the unregistered component handling section appears between context detection and 4a.

**Step 3: Commit**

```bash
git add skills/generate-blog-post/SKILL.md
git commit -m "feat(generate-blog-post): add unregistered component handling"
```

---

### ✅ Task 5: Rewrite Step 4b for context-aware output

**Files:**
- Modify: `skills/generate-blog-post/SKILL.md` (the `### 4b. Save output` section)

**Step 1: Verify current 4b is markdown-only**

Read `skills/generate-blog-post/SKILL.md` and confirm 4b currently says `Save the finalized blog post to output/blog-{topic-slug}-{date}.md`.

**Step 2: Replace 4b with context-aware output and standardize path variable**

> **Behavioral change:** The path variable changes from `{topic-slug}` to `{slug}` throughout Step 4. This is intentional — the MDX filename convention uses `{slug}` (matching the `[slug]` route parameter in Next.js). Apply the same rename to section 4c's critique log path (`learnings/blog-posts/{slug}-{date}.md`) for consistency.

Replace the `### 4b. Save output` section with:

```markdown
### 4b. Save output

**Context A (Next.js/MDX detected):**

1. Save the MDX file to `src/content/blog/{slug}.mdx`
2. Generate the HTML preview (see "HTML preview generation" below) and save to `output/blog-{slug}-preview.html`

**Fallback (no MDX infrastructure):**

Save the finalized blog post as markdown to `output/blog-{slug}-{date}.md` (current behavior — no MDX frontmatter, no components, plain markdown format).
```

**Step 3: Verify the change**

Read back 4b and confirm it has both Context A and Fallback paths.

**Step 4: Commit**

```bash
git add skills/generate-blog-post/SKILL.md
git commit -m "feat(generate-blog-post): rewrite Step 4b for context-aware output"
```

---

### ✅ Task 6: Add HTML preview generation section

**Files:**
- Modify: `skills/generate-blog-post/SKILL.md` (add new section after 4b, before 4c)

**Step 1: Add HTML preview generation section**

Insert after `### 4b. Save output` and before `### 4c. Write critique log`:

```markdown
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
```

**Step 2: Verify the change**

Read back and confirm the HTML preview generation section appears between 4b and 4c with token extraction, fallback chain, preview structure details, and validation checks.

**Step 3: Commit**

```bash
git add skills/generate-blog-post/SKILL.md
git commit -m "feat(generate-blog-post): add HTML preview generation section"
```

---

### ✅ Task 7: Add asset manifest to delivery

**Prerequisite:** Task 6 must be complete — this task's insertion anchor ("after the HTML preview generation section") only exists after Task 6 runs.

**Files:**
- Modify: `skills/generate-blog-post/SKILL.md` (add section after HTML preview generation, before 4c)

**Step 1: Add asset manifest section**

Insert after the HTML preview generation section and before `### 4c. Write critique log`:

```markdown
### Asset manifest

When Context A is detected, include a manifest of required images in the delivery output. The user places actual image files before publishing. The HTML preview shows placeholder boxes for images that don't exist yet.

```
Required images:
- public/images/blog/{slug}/hero.webp — Hero image (recommended 1360×800)
```

Note: The `heroImage` frontmatter field uses `/images/blog/{slug}/hero.webp` (web path), while the asset manifest uses `public/images/blog/{slug}/hero.webp` (filesystem path). Both refer to the same file.
```

**Step 2: Verify the change**

Read back and confirm the asset manifest section appears in the correct position.

**Step 3: Commit**

```bash
git add skills/generate-blog-post/SKILL.md
git commit -m "feat(generate-blog-post): add asset manifest to delivery"
```

---

### Task 8: Rewrite Step 4d for context-aware delivery output

**Files:**
- Modify: `skills/generate-blog-post/SKILL.md` (the `### 4d. Present final output` section)

**Step 1: Verify current 4d is markdown-only**

Read `skills/generate-blog-post/SKILL.md` and confirm 4d shows a single output block with `output/blog-{topic-slug}-{date}.md`.

**Step 2: Replace 4d with context-aware delivery**

Replace the `### 4d. Present final output` section with:

```markdown
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
```

**Step 3: Verify the change**

Read back 4d and confirm both Context A and Fallback delivery summaries are present.

**Step 4: Commit**

```bash
git add skills/generate-blog-post/SKILL.md
git commit -m "feat(generate-blog-post): rewrite Step 4d for context-aware delivery"
```

---

### Task 9: Create ewp-site setup reference guide

**Files:**
- Create: `skills/generate-blog-post/references/ewp-site-setup.md`

**Step 1: Verify the file does not exist**

Use Glob to confirm `skills/generate-blog-post/references/ewp-site-setup.md` does not exist.

**Step 2: Create the references directory and setup guide**

```bash
mkdir -p skills/generate-blog-post/references
```

Write `skills/generate-blog-post/references/ewp-site-setup.md`:

```markdown
# ewp-site Setup Guide for Blog MDX Output

This guide describes the changes needed in the consuming Next.js project to fully render enhanced blog posts generated by the `generate-blog-post` skill.

**Without these changes**, the skill still generates valid MDX — enhanced frontmatter fields are silently ignored and `<Callout>`/`<CTA>` components are stripped to markdown equivalents. All existing blog posts continue to work unchanged.

## 1. Extend BlogPost interface

In `src/lib/blog.ts`, add optional fields to the `BlogPost` interface:

```typescript
heroImage?: string;
readingTime?: string;
```

Update the `parseBlogPost` function's return statement to include both new fields from the parsed frontmatter data.

## 2. Update blog post page

In `src/app/blog/[slug]/page.tsx`:

- Render hero image via `next/image` when `post.heroImage` is present
- Show reading time in the header metadata row alongside date and category
- Hero image should appear between the header metadata and the article body

## 3. Register MDX components

In `src/lib/mdx-components.tsx`, register two new components in the `mdxComponents` map:

**Callout** — visually distinct from the existing blockquote override:
- Accent-colored left border (e.g., `--color-accent`)
- Subtle background (e.g., `--color-accent-subtle`)
- Padding consistent with the site's spacing system

**CTA** — bottom section for calls to action:
- Background color (e.g., `--color-surface` or `--color-muted`)
- Centered text layout
- Prominent link styling

This follows the existing pattern: `blockquote`, `img`, `h2`, `h3` are already mapped in `mdxComponents`.

## 4. Create blog images directory

Create `public/images/blog/`. This follows the existing `public/images/{subdirectory}` convention (candids, hero, icons, projects, skills).

## 5. Listing cards (no changes in v1)

Hero images do NOT appear on listing cards in v1. The `BlogPostCard` component stays unchanged.

## Reference

See `docs/plans/2026-03-23-ewp-site-blog-integration.md` for the full integration specification.
```

**Step 3: Verify the file was created**

Read back `skills/generate-blog-post/references/ewp-site-setup.md` and confirm it contains all 5 sections.

**Step 4: Commit**

```bash
git add skills/generate-blog-post/references/ewp-site-setup.md
git commit -m "docs: add ewp-site setup guide for blog MDX output"
```

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Task granularity for SKILL.md edits | One task per logical section change | Single mega-task for all SKILL.md edits, one task per line |
| 2 | No TDD test steps for skill doc edits | Read-back verification instead | Write automated tests for skill content |
| 3 | Separate task for ewp-site-setup.md | Own task with own commit | Bundle with component handling task |
| 4 | HTML preview as inline section vs separate file | Inline section in SKILL.md | Separate reference doc for preview spec |
| 5 | Asset manifest as own task | Separate small task | Bundle with 4b or 4d rewrite |

### Appendix: Decision Details

#### Decision 1: Task granularity for SKILL.md edits
**Chose:** One task per logical section change (9 tasks total)
**Why:** Each task modifies a distinct section of SKILL.md with a clear purpose. This maps to one commit per logical change, making git history reviewable and allowing partial rollback. The alternative of a single mega-task would produce one opaque commit. Going more granular (one task per line change) would create excessive commit noise for what are often related edits within a section.
**Alternatives rejected:**
- Single mega-task: Opaque commit history, harder to review or partially revert
- Per-line tasks: Excessive overhead for related edits within a cohesive section

#### Decision 2: No TDD test steps for skill doc edits
**Chose:** Read-back verification confirms edits landed; critique panel gates behavioral correctness of the specification before execution
**Why:** This repo (`aligned_cc_skills`) is a Claude Code skills plugin — it contains markdown skill documents, not application code. There is no test framework, no test runner, and no existing tests. All 9 tasks specify behavioral changes to the skill (output format, quality gates, detection logic, delivery paths). Read-back verification after each edit confirms the change landed as written. The plan critique panel (2-round process with independent sub-agents) gates whether the behavioral specification is correct before any execution begins. The HTML preview artifact has its own validation checks specified inline in Task 6 (structural elements, CDN tag, token extraction). Writing automated tests for markdown content would be over-engineering.
**Alternatives rejected:**
- Automated tests for skill content: No test infrastructure exists; would require setting up a test framework for markdown linting, which is out of scope

#### Decision 3: Separate task for ewp-site-setup.md
**Chose:** Own task (Task 9) with its own commit
**Why:** The setup guide is a new file in a new directory (`references/`). It has a different audience (ewp-site developers) than the skill instructions (the LLM executing the skill). Keeping it separate makes the commit message clear and the change reviewable.
**Alternatives rejected:**
- Bundle with component handling task: Mixes concerns (skill behavior vs. reference documentation)

#### Decision 4: HTML preview as inline section vs separate file
**Chose:** Inline section in SKILL.md (Task 6)
**Why:** The HTML preview generation is part of the skill's Step 4 delivery workflow — the LLM needs these instructions in-context when executing the skill. Putting the spec in a separate reference file would require the skill to cross-reference it, adding indirection. The section is ~30 lines, well within reasonable SKILL.md size.
**Alternatives rejected:**
- Separate reference doc: Adds indirection; the LLM executing the skill needs the preview spec inline to follow the delivery workflow without extra file reads

#### Decision 5: Asset manifest as own task
**Chose:** Separate small task (Task 7)
**Why:** The asset manifest is a self-contained concept (list of required images) that could be reverted independently. It's small enough to be a quick task but distinct enough from the 4b rewrite (file paths) and 4d rewrite (delivery output format) to warrant separation.
**Alternatives rejected:**
- Bundle with 4b: Conflates "where to save files" with "what images are needed"
- Bundle with 4d: The manifest content appears in 4d's output, but the manifest section defines the concept; bundling would make one task do two things
