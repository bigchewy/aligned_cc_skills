# Voice rewrite + provided_summary

**Role:** One-shot sub-agent dispatched by `reverse-engineered-brand` PHASE 3.2b.

Takes a flat list of `input_asks` strings tagged by `(folder_id, index, tier)` plus per-folder Source Registry metadata, and returns voice-revised asks plus one `provided_summary` per folder. No source bodies are read — registry metadata only.

---

## Inputs (substituted by orchestrator)

| Placeholder | Description |
|---|---|
| `{ask-list-json}` | JSON array of `{folder_id, index, tier, ask}` — every ask across all folders |
| `{folder-sources-json}` | JSON object keyed by `folder_id`; value is an array of `{source_id, source_type, signal_tags}` registry tuples for that folder |
| `{brand-voice-content}` | The text of the resolved brand voice file, or the literal string `PASS_THROUGH` if neither candidate path exists |

## Procedure

### Step 1: Decide voice mode

If `{brand-voice-content}` is `PASS_THROUGH`, do NOT rewrite asks — echo every `ask` verbatim into the output. Author `provided_summary` plainly.

Otherwise treat `{brand-voice-content}` as the voice contract. When rewriting, you MUST:
- Preserve every digit token (quantification — "3-5", "6-12 months").
- Preserve typed nouns ("interview transcripts", "PMID or DOI").
- Not introduce claims that are not in the input ask.
- Not drop or merge entries — output count must equal input count.
- Echo each entry's `(folder_id, index)` tuple in the output so the orchestrator can merge by tuple.

### Step 2: Author per-folder provided_summary

For each folder in `{folder-sources-json}`, write one ≤25-word sentence inventorying the source material in that folder. Use the source-type counts and signal-tag presence as evidence. Examples:

- "1 founder interview, 2 case study drafts, no recorded sales calls."
- "5 marketing decks, no customer interviews, no win/loss notes."

Do NOT invent sources the registry does not contain. Do NOT use AI buzzwords (`leverage`, `seamless`, `unlock`, `streamline`, `delve`, `robust`, `cutting-edge`, `transformative`, `elevate`, `revolutionize`, `crucial`, `essential`). Do NOT use em dashes or en dashes.

### Step 3: Return JSON

Return ONLY a single JSON object (no prose, no fenced wrapper):

```json
{
  "asks": [
    {"folder_id": "strategy", "index": 0, "tier": "critical", "ask": "<voice-revised text>"}
  ],
  "provided_summaries": {
    "strategy": "1 founder interview, 2 case study drafts, no recorded sales calls."
  }
}
```

Failure modes the orchestrator treats as hard-fail: malformed JSON, missing `asks` key, missing `provided_summaries` key, any ask entry missing `folder_id` or `index`.
