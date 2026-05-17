# Extract: source-extractor sub-agent prompt

This file is the prompt template the orchestrator pastes into a `subagent_type: general-purpose` Task dispatch during PHASE 1. One dispatch per source file, in parallel batches.

The orchestrator substitutes the placeholders below before dispatching. The sub-agent runs with its own context window and writes a structured JSON extract to disk — the orchestrator never reads source bodies directly.

This is NOT a registered top-level agent. It's a supporting prompt internal to `reverse-engineered-brand`. Dispatching it is the orchestrator's responsibility; reading its file is for humans auditing the framework.

---

## Prompt template (substitute placeholders, then dispatch)

You are reading a single source document for a brand-folder build and producing a compact structured JSON extract that captures brand signal without the raw file content.

**Inputs** (substituted by the orchestrator):

- `{source-path}` — absolute path or URL of the file to read
- `{source-id}` — short slug for this source (used in the registry: e.g., `#4`, `founder-essay`, `homepage`)
- `{output-json-path}` — absolute path where the structured extract JSON should be written
- `{context-blurb}` — brief description of what the brand build needs (e.g., "We're building a brand folder for Marley Medical, a digital health company. Focus on: positioning, customer voice, founder narrative, competitive alternatives, audience descriptions, proof claims.")

### Step 1: Read the Source

If `{source-path}` is a URL: use WebFetch to retrieve the page content.

If `{source-path}` is a local file:
- `.md`, `.txt`, `.html`, `.rtf`, `.org` — use Read
- `.pdf` — use Read (it supports PDFs; pass `pages` argument for large PDFs >10 pages, reading in 20-page chunks if needed)
- `.docx`, `.pptx` — use Read if supported; otherwise mark `used: "no"` and `summary: "binary format not parseable in this run"`
- Image formats — Read can describe images for `png`/`jpg`/`gif`; otherwise mark `used: "no"`

If the file is unreadable or fetch fails, write a minimal JSON with `used: "no"` and an error in `summary`, then return.

### Step 2: Classify and Extract

Build a structured extract with these fields:

- `id` — `{source-id}` from input
- `path` — `{source-path}` from input
- `type` — one of: `url-page`, `markdown`, `pdf`, `deck`, `transcript`, `doc`, `image`, `other`
- `used` — `yes` (read and produced signal) | `partial` (read but limited signal) | `no` (deemed out of scope or unparseable)
- `signal_tags` — zero or more from the controlled vocabulary: `positioning`, `narrative`, `messaging`, `voice`, `persona`, `audience`, `competitive`, `proof-points`, `clinical`, `compliance`, `design`, `pricing`, `founder-story`, `customer-voice`, `objections`, `landscape`
- `summary` — 2 to 4 sentences. What this source contains and why it matters to the brand build (or why it doesn't). This is the part the orchestrator sees in the Source Registry. Be specific and concrete.
- `key_quotes` — 3 to 10 short verbatim quotes (≤30 words each) that carry brand signal. Include speaker attribution if the source identifies one ("Founder, 2021 narrative deck:"). Quotes survive into slice synthesis as the high-fidelity signal.
- `entities` — flat array of named things mentioned in the source. Each entry has:
  - `name` — the entity's name (e.g., "DispatchTrack", "VP of Operations", "75% of HTN patients not at goal")
  - `role` — one of: `competitor` | `customer` | `partner` | `person` | `audience` | `claim` | `other`
  - `verbatim_quote` — optional 1-line verbatim quote from the source that supports this entity
  - `notes` — optional context (e.g., "named alongside legacy systems", "mentioned as a target persona")
- `slice_relevance` — for each brand-folder slice this source is load-bearing for, a one-sentence note on what to extract. Example: `{ "strategy/positioning.md": "Component 1 — describes the 'muddling through' alternative state in detail" }`. Omit slices where the source has no signal.
- `concerns` — flags for the orchestrator: e.g., `["dated: 2020 — may be pre-rebrand"]`, `["outlier: contradicts other sources on pricing"]`, `["partial: only first 20 pages of a 60-page deck were read"]`. Empty array if no concerns.

**Length budget:** The full extract JSON should be 500-1500 words. Long enough to capture the key signal; short enough that the orchestrator can load 30+ extracts without context bloat. Resist the urge to summarize the entire document — focus on what's load-bearing for brand synthesis.

### Step 3: Write the JSON

Write the extract to `{output-json-path}` as valid JSON. Pretty-print with 2-space indent for human readability.

If the parent directory does not exist, create it first.

### Step 4: Return Compact Status to Orchestrator

Return a short response (≤150 words) with:

1. A one-line status: `Extracted {source-id} ({type}) → {output-json-path}` or `Failed: {reason}`
2. The Source Registry entry (the orchestrator will copy this into the registry without further processing):

```
REGISTRY_ENTRY:
{
  "id": "{source-id}",
  "path": "{source-path}",
  "type": "{type}",
  "used": "yes|partial|no",
  "signal_tags": [...],
  "summary": "...",
  "extract_json_path": "{output-json-path}"
}
```

Do not echo the full extract back. Do not paste raw source content. The orchestrator gets the registry entry only; full extract sits on disk for later use by slice synthesizers.
