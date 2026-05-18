# Voice rewrite + provided_summary

**Role:** One-shot sub-agent dispatched by `reverse-engineered-brand` PHASE 3.2b.

Takes a flat list of `input_asks` strings tagged by `(group_id, index, tier)` plus per-group Source Registry metadata, and returns voice-revised asks plus one `provided_summary` per group. No source bodies are read — registry metadata only.

---

## Inputs (substituted by orchestrator)

| Placeholder | Description |
|---|---|
| `{ask-list-json}` | JSON array of `{group_id, index, tier, ask}` — every ask across all `display_groups[]`, post-aggregation |
| `{group-sources-json}` | JSON object keyed by `group_id`; value is the aggregated registry source list across constituent folders |
| `{brand-voice-content}` | Resolved brand voice file contents, or the literal string `PASS_THROUGH` if neither candidate path exists |

## Procedure

### Step 0: Shape transformation (runs BEFORE Step 1)

Before applying brand-voice rewriting, transform each incoming `ask` string to the doc-category shape. Three rules:

a. **Starts with a noun** (e.g., `"Recorded customer or prospect conversations"`), not a verb or conditional.
b. **Names a document category** (e.g., `"pitch decks"`, `"buyer interview transcripts"`, `"compliance correspondence"`), not a methodology prescription (`"Source-attributed metrics with date and method"`) or an interview question (`"Customer interviews answering one question: what phrase do you use…"`).
c. **Zero conditional clauses.** Strip leading `If you have…`, `Ideally…`, `When…`, `Where the buyer named X…`. Strip subordinate clauses with the same pattern.

Examples:

| Input ask | Shape-transformed ask |
|---|---|
| `If you have customer interviews answering one question: what phrase do you use when you describe us to a colleague?` | `Recorded customer or prospect conversations` |
| `Source-attributed metrics with date and method. A number without a date and a method is a guess.` | `Internal dashboards or metric source files` |
| `Ideally, recordings of three recent sales calls where the buyer mentioned a competitor.` | `Recorded customer or prospect conversations` |

After shape transformation, the ask MUST:
- Be ≤12 words after trim (PHASE 3.2c Check 4 hard-fails otherwise).
- NOT start with any of: `if`, `ideally`, `when`, `where the buyer` (PHASE 3.2c Check 5 verb-form rejection regex; case-insensitive).

Preserve digit tokens and typed nouns (`PMID`, `DOI`, `SOC 2`).

### Step 1: Decide voice mode

If `{brand-voice-content}` is `PASS_THROUGH`, do NOT rewrite asks — echo every `ask` verbatim into the output. Author `provided_summary` plainly.

Otherwise treat `{brand-voice-content}` as the voice contract. When rewriting, you MUST:
- Preserve every digit token (quantification — "3-5", "6-12 months").
- Preserve typed nouns ("interview transcripts", "PMID or DOI").
- Not introduce claims that are not in the input ask.
- Not drop or merge entries — output count must equal input count.
- Echo each entry's `(group_id, index)` tuple in the output so the orchestrator can merge by tuple.

### Step 2: Author per-group provided_summary

For each `group_id` in `{group-sources-json}`, write one ≤25-word sentence inventorying the aggregated source material across the group's constituent folders. Use the union of source-type counts and signal-tag presence as evidence. Examples:

- `"3 marketing decks, 1 founder essay, 1 partial product brief; no recorded sales calls."`
- `"5 case study drafts, 1 outcome dashboard; no peer-reviewed citations or security correspondence."`

Same banned phrases as Step 1 (no em/en dashes; no AI buzzwords). Same digit/typed-noun preservation rules.

### Step 3: Return JSON

Return ONLY a single JSON object (no prose, no fenced wrapper):

```json
{
  "asks": [
    {"group_id": "how-you-show-up", "index": 0, "tier": "critical", "ask": "<voice-revised, shape-transformed text>"}
  ],
  "provided_summaries": {
    "how-you-show-up": "3 marketing decks, 1 founder essay; no recorded sales calls.",
    "who-you-sell-to": "...",
    "who-you-sell-against": "...",
    "what-you-can-prove": "..."
  }
}
```

Failure modes the orchestrator treats as hard-fail: malformed JSON, missing `asks` key, missing `provided_summaries` key, any ask entry missing `group_id` or `index`.
