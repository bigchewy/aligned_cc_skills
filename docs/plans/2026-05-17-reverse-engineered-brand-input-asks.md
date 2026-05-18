---
mcp-tools-required: []
---

# Reverse-Engineered Brand — Per-Tab Input Asks Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Add per-folder `input_asks` and `provided_summary` to the `reverse-engineered-brand` build so `review.html` tells the client what raw material would strengthen each tab.

**Source Design Doc:** `docs/plans/2026-05-17-reverse-engineered-brand-input-asks-design.md`

**Mockups:** `docs/mockups/2026-05-17-reverse-engineered-brand-input-asks.html`

**Architecture:** Each owning framework declares its inputs in its YAML frontmatter via a new `input_asks` array. PHASE 3.2 of the `reverse-engineered-brand` orchestrator aggregates these per-folder, dedupes, dispatches a brand-voice sub-agent that also writes a `provided_summary` per folder, and runs a verification gate. The schema bumps to v0.4.0. `review.html` gets a third Overview sub-tab ("Inputs Needed") and a per-tab callout on single-instance content tabs.

**Tech Stack:** YAML frontmatter, Markdown framework prompts, locked HTML template (vanilla JS), Python/pytest for the coverage tests, JSON schema fixtures.

---

## File Touch Map (read before starting)

Each task lists its own files in detail. This is the union, so the reader knows the blast radius:

- `frameworks/reverse-engineered-brand/open-questions-schema.md` (Task 10)
- `frameworks/reverse-engineered-brand/prompt.md` (Tasks 14, 14b, 15, 16, 17, 18)
- `frameworks/reverse-engineered-brand/voice-rewrite.md` (Task 16, new sibling template)
- `frameworks/reverse-engineered-brand/review-template.html` (Tasks 20, 21)
- `frameworks/reverse-engineered-brand/render-review-html.md` (Task 19)
- `frameworks/reverse-engineered-brand/audience-taxonomy.md` (Task 9)
- `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/{valid-minimal,valid-with-alternatives,valid-v040-minimal}.json` (Tasks 11, 12)
- `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/README.md` (Task 11)
- `frameworks/reverse-engineered-brand/test-fixtures/render/{fixture-tiny,fixture-realistic,fixture-stress}.json` (Task 13)
- `frameworks/5-components-positioning/prompt.md` (Task 2)
- `frameworks/strategic-narrative/prompt.md` (Task 3)
- `frameworks/messaging-distillation/prompt.md` (Task 4)
- `frameworks/brand-voice/prompt.md` (Task 5)
- `frameworks/buyer-persona/prompt.md` (Task 6)
- `frameworks/competitive-battle-card/prompt.md` (Task 7)
- `frameworks/proof-points-audit/prompt.md` (Task 8)
- `tools/test_input_asks_coverage.py` (Task 1, exercised again by Tasks 2-9)
- `tools/test_oq_schema_v040.py` (Task 11)

**Task ordering dependency:** Tasks 2-8 each modify a different framework's `prompt.md` so they have no file conflict, but they all add evidence to the same coverage test from Task 1; complete them in numerical order so the test failure list shrinks monotonically. Tasks 14, 14b, 15, 16, 17, 18 all modify `frameworks/reverse-engineered-brand/prompt.md` and MUST run in numerical order — they each anchor on the previous task's output. Tasks 20-21 both modify `review-template.html` in numerical order.

---

## Prerequisites

> None. This plan introduces no external services, env vars, or one-time setup. All changes are to files inside this repo. The Python test commands assume `pytest` and `pyyaml` are already on PATH/installed — both are existing repo dependencies (used by `tools/test_sync_framework_frontmatter.py` which imports `yaml`).

---

### ✅ Task 1: Add input_asks frontmatter coverage test (failing)

**Files:**
- Create: `tools/test_input_asks_coverage.py`

**Step 1: Write the failing test**

```python
"""Coverage test: every framework expected to populate `input_asks` declares it.

The `reverse-engineered-brand` orchestrator's PHASE 3.2 reads `input_asks` from each
owning framework's frontmatter. If the field is missing or malformed, the Inputs
Needed surface in `review.html` will silently render empty for that folder.
"""
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent

# Frameworks that must declare `input_asks` per the per-tab catalog in
# docs/plans/2026-05-17-reverse-engineered-brand-input-asks-design.md.
REQUIRED_FRAMEWORKS = [
    "5-components-positioning",
    "strategic-narrative",
    "messaging-distillation",
    "brand-voice",
    "buyer-persona",
    "competitive-battle-card",
    "proof-points-audit",
]

VALID_TIERS = {"critical", "recommended", "optional"}


def _read_frontmatter(prompt_path: Path) -> dict:
    text = prompt_path.read_text()
    assert text.startswith("---\n"), f"{prompt_path}: missing frontmatter"
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end]) or {}


@pytest.mark.parametrize("framework_id", REQUIRED_FRAMEWORKS)
def test_framework_declares_input_asks(framework_id):
    prompt = REPO_ROOT / "frameworks" / framework_id / "prompt.md"
    fm = _read_frontmatter(prompt)
    asks = fm.get("input_asks")
    assert isinstance(asks, list) and asks, (
        f"{framework_id}: input_asks must be a non-empty list"
    )
    for i, entry in enumerate(asks):
        assert isinstance(entry, dict), f"{framework_id} input_asks[{i}]: must be a mapping"
        assert entry.get("tier") in VALID_TIERS, (
            f"{framework_id} input_asks[{i}].tier: must be one of {VALID_TIERS}, "
            f"got {entry.get('tier')!r}"
        )
        ask = entry.get("ask")
        assert isinstance(ask, str) and ask.strip(), (
            f"{framework_id} input_asks[{i}].ask: must be a non-empty string"
        )


def test_audience_taxonomy_has_ideal_inputs_section():
    """`audience-taxonomy.md` is not a framework prompt, so it carries its
    `input_asks` under a `## Ideal inputs` heading instead of in frontmatter."""
    taxonomy = REPO_ROOT / "frameworks" / "reverse-engineered-brand" / "audience-taxonomy.md"
    text = taxonomy.read_text()
    assert "\n## Ideal inputs\n" in text, (
        "audience-taxonomy.md must contain a `## Ideal inputs` section"
    )
    # The section must include at least one input_asks YAML block.
    assert "input_asks:" in text, (
        "audience-taxonomy.md `## Ideal inputs` must include an `input_asks:` block"
    )
```

**Step 2: Run test to verify it fails**

Run: `pytest tools/test_input_asks_coverage.py -v`
Expected: All 7 parametrized cases FAIL with `input_asks must be a non-empty list`, and `test_audience_taxonomy_has_ideal_inputs_section` FAILS with the missing-section message.

**Step 3: Commit**

```bash
git add tools/test_input_asks_coverage.py
git commit -m "test: add input_asks frontmatter coverage test (failing)"
```

---

### ✅ Task 2: Add input_asks to 5-components-positioning

**Files:**
- Modify: `frameworks/5-components-positioning/prompt.md` (the frontmatter block at the top)

**Step 1: Identify the failing test**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks[5-components-positioning] -v`
Expected: FAIL with `input_asks must be a non-empty list`.

**Step 2: Edit the frontmatter**

Replace the existing frontmatter block (between the leading `---` markers) with:

```yaml
---
required_documents:
- positioning statement
helpful_documents:
- competitive landscape
- customer research
deliverable_type: content
input_asks:
- tier: critical
  ask: "The alternative each recent buyer almost chose instead of you (one line per buyer, from email, survey, or sales-call note)"
- tier: recommended
  ask: "Win/loss notes from the last 6-12 months"
- tier: optional
  ask: "Internal positioning memo or sales pitch deck"
---
```

**Step 3: Run the parametrized test**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks[5-components-positioning] -v`
Expected: PASS.

**Step 4: Commit**

```bash
git add frameworks/5-components-positioning/prompt.md
git commit -m "feat(5-components-positioning): declare input_asks in frontmatter"
```

---

### ✅ Task 3: Add input_asks to strategic-narrative + populate required_documents

**Files:**
- Modify: `frameworks/strategic-narrative/prompt.md` (the frontmatter block at the top)

**Step 1: Identify the failing test**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks[strategic-narrative] -v`
Expected: FAIL with `input_asks must be a non-empty list`.

**Step 2: Edit the frontmatter**

The current frontmatter has `required_documents: []`. Per the design's Foundation work table, populate `required_documents` with the doc class the framework actually consumes, then add `input_asks`. Replace the frontmatter block with:

```yaml
---
required_documents:
- an internal strategy memo, talk transcript, or sales conversation describing the
  market shift the brand sees
helpful_documents:
- positioning statement
- company strategy
deliverable_type: content
input_asks:
- tier: critical
  ask: "An internal strategy memo, talk transcript, or sales conversation describing the market shift you see"
- tier: recommended
  ask: "Customer quotes describing the old way of doing things they are tired of"
- tier: optional
  ask: "Analyst reports or industry data on the market shift"
---
```

> Behavior change (acknowledge): `required_documents` was empty before; downstream readers that branch on "no required docs" will now treat strategic-narrative as having one required input. The only known reader is the orchestrator's framework-dispatch step, which does not branch on this list — it passes filtered extracts based on `signal_tags`, not on `required_documents`. The field is informational metadata for the framework's documentation surface.

**Step 3: Run the parametrized test**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks[strategic-narrative] -v`
Expected: PASS.

**Step 4: Commit**

```bash
git add frameworks/strategic-narrative/prompt.md
git commit -m "feat(strategic-narrative): populate required_documents and declare input_asks"
```

---

### ✅ Task 4: Add input_asks to messaging-distillation

**Files:**
- Modify: `frameworks/messaging-distillation/prompt.md` (the frontmatter block at the top)

**Step 1: Identify the failing test**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks[messaging-distillation] -v`
Expected: FAIL.

**Step 2: Edit the frontmatter**

Replace the frontmatter block with (preserve all existing fields, append `input_asks`):

```yaml
---
required_documents:
- completed strategy/positioning.md (5-components output)
helpful_documents:
- strategy/narrative.md
- personas/*.md
- proof/proof-points.md
- sample existing copy
deliverable_type: content
input_asks:
- tier: critical
  ask: "Customer interviews answering: what phrase do you use when you describe us to a colleague?"
- tier: recommended
  ask: "Sample existing copy from across surfaces (homepage, deck, sales emails, social)"
- tier: optional
  ask: "Internal naming conventions or category-language guide"
---
```

**Step 3: Run the parametrized test**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks[messaging-distillation] -v`
Expected: PASS.

**Step 4: Commit**

```bash
git add frameworks/messaging-distillation/prompt.md
git commit -m "feat(messaging-distillation): declare input_asks in frontmatter"
```

---

### ✅ Task 5: Add input_asks to brand-voice

**Files:**
- Modify: `frameworks/brand-voice/prompt.md` (the frontmatter block at the top)

**Step 1: Identify the failing test**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks[brand-voice] -v`
Expected: FAIL.

**Step 2: Edit the frontmatter**

Replace the frontmatter block with:

```yaml
---
required_documents:
- 3-10 sample pieces of existing copy (homepage, blog posts, founder tweets, sales
  emails)
helpful_documents:
- competitor copy samples
- category-name and tagline from messaging.md
deliverable_type: content
input_asks:
- tier: critical
  ask: "3-10 sample pieces of existing copy across surfaces"
- tier: recommended
  ask: "Competitor copy samples on equivalent surfaces"
- tier: optional
  ask: "Existing tone guidelines or banned-phrase list, if any"
---
```

**Step 3: Run the parametrized test**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks[brand-voice] -v`
Expected: PASS.

**Step 4: Commit**

```bash
git add frameworks/brand-voice/prompt.md
git commit -m "feat(brand-voice): declare input_asks in frontmatter"
```

---

### ✅ Task 6: Add input_asks to buyer-persona + restructure required_documents

**Files:**
- Modify: `frameworks/buyer-persona/prompt.md` (the frontmatter block at the top)

**Step 1: Identify the failing test**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks[buyer-persona] -v`
Expected: FAIL.

**Step 2: Edit the frontmatter**

Per the design's Foundation work table, the existing `required_documents: [the role being profiled (...)]` entry is actually a *parameter*, not a document. Move it to a new `required_inputs` key and replace `required_documents` with the actual document class. Replace the frontmatter block with:

```yaml
---
required_inputs:
- the role being profiled (e.g., CMO, VP-Ops, Chief People Officer)
required_documents:
- customer interview transcripts including the customer's role
helpful_documents:
- customer research
- competitor positioning
deliverable_type: analysis
input_asks:
- tier: critical
  ask: "3-5 customer interview transcripts including the customer's role"
- tier: recommended
  ask: "Sales call recordings or transcripts"
- tier: optional
  ask: "Support tickets surfacing recurring pain language"
---
```

> Behavior change (acknowledge): `required_documents` semantically shifts from "the role is the input" to "interview transcripts are the input". The role is preserved in a sibling `required_inputs` key. The buyer-persona prompt body itself elicits the role in PHASE 1; this metadata is documentation only and has no callers that branch on its exact content. The `sync_framework_frontmatter.py` script in `tools/` only mirrors `deliverable_type` from the registry, so adding `required_inputs` will not be overwritten on the next sync.

**Step 3: Run the parametrized test**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks[buyer-persona] -v`
Expected: PASS.

**Step 4: Run the sync-script test to confirm no regression**

Run: `pytest tools/test_sync_framework_frontmatter.py -v`
Expected: All pre-existing tests PASS — the sync script touches only `deliverable_type` and must leave `required_inputs` and `input_asks` untouched.

**Step 5: Commit**

```bash
git add frameworks/buyer-persona/prompt.md
git commit -m "feat(buyer-persona): restructure required_documents, add input_asks"
```

---

### ✅ Task 7: Add input_asks to competitive-battle-card

**Files:**
- Modify: `frameworks/competitive-battle-card/prompt.md` (the frontmatter block at the top)

**Step 1: Identify the failing test**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks[competitive-battle-card] -v`
Expected: FAIL.

**Step 2: Edit the frontmatter**

Replace the frontmatter block with:

```yaml
---
required_documents:
- completed strategy/positioning.md (Component 1: competitive alternatives)
- completed language/messaging.md (value-prop phrasings)
helpful_documents:
- customer win/loss interviews
- competitor public materials
deliverable_type: content
input_asks:
- tier: critical
  ask: "Win/loss interviews where the buyer named a specific competitor"
- tier: recommended
  ask: "Competitor public materials beyond the homepage (pricing pages, case studies, integration lists)"
- tier: optional
  ask: "Sales objection log organized by competitor name"
---
```

**Step 3: Run the parametrized test**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks[competitive-battle-card] -v`
Expected: PASS.

**Step 4: Commit**

```bash
git add frameworks/competitive-battle-card/prompt.md
git commit -m "feat(competitive-battle-card): declare input_asks in frontmatter"
```

---

### ✅ Task 8: Add input_asks to proof-points-audit

**Files:**
- Modify: `frameworks/proof-points-audit/prompt.md` (the frontmatter block at the top)

**Step 1: Identify the failing test**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks[proof-points-audit] -v`
Expected: FAIL.

**Step 2: Edit the frontmatter**

Replace the frontmatter block with:

```yaml
---
required_documents:
- existing customer-facing copy (homepage, deck, one-pager)
helpful_documents:
- customer interview transcripts
- case study drafts
- third-party reports
- regulatory filings
deliverable_type: analysis
input_asks:
- tier: critical
  ask: "Source-attributed metrics with date and method"
- tier: recommended
  ask: "Case study drafts naming customer, outcome, and time window"
- tier: optional
  ask: "Third-party reports or analyst coverage citing the company"
---
```

**Step 3: Run the parametrized test**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks[proof-points-audit] -v`
Expected: PASS.

**Step 4: Run the full coverage test to confirm all seven frameworks pass**

Run: `pytest tools/test_input_asks_coverage.py::test_framework_declares_input_asks -v`
Expected: All 7 parametrized cases PASS.

**Step 5: Commit**

```bash
git add frameworks/proof-points-audit/prompt.md
git commit -m "feat(proof-points-audit): declare input_asks in frontmatter"
```

---

### ✅ Task 9: Add `## Ideal inputs` section to audience-taxonomy.md

**Files:**
- Modify: `frameworks/reverse-engineered-brand/audience-taxonomy.md` (append a new top-level section)

**Step 1: Identify the failing test**

Run: `pytest tools/test_input_asks_coverage.py::test_audience_taxonomy_has_ideal_inputs_section -v`
Expected: FAIL.

**Step 2: Edit the file**

Append the following section to the end of `audience-taxonomy.md`, after the existing `## When a brand operates outside the taxonomy` section:

```markdown
## Ideal inputs

The `audiences/` folder is populated via classification (not framework dispatch), so its `input_asks` live here rather than in a framework's frontmatter. The orchestrator reads this section at PHASE 3.2 and merges these asks into the `audiences` folder entry alongside any framework-dispatched ones.

```yaml
input_asks:
- tier: critical
  ask: "Documents naming each segment served (signed agreements, BAAs, segment-specific case studies)"
- tier: recommended
  ask: "Pricing models broken out by channel or segment"
- tier: optional
  ask: "Sales notes describing channel-specific buying criteria"
```
```

**Step 3: Run the test**

Run: `pytest tools/test_input_asks_coverage.py::test_audience_taxonomy_has_ideal_inputs_section -v`
Expected: PASS.

**Step 4: Commit**

```bash
git add frameworks/reverse-engineered-brand/audience-taxonomy.md
git commit -m "feat(audience-taxonomy): add Ideal inputs section with input_asks"
```

---

### ✅ Task 10: Bump open-questions-schema to v0.4.0

**Files:**
- Modify: `frameworks/reverse-engineered-brand/open-questions-schema.md` (header version, top-level structure, `folders[]` table, backward-compat paragraph)

**Step 1: Edit the schema doc**

Apply these changes in order:

1. **Header** — change `# Open Questions Schema v0.3.0` to `# Open Questions Schema v0.4.0`.

2. **Top-level JSON example** — change `"schema_version": "0.3.0"` to `"schema_version": "0.4.0"` in the code block under `## Top-level structure`.

3. **`schema_version` row in the top-level table** — change the Notes from `Currently "0.3.0"` to `Currently "0.4.0"`.

4. **Remove the entire `### Backward compatibility (v0.2.0 → v0.3.0)` section.** Per Decision 3 in the design doc, v0.4.0 is a breaking bump with no fallback — the framework regenerates the JSON on every build, so no installed base of v0.3 JSON survives a re-run. Delete the heading and both paragraphs underneath it, plus the trailing `---` separator immediately following the section.

5. **Add two rows to the `folders` entry schema table** (the table immediately under `## \`folders\` entry schema`). Append these rows after the existing `summary` row:

| `provided_summary` | string | yes (v0.4.0+) | **1 sentence, ≤25 words.** Plain-language inventory of what source material this folder drew on (e.g., "1 founder interview, 2 case study drafts, no recorded sales calls"). Generated by the Step 3.2b brand-voice sub-agent from Source Registry metadata only — no source-body reads. Pairs with `input_asks` in the per-tab callout to frame the ask as a snapshot of what we received vs. what would strengthen the build. |
| `input_asks` | array | yes (v0.4.0+) | Tiered list of raw-material categories that would strengthen this folder's drafts. Each entry: `{ tier: "critical" \| "recommended" \| "optional", ask: string }`. Aggregated at PHASE 3.2 from each owning framework's `input_asks` frontmatter (and from `audience-taxonomy.md ## Ideal inputs` for `audiences`, and `prompt.md` PHASE 1.5a inline list for `competitive`). Dedupe rule: case-insensitive trim match on `ask`; higher tier wins. Voice-rewritten by the Step 3.2b sub-agent before write. |

**Step 2: Verify by reading the file back**

Read `frameworks/reverse-engineered-brand/open-questions-schema.md` (full file). Confirm:
- Title says v0.4.0.
- No occurrence of `## Backward compatibility` remains anywhere in the file.
- The `folders` entry schema table contains rows for `provided_summary` and `input_asks`.

> Behavior change (acknowledge): v0.4.0 is a **breaking** schema change. The Step 2 shape-warning logic in `render-review-html.md` warns on missing fields but does NOT fail — that warning path now catches v0.3.0 files too. Existing on-disk v0.3.0 `.open-questions.json` files (artifacts of prior runs) will render with empty Inputs Needed sections and warnings in NOTES. The framework regenerates the JSON on every run, so this only affects re-opens of stale artifacts.

**Step 3: Commit**

```bash
git add frameworks/reverse-engineered-brand/open-questions-schema.md
git commit -m "docs(oq-schema): bump to v0.4.0 with input_asks and provided_summary"
```

---

### ✅ Task 11: Add v0.4.0 schema fixture + parser test

**Files:**
- Create: `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/valid-v040-minimal.json`
- Create: `tools/test_oq_schema_v040.py`
- Modify: `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/README.md` (add row for the new fixture)

**Step 1: Write the failing test**

```python
"""Parse-validate the v0.4.0 fixture against the v0.4.0 schema fields.

Schema reference: frameworks/reverse-engineered-brand/open-questions-schema.md
"""
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = (
    REPO_ROOT
    / "frameworks/reverse-engineered-brand/test-fixtures/oq-schema/valid-v040-minimal.json"
)

VALID_TIERS = {"critical", "recommended", "optional"}


def _load() -> dict:
    return json.loads(FIXTURE.read_text())


def test_schema_version_is_v040():
    assert _load()["schema_version"] == "0.4.0"


def test_each_folder_has_provided_summary_and_input_asks():
    data = _load()
    assert data["folders"], "fixture must include at least one folder"
    for folder in data["folders"]:
        assert isinstance(folder.get("provided_summary"), str) and folder["provided_summary"].strip(), (
            f"folder {folder.get('id')}: provided_summary must be a non-empty string"
        )
        asks = folder.get("input_asks")
        assert isinstance(asks, list) and asks, (
            f"folder {folder.get('id')}: input_asks must be a non-empty list"
        )
        for i, entry in enumerate(asks):
            assert entry.get("tier") in VALID_TIERS, (
                f"folder {folder.get('id')} input_asks[{i}].tier: invalid"
            )
            assert isinstance(entry.get("ask"), str) and entry["ask"].strip(), (
                f"folder {folder.get('id')} input_asks[{i}].ask: must be non-empty"
            )


def test_provided_summary_is_one_sentence_under_25_words():
    """Mirrors the v0.4.0 schema constraint: 1 sentence, ≤25 words."""
    for folder in _load()["folders"]:
        summary = folder["provided_summary"]
        words = summary.split()
        assert len(words) <= 25, (
            f"folder {folder['id']}: provided_summary is {len(words)} words (max 25)"
        )
```

**Step 2: Run test to verify it fails**

Run: `pytest tools/test_oq_schema_v040.py -v`
Expected: All three tests FAIL (`FileNotFoundError` on the fixture).

**Step 3: Create the fixture**

Write to `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/valid-v040-minimal.json`:

```json
{
  "schema_version": "0.4.0",
  "source_counts": { "total": 3, "raw_material": 2, "primary_research": 1 },
  "source_narratives": {
    "raw_material": "Two marketing decks. No product specs.",
    "primary_research": "One founder interview transcript. No buyer interviews."
  },
  "folders": [
    {
      "id": "strategy",
      "label": "Strategy",
      "status": "Partial",
      "grade": 3,
      "summary": "Working hypothesis converges on spreadsheets as the primary competitive alternative. Category framing remains open. Two P0 questions need resolution before drafts can ship.",
      "p0_count": 2,
      "p1_count": 1,
      "p2_count": 0,
      "framework_dispatches": [
        { "framework_id": "5-components-positioning", "fills": ["strategy/positioning.md"] }
      ],
      "provided_summary": "1 founder interview, 2 marketing decks, no recorded sales calls.",
      "input_asks": [
        { "tier": "critical", "ask": "The alternative each recent buyer almost chose instead of you (one line per buyer, from email, survey, or sales-call note)" },
        { "tier": "recommended", "ask": "Win/loss notes from the last 6-12 months" }
      ]
    }
  ],
  "behavioral_alternatives": [],
  "competitors": [],
  "open_questions": []
}
```

**Step 4: Update the fixtures README**

Add a row to the table in `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/README.md`:

| `valid-v040-minimal.json` | Pass (v0.4.0 schema with `input_asks` + `provided_summary`) |

Insert it between `valid-gap-slice.json` and `invalid-missing-impact.json`.

**Step 5: Run tests**

Run: `pytest tools/test_oq_schema_v040.py -v`
Expected: All three tests PASS.

**Step 6: Commit**

```bash
git add tools/test_oq_schema_v040.py \
  frameworks/reverse-engineered-brand/test-fixtures/oq-schema/valid-v040-minimal.json \
  frameworks/reverse-engineered-brand/test-fixtures/oq-schema/README.md
git commit -m "test(oq-schema): add v0.4.0 fixture and parser test"
```

---

### ✅ Task 12: Update existing oq-schema fixtures to v0.4.0

**Files:**
- Modify: `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/valid-minimal.json`
- Modify: `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/valid-with-alternatives.json`

**Step 1: Update `valid-minimal.json`**

Replace the entire file contents with:

```json
{
  "schema_version": "0.4.0",
  "source_counts": { "total": 1, "raw_material": 1, "primary_research": 0 },
  "source_narratives": {
    "raw_material": "One pitch deck. Limited coverage; most areas have no independent corroboration.",
    "primary_research": "No customer interviews. The customer-voice areas will be sparse."
  },
  "folders": [
    {
      "id": "strategy",
      "label": "Strategy",
      "status": "Strong",
      "grade": 5,
      "summary": "Working hypothesis converges on spreadsheets as the primary competitive alternative; one open question on category framing remains.",
      "p0_count": 1,
      "p1_count": 0,
      "p2_count": 0,
      "framework_dispatches": [
        {"framework_id": "5-components-positioning", "fills": "strategy/positioning.md", "why_first": "Anchors downstream messaging and positioning"}
      ],
      "provided_summary": "1 pitch deck, no customer interviews, no recorded sales calls.",
      "input_asks": [
        { "tier": "critical", "ask": "The alternative each recent buyer almost chose instead of you (one line per buyer, from email, survey, or sales-call note)" }
      ]
    }
  ],
  "behavioral_alternatives": [],
  "competitors": [],
  "open_questions": [
    {
      "id": "Q-strategy-positioning-1",
      "global_id": "OQ-1",
      "file": "strategy/positioning.md",
      "slice": "competitive-alternatives",
      "framework_slot": "phase-1-competitive-alternatives",
      "question": "Is the real alternative spreadsheets + manual dispatch?",
      "inferred_value": "spreadsheets + manual dispatch",
      "draft_excerpt": "Best customers were previously cobbling together spreadsheets.",
      "confidence": "medium",
      "impact": "P0",
      "evidence": ["source:#4"],
      "deepen_with": "5-components-positioning",
      "why_it_matters": "Component 1 anchors the positioning frame.",
      "emitted_at": "2026-05-17T14:32:00Z"
    }
  ]
}
```

**Step 2: Update `valid-with-alternatives.json`**

Apply only the v0.4.0 additions to the existing file — do not rewrite unrelated fields. In particular:

1. Change `"schema_version": "0.2.0"` to `"schema_version": "0.4.0"`.
2. Add top-level `source_counts` and `source_narratives` blocks immediately after `schema_version`:
   ```json
     "source_counts": { "total": 6, "raw_material": 5, "primary_research": 1 },
     "source_narratives": {
       "raw_material": "Five marketing decks. Limited product-spec coverage.",
       "primary_research": "One customer call. No competitor dossiers commissioned."
     },
   ```
3. Inside the single `folders[0]` entry, after the `framework_dispatches` line and before the closing `}`, add `grade`, `summary`, `provided_summary`, and `input_asks`:
   ```json
       "grade": 4,
       "summary": "Working hypothesis converges on spreadsheets as the alternative; differentiated attributes still unconfirmed.",
       "provided_summary": "5 marketing decks, 1 customer call, no win/loss notes.",
       "input_asks": [
         { "tier": "critical", "ask": "The alternative each recent buyer almost chose instead of you (one line per buyer, from email, survey, or sales-call note)" },
         { "tier": "recommended", "ask": "Win/loss notes from the last 6-12 months" }
       ]
   ```

**Step 3: Verify with the v0.4.0 schema test**

Extend the test from Task 11 by running it against both updated fixtures. Add this parametrized variant to `tools/test_oq_schema_v040.py`:

```python
@pytest.mark.parametrize("fixture_name", ["valid-minimal.json", "valid-with-alternatives.json"])
def test_legacy_fixtures_updated_to_v040(fixture_name):
    """Existing schema fixtures must be re-stamped to v0.4.0 with the new fields."""
    path = (
        REPO_ROOT
        / "frameworks/reverse-engineered-brand/test-fixtures/oq-schema"
        / fixture_name
    )
    data = json.loads(path.read_text())
    assert data["schema_version"] == "0.4.0", f"{fixture_name}: schema_version not v0.4.0"
    assert "source_counts" in data, f"{fixture_name}: source_counts missing"
    assert "source_narratives" in data, f"{fixture_name}: source_narratives missing"
    for folder in data["folders"]:
        assert "grade" in folder, f"{fixture_name} folder {folder['id']}: grade missing"
        assert "summary" in folder, f"{fixture_name} folder {folder['id']}: summary missing"
        assert "provided_summary" in folder, f"{fixture_name} folder {folder['id']}: provided_summary missing"
        assert "input_asks" in folder, f"{fixture_name} folder {folder['id']}: input_asks missing"
```

Run: `pytest tools/test_oq_schema_v040.py -v`
Expected: All tests PASS (the two new parametrized cases plus the prior three).

**Step 4: Commit**

```bash
git add frameworks/reverse-engineered-brand/test-fixtures/oq-schema/valid-minimal.json \
  frameworks/reverse-engineered-brand/test-fixtures/oq-schema/valid-with-alternatives.json \
  tools/test_oq_schema_v040.py
git commit -m "test(oq-schema): update legacy fixtures to v0.4.0"
```

---

### ✅ Task 13: Update render fixtures to v0.4.0

**Files:**
- Modify: `frameworks/reverse-engineered-brand/test-fixtures/render/fixture-tiny.json`
- Modify: `frameworks/reverse-engineered-brand/test-fixtures/render/fixture-realistic.json`
- Modify: `frameworks/reverse-engineered-brand/test-fixtures/render/fixture-stress.json`

> **Implementer note on render fixtures:** Render fixtures are hand-maintained JSON files used for manual spot-checks against `review-template.html` (per the test-fixtures README). They have no automated runner today — the v0.4.0 test added here is the first one. Update them in-place; do not regenerate them from a build.

**Step 1: Update each render fixture**

For all three files:

1. Change `"schema_version"` to `"0.4.0"`.
2. Ensure top-level `source_counts` and `source_narratives` are present (add them if missing — `fixture-tiny.json` already has `source_count: 3` as the legacy singular; **delete** the singular `source_count` key and replace with the new `source_counts`/`source_narratives` shape).
3. **Delete legacy `exec_summary` top-level block** if present (`fixture-tiny.json` and `fixture-with-alternatives.json` both have it as v0.2.0 baggage; per-folder `summary` and top-level `source_narratives` replace it in v0.4.0).
4. For each `folders[]` entry, add `grade`, `summary` (1-3 sentences, brand-specific), `provided_summary`, and `input_asks`. Use `grade: 3` as a reasonable default for `Partial` status, `grade: 5` for `Strong`, and `grade: 2` for `Weak`.
5. For `fixture-realistic.json` and `fixture-stress.json`, populate `input_asks` with 1-3 plausible entries per folder, drawn from the per-tab catalog in the design doc. Use the matching catalog ask for each folder:
   - `strategy` → entries from `5-components-positioning` + `strategic-narrative` (dedupe by ask text — see merge rule in design doc)
   - `language` → entries from `messaging-distillation` + `brand-voice`
   - `personas` → entries from `buyer-persona`
   - `market` → entries from `competitive-battle-card` + `alternatives_input_asks` (inline from Task 14b)
   - `proof` → entries from `proof-points-audit` + `clinical_evidence_input_asks` + `compliance_input_asks` (Task 14b) where the fixture is healthcare-flavored
   - `audiences` → entries from `audience-taxonomy.md ## Ideal inputs`
6. For `fixture-stress.json`, the test-fixture README notes ~130 OQs — preserve the OQ volume; only the per-folder additions are required.

**Step 2: Add a render-fixture sanity test to the v0.4.0 test file**

Append to `tools/test_oq_schema_v040.py`:

```python
@pytest.mark.parametrize(
    "fixture_name",
    ["fixture-tiny.json", "fixture-realistic.json", "fixture-stress.json"],
)
def test_render_fixtures_updated_to_v040(fixture_name):
    """Render fixtures used to spot-check `review-template.html` must carry v0.4.0 fields."""
    path = (
        REPO_ROOT
        / "frameworks/reverse-engineered-brand/test-fixtures/render"
        / fixture_name
    )
    data = json.loads(path.read_text())
    assert data["schema_version"] == "0.4.0", f"{fixture_name}: not v0.4.0"
    assert "source_counts" in data, f"{fixture_name}: source_counts missing"
    assert "source_narratives" in data, f"{fixture_name}: source_narratives missing"
    assert "source_count" not in data, f"{fixture_name}: legacy singular source_count must be removed"
    assert "exec_summary" not in data, f"{fixture_name}: legacy exec_summary block must be removed"
    for folder in data["folders"]:
        assert "grade" in folder, f"{fixture_name} folder {folder['id']}: grade missing"
        assert "summary" in folder, f"{fixture_name} folder {folder['id']}: summary missing"
        assert "provided_summary" in folder, f"{fixture_name} folder {folder['id']}: provided_summary missing"
        assert "input_asks" in folder, f"{fixture_name} folder {folder['id']}: input_asks missing"
```

**Step 3: Run tests**

Run: `pytest tools/test_oq_schema_v040.py -v`
Expected: All tests PASS, including the three new render-fixture cases.

**Step 4: Commit**

```bash
git add frameworks/reverse-engineered-brand/test-fixtures/render/ \
  tools/test_oq_schema_v040.py
git commit -m "test(render): update render fixtures to v0.4.0 with input_asks and provided_summary"
```

---

### ✅ Task 14: Add competitive_context_input_asks inline in prompt.md PHASE 1.5a

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (Step 1.5a block under `### PHASE 1.5: Competitor Research`)

**Step 1: Edit Step 1.5a**

In the bulleted list under `**Step 1.5a — Orchestrator-side aggregation (cheap, no sub-agents):**`, insert a new bullet immediately AFTER the existing `Write {brand-folder-path}/.build/competitor-list.json (...)` bullet and BEFORE `**Step 1.5b — Sub-agent dossier dispatch (parallel):**`:

```markdown
- **Competitive Context input asks (inline):** hold the following array in memory; PHASE 3.2 reads it when building the `competitive` folder entry. This is the single source of truth for the Competitive Context tab's `input_asks` — no separate file, no per-framework fanout (per Decision 4 in the design doc).

  ```yaml
  competitive_context_input_asks:
    - tier: critical
      ask: "Quotes from prospects describing the alternatives they used before considering you"
    - tier: recommended
      ask: "Win/loss interviews comparing your offering to non-product alternatives"
    - tier: optional
      ask: "Pre-purchase research notes describing how prospects framed the old way"
  ```
```

**Step 2: Verify with Grep**

Run a Grep for the new anchor string:

```
Pattern: competitive_context_input_asks
Path: frameworks/reverse-engineered-brand/prompt.md
output_mode: count
```

Expected: 1 match.

**Step 3: Commit**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reb): add competitive_context_input_asks inline in PHASE 1.5a"
```

---

### ✅ Task 14b: Add slice-specific inline input_asks for alternatives, clinical-evidence, compliance

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (insert a new orchestrator-side block at the end of PHASE 2 Step 2.1, where the slice list is determined)

**Why this task exists:** Three slices in the slice-mapping table at PHASE 2 (`prompt.md` lines 150-162) have asks that DIFFER from their owning framework's asks:

- `market/alternatives.md` is owned by `5-components-positioning` (Component 1), but its catalog asks ("Quotes from prospects describing alternatives", "Cost-of-inaction data", "Pre-purchase research notes") are distinct from positioning's asks.
- `proof/clinical-evidence.md` is owned by `proof-points-audit` (healthcare extension), with asks for PMID/DOI citations.
- `proof/compliance.md` is owned by `proof-points-audit`, with asks for active certifications.

Putting these in the owning framework's frontmatter would duplicate them across folders. Putting them inline in `prompt.md` (the existing pattern for `competitive_context_input_asks`) keeps them slice-scoped and lets PHASE 3.2 aggregation route them correctly.

**Step 1: Insert the inline asks block**

> **Fence reconciliation note:** The block below is shown here inside a triple-backtick markdown fence so the plan renders cleanly, but it contains an inner triple-backtick `yaml` fence. When inserting into `prompt.md`, paste only the content (the `**Slice-specific input_asks (...)** ... ``` ` closing yaml fence). Do NOT include the outer wrapping triple-backticks shown in this plan; they exist only to demarcate this plan's example. The yaml block must remain triple-fenced in `prompt.md` so other tooling (the existing fenced-block-skipping scan in `writing-plans`) treats it correctly.

Locate `**Step 2.2: Build the canonical pre-synthesis blob.**` and insert the following block IMMEDIATELY ABOVE it (so it lands at the end of Step 2.1's block):

````markdown
**Slice-specific input_asks (inline, NEW v0.4.0+).** For slices whose asks differ from their owning framework's asks, hold the following arrays in memory; PHASE 3.2 reads them when building the `market` and `proof` folder entries (per Task 14b in the implementation plan).

```yaml
alternatives_input_asks:
  - tier: critical
    ask: "Quotes from prospects describing alternatives"
  - tier: recommended
    ask: "Cost-of-inaction data: what the status quo costs the buyer"
  - tier: optional
    ask: "Pre-purchase research notes from prospects"

clinical_evidence_input_asks:
  - tier: critical
    ask: "Peer-reviewed citations with PMID or DOI"
  - tier: recommended
    ask: "Internal clinical study summaries naming method, N, and effect size"
  - tier: optional
    ask: "Regulatory submission filings or correspondence"

compliance_input_asks:
  - tier: critical
    ask: "Active certifications with auditor name, issue date, and expiration"
  - tier: recommended
    ask: "Compliance attestation letters from named customers"
  - tier: optional
    ask: "Customer-facing compliance one-pager or trust-center URL"
```

These arrays REPLACE the owning framework's asks when aggregating `market/alternatives.md`, `proof/clinical-evidence.md`, and `proof/compliance.md` respectively. PHASE 3.2 uses the slice-specific array if present; otherwise it falls back to the owning framework's frontmatter asks.
````

**Step 2: Verify with Grep**

Run Grep:
```
Pattern: alternatives_input_asks|clinical_evidence_input_asks|compliance_input_asks
Path: frameworks/reverse-engineered-brand/prompt.md
output_mode: count
```
Expected: ≥ 3 matches.

**Step 3: Commit**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reb): add slice-specific input_asks for alternatives, clinical-evidence, compliance"
```

---

### ✅ Task 15: Add per-folder input_asks aggregation to PHASE 3.2

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (Step 3.2 block under `### PHASE 3: Load`)

**Step 1: Edit Step 3.2**

Locate `**Step 3.2: Build the `folders` array.**` and the bulleted list that follows it. After the final bullet (the one beginning `**Write `summary`** ...`), append a new bullet:

```markdown
- **Aggregate `input_asks`** (NEW, v0.4.0+). For each folder, build the `input_asks` array by collecting from every slice that contributed to this folder. The orchestrator reads each framework's `prompt.md` frontmatter directly here — this is permitted by the carve-out at `prompt.md` lines 25-26 ("Bounded spec/template files ... are allowed in orchestrator context"). Frontmatter blocks are bounded (≤30 lines each). Read each only once and parse the YAML front-matter for `input_asks`:
  - Framework-dispatched slices: open `frameworks/{owning-framework-id}/prompt.md`, parse the YAML front-matter, take the `input_asks` array. The `owning-framework-id` for each slice is in the slice-mapping table at PHASE 2 (`prompt.md` lines 150-162). Skip frameworks whose front-matter omits the field.
  - `audiences` folder: read the `input_asks` YAML block from the `## Ideal inputs` section of `frameworks/reverse-engineered-brand/audience-taxonomy.md`.
  - `competitive` folder: read the in-memory `competitive_context_input_asks` array from PHASE 1.5a.
  - Slice-specific overrides (the `market/alternatives.md`, `proof/clinical-evidence.md`, `proof/compliance.md` slices): read the slice-specific inline `input_asks` arrays declared at PHASE 2 by Task 14b (`alternatives_input_asks`, `clinical_evidence_input_asks`, `compliance_input_asks`). Use these INSTEAD of the owning framework's asks for those specific slices (positioning's asks still feed `strategy/positioning.md`; alternatives' asks feed `market/alternatives.md`).

  **Dedupe-by-text merge rule.** Concatenate all asks for the folder, then dedupe by `ask` text using case-insensitive whitespace-trimmed comparison. On collision, the higher tier wins (`critical` > `recommended` > `optional`). Within each tier, preserve first-seen order for determinism.

  **Single-slice folder behavior.** If a folder hosts exactly one framework-dispatched slice, the dedupe step is a no-op and the asks pass through in framework-declared order.

  **Multi-slice folder behavior.** `strategy/` (positioning + narrative), `language/` (messaging + voice), `market/` (competitive + alternatives), and `proof/` (proof-points + clinical + compliance) each collect from multiple frameworks; the dedupe rule keeps the consolidated Overview list clean.

  **Write `provided_summary` placeholder.** Set `provided_summary` to `null` here — the Step 3.2b sub-agent populates it. The verification gate in Step 3.2c hard-fails if any folder still has `provided_summary: null` at JSON-write time.
```

**Step 2: Verify with Grep**

Run Grep:
```
Pattern: Aggregate `input_asks`
Path: frameworks/reverse-engineered-brand/prompt.md
output_mode: count
```
Expected: 1 match.

**Step 3: Commit**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reb): aggregate per-folder input_asks in PHASE 3.2 with dedupe-by-text"
```

---

### ✅ Task 16: Add PHASE 3.2b brand-voice + provided_summary sub-agent

**Files:**
- Create: `frameworks/reverse-engineered-brand/voice-rewrite.md` (sibling prompt template)
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (insert a new `**Step 3.2b**` block between Step 3.2 and Step 3.3 under `### PHASE 3: Load`)

**Why a sibling template:** The framework's convention paragraph at `prompt.md:14-17` says sub-agent prompt content lives in sibling template files (`extract.md`, `auto-mode-preamble.md`, `competitor-dossier.md`, `render-review-html.md`). Adding a fifth sibling keeps this rule intact, AND the convention paragraph itself must be updated to enumerate the new file (see Step 2a).

**Step 1: Create the sibling template**

Write `frameworks/reverse-engineered-brand/voice-rewrite.md`:

```markdown
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
```

**Step 2a: Update the sub-agent enumeration paragraph**

In `frameworks/reverse-engineered-brand/prompt.md`, locate the paragraph at line ~16 that reads "Their prompt content lives in framework-internal supporting files (siblings of this prompt) — `extract.md`, `auto-mode-preamble.md`, `competitor-dossier.md`, `render-review-html.md`." Replace it with the same paragraph but adding `voice-rewrite.md` to the list:

> Their prompt content lives in framework-internal supporting files (siblings of this prompt) — `extract.md`, `auto-mode-preamble.md`, `competitor-dossier.md`, `render-review-html.md`, `voice-rewrite.md`.

Without this update, the enumeration drifts out of sync with the actual sibling file set.

**Step 2: Insert the orchestrator step**

Locate `**Step 3.3: Aggregate competitor dossiers.**` in `frameworks/reverse-engineered-brand/prompt.md` and insert the following block IMMEDIATELY ABOVE it (so it becomes Step 3.2b → Step 3.2c → Step 3.3 in order):

```markdown
**Step 3.2b: Brand-voice rewrite + `provided_summary` generation (NEW).**

After Step 3.2 produces `folders[].input_asks` with placeholder `provided_summary: null`, dispatch a single sub-agent (Task, `subagent_type: general-purpose`) using the prompt template at `frameworks/reverse-engineered-brand/voice-rewrite.md`. The sub-agent (a) rewrites every `ask` string in the project's brand voice, and (b) authors one `provided_summary` string per folder from Source Registry metadata.

**Inputs to the sub-agent (orchestrator constructs the prompt body):**

- The flat list of every `ask` string across all folders, tagged by `(folder_id, index, tier)` so the response can be merged back deterministically. The sub-agent MUST echo back each entry's `(folder_id, index)` tuple — those are the merge keys, not array order. Merge by tuple, NOT by position.
- Per-folder lists of `(source_id, source_type, signal_tags)` tuples from the Source Registry built in PHASE 1. **Registry metadata only — no source bodies.** This preserves the iron context-bloat guard.
- The path to the brand voice file. **Resolution order at runtime, not authorship time:**
  1. `{brand-folder-path}/guidelines/brand-voice.md` (project-relative; the brand-folder spec puts guidelines inside the brand folder)
  2. `$HOME/.claude/brand-voice.md` (global)
  3. Pass-through (neither file exists) — sub-agent returns ask strings unchanged and authors `provided_summary` plainly.

  If the resolved file exists, read it once and include its contents in the sub-agent prompt with the instruction: "Rewrite each ask string to match this voice. Preserve quantification ('3-5'), preserve typed nouns ('interview transcripts'), do not introduce new claims, do not drop or merge entries."

**Sub-agent returns:**

```json
{
  "asks": [
    {"folder_id": "strategy", "index": 0, "tier": "critical", "ask": "<voice-revised text>"},
    {"folder_id": "strategy", "index": 1, "tier": "recommended", "ask": "<voice-revised text>"}
  ],
  "provided_summaries": {
    "strategy": "1 founder interview, 2 case study drafts, no recorded sales calls.",
    "language": "...",
    "audiences": "..."
  }
}
```

The orchestrator merges the response back into `folders[]`:
- For each ask entry returned by the sub-agent, locate the original by the `(folder_id, index)` tuple — NOT by array position in the response. Replace `folders[folder_id].input_asks[index].ask` with the voice-revised string. Tier is unchanged.
- For each folder, set `folders[folder_id].provided_summary` to the corresponding string from `provided_summaries`.
- Any tuple from the input list that has no match in the response is a sub-agent omission — the verification gate in Step 3.2c catches it via Check 1 (array length parity).

**Substitute these placeholders into `voice-rewrite.md` before dispatch:**

- `{ask-list-json}` — the JSON-encoded array described above
- `{folder-sources-json}` — the JSON-encoded per-folder registry slice
- `{brand-voice-content}` — the resolved file's contents, or the literal `PASS_THROUGH` string if neither resolved path exists

**On sub-agent dispatch failure** (timeout, malformed JSON return, missing keys): abort the build with a hard-fail message naming the sub-agent and the failure mode. Do NOT silently fall back to pre-rewrite asks — the verification gate in Step 3.2c assumes the rewrite happened.
```

**Step 3: Verify with Grep**

Run Grep:
```
Pattern: Step 3.2b: Brand-voice rewrite
Path: frameworks/reverse-engineered-brand/prompt.md
output_mode: count
```
Expected: 1 match.

Run Grep:
```
Pattern: voice-rewrite\.md
Path: frameworks/reverse-engineered-brand/prompt.md
output_mode: count
```
Expected: 1 match (the dispatch line).

**Step 4: Commit**

```bash
git add frameworks/reverse-engineered-brand/voice-rewrite.md \
  frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reb): add voice-rewrite.md sub-agent template and PHASE 3.2b dispatch"
```

---

### ✅ Task 17: Add PHASE 3.2c verification gate

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (insert a new `**Step 3.2c**` block after Step 3.2b and before Step 3.3)

**Step 1: Insert the verification gate**

Locate `**Step 3.3: Aggregate competitor dossiers.**` and insert the following block IMMEDIATELY ABOVE it (Step 3.2b is already in place from Task 16; this step lands between Step 3.2b and Step 3.3):

```markdown
**Step 3.2c: Input-ask verification gate (NEW).**

Three checks run against the merged `folders[]` array. All three are hard-fail; on any failure, abort the build and print the named failure list. Do NOT proceed to write the JSON.

**Check 1 — Array length parity.** For each folder, the count of `input_asks` after Step 3.2b must equal the count before Step 3.2b. The sub-agent cannot drop or add entries. On mismatch: hard-fail with `folder: {id}, before: {N}, after: {M}`.

**Check 2 — Banned-phrase regex.** Apply the following case-insensitive regex set to every post-pass `ask` string AND every `provided_summary` string. On any match, hard-fail with `field: {ask|provided_summary}, folder: {id}, matched: {pattern}, value: {string}`:

- Em dash or en dash: `[—–]`
- "It's not X, it's Y" construction: `\bit'?s not\b[^.!?]+,?\s+(it'?s )?`
- AI buzzwords (single regex, alternation): `\b(leverage|seamless|unlock|streamline|delve|robust|cutting-edge|transformative|elevate|revolutionize|crucial|essential)\b`

**Check 3 — Tier preservation.** For each folder, walk `input_asks` by index. The `tier` at index `i` post-rewrite must equal the `tier` at index `i` pre-rewrite. On mismatch: hard-fail with `folder: {id}, index: {i}, before: {tier_before}, after: {tier_after}`.

On any check failure: print all failures (do not stop at the first), then abort. Voice failures should be rare; when they happen, the operator's recovery is "edit the brand-voice file or re-prompt the sub-agent". No silent fallback.

If all checks pass, proceed to Step 3.3.
```

**Step 2: Verify with Grep**

Run Grep:
```
Pattern: Step 3.2c: Input-ask verification gate
Path: frameworks/reverse-engineered-brand/prompt.md
output_mode: count
```
Expected: 1 match.

**Step 3: Commit**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reb): add PHASE 3.2c input-ask verification gate"
```

---

### ✅ Task 18: Bump schema_version to 0.4.0 in PHASE 3.6 JSON template and version.yaml

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (Step 3.6 block — the `version.yaml` template and the `.open-questions.json` example)

**Step 1: Edit Step 3.6**

Within `**Step 3.6: Write top-level brand-folder files.**`:

1. **`version.yaml` template.** Change `schema_version: "0.3.0"` to `schema_version: "0.4.0"`.

2. **`.open-questions.json` JSON example.** In the json code block:
   - Change `"schema_version": "0.3.0"` to `"schema_version": "0.4.0"`.
   - Add `"provided_summary"` and `"input_asks"` fields to the first (and only) folder example. Insert immediately after the `framework_dispatches` array's closing `]` and before the closing `}` of the folder:
     ```json
           "provided_summary": "1 founder interview, 2 case study drafts, no recorded sales calls.",
           "input_asks": [
             { "tier": "critical", "ask": "<voice-rewritten ask>" },
             { "tier": "recommended", "ask": "<voice-rewritten ask>" }
           ]
     ```

3. **Compute `source_counts` and `source_narratives` paragraph.** Inside Step 3.6 only (NOT elsewhere in the file), search for the literal string `v0.3.0` (no trailing `+`) and replace each occurrence with `v0.4.0`. Replace each match found — the count may be 1 or 2 depending on edits already made by substeps 1 and 2. The verification Grep at Step 2 will confirm 0 remaining `v0.3.0` matches inside Step 3.6. Do NOT touch the unrelated `v0.3.0+` reference in PHASE 3.2 Step 3.2's grade-rubric paragraph — it is scoped to grade-rubric backward compatibility and is out of scope here.

**Step 2: Verify with Grep**

Run Grep:
```
Pattern: schema_version
Path: frameworks/reverse-engineered-brand/prompt.md
output_mode: content
-n: true
```
Expected: two matches, both pointing at `0.4.0` (one in `version.yaml`, one in the `.open-questions.json` example).

Run Grep:
```
Pattern: v0\.3\.0
Path: frameworks/reverse-engineered-brand/prompt.md
output_mode: content
-n: true
```
Expected: 0 matches inside Step 3.6's content range. The grade-rubric reference outside Step 3.6 may legitimately remain — read the line of each match to confirm none are inside Step 3.6.

**Step 3: Commit**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reb): bump schema_version to 0.4.0 in PHASE 3.6 templates"
```

---

### Task 19: Extend render-review-html.md to consume input_asks and provided_summary

**Files:**
- Modify: `frameworks/reverse-engineered-brand/render-review-html.md` (Step 2 shape-warning list)

**Step 1: Edit the shape-warning list**

In `### Step 2: Read and validate the JSON`, the bulleted list under "Shape warnings (non-blocking)" currently has four entries (`source_counts`, `source_narratives`, `folders[].grade`, `folders[].summary`). Append two more entries:

```markdown
- `folders[].provided_summary` (string) — used by the per-tab Inputs Needed callout
- `folders[].input_asks` (array of `{tier, ask}`) — used by the Overview "Inputs Needed" sub-tab and the per-tab callouts
```

Also update the surrounding prose so the renderer remains the spot that names the consumers. Change the paragraph immediately above the list so it reads "v0.4.0+ fields" instead of "v0.3.0+ fields", and append a sentence: "v0.3.0 files render with empty Inputs Needed sections and a shape-warning in NOTES; no fallback is provided."

**Step 2: Verify with Grep**

Run Grep:
```
Pattern: folders\[\]\.input_asks
Path: frameworks/reverse-engineered-brand/render-review-html.md
output_mode: count
```
Expected: 1 match.

**Step 3: Commit**

```bash
git add frameworks/reverse-engineered-brand/render-review-html.md
git commit -m "docs(render): list input_asks and provided_summary as v0.4.0 shape-warning fields"
```

---

### Task 20: Template — add Inputs Needed sub-tab, per-tab callout containers, tier-badge CSS

**Files:**
- Modify: `frameworks/reverse-engineered-brand/review-template.html` (CSS in `<head>`, Overview sub-tab bar, per-folder content-tab `<div>` containers — no JS in this task; the data binding lands in Task 21)

**Step 1: Add tier-badge and callout CSS**

Locate the closing `</style>` tag in the `<head>` block (it sits a few lines above `</head>`, after the `.source-list .src-meta` rule). Immediately BEFORE `</style>`, insert:

```html
    /* Tier badges for input_asks (v0.4.0+) */
    .tier-badge {
      display: inline-block;
      font-size: 0.7rem;
      padding: 1px 8px;
      border-radius: 9999px;
      font-weight: 600;
      margin-right: 8px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .tier-critical { background: #fef2f2; color: #b91c1c; }
    .tier-recommended { background: var(--color-accent-subtle); color: var(--color-accent); }
    .tier-optional { background: var(--color-surface); color: var(--color-dimmed); border: 1px dashed var(--color-border); }

    /* Inline tab-name tag next to each ask in the consolidated list */
    .ask-tab-tag {
      display: inline-block;
      font-size: 0.72rem;
      padding: 1px 8px;
      border-radius: 6px;
      background: var(--color-muted);
      color: var(--color-dimmed);
      margin-left: 8px;
      font-family: var(--font-mono);
    }

    /* Inputs Needed list rows */
    .inputs-tier-heading {
      font-size: 0.95rem;
      font-weight: 600;
      margin: 18px 0 8px 0;
    }
    .inputs-tier-count {
      color: var(--color-dimmed);
      font-weight: 500;
      font-size: 0.85rem;
      margin-left: 6px;
    }
    .inputs-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .inputs-list li {
      padding: 6px 0;
      font-size: 0.9rem;
      line-height: 1.6;
    }
    .inputs-list a {
      color: var(--color-foreground);
      text-decoration: none;
    }
    .inputs-list a:hover { color: var(--color-accent); }

    /* Per-tab callout ("What you provided / What would strengthen this") */
    .input-callout {
      background: var(--color-accent-subtle);
      border: 1px solid var(--color-accent);
      border-radius: 12px;
      padding: 16px 20px;
      margin-bottom: 20px;
    }
    .input-callout h3 {
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--color-foreground);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin: 0 0 10px 0;
    }
    .input-callout .provided {
      font-size: 0.88rem;
      color: var(--color-secondary);
      margin: 0 0 12px 0;
      line-height: 1.6;
    }
    .input-callout ul {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .input-callout li {
      font-size: 0.88rem;
      color: var(--color-foreground);
      line-height: 1.6;
      padding: 4px 0;
    }
```

**Step 2: Add the third Overview sub-tab button**

Locate the `<div class="sub-tab-bar">` inside `<div id="panel-overview" class="tab-panel active">`. It contains two buttons (Executive Summary, Sections at a Glance). Append a third button as the last child of the sub-tab bar:

```html
      <button class="sub-tab-btn" onclick="switchSubTab('overview','overview-inputs')">Inputs Needed</button>
```

**Step 3: Add the third Overview sub-panel**

Locate `<!-- Overview / Sections at a Glance -->` and its following `<div id="sub-overview-focus" class="sub-panel">...</div>`. Immediately AFTER the closing `</div>` of `sub-overview-focus` and BEFORE the outer `</div>` that closes `panel-overview`, insert:

```html
    <!-- Overview / Inputs Needed -->
    <div id="sub-overview-inputs" class="sub-panel">
      <div class="section">
        <h2>Inputs Needed</h2>
        <p class="description">If you'd like to strengthen this report, here's what would help — organized by impact. We pulled what we could from what you sent; this list names categories of raw material that would change the result on the tab noted next to each item.</p>
        <div id="inputs-needed-critical"></div>
        <div id="inputs-needed-recommended"></div>
        <div id="inputs-needed-optional"></div>
      </div>
    </div>
```

**Step 4: Add per-tab callout containers to single-instance content tabs**

For each of the following panels — `panel-strategy`, `panel-language`, `panel-market`, `panel-proof`, `panel-design`, `panel-competitive` — insert an empty callout container `<div>` at the top of the panel body. For `panel-strategy`, `panel-language`, `panel-market`, `panel-proof`, `panel-design`, place the container immediately INSIDE the panel `<div>` and BEFORE the existing `<div id="panel-{folder}-content"></div>`. For `panel-competitive` (which has a `<div class="section">` instead of a `-content` div), place it immediately INSIDE `panel-competitive` and BEFORE the existing `<div class="section">`. Markup:

```html
    <div class="input-callout" id="callout-{folder}" style="display:none"></div>
```

Substitute `{folder}` with each panel's id stem (`strategy`, `language`, `market`, `proof`, `design`, `competitive`). The `display:none` default keeps the callout invisible until Task 21's JS populates it.

> **Multi-instance folders skip this step.** `panel-personas` and `panel-audiences` do NOT get a per-tab callout in v1 — per the design's renderer point 4, multi-instance folders can have many sub-files and collapsing per-role evidence loses signal. The Overview sub-tab still surfaces their asks via the consolidated list.

**Step 5: Structural-decision verification (machine-checkable)**

The design's mockup at `docs/mockups/2026-05-17-reverse-engineered-brand-input-asks.html` is a design-decisions document, not a UI fidelity render. Confirm via Read + Grep that the template now matches these three structural decisions from the design — no browser open required:

- **Inputs Needed is the third Overview sub-tab.** Grep the template for `switchSubTab('overview','overview-inputs')` — expect 1 match. Grep for `id="sub-overview-inputs"` — expect 1 match. The button must be appended AFTER the existing two sub-tab buttons (read the sub-tab-bar div and confirm order).
- **Per-tab callouts only on single-instance content tabs.** Grep for `class="input-callout"`; expect 6 matches, one per single-instance folder. (The literal `class="..."` form already excludes the CSS rule `.input-callout {`.) Grep `id="callout-personas"` and `id="callout-audiences"` — expect 0 matches each (multi-instance folders excluded).
- **Tier-badge CSS classes exist.** Grep for `\.tier-critical`, `\.tier-recommended`, `\.tier-optional` — expect 1 match each in the `<style>` block.

**Step 6: Verify with Grep**

Run Grep:
```
Pattern: sub-overview-inputs
Path: frameworks/reverse-engineered-brand/review-template.html
output_mode: count
```
Expected: 2 matches (sub-tab button onclick + panel id).

Run Grep:
```
Pattern: input-callout
Path: frameworks/reverse-engineered-brand/review-template.html
output_mode: count
```
Expected: ≥ 7 matches (CSS class + descendant CSS rules + 6 callout containers).

**Step 7: Commit**

```bash
git add frameworks/reverse-engineered-brand/review-template.html
git commit -m "feat(template): add Inputs Needed sub-tab and per-tab callout shells"
```

---

### Task 21: Template — wire JS to populate Inputs Needed list and per-tab callouts

**Files:**
- Modify: `frameworks/reverse-engineered-brand/review-template.html` (append a renderer function inside the existing `<script>` block)

**Step 1: Add the renderer function**

Locate the existing `<script>` block (it opens with `const OPEN_QUESTIONS = {open-questions-json};`). Within the same `<script>` block, append a new section AFTER the existing `function switchSubTab(parentId, subId) { ... }` definition (so it can use `switchTab` and DOM helpers) and BEFORE the closing `</script>` tag.

Use safe DOM construction (`document.createElement` + `textContent`) for every interpolation of `OPEN_QUESTIONS`-sourced strings. Static structural markup (`appendChild` of fresh elements) is fine. Do NOT use `innerHTML` with any user-derived value — the v0.3.0 sanitization contract from `render-review-html.md` Step 3 only sanitizes `</`; it does not neutralize HTML entities, so building DOM from `textContent` is the only safe path here.

```javascript
    // ── v0.4.0: Inputs Needed (Overview sub-tab) + per-tab callouts ──
    var FOLDER_LABEL_TO_TAB = {
      'Strategy': 'strategy',
      'Language': 'language',
      'Audiences': 'audiences',
      'Personas': 'personas',
      'Market': 'market',
      'Proof': 'proof',
      'Design': 'design',
      'Competitive': 'competitive'
    };
    var SINGLE_INSTANCE_FOLDERS = {
      strategy: true,
      language: true,
      market: true,
      proof: true,
      design: true,
      competitive: true
    };
    function iaEl(tag, opts) {
      var node = document.createElement(tag);
      opts = opts || {};
      if (opts.className) node.className = opts.className;
      if (opts.text != null) node.textContent = opts.text;
      if (opts.style) node.setAttribute('style', opts.style);
      return node;
    }
    function iaMakeTierGroup(tier, label, items) {
      var heading = iaEl('h3', { className: 'inputs-tier-heading' });
      var badge = iaEl('span', { className: 'tier-badge tier-' + tier, text: label });
      var count = iaEl('span', { className: 'inputs-tier-count', text: String(items.length) });
      heading.appendChild(badge);
      heading.appendChild(count);
      var list = iaEl('ul', { className: 'inputs-list' });
      items.forEach(function(it) {
        var li = iaEl('li');
        var link = iaEl('a', { text: it.ask });
        link.setAttribute('href', 'javascript:void(0)');
        link.addEventListener('click', function() { switchTab(it.tabId); });
        var tag = iaEl('span', { className: 'ask-tab-tag', text: it.folderLabel });
        li.appendChild(link);
        li.appendChild(tag);
        list.appendChild(li);
      });
      var wrap = document.createDocumentFragment();
      wrap.appendChild(heading);
      wrap.appendChild(list);
      return wrap;
    }
    function renderInputAsks() {
      var folders = (OPEN_QUESTIONS && OPEN_QUESTIONS.folders) || [];
      var byTier = { critical: [], recommended: [], optional: [] };
      folders.forEach(function(folder) {
        var asks = folder.input_asks || [];
        var tabId = FOLDER_LABEL_TO_TAB[folder.label] || folder.id;
        asks.forEach(function(a) {
          if (!a || !a.tier || !a.ask) return;
          if (!byTier[a.tier]) return;
          byTier[a.tier].push({ ask: a.ask, folderLabel: folder.label, tabId: tabId });
        });
      });
      var tiers = [
        ['inputs-needed-critical', 'critical', 'Critical'],
        ['inputs-needed-recommended', 'recommended', 'Recommended'],
        ['inputs-needed-optional', 'optional', 'Optional']
      ];
      tiers.forEach(function(t) {
        var container = document.getElementById(t[0]);
        if (!container) return;
        while (container.firstChild) container.removeChild(container.firstChild);
        var items = byTier[t[1]] || [];
        if (!items.length) return;
        container.appendChild(iaMakeTierGroup(t[1], t[2], items));
      });
    }
    function renderPerTabCallouts() {
      var folders = (OPEN_QUESTIONS && OPEN_QUESTIONS.folders) || [];
      folders.forEach(function(folder) {
        var tabId = FOLDER_LABEL_TO_TAB[folder.label] || folder.id;
        if (!SINGLE_INSTANCE_FOLDERS[tabId]) return;
        var container = document.getElementById('callout-' + tabId);
        if (!container) return;
        var provided = folder.provided_summary || '';
        var asks = folder.input_asks || [];
        if (!provided && !asks.length) {
          container.style.display = 'none';
          return;
        }
        while (container.firstChild) container.removeChild(container.firstChild);
        container.appendChild(iaEl('h3', { text: 'What you provided' }));
        var providedP = iaEl('p', { className: 'provided' });
        if (provided) {
          providedP.textContent = provided;
        } else {
          var emp = iaEl('em', { text: 'No source summary available.' });
          providedP.appendChild(emp);
        }
        container.appendChild(providedP);
        container.appendChild(iaEl('h3', { text: 'What would strengthen this' }));
        if (asks.length) {
          var list = iaEl('ul');
          asks.forEach(function(a) {
            if (!a || !a.tier || !a.ask) return;
            var li = iaEl('li');
            li.appendChild(iaEl('span', { className: 'tier-badge tier-' + a.tier, text: a.tier }));
            li.appendChild(document.createTextNode(a.ask));
            list.appendChild(li);
          });
          container.appendChild(list);
        } else {
          var none = iaEl('p', { className: 'provided' });
          none.appendChild(iaEl('em', { text: 'This area has no outstanding asks — coverage is sufficient.' }));
          container.appendChild(none);
        }
        container.style.display = '';
      });
    }
    document.addEventListener('DOMContentLoaded', function() {
      renderInputAsks();
      renderPerTabCallouts();
    });
```

**Step 2: Static-content verification (machine-checkable)**

Read the modified `review-template.html` and confirm the following are present (these are textual checks the executor LLM can run via Read + Grep, no browser required):

- The text `renderInputAsks` appears exactly twice (definition + DOMContentLoaded call).
- The text `renderPerTabCallouts` appears exactly twice.
- The string `OPEN_QUESTIONS.folders` (or `OPEN_QUESTIONS && OPEN_QUESTIONS.folders`) appears within both render functions — confirms the new code reads from the embedded JSON object.
- For each single-instance folder id (`strategy`, `language`, `market`, `proof`, `design`, `competitive`), the string `callout-{folder-id}` appears in both the HTML (the empty `<div>` from Task 20) and the JS (the `getElementById` call).
- Confirm no NEW `.innerHTML =` assignments (count from `frameworks/reverse-engineered-brand/review-template.html` must equal the pre-Task-20 baseline — both must be 0 unless the prior template already had `.innerHTML =` lines, in which case the count is unchanged).

End-to-end browser-rendered visual verification is deferred to `## Manual Steps (Post-Automation)` (see below) because it requires a human to open the file.

**Step 3: Verify with Grep**

Run Grep:
```
Pattern: renderInputAsks
Path: frameworks/reverse-engineered-brand/review-template.html
output_mode: count
```
Expected: 2 matches (function definition + DOMContentLoaded invocation).

Run Grep:
```
Pattern: renderPerTabCallouts
Path: frameworks/reverse-engineered-brand/review-template.html
output_mode: count
```
Expected: 2 matches.

Run Grep (confirm no `innerHTML` regression):
```
Pattern: \.innerHTML\s*=
Path: frameworks/reverse-engineered-brand/review-template.html
output_mode: count
```
Expected: count unchanged from the pre-Task-20 baseline. If the count rose, the new code violated the DOM-construction discipline from Decision 8 — fix before commit.

**Step 4: Commit**

```bash
git add frameworks/reverse-engineered-brand/review-template.html
git commit -m "feat(template): wire DOM-safe JS for Inputs Needed and per-tab callouts"
```

---

### Task 22: Run full test suite as final verification

**Files:**
- None modified.

**Step 1: Run all touched tests**

Run: `pytest tools/test_input_asks_coverage.py tools/test_oq_schema_v040.py tools/test_sync_framework_frontmatter.py -v`
Expected: All tests PASS.

**Step 2: Confirm input_asks declarations are present where expected**

Run Grep (no leading `^` anchor so indented YAML inside fenced blocks still matches):
```
Pattern: input_asks:
Path: frameworks
type: md
output_mode: files_with_matches
```
Expected: at least 9 files — the 7 framework `prompt.md` files in `REQUIRED_FRAMEWORKS`, plus `frameworks/reverse-engineered-brand/audience-taxonomy.md` (Task 9 `## Ideal inputs` block), plus `frameworks/reverse-engineered-brand/prompt.md` (Task 14 inline `competitive_context_input_asks` + Task 14b's three slice-specific inline blocks). May also match `frameworks/reverse-engineered-brand/voice-rewrite.md` if the template content includes the example payload.

**Step 3: Confirm no innerHTML regression in the template**

Run Grep:
```
Pattern: \.innerHTML\s*=
Path: frameworks/reverse-engineered-brand/review-template.html
output_mode: count
```
Expected: unchanged from the pre-Task-20 baseline. The plan's discipline (Decision 8) is `createElement` + `textContent` only.

**Step 4: No commit required** — this is verification only.

---

## Manual Steps (Post-Automation)

> Complete these once the autopilot has finished Task 22. They cannot run inside `claude -p` because they require a browser session.

### Visual smoke test of the new Inputs Needed surface

1. From the repo root, copy `frameworks/reverse-engineered-brand/review-template.html` to a scratch file (e.g., `/tmp/smoke-review.html`).
2. Open `frameworks/reverse-engineered-brand/test-fixtures/render/fixture-tiny.json`. Substitute its JSON for the literal token `{open-questions-json}` in the scratch file. Substitute `{brand-folder-path}` with any string (e.g., `/tmp/demo-brand`). Substitute `{org-name}` with any string (e.g., `Demo`).
3. Open the scratch file in a browser.
4. Confirm by inspection:
   - Overview tab shows three sub-tabs (Executive Summary, Sections at a Glance, **Inputs Needed**).
   - Inputs Needed shows tiered headings with badges (Critical / Recommended / Optional).
   - Clicking an ask link navigates to the matching tab.
   - Strategy (and other single-instance) tabs show a callout card above their existing content with "What you provided" + "What would strengthen this".
   - Personas and Audiences tabs show NO callout card.
5. Repeat the substitution with `fixture-realistic.json` and `fixture-stress.json` to spot-check at larger volumes.

If anything looks broken, file a Kanban entry per `skills/_shared/kanban-entry-format.md` and reference this plan.

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Test runner | pytest in `tools/test_*.py` | New e2e/ test; jsonschema validator library; no tests |
| 2 | New test file location | `tools/test_input_asks_coverage.py` + `tools/test_oq_schema_v040.py` | Single combined file; per-framework test files |
| 3 | Per-framework frontmatter tasks (one task each) | Seven separate commit tasks (Tasks 2-8) | One bulk task editing all seven frontmatters |
| 4 | Sub-agent prompt body location | Inline in Step 3.2b text, not a sibling template file | New `voice-rewrite.md` template alongside `extract.md`/`competitor-dossier.md` |
| 5 | Brand-voice file resolution order | Project-relative first, then `$HOME/.claude/brand-voice.md` | Hardcoded global path; user-supplied path arg |
| 6 | Multi-slice folder behavior in Task 15 | Document single-slice and multi-slice cases explicitly | Defer multi-slice to a later phase |
| 7 | Per-tab callout containers in HTML | Empty `<div>` per single-instance tab, populated by template JS at load | Server-side render-time string assembly inside the renderer sub-agent |
| 8 | DOM construction discipline in Task 21 | `createElement` + `textContent` only; no `.innerHTML =` with user data; helpers prefixed `ia*` to avoid template namespace collisions | Single `innerHTML` write with manual HTML-escape helper |
| 9 | Slice-specific input_asks for alternatives / clinical-evidence / compliance | Inline in `prompt.md` PHASE 2 Step 2.1 as `alternatives_input_asks` / `clinical_evidence_input_asks` / `compliance_input_asks` arrays (Task 14b) | Extend `5-components-positioning` and `proof-points-audit` frontmatter with per-slice subkeys |

### Appendix: Decision Details

#### Decision 1: Test runner

**Chose:** pytest in `tools/test_*.py`, matching the existing `tools/test_sync_framework_frontmatter.py` convention.

**Why:** The repo already has two distinct pytest setups — `tools/test_*.py` (which import sibling modules directly without a `conftest.py` or `pyproject.toml`) and `e2e/tests/test_*.py` (full pytest harness with its own config). The work here tests artifact structure (frontmatter YAML parsing, fixture JSON shape), not LLM behavior, so the lightweight `tools/` pattern fits. Reusing the pattern keeps test invocation identical to what the implementer is already used to.

**Alternatives rejected:**
- **New e2e/ test:** `e2e/` is reserved for promptfoo-driven LLM behavior evals; structural artifact tests don't belong there.
- **jsonschema library:** Adding a runtime dependency for one schema (in a repo with no root-level `requirements.txt`) is overkill. Hand-rolled assertions read better and have no install footprint.
- **No tests:** Schema bumps and frontmatter additions are the changes that silently break consumers (the orchestrator reads frontmatter; the renderer reads schema fields). The cost of an automated coverage check is a few dozen lines; the cost of a missing entry is a silently empty Inputs Needed section on a real client build.

#### Decision 2: New test file location

**Chose:** Two new files in `tools/`: one for frontmatter coverage, one for v0.4.0 schema fixtures.

**Why:** The two tests target different artifact classes (markdown frontmatter vs. JSON fixtures) and have different failure modes. Splitting keeps each file focused and makes it easy to skip one if the other is under active edit.

**Alternatives rejected:**
- **Single combined file:** Would conflate two unrelated assertion sets. The frontmatter test parametrizes over framework ids; the fixture test parametrizes over fixture names. Mixing them makes the parametrize lists harder to read.
- **Per-framework test files:** Seven `test_input_asks_<id>.py` files explode the directory listing without adding signal — `pytest.mark.parametrize` already gives per-framework granularity.

#### Decision 3: Per-framework frontmatter tasks

**Chose:** Seven separate commit tasks (Tasks 2-8), one per framework.

**Why:** Each framework is its own logical unit, owned by a different domain expert, with its own catalog of asks. Splitting per framework matches the natural rollback boundary (if one framework's asks need rewording, `git revert` hits exactly that commit) and matches the granularity rule in the writing-plans skill (bite-sized tasks, ~5-15 minutes each). The TDD coverage test from Task 1 gives each task its own per-framework failing test case, so progress is visible per commit.

**Alternatives rejected:**
- **One bulk task editing all seven frontmatters in one commit:** Violates the bite-sized-task rule. Also makes a single failing assertion harder to attribute to a specific edit.

#### Decision 4: Sub-agent prompt body location

**Chose:** New sibling template file `frameworks/reverse-engineered-brand/voice-rewrite.md`, dispatched from PHASE 3.2b. Per Round 1 critique (Architect M1), this restores consistency with the convention documented at `prompt.md:14-17` that all sub-agent prompts live in sibling files.

**Why:** The framework's prompt body explicitly says "All sub-agents are dispatched via the Task tool ... Their prompt content lives in framework-internal supporting files (siblings of this prompt)." Inlining the voice-rewrite body would force either an exception note in that convention paragraph or a silent divergence. The sibling file is short (~40 lines), matches the existing `extract.md`/`competitor-dossier.md`/`render-review-html.md` shape, and keeps the orchestrator prompt readable.

**Alternatives rejected:**
- **Inline in Step 3.2b:** Mirrors `competitive_context_input_asks` (which IS data, not a sub-agent prompt). The convention distinguishes "data the orchestrator reads" (inline OK) from "prompt content dispatched to a sub-agent" (sibling file). Inlining would conflate the two patterns.

#### Decision 5: Brand-voice file resolution order

**Chose:** Project-relative (`{brand-folder-path}/guidelines/brand-voice.md`) first, then global (`$HOME/.claude/brand-voice.md`), then pass-through.

**Why:** Matches the resolution order documented in `skills/brainstorming/authoring-critique-checklist.md` (project-relative `brand/guidelines/brand-voice.md` first; `~/.claude/brand-voice.md` fallback). Resolving at runtime — not at framework authorship time — fixes the portability issue named in the design doc: the framework ships portably for any user, regardless of which brand-voice files they have. Note: `docs/brand-folder-spec.md` separately defines `language/voice.md` inside the brand folder; that file is the framework-authored *voice slice*, distinct from the *brand-voice contract* used to rewrite client-facing copy. The pass-through fallback handles the case where neither file exists.

**Alternatives rejected:**
- **Hardcoded `~/.claude/brand-voice.md`:** Breaks portability for users who maintain a project-specific voice file.
- **User-supplied path arg:** Would require a PHASE 0 intake change, which the design's Hard Constraint 1 forbids.

#### Decision 6: Multi-slice folder behavior in Task 15

**Chose:** Document single-slice and multi-slice behavior explicitly in the same Step 3.2 bullet, including which folders are multi-slice.

**Why:** The orchestrator is an LLM following the prompt as documentation. Without an explicit enumeration of which folders are multi-slice, the LLM will guess from context and likely miss `proof/` (which can host proof-points + optional clinical + optional compliance, not just one). Listing them inline makes the behavior deterministic regardless of context window state at PHASE 3.2.

**Alternatives rejected:**
- **Defer multi-slice to a later phase:** Multi-slice folders exist in real builds today (the `strategy/` folder always hosts both positioning and narrative in the dispatch table at `prompt.md:150-162`). Deferring would ship a feature that's broken for the most-common case.

#### Decision 7: Per-tab callout containers in HTML

**Chose:** Add empty `<div class="input-callout">` containers to each single-instance tab in the template; JS populates them at `DOMContentLoaded`.

**Why:** Keeps the rendering boundary consistent with the existing template pattern. The current `panel-strategy-content`, `panel-language-content`, etc. divs are also JS-populated at load. Adding pre-rendered HTML strings would require teaching the renderer sub-agent to generate HTML — which it currently does not do; it only does token substitution per `render-review-html.md`'s contract. Keeping rendering in template JS preserves the renderer's narrow responsibility.

**Alternatives rejected:**
- **Server-side render-time string assembly inside the renderer sub-agent:** Would expand the renderer's contract from "substitute three tokens, verify, open" to "iterate folders[].input_asks and build HTML strings". This is a larger surface change and breaks the sanitization model that the renderer's verify-before-open contract depends on.

#### Decision 8: DOM construction discipline in Task 21

**Chose:** Use `document.createElement` + `textContent` + `appendChild` exclusively for any node carrying `OPEN_QUESTIONS`-derived strings. No `.innerHTML =` assignments with user data.

**Why:** The renderer's existing sanitization (per `render-review-html.md` Step 3) only escapes `</` to prevent script-tag breakouts. It does NOT HTML-encode angle brackets, quotes, or ampersands. A user-supplied brand voice file or an LLM-rewritten ask string could contain those characters legitimately ("&" in copy, "<" in code spans). The browser's text node API handles them safely. Using `textContent` is the standard XSS prevention pattern and removes any need for a hand-rolled escape helper that future edits could forget to apply.

**Alternatives rejected:**
- **Single `innerHTML` write with manual HTML-escape helper:** Smaller code, but every future edit must remember to call the helper. The DOM-construction style makes the safety property structural rather than disciplinary.

#### Decision 9: Slice-specific input_asks for alternatives, clinical-evidence, compliance

**Chose:** Inline arrays in `prompt.md` PHASE 2 Step 2.1 (`alternatives_input_asks`, `clinical_evidence_input_asks`, `compliance_input_asks`), aggregated into the matching folder at PHASE 3.2 (Task 14b).

**Why:** Three slices in the slice-mapping table have catalog asks that differ from their owning framework's asks: `market/alternatives.md` is owned by `5-components-positioning` but the design specifies distinct cost-of-inaction asks; `proof/clinical-evidence.md` and `proof/compliance.md` are owned by `proof-points-audit` (healthcare extension) but the design specifies regulated-industry-specific asks (PMID/DOI, certifications). Putting these in the owning framework's frontmatter would either (a) duplicate the asks across the framework's primary slice and the variant slice, or (b) force a per-slice frontmatter sub-schema that no current consumer reads. Inlining in `prompt.md` mirrors the existing `competitive_context_input_asks` pattern from Task 14.

**Alternatives rejected:**
- **Per-slice frontmatter subkeys:** Would require a new frontmatter shape (e.g., `input_asks_by_slice: { "strategy/positioning.md": [...], "market/alternatives.md": [...] }`) that the coverage test, sync script, and orchestrator aggregation would all need to support. The inline option ships the same behavior with no schema surface change.


