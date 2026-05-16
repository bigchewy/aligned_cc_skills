# Synthesize: slice-synthesizer sub-agent prompt

This file is the prompt template the orchestrator pastes into a `subagent_type: general-purpose` Task dispatch during PHASE 2. One dispatch per slice instance, in a single parallel batch.

The orchestrator substitutes the placeholders below before dispatching. The sub-agent runs with its own context window, reads the owning framework spec + relevant source extracts from disk, and writes a slice draft + open questions JSON to disk — the orchestrator never reads slice bodies or source extracts directly.

This is NOT a registered top-level agent. It's a supporting prompt internal to `reverse-engineered-brand`. Dispatching it is the orchestrator's responsibility; reading its file is for humans auditing the framework.

---

## Prompt template (substitute placeholders, then dispatch)

You are synthesizing one slice of a canonical brand folder from a filtered set of source extracts, conforming to the slice's owning framework's output shape.

**Inputs** (substituted by the orchestrator):

- `{slice-id}` — slice identifier (e.g., `strategy/positioning.md`, `personas/vp-ops.md`)
- `{owning-framework-id}` — framework id from the orchestrator's slice→framework mapping (e.g., `5-components-positioning`), or JSON `null` for GAP slices. (When `null`, the surrounding JSON must contain literal `null`, not the string `"null"`.)
- `{owning-framework-path}` — absolute path to the framework's `prompt.md` (e.g., `/path/to/frameworks/5-components-positioning/prompt.md`), or empty string for GAP slices
- `{brand-folder-spec-path}` — absolute path to `docs/brand-folder-spec.md` so the sub-agent can look up the slice's frontmatter contract
- `{extract-json-paths}` — JSON array of absolute paths to source-extract JSON files relevant to this slice (already filtered by the orchestrator using `signal_tags`)
- `{output-draft-path}` — absolute path where the slice's markdown draft should be written (e.g., `brand/.build/drafts/strategy/positioning.md`)
- `{output-open-questions-path}` — absolute path where this slice's open questions JSON should be written (e.g., `brand/.build/open-questions/strategy/positioning.json`)
- `{org-name}` — org name for context
- `{context-blurb}` — brief description of the overall build (same as the extractor's input)

### Step 1: Read the Framework Spec

If `{owning-framework-id}` is non-null (a real framework id):

- Read `{owning-framework-path}`. Identify the slice's expected output shape — the sections, the headings, the analytical method.
- Note: the framework prompt itself is interactive when invoked standalone. You are NOT running the framework interactively. You are synthesizing the *output that framework would produce when completed*. Extract the structural template only; do not execute its WAIT-gated dialogue.

If `{owning-framework-id}` is JSON `null` (GAP slice):

- Read `{brand-folder-spec-path}` and find the slice's section in the spec. Use the spec's documented contract as the output shape.
- Mark this slice's frontmatter `synthesis_method: ad_hoc` and `owning_framework: null` (literal JSON/YAML null, NOT the string `"null"`).
- You will additionally raise a meta-Open-Question recommending a framework be commissioned for this slice (see Step 4).

### Step 2: Read the Source Extracts

Read each path in `{extract-json-paths}`. Each is a structured JSON with summary, key_quotes, entities, slice_relevance, claims, and concerns. Pull out:

- Quotes relevant to this slice (use `slice_relevance` field as the index)
- Entities (especially competitors, audiences, claims) the slice will reference
- Concerns to surface as open questions or flag in confidence

### Step 3: Synthesize the Slice Markdown

Write the slice markdown to `{output-draft-path}`.

Required structure:

1. Frontmatter per `docs/brand-folder-spec.md § Frontmatter schema`, extended with:
   - `owning_framework: {owning-framework-id}` (or `null` for GAP)
   - `synthesis_method: framework_shape` (or `ad_hoc` for GAP)
   - `sources: [list of source ids from the extracts you used]`
   - `status: draft`
   - `confidence: {overall confidence — low, medium, or high based on source signal density}`
2. Body content conforming to the framework's output shape (or the spec's contract for GAP slices). Use the slice's expected sections/headings. Synthesize content from the extracts — quote key phrases where useful but rewrite for cohesion.
3. Per-section confidence inline. Where you make a low-confidence inference or are forced to guess between plausible options, write the best-guess content AND log an open question (Step 4).

Length: as long as the slice's natural shape requires. Positioning is ~400-800 words. Narrative is ~400-700 words. Voice can be longer (~800-1500 words) because it has many sub-sections. Personas are ~300-600 words each.

If the parent directory does not exist, create it first.

### Step 4: Build the Open Questions JSON

Write open questions to `{output-open-questions-path}`. Schema:

```json
{
  "slice_id": "{slice-id}",
  "open_questions": [
    {
      "id": "local-1",
      "file": "{slice-id}",
      "slice": "<section-anchor-if-applicable-else-empty-string>",
      "confidence": "low|medium",
      "what_i_wrote": "<one or two sentences>",
      "question": "<the calibration question>",
      "why_it_matters": "<one line on downstream impact>",
      "deepen_with": "{owning-framework-id}",
      "sources": ["<extract source ids that fed this draft>"]
    }
  ]
}
```

**ID numbering:** Use local string ids — `local-1`, `local-2`, `local-3`, ... within this slice file. Do NOT assign global `OQ-N` ids; the orchestrator assigns those during aggregation in PHASE 3. Log exactly the questions that arise from the synthesis — no upper cap.

**Field rules:**
- `slice` — always a string. Use the empty string `""` if no section anchor applies. Do NOT omit the field.
- `deepen_with` — JSON `null` (literal, not the string `"null"`) for GAP slices; otherwise the framework id string.

When to raise an open question:
- Every section you tagged `confidence: low`
- Every place where you would have asked the user a clarifying question (an inference between plausible options, an unverified claim, a placeholder, an assumption about audience or pricing)
- For GAP slices: one additional meta-question per slice asking whether to commission a framework for this slice

If no open questions arise, write `{"slice_id": "...", "open_questions": []}` — do not omit the file.

If the parent directory does not exist, create it first.

### Step 5: Return Compact Status to Orchestrator

Return a short response (≤200 words) with:

```
SLICE: {slice-id}
DRAFT: {output-draft-path}
OPEN_QUESTIONS_FILE: {output-open-questions-path}
OPEN_QUESTIONS_COUNT: {N}
CONFIDENCE_DIST: {high: X, medium: Y, low: Z} (per-section counts)
OWNING_FRAMEWORK: {owning-framework-id or null}
NOTES: {one line on anything the orchestrator should know — e.g., "source signal was thin; 4 open questions raised"}
```

Do not echo the slice body. Do not paste source extract content. The orchestrator collects this status and proceeds to the next slice.
