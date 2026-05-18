# Group bullets — headline_claim + thinnest_gap

**Role:** One-shot sub-agent dispatched by `reverse-engineered-brand` PHASE 3.2 (one per `display_groups[]` entry; 4 in parallel).

Reads the constituent folders' slice draft files and OQ JSON files (off disk; orchestrator never loads draft bodies into context), and writes two strings to a build artifact: `headline_claim` and `thinnest_gap`.

---

## Inputs (substituted by orchestrator)

| Placeholder | Description |
|---|---|
| `{group-id}` | Stable group id (e.g., `how-you-show-up`) |
| `{group-label}` | CEO-vocabulary label (e.g., `How you show up`) |
| `{constituent-folder-ids}` | JSON array of folder ids in this group |
| `{slice-draft-paths}` | JSON array of absolute paths to constituent folders' `.draft.md` files |
| `{constituent-oq-paths}` | JSON array of absolute paths to constituent folders' `.oq.json` files |
| `{canonical-pre-synthesis-blob-path}` | Absolute path to the same blob used in PHASE 2 framework dispatch (read-only orientation) |
| `{output-json-path}` | Absolute path where this sub-agent writes its result, e.g. `{brand-folder-path}/.build/groups/{group-id}.json` |

## Procedure

### Step 1: Read inputs

1. For each path in `{slice-draft-paths}`, Read the file. (These are the slice-level draft markdown files — bounded, not the full source corpus.)
2. For each path in `{constituent-oq-paths}`, Read the file and parse as JSON.
3. Read `{canonical-pre-synthesis-blob-path}` once — this orients you to the brand's overall posture without re-reading source bodies.

### Step 2: Author `headline_claim` (≤14 words)

Write a single declarative statement summarizing the load-bearing claim across this group's constituent areas. Constraints:

- **Declarative.** No questions, no conditionals.
- **Brand-specific.** Not a generic definition of the area. State what THIS brand's drafts converged on.
- **≤14 words after trim.** Count: `trim().split(/\s+/).filter(Boolean).length`. PHASE 3.2c Check 4 hard-fails if longer.
- **No banned phrases.** No em/en dashes, no `it's not X, it's Y` construction, no AI buzzwords (`leverage|seamless|unlock|streamline|delve|robust|cutting-edge|transformative|elevate|revolutionize|crucial|essential`).

Example for `how-you-show-up`: `"A virtual cardiometabolic practice for patients between primary care and specialists."`

### Step 3: Author `thinnest_gap` (≤14 words)

Write a single declarative statement naming the most load-bearing open gap across this group. Same constraints as Step 2. Same word cap, same banned phrases.

Example for `how-you-show-up`: `"How you price and where your edge sits versus employer programs."`

### Step 4: Self-check before write

Before writing the output file, run these checks and rewrite if any fail:

- Word count of `headline_claim` ≤14.
- Word count of `thinnest_gap` ≤14.
- Neither field is empty after trim.
- Neither contains em-dash, en-dash, or any banned word from the Step 2 list.
- `thinnest_gap` does NOT end with a question mark.

### Step 5: Write the output file

Write JSON to `{output-json-path}`:

```json
{ "headline_claim": "...", "thinnest_gap": "..." }
```

Return a one-line confirmation to the orchestrator (the orchestrator reads the file separately; the return value is just a heartbeat).

## Failure modes treated as hard-fail by orchestrator

- File not written (timeout).
- Malformed JSON in the written file.
- Missing `headline_claim` or `thinnest_gap` key.
- Either field empty after trim (Check 5).
- Either field exceeds 14 words (Check 4).
- Either field contains a banned phrase (Check 2).

On any of these, PHASE 3.2c emits a hard-fail naming this sub-agent (group id) and the failure mode. The orchestrator's `.build/groups/{group-id}.json` resume path detects the file's absence on retry and re-dispatches the failed group only.
