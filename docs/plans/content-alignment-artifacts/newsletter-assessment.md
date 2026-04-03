# Newsletter Infrastructure Assessment

**Date:** 2026-04-03

## Current State

### Newsletter Platform: Buttondown (already integrated)

ewp-site already has a working newsletter integration:

- **Component:** `src/components/blog/EmailCapture.tsx` — form that POSTs to Buttondown's embed-subscribe API
- **Placement:** Renders in the footer of every blog post page (`src/app/blog/[slug]/page.tsx`, line 66)
- **Copy:** "Get the next post by email" with a subscribe button
- **Environment variable:** `NEXT_PUBLIC_BUTTONDOWN_USERNAME` (defined in `.env.local.example`, needs to be set in production `.env.local`)

### Blog Infrastructure: MDX + Next.js (working)

- **Content location:** `src/content/blog/` — MDX files with gray-matter frontmatter
- **Existing posts:** 6 posts (CEO coaching / org systems voice)
- **Frontmatter:** `title`, `date`, `description`, `category`, `featured`
- **Rendering:** Next.js dynamic route at `/blog/[slug]` with MDX Remote
- **Blog index:** `/blog` listing page

### What Needs Attention

1. **Buttondown username not configured:** `.env.local` doesn't exist (or doesn't contain `NEXT_PUBLIC_BUTTONDOWN_USERNAME`). The EmailCapture component is built but will fail silently without this env var set in production.

2. **No standalone signup page:** Newsletter signup only exists in blog post footers. The design doc calls for signup links from README and kickstart output — these need a standalone URL. Options:
   - **Buttondown hosted page:** `https://buttondown.com/{username}` — zero effort, works immediately once the Buttondown account exists
   - **Dedicated `/subscribe` route on ewp-site:** More branded, more work
   - **Recommendation:** Use the Buttondown hosted page for cross-surface links (README, kickstart). It works immediately and doesn't require ewp-site changes.

## Signup URL

**Pending user input:** The Buttondown username is needed to construct the signup URL.

Once known, the standalone signup URL is: `https://buttondown.com/{username}`

The embed API URL (already used by EmailCapture.tsx) is: `https://buttondown.com/api/emails/embed-subscribe/{username}`

## Blog Post Publish Location

The flagship blog post should be published as an MDX file at:
```
/Users/ericpage/software/ewp-site/src/content/blog/positioning-exercise-at-2am.mdx
```

Frontmatter format:
```yaml
---
title: "How to Run a Positioning Exercise with April Dunford at 2 AM"
date: "2026-04-XX"
description: "Walk through an actual positioning exercise using AI-native methodology — real frameworks, quality gates, and expert critique."
category: "AI Enablement"
featured: true
---
```

## Recommendation

1. **Confirm Buttondown account exists** and get the username (Eric action item)
2. **Set `NEXT_PUBLIC_BUTTONDOWN_USERNAME`** in ewp-site production environment
3. **Use `https://buttondown.com/{username}`** as the cross-surface signup URL for README, kickstart, and external references
4. **No ewp-site code changes needed** — EmailCapture component and blog infrastructure are ready

## Decision Needed

Eric: What is the Buttondown username? Once provided, all newsletter links across surfaces can be finalized.
