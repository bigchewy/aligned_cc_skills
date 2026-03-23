# ewp-site Blog Integration

**Date:** 2026-03-23
**Status:** Draft
**Scope:** Update ewp-site to support enhanced blog output from generate-blog-post skill
**Parent design:** `docs/plans/2026-03-23-blog-html-rendering-design.md`
**Project:** `/Users/ericpage/software/ewp-site`

## Problem

The generate-blog-post skill is being upgraded to produce MDX with enhanced frontmatter (`heroImage`, `readingTime`) and two MDX components (`<Callout>`, `<CTA>`). The ewp-site needs coordinated changes to consume these new features. Without these changes, the skill still generates valid MDX — new frontmatter fields are silently ignored and components are stripped to markdown equivalents — but the full marketing blog experience doesn't render.

## Prerequisites

The skill generates valid MDX regardless of whether these changes are made. All changes below are additive — existing blog posts continue to work unchanged.

## Changes

### 1. Extend BlogPost interface (`src/lib/blog.ts`)

Add optional fields to the `BlogPost` interface:

```typescript
heroImage?: string;
readingTime?: string;
```

Update the `parseBlogPost` function's return statement to include both new fields from the parsed frontmatter data.

### 2. Update blog post page (`src/app/blog/[slug]/page.tsx`)

- Render hero image via `next/image` when `post.heroImage` is present
- Show reading time in the header metadata row alongside date and category
- Hero image should appear between the header metadata and the article body

### 3. Add MDX components (`src/lib/mdx-components.tsx`)

Register two new components in the `mdxComponents` map:

**Callout** — visually distinct from the existing blockquote override:
- Accent-colored left border
- Subtle background (e.g., `--color-accent-subtle`)
- Padding consistent with the site's spacing system

**CTA** — bottom section for calls to action:
- Background color (e.g., `--color-surface` or `--color-muted`)
- Centered text layout
- Prominent link styling

This follows the existing pattern: `blockquote`, `img`, `h2`, `h3` are already mapped in `mdxComponents`.

### 4. Create blog images directory

Create `public/images/blog/`. Follows the existing `public/images/{subdirectory}` convention (candids, hero, icons, projects, skills).

### 5. Blog listing cards

Hero images do NOT appear on listing cards in v1. The `BlogPostCard` component and its props stay unchanged. Listing card images are a separate enhancement if wanted later.

### 6. Test updates

**`src/content/blog/__tests__/conversion.test.ts`:**
- Validate `heroImage` is a valid `/images/` path when present
- Validate `readingTime` is a non-empty string when present
- Existing validations (title, date required) unchanged

**New test for hero image rendering:**
- When `heroImage` is present in frontmatter, `[slug]/page.tsx` renders a `next/image` element
- When `heroImage` is absent, no image element renders (existing behavior preserved)

**`src/components/blog/__tests__/BlogPostCard.test.tsx`:**
- No changes needed in v1 (no new props)

## Out of Scope

- **Listing card images:** Adding hero images to `BlogPostCard` on the blog listing page
- **Author field:** Single-author site; not needed
- **Section icons:** Deferred pending icon integration pattern
- **Social share:** Requires interactive implementation beyond this integration
- **Inline body images:** The existing `img` override in mdx-components.tsx uses hardcoded `width={680}` and `height={400}`. If inline images with custom dimensions are needed later, the `img` override needs updating. Not in v1 scope.
