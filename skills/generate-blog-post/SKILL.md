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

```markdown
# {Title}

*{Meta description — under 160 characters}*

{Hook — 2-3 sentences, ends with tension or question}

## {Problem section heading}
{2-3 paragraphs — names the shift, describes failing status quo}

## {Insight section heading}
{2-3 paragraphs — names root cause, offers new lens}

## {Evidence section heading}
{2-3 paragraphs — proof points woven into narrative}

## {Implication section heading}
{2-3 paragraphs — New Reality + 80/20 brand mention}

## {Conclusion heading}
{1 paragraph — restate insight, New Reality, single CTA}
```

Target length: 1,000–1,500 words.

### Generation status

Display a brief status update to the requestor:

```
Generating blog post on "{topic}" using {vertical or 'cross-vertical'} positioning...
```

The requestor does not interact during generation.

### Quality gates (all 14 must pass before presenting draft)

1. All 8 structural elements present: Title, Meta Description, Hook, Problem, Insight, Evidence, Implication, Conclusion/CTA
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

### 4a. Apply findings

Apply all accepted findings (by number from Step 3 triage) to the markdown draft. Re-run the Step 2 quality gates on the revised post. **Maximum 2 revision attempts.** If the quality gates still fail after 2 attempts, present the current draft to the requestor with the failing gates noted — do not loop indefinitely.

### 4b. Save output

Save the finalized blog post to `output/blog-{topic-slug}-{date}.md`.

### 4c. Write critique log

Save to `learnings/blog-posts/{topic-slug}-{date}.md`:

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

```
Blog post generated: output/blog-{topic-slug}-{date}.md
Critique log: learnings/blog-posts/{topic-slug}-{date}.md

{count} review findings applied ({accepted} accepted, {rejected} rejected).
```
