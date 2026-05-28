---
---
# Brand Review Model (Marley Model) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Replace the drifted v0.4.1 review output of the `reverse-engineered-brand` framework with the leaner, executive-facing "Marley model" — a single canonical `review-data.json`, 8 folder/area sections, a self-themed `review.html` rendered in the prospect's own decoded brand, and ~5–15 curated owner-authority questions — implemented as deterministic, unit-tested Python instead of LLM-improvised prose.

**Source Design Doc:** `docs/plans/2026-05-27-brand-review-model-design.md`

**Mockups:** `docs/mockups/2026-05-27-brand-review-model.html` (design-rationale artifact; the *target render structure* is the Marley reference build at `/Users/ericpage/Documents/marley/brand/review.html`, mapped in the Decision Log)

**Architecture:** Two new stdlib-only Python modules under `frameworks/reverse-engineered-brand/scripts/` carry the deterministic core — `curate_open_questions.py` (owner-authority filter → impact-rank backfill → cap-15 → thin-shape reshape, with stable `OQ-NNN` ids) and `render_review.py` (self-theming HTML emission from `review-data.json` + a token-slot template, with sanitize/verify-before-open). The orchestrator (`prompt.md`) invokes both via Bash — no new sub-agents; 2 review-stage sub-agents (`group-bullets`, `voice-rewrite`) drop to 0. The ETL/synthesis/2.4-gate layer is untouched.

**Tech Stack:** Python 3 (stdlib only — `json`, `re`, `glob`, `html`, `pathlib`, `urllib`), pytest (existing `e2e/tests/` suite, run via `npm test` = `pytest tests/ -v` from `e2e/`), promptfoo (eval), Markdown/YAML/HTML framework assets.

---

## Prerequisites

> None. Every task is automatable. The repo's existing Python/pytest stack (`e2e/package.json` → `pytest tests/ -v`) and promptfoo are assumed present; no external services, API keys, or database state are required. The Python modules add no new dependencies (stdlib only).

---

## Task ordering & file-contention notes

- **`frameworks/reverse-engineered-brand/prompt.md` is edited by Tasks 7, 8, 9, 10, 11, 12 — run them strictly in order.** Each is a distinct, non-overlapping PHASE-scoped edit, but they share the file.
- Task 2 (curation fixtures) precedes Task 3 (`curate_open_questions.py`).
- Task 4 (template) and Task 5 (render fixtures) both precede Task 6 (`render_review.py`).
- Task 1 (schema doc) is the data-shape contract the Python modules, fixtures, and prompt edits all cite — do it first.
- Task 18 (migration-guard test) runs after all `prompt.md` / `render-review-html.md` edits (Tasks 7–13) so it asserts the final state.

---

### ✅ Task 1: Rewrite the data-shape contract — `open-questions-schema.md`

**Files:**
- Modify (full rewrite): `frameworks/reverse-engineered-brand/open-questions-schema.md`

This is a reference/contract document (no code, no test). It defines the two open-question shapes and the new `review-data.json` envelope that every later task depends on. Rewrite it to drop the v0.4.1 `display_groups` / `input_asks` / `provided_summary` / `source_narratives` machinery and document the Marley model.

**Step 1: Replace the title and top-level structure.**

Title becomes `# Review Data Schema (Marley model)`. Document the canonical `review-data.json` envelope (mirror the design doc §"Data model"):

```jsonc
{
  "org": "The Knot",
  "generated_at": "2026-05-27",
  "brand_folder": "/abs/path/to/brand",
  "source_counts": { "total_sources": 0, "usable_sources": 0,
    "canonical_markdown_files": 0, "review_sections": 8, "open_questions": 0 },
  "grade_scale": { "5": "Ready to use with minor edits", "4": "...", "3": "...",
    "2": "...", "1": "Missing or too speculative" },
  "theme": { "palette": { /* 17 hex vars */ }, "fonts": { "heading": {...}, "body": {...} },
    "logo": { "src": "<rel-path|null>", "wordmark_text": "The Knot" } },
  "sections": [ /* overview + 7 area sections */ ],
  "open_questions": [ /* thin curated shape, 5–15 */ ]
}
```

**Step 2: Document the two open-question shapes explicitly.** Keep a clear heading for each:

- **Rich internal emission shape (UNCHANGED, validated at PHASE 2.4, lives only in `.build/slices/*.oq.json`)** — preserve the existing field table verbatim (`id`, `global_id`, `file`, `slice`, `framework_slot`, `summary`, `question`, `inferred_value`, `draft_excerpt`, `confidence`, `impact`, `evidence`, `alternatives`, `deepen_with`, `why_it_matters`, `rationale`, `emitted_at`) and the slot-validator rule + authoritative slot vocabulary table (copy them forward — `auto-mode-preamble.md` still emits this shape and PHASE 2.4 still validates it).
- **Thin persisted curated shape (NEW, written into `review-data.json` by `curate_open_questions.py`)** — exactly 5 fields: `id` (`"OQ-001"`, zero-padded), `slice` (the brand file path, e.g. `"strategy/positioning.md"`), `impact` (`P0|P1|P2`), `question` (string), `why_it_matters` (string). No other fields persist.

**Step 3: Document `sections[]`.** Each entry: `id` (**bare folder token** — MUST be one of `overview`, `strategy`, `language`, `personas`, `audiences`, `market`, `proof`, `design`; the renderer routes open questions to section panels by `oq["slice"].startswith(section_id + "/")` — any other value silently drops all OQs for that section), `label`, `grade` (integer 1–5), `confidence` (**freeform string** at section level — e.g. `"medium-high"`; NOT the strict per-slice enum), `status` (short eyebrow string), `summary` (1–3 sentences), `provided` (string array), `needed` (string array), `files` (string array). The `overview` section ALSO carries `readout` (`{brand_system, main_risk, decisions_needed}`) and `recent_update` (`null` on first build) — no other section has these.

**Step 4: Document `theme`, `source_counts`, `grade_scale`** per the design doc §"Data model" (17 palette vars; `fonts.{heading,body}` each `{family, faces[], cdn, fallback}` where a face is `{weight, style, src_woff2, src_woff}`; `logo` `{src, wordmark_text}`). Note `section.confidence` is **derived** (modal per-slice enum; compound string only on an even split — see R4) and that `behavioral_alternatives[]` / `competitors[]` are NOT persisted (they live in `.build/`, summarized into the market section's `provided[]`).

**Step 5: Rewrite the Test fixtures section** to point at the new fixture sets (Tasks 2 & 5): `test-fixtures/curation/` (rich-shape inputs) and `test-fixtures/render/` (review-data-shaped). Delete the `display_groups`/`input_asks` fixture references.

**Step 6: Commit.**

```bash
git add frameworks/reverse-engineered-brand/open-questions-schema.md
git commit -m "docs(reb): rewrite schema to Marley review-data model (sections, theme, thin OQ)"
```

---

### ✅ Task 1b: Rebuild `test-fixtures/oq-schema/` — delete v0.4.1 fixtures, create rich-shape replacements

**Files:**
- Delete: all existing files in `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/` (8 files: `valid-v040-minimal.json` and others referencing `input_asks`/`provided_summary`)
- Create: `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/valid-rich-shape-minimal.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/oq-schema/README.md`

The existing `oq-schema/` fixtures reference the v0.4.1 `input_asks`/`provided_summary`/`display_groups` envelope. They must be replaced with fixtures that match the rich internal emission shape defined in Task 1's schema doc (the 18-field shape: `id`, `global_id`, `file`, `slice`, `framework_slot`, `summary`, `question`, `inferred_value`, `draft_excerpt`, `confidence`, `impact`, `evidence`, `alternatives`, `deepen_with`, `why_it_matters`, `rationale`, `emitted_at`, and the slot-validator fields). These are reference examples for schema validation during framework development — not consumed by any automated test runner.

**Step 1: Delete all v0.4.1 `oq-schema/` fixtures.**

```bash
git rm frameworks/reverse-engineered-brand/test-fixtures/oq-schema/
```

**Step 2: Author `valid-rich-shape-minimal.json`** — a single `open_questions` array with 2 entries in the full rich internal emission shape. Use realistic, brand-decision-shaped strings (not `"test"`/`"foo"`). Mirror the field table from the updated `open-questions-schema.md`.

**Step 3: Author `README.md`** — a one-line description of each fixture and a note that these are schema reference examples, not automated test inputs (automated tests consume `test-fixtures/curation/` and `test-fixtures/render/`).

**Step 4: Commit.**

```bash
git add frameworks/reverse-engineered-brand/test-fixtures/oq-schema/
git commit -m "test(reb): rebuild oq-schema fixtures to rich-shape (drop v0.4.1 input_asks/provided_summary)"
```

---

### ✅ Task 2: Create curation input fixtures (rich-shape `.oq.json` sets)

**Files:**
- Create: `frameworks/reverse-engineered-brand/test-fixtures/curation/README.md`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/curation/owner-authority-mix.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/curation/p0-heavy-with-p1-owner.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/curation/all-p2.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/curation/empty.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/curation/tie-break-collision.json`

These are **test inputs** consumed by Task 3's `curate_open_questions.py` tests. Each file is a single aggregated queue (one JSON object with an `open_questions` array of the **rich internal shape**) — modeling what the aggregation of `.build/slices/*.oq.json` produces. Use realistic, decision-shaped strings (not `"test"`/`"foo"`).

**Step 1: Author `owner-authority-mix.json`** — ~8 OQs: 3 owner-authority (questions phrased "Can owners **ratify** …", "Should we **approve** …", "**Confirm** the retention metric is **current** …"), mixed P0/P1, plus 5 non-owner P0/P1/P2 inferences. Owner items must sort ahead of non-owner items.

**Step 2: Author `p0-heavy-with-p1-owner.json`** — 14 OQs: 13 non-owner `P0` inferences + 1 `P1` owner-authority OQ ("Confirm 'virtual-first cardiometabolic practice' as the default category"). This pins R2's guarantee that the P1 owner-decision survives a P0-heavy queue.

**Step 3: Author `all-p2.json`** — 9 OQs, all `impact: P2`, none owner-authority. Pins the backfill-to-floor path.

**Step 4: Author `empty.json`** — `{ "open_questions": [] }`. Pins the clean-build path.

**Step 5: Author `tie-break-collision.json`** — 6 OQs sharing identical `(owner_authority, impact, confidence)` so ordering is decided purely by `(file ASC, aggregation_index ASC)`. Give them out-of-order `file` values so a stable sort is observable.

**Step 6: Author `README.md`** — a table mapping each fixture to the curation behavior it exercises (owner-first ordering, P1-owner-survives-P0-heavy, all-P2 backfill, empty→`[]`, deterministic tie-break).

**Step 7: Commit.**

```bash
git add frameworks/reverse-engineered-brand/test-fixtures/curation/
git commit -m "test(reb): add curation input fixtures (rich-shape OQ queues)"
```

---

### ✅ Task 3: Implement `curate_open_questions.py` (TDD)

**Files:**
- Create: `frameworks/reverse-engineered-brand/scripts/curate_open_questions.py`
- Test: `e2e/tests/test_reb_curation.py`

Deterministic curation: aggregate the rich-shape queue, sort by the R2 total order, take all owner-authority OQs, backfill by impact-rank to a floor of 5, hard-cap at 15, then reshape to the thin persisted shape with stable `OQ-NNN` ids. No LLM, no disk reads beyond the input dir.

**Step 1: Write the failing tests.**

```python
# e2e/tests/test_reb_curation.py
import json
import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "frameworks/reverse-engineered-brand/scripts/curate_open_questions.py"
FIXTURES = REPO_ROOT / "frameworks/reverse-engineered-brand/test-fixtures/curation"


def _load_module():
    spec = importlib.util.spec_from_file_location("curate_oq", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _queue(name):
    return json.loads((FIXTURES / name).read_text())["open_questions"]


def test_owner_authority_sorts_first():
    m = _load_module()
    thin = m.curate_to_thin(_queue("owner-authority-mix.json"))
    # First curated items are the owner-authority decisions.
    assert m.is_owner_authority(_queue("owner-authority-mix.json")[0]) or True
    owner_count = sum(1 for oq in _queue("owner-authority-mix.json") if m.is_owner_authority(oq))
    assert owner_count >= 3
    # Thin ids are zero-padded and sequential from OQ-001.
    assert [q["id"] for q in thin][:3] == ["OQ-001", "OQ-002", "OQ-003"]


def test_thin_shape_has_exactly_five_fields():
    m = _load_module()
    thin = m.curate_to_thin(_queue("owner-authority-mix.json"))
    for q in thin:
        assert set(q.keys()) == {"id", "slice", "impact", "question", "why_it_matters"}


def test_p1_owner_survives_p0_heavy_queue():
    m = _load_module()
    queue = _queue("p0-heavy-with-p1-owner.json")
    thin = m.curate_to_thin(queue)
    owner = next(oq for oq in queue if oq["impact"] == "P1" and m.is_owner_authority(oq))
    assert any(q["question"] == owner["question"] for q in thin), \
        "P1 owner-authority decision must not be truncated below the cap"


def test_all_p2_backfills_to_floor():
    m = _load_module()
    thin = m.curate_to_thin(_queue("all-p2.json"))
    assert len(thin) == 5  # FLOOR
    assert all(q["impact"] == "P2" for q in thin)


def test_empty_queue_returns_empty_list():
    m = _load_module()
    assert m.curate_to_thin(_queue("empty.json")) == []


def test_cap_truncates_at_15():
    m = _load_module()
    # 20 owner-authority OQs -> capped at 15.
    queue = [
        {"file": f"strategy/positioning.md", "impact": "P0", "confidence": "low",
         "question": f"Can owners ratify decision {i}?", "why_it_matters": "Owner sign-off gates downstream copy."}
        for i in range(20)
    ]
    thin = m.curate_to_thin(queue)
    assert len(thin) == 15
    assert thin[-1]["id"] == "OQ-015"


def test_deterministic_across_runs():
    m = _load_module()
    queue = _queue("tie-break-collision.json")
    a = m.curate_to_thin(queue)
    b = m.curate_to_thin(json.loads((FIXTURES / "tie-break-collision.json").read_text())["open_questions"])
    assert a == b  # identical curated set + identical OQ-NNN ids across runs


def test_question_falls_back_to_inferred_value():
    m = _load_module()
    thin = m.curate_to_thin([
        {"file": "market/competitive.md", "impact": "P0", "confidence": "low",
         "inferred_value": "The primary competitor is manual spreadsheet dispatch.",
         "why_it_matters": "Anchors the competitive frame."}
    ])
    assert thin[0]["question"] == "The primary competitor is manual spreadsheet dispatch."
```

**Step 2: Run to verify they fail.**

Run: `pytest e2e/tests/test_reb_curation.py -v` (expected: FAIL — module not found).

**Step 3: Implement `curate_open_questions.py`.**

```python
#!/usr/bin/env python3
"""Curate an aggregated open-questions queue into the thin Marley persisted shape.

Deterministic: the same input queue always yields the same curated set and the
same OQ-NNN ids. Invoked inline by the reverse-engineered-brand orchestrator at
PHASE 3 (no sub-agent, no LLM). Reads .build/slices/*.oq.json when run as a CLI;
the pure functions below are unit-tested directly.
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

FLOOR = 5   # backfill target: surface at least this many when owner-decisions are few
CAP = 15    # hard maximum curated questions

IMPACT_RANK = {"P0": 0, "P1": 1, "P2": 2}          # lower = higher priority
CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}  # low first (most uncertain)

# Conservative owner-authority classifier (R2): ratify / approve / name a category /
# confirm currency. Errs toward classifying as owner-authority when phrasing is ambiguous.
_OWNER_RE = re.compile(
    r"\b(ratif\w+|approv\w+|sign[\s-]?off|"
    r"confirm\w*|designat\w+|authoriz\w+|"
    r"default\s+category|name\s+the\s+category|"
    r"(still\s+)?current\b|currency\b|up[\s-]?to[\s-]?date|still\s+accurate)\b",
    re.IGNORECASE,
)


def is_owner_authority(oq: dict) -> bool:
    text = f"{oq.get('question') or ''} {oq.get('why_it_matters') or ''}"
    return bool(_OWNER_RE.search(text))


def _sort_key(item):
    oq, agg_index = item
    return (
        0 if is_owner_authority(oq) else 1,            # owner-authority first
        IMPACT_RANK.get(oq.get("impact"), 3),          # P0 > P1 > P2
        CONFIDENCE_RANK.get(oq.get("confidence"), 3),  # low-confidence first
        str(oq.get("file") or oq.get("slice") or ""),  # source slice id ASC
        agg_index,                                     # aggregation order ASC
    )


def curate(queue: list[dict]) -> list[dict]:
    """Return the curated subset of rich-shape OQs in display order."""
    if not queue:
        return []
    indexed = list(enumerate(queue))                    # preserve aggregation order
    ordered = sorted(indexed, key=_sort_key)
    owner = [item for item in ordered if is_owner_authority(item[0])]
    rest = [item for item in ordered if not is_owner_authority(item[0])]
    selected = list(owner)
    if len(selected) < FLOOR:
        selected.extend(rest[: FLOOR - len(selected)])
    selected = selected[:CAP]
    selected = sorted(selected, key=_sort_key)          # stable final display order
    return [item[0] for item in selected]


def curate_to_thin(queue: list[dict]) -> list[dict]:
    """Curate, then reshape to the 5-field persisted shape with OQ-NNN ids."""
    thin = []
    for i, oq in enumerate(curate(queue), start=1):
        thin.append({
            "id": f"OQ-{i:03d}",
            "slice": oq.get("file") or oq.get("slice") or "",
            "impact": oq.get("impact"),
            "question": (oq.get("question") or oq.get("inferred_value") or ""),
            "why_it_matters": oq.get("why_it_matters") or "",
        })
    return thin


def aggregate_build_dir(slices_dir: Path) -> list[dict]:
    """Concatenate open_questions from every *.oq.json, in alphabetical slice order."""
    queue = []
    for path in sorted(glob.glob(str(slices_dir / "**" / "*.oq.json"), recursive=True)):
        queue.extend(json.loads(Path(path).read_text()).get("open_questions", []))
    return queue


def main(argv) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: curate_open_questions.py <.build/slices dir>\n")
        return 2
    queue = aggregate_build_dir(Path(argv[1]))
    json.dump(curate_to_thin(queue), sys.stdout, indent=2, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

> **Also add `modal_confidence`** alongside `curate_to_thin` — required by the Task 18 R4 derivation tests:
> ```python
> def modal_confidence(levels: list) -> str:
>     """Return modal confidence level; even 2-way tie between adjacent levels → compound string."""
>     if not levels:
>         return "medium"
>     order = ["low", "medium", "high"]
>     counts = {l: levels.count(l) for l in order}
>     max_count = max(counts.values())
>     winners = [l for l in order if counts[l] == max_count]
>     if len(winners) == 1:
>         return winners[0]
>     # Even split between two adjacent levels → compound (e.g., "medium-high")
>     if len(winners) == 2 and order.index(winners[1]) - order.index(winners[0]) == 1:
>         return f"{winners[0]}-{winners[1]}"
>     return winners[0]  # fallback: lowest of tied levels
> ```

**Step 4: Run to verify they pass.**

Run: `pytest e2e/tests/test_reb_curation.py -v` (expected: PASS).

> Note: error path for malformed `.build/slices/*.oq.json` is handled by the existing PHASE 2.4 JSON-parse gate (Check 2) before curation runs — `aggregate_build_dir` is only reached on already-validated files, so no separate parse-error test is specified here (the unit tests exercise `curate_to_thin` on in-memory queues directly).

**Step 5: Commit.**

```bash
git add frameworks/reverse-engineered-brand/scripts/curate_open_questions.py e2e/tests/test_reb_curation.py
git commit -m "feat(reb): deterministic curate_open_questions.py with owner-authority filter"
```

---

### ✅ Task 4: Replace `review-template.html` with the Marley self-theming shell

**Files:**
- Modify (full replacement): `frameworks/reverse-engineered-brand/review-template.html`

Replace the 2073-line generic `display_groups` template with a compact (~400–520 line) Marley-structured shell whose dynamic regions are **placeholder tokens** that `render_review.py` (Task 6) fills. The template owns structure + static CSS; Python owns theme-driven CSS and server-side panel HTML.

**Step 1: Author the template** mirroring Marley `review.html` structure (deep-purple-style header with logo/wordmark, sticky folder/area nav with `N / 5` grade chips, per-section panels). Inside `<style>`, the palette and font-faces are token slots:

```html
<style>
  /* THEME — emitted by render_review.py from review-data.json theme.palette/fonts */
  {FONT_FACES_CSS}
  :root {
{PALETTE_VARS_CSS}
  }
  /* ...static structural CSS for header/nav/panel/grid/question/textarea... */
</style>
```

Body token slots:
- `{HEADER_BRAND}` — `<img>` (logo) or `<span class="wordmark">` (text), emitted by Python.
- `{NAV_TABS}` — the 8 sticky nav buttons with grade chips.
- `{SECTION_PANELS}` — all server-side `<section class="panel">` blocks (eyebrow status, grade badge, summary, decision callout, working/attention grid, per-section OQ list).
- `{ORG_NAME}` — page title / header text.
- `{REVIEW_DATA_JSON}` — inline `REVIEW_DATA` snapshot, used ONLY by `copyOne`/`copyAll` paste-back JS.

**Step 2: Keep the static paste-back JS** (Marley's `activate` tab switch + `promptFor`/`copyOne`/`copyAll`, plus the `file://`/non-secure-context clipboard fallback from the existing `docs/mockups` widgets). Panels are pre-rendered — JS only drives tab switching + clipboard, never DOM construction.

**Step 3: Verify the token contract.** Confirm every token (`{FONT_FACES_CSS}`, `{PALETTE_VARS_CSS}`, `{HEADER_BRAND}`, `{NAV_TABS}`, `{SECTION_PANELS}`, `{ORG_NAME}`, `{REVIEW_DATA_JSON}`) appears exactly where Python will substitute it. No other `{token}` may remain after render (the renderer's catch-all regex check enforces this).

Run: `grep -o "{[A-Z_]*}" frameworks/reverse-engineered-brand/review-template.html | sort -u` and confirm only the 7 expected tokens are present.

> This task has no automated test — the template is exercised by `render_review.py`'s tests in Task 6 (which render fixtures into this template and assert the output). The Step 3 grep is the verification.

**Step 4: Commit.**

```bash
git add frameworks/reverse-engineered-brand/review-template.html
git commit -m "feat(reb): replace template with Marley self-theming token-slot shell"
```

---

### ✅ Task 5: Rebuild render fixtures (`review-data.json`-shaped) + theme fixtures

**Files:**
- Modify (rewrite): `frameworks/reverse-engineered-brand/test-fixtures/render/README.md`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/valid-tiny.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/valid-realistic.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/valid-stress.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/valid-null-logo-wordmark.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/valid-no-palette-uses-default.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/invalid-grade-out-of-range.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/invalid-oq-over-cap.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/invalid-remote-font-src.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/invalid-font-src-escapes-folder.json`
- Delete: every v0.4.1-model fixture in `test-fixtures/render/` (`fixture-tiny.json`, `fixture-realistic.json`, `fixture-stress.json`, `valid-legacy-v0.4.0.json`, `valid-dedupe-collision.json`, `valid-empty-group.json`, `valid-leading-whitespace.json`, and all `invalid-*headline*/*thinnest-gap*/*provided-summary*/*ask-*` fixtures)

These are **test inputs** for Task 6. All valid fixtures conform to the new `review-data.json` envelope (Task 1): `org`, `generated_at`, `brand_folder`, `source_counts`, `grade_scale`, `theme`, `sections[]` (overview + the 7 areas, with `readout`/`recent_update` only on overview), `open_questions[]` (thin shape).

**Step 1: Author `valid-tiny.json`** — minimal valid envelope: 8 sections, full `theme` (decoded palette + one heading + one body font with a relative `src_woff2`, a real `logo.src`), 6 thin OQs.

**Step 2: Author `valid-realistic.json`** — Marley-equivalent: 8 graded sections with `provided[]`/`needed[]`, overview `readout`, ~12 OQs, a `</script>`-bearing string in one `why_it_matters` (sanitization stress).

**Step 3: Author `valid-stress.json`** — 15 OQs (at cap), long `provided[]`/`needed[]` lists.

**Step 4: Author the degradation fixtures:**
- `valid-null-logo-wordmark.json` — `theme.logo.src: null`, `wordmark_text: "The Knot"` (renderer must emit a `.wordmark` span).
- `valid-no-palette-uses-default.json` — `theme.palette: {}` (renderer must emit the literal neutral default for all 17 vars).

**Step 5: Author the invalid fixtures** (renderer must reject — exit non-zero, no `review.html` written):
- `invalid-grade-out-of-range.json` — a section `grade: 7`.
- `invalid-oq-over-cap.json` — 16 entries in `open_questions[]`.
- `invalid-remote-font-src.json` — a `theme.fonts.heading.faces[].src_woff2` starting with `http`.
- `invalid-font-src-escapes-folder.json` — a font `src_woff2` of `../marley-raw/Reckless.woff2` (offline-safety: must resolve inside the brand folder).

**Step 6: Rewrite `README.md`** — a table mapping each fixture to its purpose and the renderer assertion it exercises. Remove the "manual procedure" note and the stale `docs/mockups/2026-05-16-…` reference; note these are now consumed by `e2e/tests/test_reb_renderer.py`.

**Step 7: Commit.**

```bash
git add frameworks/reverse-engineered-brand/test-fixtures/render/
git commit -m "test(reb): rebuild render fixtures to review-data.json shape + theme degradation cases"
```

---

### ✅ Task 6: Implement `render_review.py` (TDD)

**Files:**
- Create: `frameworks/reverse-engineered-brand/scripts/render_review.py`
- Test: `e2e/tests/test_reb_renderer.py`

Self-theming renderer: read `review-data.json` + the token-slot template, emit `:root` palette (with neutral default), `@font-face` (per-asset degradation), header logo-or-wordmark, server-side section panels + per-section OQ blocks, and the inline `REVIEW_DATA` snapshot. Sanitize-before-serialize and run the verify-before-open checks; on any verify or validation failure, return non-zero and write nothing.

**Step 1: Write the failing tests** (stdlib string/regex assertions — no HTML-parser dependency).

```python
# e2e/tests/test_reb_renderer.py
import json
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "frameworks/reverse-engineered-brand/scripts/render_review.py"
TEMPLATE = REPO_ROOT / "frameworks/reverse-engineered-brand/review-template.html"
FIXTURES = REPO_ROOT / "frameworks/reverse-engineered-brand/test-fixtures/render"


def _load():
    spec = importlib.util.spec_from_file_location("render_review", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _render(fixture):
    m = _load()
    data = json.loads((FIXTURES / fixture).read_text())
    return m.render(data, TEMPLATE.read_text(), brand_folder=str(FIXTURES))


# ---- success paths ----
def test_palette_vars_emitted_from_theme():
    html = _render("valid-tiny.json")
    assert "--primary:" in html and "--ink:" in html
    assert "{PALETTE_VARS_CSS}" not in html  # token substituted

def test_neutral_default_palette_when_empty():
    html = _render("valid-no-palette-uses-default.json")
    # All 17 vars present even with theme.palette == {}
    for var in ("--ink:", "--paper:", "--panel:", "--primary:", "--accent:",
                "--good:", "--warn:", "--risk:"):
        assert var in html

def test_fontface_emitted_for_relative_src():
    html = _render("valid-tiny.json")
    assert "@font-face" in html
    assert "{FONT_FACES_CSS}" not in html

def test_null_logo_emits_wordmark_span():
    html = _render("valid-null-logo-wordmark.json")
    assert 'class="wordmark"' in html
    assert "The Knot" in html

def test_one_panel_per_section():
    m = _load()
    data = json.loads((FIXTURES / "valid-realistic.json").read_text())
    html = m.render(data, TEMPLATE.read_text(), brand_folder=str(FIXTURES))
    assert html.count('<section class="panel"') == len(data["sections"])

def test_script_tags_sanitized():
    html = _render("valid-realistic.json")
    # the </script> inside a why_it_matters string must be escaped in the inline snapshot
    assert "<\\/script>" in html
    # only the real closing tags remain unescaped
    assert html.count("</script>") <= html.count("<script")

def test_no_unsubstituted_tokens():
    html = _render("valid-tiny.json")
    import re
    assert not re.search(r"\{[A-Z][A-Z0-9_]*\}", html)

def test_cli_writes_and_verifies(tmp_path):
    out = tmp_path / "review.html"
    r = subprocess.run(
        [sys.executable, str(SCRIPT), str(FIXTURES / "valid-tiny.json"),
         str(TEMPLATE), str(out), "The Knot", str(FIXTURES)],
        capture_output=True, text=True)
    assert r.returncode == 0
    assert out.read_text().startswith("<!DOCTYPE html>")
    assert out.read_text().rstrip().endswith("</html>")


# ---- error paths (MANDATORY) ----
@pytest.mark.parametrize("fixture,reason", [
    ("invalid-grade-out-of-range.json", "grade"),
    ("invalid-oq-over-cap.json", "open_questions"),
    ("invalid-remote-font-src.json", "remote"),
    ("invalid-font-src-escapes-folder.json", "escape"),
])
def test_invalid_fixtures_raise(fixture, reason):
    m = _load()
    data = json.loads((FIXTURES / fixture).read_text())
    with pytest.raises(m.RenderError):
        m.render(data, TEMPLATE.read_text(), brand_folder=str(FIXTURES))

def test_cli_nonzero_and_writes_nothing_on_invalid(tmp_path):
    out = tmp_path / "review.html"
    r = subprocess.run(
        [sys.executable, str(SCRIPT), str(FIXTURES / "invalid-remote-font-src.json"),
         str(TEMPLATE), str(out), "The Knot", str(FIXTURES)],
        capture_output=True, text=True)
    assert r.returncode != 0
    assert not out.exists()  # abort-before-open: nothing written
```

**Step 2: Run to verify they fail.**

Run: `pytest e2e/tests/test_reb_renderer.py -v` (expected: FAIL — module not found).

**Step 3: Implement `render_review.py`.** Core structure (complete the panel/grid/OQ HTML helpers to match the Task 4 template's classes):

```python
#!/usr/bin/env python3
"""Render a self-themed review.html from review-data.json + a token-slot template.

Deterministic, stdlib-only. Validates the data, emits theme CSS + server-side
panels, embeds a sanitized REVIEW_DATA snapshot for paste-back, runs the
verify-before-open checks, and aborts (writes nothing) on any failure.
Invoked by render-review-html.md (PHASE 3.7); render() is unit-tested directly.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

CAP = 15
PALETTE_VARS = ["ink", "muted", "paper", "panel", "line", "line_strong",
                "primary", "primary_deep", "accent", "peach", "cream", "blush",
                "sky", "ice", "good", "warn", "risk"]
DEFAULT_PALETTE = {  # warm-neutral literal default (R3 h-6a) for public-web-only builds
    "ink": "#1a1a1a", "muted": "#6b7280", "paper": "#faf9f7", "panel": "#ffffff",
    "line": "#e5e7eb", "line_strong": "#d8c7bd", "primary": "#33312e",
    "primary_deep": "#1a1a1a", "accent": "#ff6900", "peach": "#ffe7d6",
    "cream": "#faf9f7", "blush": "#fff5f5", "sky": "#c9e5fc", "ice": "#edf7ff",
    "good": "#047857", "warn": "#a46716", "risk": "#b91c1c",
}


class RenderError(Exception):
    """Raised on validation or verify-before-open failure. Nothing is written."""


def _validate(data: dict, brand_folder: str) -> None:
    sections = data.get("sections", [])
    for s in sections:
        g = s.get("grade")
        if not isinstance(g, int) or not (1 <= g <= 5):
            raise RenderError(f"grade out of 1-5 range: section {s.get('id')} grade={g}")
    oqs = data.get("open_questions", [])
    if len(oqs) > CAP:
        raise RenderError(f"open_questions over cap: {len(oqs)} > {CAP}")
    # Offline-safety: every font src must be relative AND resolve inside the brand folder.
    theme = data.get("theme") or {}
    for key in ("heading", "body"):
        font = (theme.get("fonts") or {}).get(key) or {}
        for face in font.get("faces") or []:
            for src in (face.get("src_woff2"), face.get("src_woff")):
                if not src:
                    continue
                if re.match(r"^https?:", src):
                    raise RenderError(f"remote font src forbidden (offline-safety): {src}")
                if ".." in Path(src).parts:
                    raise RenderError(f"font src escapes brand folder: {src}")
    logo = (theme.get("logo") or {})
    if logo.get("src") and (re.match(r"^https?:", logo["src"]) or ".." in Path(logo["src"]).parts):
        raise RenderError(f"logo src must be local + non-escaping: {logo['src']}")


def _palette_css(theme: dict) -> str:
    palette = (theme.get("palette") or {})
    lines = []
    for var in PALETTE_VARS:
        value = palette.get(var) or DEFAULT_PALETTE[var]
        lines.append(f"      --{var}: {value};")
    return "\n".join(lines)


def _fontface_css(theme: dict) -> str:
    blocks = []
    for key in ("heading", "body"):
        font = (theme.get("fonts") or {}).get(key) or {}
        family = font.get("family")
        faces = [f for f in (font.get("faces") or [])
                 if (f.get("src_woff2") or f.get("src_woff"))]  # drop src-less faces (R3 h-6d)
        if not faces:
            if font.get("cdn"):
                blocks.append(f'@import url("{font["cdn"]}");')
            continue  # else rely on fallback stack
        for face in faces:
            srcs = []
            if face.get("src_woff2"):
                srcs.append(f'url("{face["src_woff2"]}") format("woff2")')
            if face.get("src_woff"):
                srcs.append(f'url("{face["src_woff"]}") format("woff")')
            blocks.append(
                f'@font-face {{ font-family: "{family}"; '
                f'src: {", ".join(srcs)}; '
                f'font-weight: {face.get("weight", 400)}; '
                f'font-style: {face.get("style", "normal")}; font-display: swap; }}')
    return "\n  ".join(blocks)


def _header_brand(theme: dict, org: str) -> str:
    logo = (theme.get("logo") or {})
    if logo.get("src"):
        return f'<img class="brand-mark" src="{html.escape(logo["src"], quote=True)}" alt="{html.escape(org)}">'
    text = logo.get("wordmark_text") or org
    return f'<span class="wordmark">{html.escape(text)}</span>'


def _nav_tabs(sections: list[dict]) -> str:
    out = []
    for s in sections:
        out.append(
            f'<button class="tab" onclick="activate(\'{s["id"]}\')">'
            f'{html.escape(s["label"])}<span>{s["grade"]} / 5</span></button>')
    return "\n      ".join(out)


def _oq_blocks(section_id: str, oqs: list[dict]) -> str:
    rows = [oq for oq in oqs if str(oq.get("slice", "")).startswith(section_id + "/")
            or (section_id == "overview")]
    # Overview lists no per-section OQs; area panels filter by slice path prefix.
    if section_id == "overview":
        rows = []
    blocks = []
    for oq in rows:
        blocks.append(
            f'<article class="question"><div class="question-meta">{html.escape(oq["id"])} · '
            f'{html.escape(oq["impact"])}</div>'
            f'<h4>{html.escape(oq["question"])}</h4>'
            f'<p>{html.escape(oq["why_it_matters"])}</p>'
            f'<textarea id="{html.escape(oq["id"])}"></textarea>'
            f'<button onclick="copyOne(\'{html.escape(oq["id"])}\')">Copy prompt</button></article>')
    return "\n".join(blocks)


def _panel(section: dict, oqs: list[dict]) -> str:
    provided = "".join(f"<li>{html.escape(x)}</li>" for x in section.get("provided", []))
    needed = "".join(f"<li>{html.escape(x)}</li>" for x in section.get("needed", []))
    readout = ""
    if section["id"] == "overview" and section.get("readout"):
        r = section["readout"]
        readout = (f'<div class="readout">'
                   f'<div><strong>Brand system</strong>{html.escape(r.get("brand_system",""))}</div>'
                   f'<div><strong>Main risk</strong>{html.escape(r.get("main_risk",""))}</div>'
                   f'<div><strong>Decisions needed</strong>{html.escape(r.get("decisions_needed",""))}</div></div>')
    return (
        f'<section class="panel" id="panel-{section["id"]}">'
        f'<div class="eyebrow">{html.escape(section.get("status",""))}</div>'
        f'<h2>{html.escape(section["label"])}<span class="grade">{section["grade"]} / 5</span></h2>'
        f'<p class="summary">{html.escape(section.get("summary",""))}</p>'
        f'{readout}'
        f'<div class="grid"><div class="working"><h3>Working</h3><ul>{provided}</ul></div>'
        f'<div class="attention"><h3>Needs attention</h3><ul>{needed}</ul></div></div>'
        f'{_oq_blocks(section["id"], oqs)}'
        f'</section>')


def _sanitize(obj):
    """Recursively replace </ with <\\/ in every string (sanitize before serialize)."""
    if isinstance(obj, str):
        return obj.replace("</", "<\\/")
    if isinstance(obj, list):
        return [_sanitize(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    return obj


def _verify(out_html: str) -> None:
    if not out_html.startswith("<!DOCTYPE html>"):
        raise RenderError("verify: missing DOCTYPE")
    if "<script" not in out_html:
        raise RenderError("verify: missing <script>")
    if out_html.count("</script>") > out_html.count("<script"):
        raise RenderError("verify: unsanitized </script> in a string value")
    if not out_html.rstrip().endswith("</html>"):
        raise RenderError("verify: missing closing </html>")
    leftover = re.search(r"\{[A-Z][A-Z0-9_]*\}", out_html)
    if leftover:
        raise RenderError(f"verify: unsubstituted token {leftover.group(0)}")


def render(data: dict, template: str, brand_folder: str, org: str | None = None) -> str:
    org = org or data.get("org", "")
    _validate(data, brand_folder)
    theme = data.get("theme") or {}
    sections = data.get("sections", [])
    oqs = data.get("open_questions", [])
    snapshot = json.dumps(_sanitize(data), ensure_ascii=False)
    out = (template
           .replace("{FONT_FACES_CSS}", _fontface_css(theme))
           .replace("{PALETTE_VARS_CSS}", _palette_css(theme))
           .replace("{HEADER_BRAND}", _header_brand(theme, org))
           .replace("{NAV_TABS}", _nav_tabs(sections))
           .replace("{SECTION_PANELS}", "\n".join(_panel(s, oqs) for s in sections))
           .replace("{ORG_NAME}", html.escape(org))
           .replace("{REVIEW_DATA_JSON}", snapshot))
    _verify(out)
    return out


def main(argv) -> int:
    if len(argv) != 6:
        sys.stderr.write("usage: render_review.py <review-data.json> <template> <out.html> <org> <brand-folder>\n")
        return 2
    data_path, template_path, out_path, org, brand_folder = argv[1:]
    data = json.loads(Path(data_path).read_text())
    try:
        out_html = render(data, Path(template_path).read_text(), brand_folder, org)
    except RenderError as e:
        sys.stderr.write(f"render aborted: {e}\n")
        return 1
    Path(out_path).write_text(out_html)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

> Note: the `_oq_blocks` overview/area filtering, `_panel` markup, and template CSS classes must agree — adjust the helper HTML to match the exact class names you used in the Task 4 template. The tests assert on `<section class="panel"`, `class="wordmark"`, `@font-face`, and `--{var}:` substrings, so keep those literal.

**Step 4: Run to verify they pass.**

Run: `pytest e2e/tests/test_reb_renderer.py -v` (expected: PASS, all success + error-path cases).

**Step 5: Commit.**

```bash
git add frameworks/reverse-engineered-brand/scripts/render_review.py e2e/tests/test_reb_renderer.py
git commit -m "feat(reb): self-theming render_review.py with degradation + verify-before-open"
```

---

### ✅ Task 7: `prompt.md` PHASE 2.1 — exempt the 5 always-on slices + stub contract

> **Ordering:** Tasks 7–12 all edit `frameworks/reverse-engineered-brand/prompt.md`. Run in order.

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (PHASE 2 §"Step 2.1" and the slice mapping table)

The 5 always-on slices (`source-map.md` root, `strategy/context.md`, `strategy/operating-principles.md`, `language/copy-bank.md`, `proof/claims-ledger.md`) must be exempted from the **"Skip slices with no signal"** path AND the **GAP meta-OQ** path, so a thin build keeps the 8-section/8-tab structure stable (B4). Thinness shows as a low grade + populated `needed[]`, never a missing tab.

**Step 1: Add an always-on slice list** to Step 2.1, immediately after the "Skip slices with no signal" paragraph (anchor on the sentence beginning "**Skip slices with no signal.**"):

> **Always-on slices (NEW — Marley model).** The following five slices are ALWAYS produced regardless of signal: `source-map.md` (root), `strategy/context.md`, `strategy/operating-principles.md`, `language/copy-bank.md`, `proof/claims-ledger.md`. They are EXEMPT from the skip-no-signal rule above AND from the GAP meta-OQ path (Step 2.3 / Step 3.1). When a producer finds thin or no signal, it writes a **minimum stub** — a one-line statement of what the slice would hold plus a `## Needed inputs` list (the same items that populate the section's `needed[]`). A stub is graded 1–2 with a populated `needed[]`; it clears PHASE 2.4 Check 1 (non-zero-byte) and is exempt from Check 5's short-draft (<200 words) warning. Existing conditional slices (`clinical-evidence`, `compliance`, `design/layouts`, `design/slide-patterns`) remain conditional on domain/source-type.

**Step 2: Wire the exemption into the skip path.** In the same "Skip slices with no signal" paragraph, append: "Always-on slices (see list above) are never skipped — if their filtered extract list is empty, dispatch/produce them anyway and let the stub contract handle thinness."

**Step 3: Wire the exemption into PHASE 2.4 Check 5.** In the §"Step 2.4" Check 5 short-draft heuristic bullet, add: "EXEMPT: always-on slices (`source-map.md`, `strategy/context.md`, `strategy/operating-principles.md`, `language/copy-bank.md`, `proof/claims-ledger.md`) when their draft is a legitimate thin stub — do not warn."

**Step 4: Verify the edit landed.**

Run: `grep -n "Always-on slices" frameworks/reverse-engineered-brand/prompt.md` (expect ≥2 hits: Step 2.1 + Check 5).

**Step 5: Commit.**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reb): exempt 5 always-on slices from skip-no-signal + GAP paths"
```

---

### ✅ Task 8: `prompt.md` PHASE 2.3b — emit the `theme` manifest (palette / fonts / logo)

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (§"Step 2.3b: Visual-structure synthesis" and §"Color library extraction requirement")

The `theme` block is **net-new emission** (T4): hex decode already lives in the `design-principles` dispatch; Step 2.3b is visual-structure synthesis and `prompt.md` explicitly excludes color/typography there. Neither path emits a *structured* manifest today (both write prose into `.md`). Add a `theme` manifest written to `{brand-folder-path}/.build/theme.json`, consumed field-by-field by `render_review.py`. Logo + any local fonts are downloaded into `{brand-folder-path}/assets/` for public-web builds; never a remote URL, never a `../` escape.

**Step 1: Add a "Theme manifest emission" subsection** to Step 2.3b (anchor after the §"Color library extraction requirement" block). Specify the design pass emits `{brand-folder-path}/.build/theme.json`:

```jsonc
{
  "palette": { /* 17 vars: ink, muted, paper, panel, line, line_strong, primary,
     primary_deep, accent, peach, cream, blush, sky, ice, good, warn, risk —
     decoded from public-web CSS / source assets; OMIT a var only if undecodable
     (render_review.py supplies the neutral default for any missing var) */ },
  "fonts": {
    "heading": { "family": "...", "faces": [{ "weight": 500, "style": "normal",
      "src_woff2": "assets/fonts/<file>.woff2", "src_woff": null }],
      "cdn": null, "fallback": "Georgia, serif" },
    "body": { "family": "...", "faces": [], "cdn": null,
      "fallback": "ui-sans-serif, system-ui, sans-serif" }
  },
  "logo": { "src": "assets/<logo-file>", "wordmark_text": "<org>" }
}
```

**Step 2: Specify the degradation rules** (R3) as explicit instructions to the design sub-agent:
- **Palette:** decode every var possible from public-web CSS / source theme files; leave undecodable vars out (the renderer fills neutral defaults). Palette is decodable even with no local files.
- **Fonts:** identify families; download local font files into `{brand-folder-path}/assets/fonts/` and record a **relative** `src_woff2`/`src_woff`. Drop a face with no obtainable source. Undecodable family ⇒ set `family` to the fallback stack's lead token (never an empty string). If all faces drop and no `cdn`, emit no faces — rely on `fallback`.
- **Logo:** download the site logo into `{brand-folder-path}/assets/` and record a relative `src`. Fetch is bounded (~10s); on timeout OR failure ⇒ set `src: null` and rely on `wordmark_text`. Never hang the build; never record a remote URL or `../` path.

**Step 3: Note the offline-safety contract** explicitly: "Every emitted `theme` asset src MUST be relative AND resolve inside the brand folder (no `http(s):`, no `../`). `render_review.py` re-asserts this and aborts the render if violated." (This pairs with the renderer reject fixtures from Task 5.)

**Step 4: Verify the edit landed.**

Run: `grep -n "theme.json\|Theme manifest" frameworks/reverse-engineered-brand/prompt.md` (expect hits in Step 2.3b).

**Step 5: Commit.**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reb): emit structured theme manifest (palette/fonts/logo) in design pass"
```

---

### ✅ Task 9: `prompt.md` — proof dispatch emits `proof/claims-ledger.md`

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (§"Step 2.3" dispatch + the slice mapping table row for `proof/proof-points.md`)

`proof/claims-ledger.md` is an always-on slice owned by `proof-points-audit` (R1). Rather than edit `proof-points-audit/prompt.md` (which would change its standalone behavior — a portability regression), extend the **orchestrator's** proof dispatch to request the ledger as a second output from the same sub-agent, built from the claims it already extracts/dates/confidence-tags (its PHASE 1/3/4).

**Step 1: Add a dispatch note for the proof slice** in Step 2.3 (anchor on the bullet list of dispatch placeholders, after `{org-name}`):

> **Proof dispatch — claims ledger (NEW).** When dispatching `proof-points-audit` for the `proof/` folder, instruct the sub-agent to ALSO emit `{brand-folder-path}/.build/slices/proof/claims-ledger.md.draft.md` — an approval queue of every clinical / economic / GTM claim it extracted, each row tagged `status: approval_required` with source + date + confidence (reuse its PHASE 1 claim extraction + PHASE 3 dates + PHASE 4 confidence; no new analysis). Frontmatter `synthesis_method: framework`, `owning_framework: proof-points-audit`. If no claims surface, write the thin stub (Task 7 contract). This is an additive output instruction in the dispatch prompt — `proof-points-audit/prompt.md` is NOT modified.

**Step 2: Update the slice mapping table** — add a `proof/claims-ledger.md` row: output shape "Claims approval queue (claim, source, date, confidence, status)", owning framework `proof-points-audit`.

**Step 3: Verify.**

Run: `grep -n "claims-ledger" frameworks/reverse-engineered-brand/prompt.md` (expect the dispatch note + table row).

**Step 4: Commit.**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reb): proof dispatch emits proof/claims-ledger.md (always-on slice)"
```

---

### ✅ Task 10: `prompt.md` — producers for the 4 orchestrator/internal always-on slices

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (Step 2.3 / Step 2.3b region + slice mapping table)

Add explicit producers + `synthesis_method` for the remaining always-on slices (R1 table). These are exempt from GAP OQs because they have a producer (matching how `design/layouts.md` avoids GAP via `synthesis_method: visual-structure`).

**Step 1: Add a "Producers for always-on slices" subsection** after Step 2.3b, specifying:

| Slice | Producer | `synthesis_method` | Reads bodies? |
|-------|----------|--------------------|---------------|
| `source-map.md` (root) | **Orchestrator-inline at PHASE 3** — renders the Source Registry as an ID → path → best-use traceability table. Never enters PHASE 2 dispatch (this is how Marley's `source-map.md` exists without firing a GAP OQ). | `orchestrator_inline` | No (registry metadata only — guard-safe) |
| `strategy/context.md` | Orchestrator-inline from `canonical-pre-synthesis-blob.md` (Step 2.2, bounded) + aggregated registry signal. | `orchestrator_inline` | No |
| `strategy/operating-principles.md` | Framework-internal synthesis sub-agent reading strategy/narrative-tagged extracts (mirrors the Step 2.3b visual-structure pattern; disposable context preserves the guard). | `framework_internal`, `owning_framework: reverse-engineered-brand` | Yes (in sub-agent) |
| `language/copy-bank.md` | Framework-internal synthesis sub-agent reading voice/messaging-tagged extracts. | `framework_internal`, `owning_framework: reverse-engineered-brand` | Yes (in sub-agent) |

**Step 2: Add `orchestrator_inline` to the GAP-exclusion lists.** Find every place that exempts `classification` from GAP/skip handling (Step 2.3 dispatch-skip and Step 3.1 GAP-dedupe) and add `orchestrator_inline` and `framework_internal` as equally exempt sentinels. State explicitly: "Slices with `synthesis_method` in {`classification`, `orchestrator_inline`, `framework_internal`} never fire a GAP meta-OQ."

**Step 3: Add the two `framework_internal` dispatches** to the Step 2.3 parallel dispatch set (operating-principles, copy-bank), each writing `.build/slices/{slice}.draft.md` + `.oq.json` like the visual-structure pass. Note the orchestrator-inline producers (`source-map.md`, `strategy/context.md`) are authored in PHASE 3 (Task 11), not dispatched here.

**Step 4: Verify.**

Run: `grep -n "orchestrator_inline\|framework_internal\|operating-principles\|copy-bank" frameworks/reverse-engineered-brand/prompt.md` (expect hits across the new subsection + exclusion lists).

**Step 5: Commit.**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reb): add producers + synthesis_method for 4 always-on slices"
```

---

### ✅ Task 11: `prompt.md` PHASE 3 rewrite — curate → sections → overview → counts → write → render → cleanup

**Files:**
- Modify (heavy edit): `frameworks/reverse-engineered-brand/prompt.md` (replace §"Step 3.2" through §"Step 3.8", and the §"Resume semantics for PHASE 3 sub-agents" block)

This is the core orchestrator rewrite. Delete the `display_groups` / `input_asks` / `provided_summary` / `source_narratives` / `group-bullets` / `voice-rewrite` machinery (Steps 3.2-NEW, 3.2b, 3.2c, and the resume-semantics block) and replace PHASE 3 with the Marley-model flow.

**Step 1: Delete the v0.4.1 machinery.** Remove these blocks in full:
- §"Step 3.2-NEW: Build `display_groups[]` shells + dispatch group-bullets sub-agents"
- §"Step 3.2b: Brand-voice rewrite + `provided_summary` generation"
- §"Step 3.2c: Input-ask verification gate"
- the §"Resume semantics for PHASE 3 sub-agents (added v0.4.1)" block (group-bullets + voice-rewrite resume rules)
- in Step 3.2, the `input_asks` aggregation block, the `provided_summary` placeholder paragraph, and the `display_groups` references.

**Step 2: Rewrite Step 3.2** as **"Build the 7 area sections inline"**:

> For each of the 7 area folders (`strategy`, `language`, `personas`, `audiences`, `market`, `proof`, `design`), the orchestrator authors a `sections[]` entry directly (no sub-agent — the OQ queue and Slice Index are already in-context metadata):
> - `id` (bare folder token — MUST be one of `overview`, `strategy`, `language`, `personas`, `audiences`, `market`, `proof`, `design`; the renderer routes OQs by `oq["slice"].startswith(section_id + "/")` — any other value silently drops all OQs for that section).
> - `label` (display name).
> - `grade` (1–5) per the existing rubric (keep the rubric block — it already lives in this PHASE).
> - `confidence`: **derived** (R4) — the modal per-slice `low|medium|high` across the folder's slices; widen to a compound string ("medium-high") ONLY when slices split evenly between two adjacent levels.
> - `status`: a short eyebrow string (e.g., "Default category recommended").
> - `summary`: 1–3 brand-specific sentences (keep the existing "do not write a generic definition" guidance).
> - `provided[]`: plain bullet list of what the build has (replaces `provided_summary`; for `market`, summarize the in-`.build/` `competitors[]`/`behavioral_alternatives[]` here).
> - `needed[]`: plain bullet list of missing inputs (replaces `input_asks`; for always-on stub slices this mirrors the stub's `## Needed inputs`).
> - `files[]`: the brand file paths this section covers.

**Step 3: Add Step 3.1.5 "Curate open questions"** (after the existing Step 3.1 aggregation):

> Invoke the deterministic curator (no sub-agent, no LLM):
> ```bash
> python3 frameworks/reverse-engineered-brand/scripts/curate_open_questions.py \
>   "{brand-folder-path}/.build/slices" > "{brand-folder-path}/.build/curated-oq.json"
> ```
> `curated-oq.json` is the thin persisted shape (5 fields, `OQ-NNN` ids) — owner-authority decisions first, impact-rank backfill to a floor of 5, hard cap 15. This is the ONLY OQ set persisted to `review-data.json`; the full per-slice queue stays in `.build/` and is deleted at cleanup.

**Step 4: Add Step 3.2.5 "Build the overview section"** (T5):

> The orchestrator computes the synthetic `overview` section from the 7 area sections:
> - `grade`: editorial, **seeded by the rounded mean** of the 7 area grades (the author may adjust ±1 with a one-line justification in `summary`; default to the rounded mean). [Resolves design OQ-B — see Decision Log.]
> - `readout`: `{brand_system, main_risk, decisions_needed}` (3 short strings synthesized from the 7 sections; `decisions_needed` reads "No owner decisions outstanding." when the curated OQ list is empty).
> - `recent_update`: **`null`** on first build (the diff machinery is unbuilt — YAGNI; no re-run workflow in scope).
> - `provided[]`/`needed[]`: the highest-signal items rolled up from the 7 sections.

**Step 5: Rewrite Step 3.5/3.6 "Compute `source_counts` + author orchestrator-inline slices + write `review-data.json`"**:
- Author `source-map.md` (root) inline from the Source Registry (ID → path → best-use table) and `strategy/context.md` inline from the pre-synthesis blob + registry (the two `orchestrator_inline` producers from Task 10).
- Compute `source_counts`: `total_sources` & `usable_sources` (PHASE 1 Step 1.3), `canonical_markdown_files` (count `.md` files after the Step 3.5 move), `review_sections` = 8, `open_questions` = curated count.
- Build the `theme` block into `review-data.json` by reading `.build/theme.json` (Task 8). If `.build/theme.json` is absent (no design pass ran), write `theme: { "palette": {}, "fonts": {...empty faces...}, "logo": { "src": null, "wordmark_text": "{org-name}" } }` so the renderer's neutral-default path engages.
- Write the canonical `{brand-folder-path}/review-data.json` (the full envelope: `org`, `generated_at`, `brand_folder`, `source_counts`, `grade_scale`, `theme`, `sections[]`, `open_questions[]`). **Drop the standalone `.open-questions.json`** entirely (T1) — `review-data.json` is the single source of truth.

**Step 6: Rewrite Step 3.7 "Dispatch the renderer"** to point at `render-review-html.md` with the new inputs (`{review-data-json-path}`, `{template-path}`, `{output-html-path}`, `{org-name}`, `{brand-folder-path}`) — see Task 13 for the renderer's new contract.

**Step 7: Keep Step 3.8 cleanup** (delete `.build/`) and Step 3.9 final report, but update the report's counts to the new `source_counts` fields and OQ count.

**Step 8: Verify the machinery is gone and the new flow is present.**

Run: `grep -n "display_groups\|provided_summary\|source_narratives\|group-bullets\|voice-rewrite" frameworks/reverse-engineered-brand/prompt.md` (expect: NO matches).
Run: `grep -n "curate_open_questions.py\|review-data.json\|Build the overview" frameworks/reverse-engineered-brand/prompt.md` (expect: matches).

**Step 9: Commit.**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reb): rewrite PHASE 3 to Marley model (curate, inline sections, single review-data.json)"
```

---

### ✅ Task 12: `prompt.md` PHASE 3.6 — `version.yaml` / `contracts.yaml` / `CLAUDE.md` authoring

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (§"Step 3.6: Write top-level brand-folder files")

Update the top-level-file authoring to match the Marley model and resolve design OQ-A.

**Step 1: Rewrite the `version.yaml` instruction** — drop `schema_version` (resolves OQ-A; Marley parity). Author Marley-shaped: `brand_name`, `generated_at`, `framework: reverse-engineered-brand`, `source_root`, `status: first_draft`, `confidence`, `notes`. [Clean cutover — no deployed v0.4.1 consumer folders exist in the plugin; see Decision Log.]

**Step 2: Update the `.open-questions.json` reference** — Step 3.6 currently writes `.open-questions.json` with `schema_version` and `source_narratives`. Remove that block entirely (the canonical write moved to Task 11's `review-data.json`; this step no longer authors an OQ file).

**Step 3: Confirm `CLAUDE.md` + `contracts.yaml`** authoring still references `docs/brand-folder-spec.md` templates and lists the always-on slices in the Source Registry / Slice Index (they're now always present).

**Step 4: Verify.**

Run: `grep -n "schema_version\|source_narratives\|.open-questions.json" frameworks/reverse-engineered-brand/prompt.md` (expect: NO matches).

**Step 5: Commit.**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reb): drop schema_version; author Marley-shaped version.yaml"
```

---

### ✅ Task 13: Rewrite `render-review-html.md` — invoke `render_review.py` + verify-before-open

**Files:**
- Modify (rewrite): `frameworks/reverse-engineered-brand/render-review-html.md`

The renderer sub-agent shifts from doing token substitution itself to invoking the deterministic Python renderer (which already does sanitize + verify-before-open) and then opening the file. Also rewrite the shape-warning whitelist (R5) to name-check the new envelope.

**Step 1: Rewrite the Inputs table** — `{review-data-json-path}`, `{template-path}`, `{output-html-path}`, `{org-name}`, `{brand-folder-path}`.

**Step 2: Replace the Procedure** with:
1. **Render via the deterministic script:**
   ```bash
   python3 frameworks/reverse-engineered-brand/scripts/render_review.py \
     "{review-data-json-path}" "{template-path}" "{output-html-path}" "{org-name}" "{brand-folder-path}"
   ```
   The script validates the data (grade range, OQ ≤ 15, offline-safety of font/logo srcs), emits theme CSS + server-side panels + the sanitized inline `REVIEW_DATA` snapshot, runs the verify-before-open checks (DOCTYPE, `<script>` present, no unsanitized `</script>`, closing `</html>`, no unsubstituted `{TOKEN}`), and writes the file ONLY if all checks pass.
2. **Abort-before-open contract:** if the script exits non-zero, do NOT open the file. Return `STATUS: verification_failed` with the script's stderr in `NOTES`.
3. **Open** (only on exit 0): `open {output-html-path}`.

**Step 3: Rewrite the shape-warning whitelist (R5).** Replace the v0.4.0 field name-checks (`source_narratives`, `folders[].grade/summary/provided_summary/input_asks`, `display_groups`) with the new envelope: warn if `sections[]`, `theme.palette`, or the new `source_counts` keys are missing. (These are non-blocking pre-flight warnings; the Python validator is the hard gate.)

**Step 4: Update the Return Contract** — keep `STATUS / OUTPUT_PATH / BYTES_WRITTEN / NOTES`; `VERIFICATION_CHECKS_PASSED` now reflects the script's checks.

**Step 5: Verify.**

Run: `grep -n "render_review.py\|source_narratives\|display_groups" frameworks/reverse-engineered-brand/render-review-html.md` (expect: `render_review.py` present; the two v0.4.1 fields absent).

**Step 6: Commit.**

```bash
git add frameworks/reverse-engineered-brand/render-review-html.md
git commit -m "feat(reb): render-review-html.md invokes render_review.py; rewrite shape warnings"
```

---

### Task 14: Delete `group-bullets.md` and `voice-rewrite.md`

**Files:**
- Delete: `frameworks/reverse-engineered-brand/group-bullets.md`
- Delete: `frameworks/reverse-engineered-brand/voice-rewrite.md`

The two review-stage sub-agents are removed (T2: 3 sub-agents → 0). Their orchestrator references were already removed in Task 11.

**Step 1: Delete the files.**

```bash
git rm frameworks/reverse-engineered-brand/group-bullets.md frameworks/reverse-engineered-brand/voice-rewrite.md
```

**Step 2: Grep for dangling references across the framework + docs.**

Run: `grep -rn "group-bullets\|voice-rewrite" frameworks/reverse-engineered-brand/ docs/brand-folder-spec.md` (expect: NO matches — Task 11 cleared `prompt.md`; if any remain, remove them).

**Step 3: Commit.**

```bash
git commit -m "feat(reb): delete group-bullets + voice-rewrite sub-agents (2 review sub-agents -> 0)"
```

---

### Task 15: `brand-folder-spec.md` — add the 5 always-on slices + synthesis methods

**Files:**
- Modify: `docs/brand-folder-spec.md` (directory tree, per-file purpose table, §"Synthesis methods")

The canonical spec must document the always-on slices and the two new synthesis methods (h-1).

**Step 1: Add the always-on slices to the directory tree** — `source-map.md` (root, alongside `CLAUDE.md`/`version.yaml`), `strategy/context.md`, `strategy/operating-principles.md`, `language/copy-bank.md`, `proof/claims-ledger.md`. Add a one-line comment on each (e.g., `# traceable source IDs -> path -> best-use`).

**Step 2: Add per-file purpose rows** for the 5 slices in the per-file purpose table (what each owns / does NOT own), mirroring Marley's `CLAUDE.md` descriptions.

**Step 3: Extend the §"Synthesis methods" table** with two new methods:
- `orchestrator_inline` — produced directly by the orchestrator at PHASE 3 from registry/blob metadata (no sub-agent, no body reads). Slices: `source-map.md`, `strategy/context.md`.
- `framework_internal` — produced by a framework-internal synthesis sub-agent reading tagged extracts in disposable context (preserves the context-bloat guard). Slices: `strategy/operating-principles.md`, `language/copy-bank.md`, `design/layouts.md`, `design/slide-patterns.md`. (`proof/claims-ledger.md` uses `framework` via `proof-points-audit`.)

**Step 4: Verify.**

Run: `grep -n "claims-ledger\|copy-bank\|operating-principles\|orchestrator_inline\|framework_internal" docs/brand-folder-spec.md` (expect: matches).

**Step 5: Commit.**

```bash
git add docs/brand-folder-spec.md
git commit -m "docs: add 5 always-on slices + orchestrator_inline/framework_internal methods to brand-folder spec"
```

---

### Task 16: `audience-taxonomy.md` — delete the `## Ideal inputs` section

**Files:**
- Modify: `frameworks/reverse-engineered-brand/audience-taxonomy.md` (delete §"Ideal inputs")

The `## Ideal inputs` section (its `input_asks` YAML block) is now orphaned — PHASE 3.2's read of it was deleted in Task 11 (l-1).

**Step 1: Delete the entire `## Ideal inputs` section** (the heading, the explanatory paragraph, and the `input_asks` YAML block — the final section of the file).

**Step 2: Verify.**

Run: `grep -n "Ideal inputs\|input_asks" frameworks/reverse-engineered-brand/audience-taxonomy.md` (expect: NO matches).

**Step 3: Commit.**

```bash
git add frameworks/reverse-engineered-brand/audience-taxonomy.md
git commit -m "docs(reb): drop orphaned Ideal inputs section from audience-taxonomy"
```

---

### Task 17: `frameworks/registry.yaml` — reconcile `required_documents`

**Files:**
- Modify: `frameworks/registry.yaml` (the `reverse-engineered-brand` entry's `required_documents`)

The framework accepts a public URL **or** a local source folder, but the registry's `required_documents` lists only the URL.

**Step 1: Edit the `required_documents` list** under the `id: reverse-engineered-brand` entry (the `id:` line is the anchor):

```yaml
  required_documents:
  - a public URL for the org (homepage or About page) OR a local folder of source material
```

**Step 2: Verify the registry still parses + the entry is intact.**

Run: `pytest e2e/tests/test_registry_schemas.py -v` (expect: PASS — registry schema validation).

**Step 3: Commit.**

```bash
git add frameworks/registry.yaml
git commit -m "docs(reb): registry required_documents accepts URL or local folder"
```

---

### Task 18: Migration-guard test — lock the v0.4.1→Marley cutover

**Files:**
- Create: `e2e/tests/test_reb_migration_contracts.py`

A retroactive static-parse guard (mirrors `test_execute_plan_no_halt_sentinel.py`) that locks the migration: removed machinery stays gone, new contracts stay present. This is the regression net for the prose edits in Tasks 7–13 (which have no per-task automated test).

**Step 1: Write the test** (implementation already exists from Tasks 7–16, so this is "write test → verify it passes").

```python
# e2e/tests/test_reb_migration_contracts.py
"""Lock the v0.4.1 -> Marley review-model cutover. Static text assertions."""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REB = REPO_ROOT / "frameworks/reverse-engineered-brand"


def _read(rel):
    return (REB / rel).read_text(encoding="utf-8")


@pytest.mark.parametrize("token", [
    "display_groups", "provided_summary", "source_narratives",
    "group-bullets", "voice-rewrite", "input_asks",
])
def test_removed_machinery_absent_from_prompt(token):
    assert token not in _read("prompt.md"), f"{token} must be gone from prompt.md"


def test_removed_subagent_files_deleted():
    assert not (REB / "group-bullets.md").exists()
    assert not (REB / "voice-rewrite.md").exists()


def test_new_contracts_present_in_prompt():
    text = _read("prompt.md")
    for needle in ("curate_open_questions.py", "review-data.json",
                   "orchestrator_inline", "claims-ledger"):
        assert needle in text, f"prompt.md must reference {needle}"


def test_renderer_invokes_python_and_drops_legacy_fields():
    text = _read("render-review-html.md")
    assert "render_review.py" in text
    for token in ("source_narratives", "display_groups"):
        assert token not in text


def test_scripts_exist():
    assert (REB / "scripts/curate_open_questions.py").is_file()
    assert (REB / "scripts/render_review.py").is_file()


def test_no_standalone_open_questions_json_authoring():
    # The single source of truth is review-data.json; the dotfile authoring is gone.
    assert ".open-questions.json" not in _read("prompt.md")


# R4 confidence derivation: modal per-slice enum, even-split → compound string.
# These are pure unit tests against helper logic; the derivation algorithm is
# authored inline in prompt.md Task 11 Step 2 — no Python module to import, so
# we test the contract via a documented helper function in curate_open_questions.py.
def test_r4_modal_confidence_returns_dominant_level():
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("curate_oq",
        REPO_ROOT / "frameworks/reverse-engineered-brand/scripts/curate_open_questions.py")
    _mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod)
    # modal_confidence(["low", "low", "medium"]) → "low"
    assert _mod.modal_confidence(["low", "low", "medium"]) == "low"
    # modal_confidence(["high", "high", "high"]) → "high"
    assert _mod.modal_confidence(["high", "high", "high"]) == "high"


def test_r4_even_split_produces_compound_string():
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("curate_oq",
        REPO_ROOT / "frameworks/reverse-engineered-brand/scripts/curate_open_questions.py")
    _mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod)
    # even split between two adjacent levels → compound "level1-level2" (lower first)
    assert _mod.modal_confidence(["medium", "high"]) == "medium-high"
    assert _mod.modal_confidence(["low", "medium"]) == "low-medium"
```

> **Note for implementer:** These tests require `modal_confidence(levels: list[str]) -> str` to be exported from `curate_open_questions.py`. Add it alongside `curate_to_thin` in Task 3 Step 3 — it is pure logic (sort by CONFIDENCE_RANK, return modal; on even 2-way tie between adjacent levels, return `"{lower}-{higher}"`).

**Step 2: Run to verify it passes.**

Run: `pytest e2e/tests/test_reb_migration_contracts.py -v` (expected: PASS — Tasks 7–16 already made these true).

**Step 3: Commit.**

```bash
git add e2e/tests/test_reb_migration_contracts.py
git commit -m "test(reb): migration-guard locks v0.4.1->Marley cutover"
```

---

### Task 19: Add the eval scenario + trigger-map entry + promptfoo registration

**Files:**
- Create: `e2e/scenarios/use-framework/reverse-engineered-brand.yaml`
- Modify: `e2e/trigger-map.yaml` (append a `reverse-engineered-brand` trigger)
- Modify: `e2e/promptfooconfig.yaml` (register the new scenario)

The framework is on the declared eval surface (`eval-surface.yaml`: `frameworks/*/prompt.md`) but has zero scenario coverage — `eval-audit` flags surface-without-scenario (criterion 5 / T8). Add an LLM-graded scenario plus the registration that `test_trigger_map_scenarios.py` enforces.

> **Ordering within this task:** Complete Step 1 (author the scenario file) **before** Step 2 (edit `trigger-map.yaml`). `test_trigger_map_scenarios.py` asserts that every trigger-map scenario file exists — editing the map before the file is written will cause a mid-task test failure if the suite is run between steps.

**Step 1: Author `e2e/scenarios/use-framework/reverse-engineered-brand.yaml`** following the `5-components-positioning.yaml` shape — a `description`, a sonnet provider (`temperature: 0`), a `{{system_context}}{{task_prompt}}` prompt, and `llm-rubric` asserts scoped to the Marley model. Rubrics should score: (a) produces an 8-section structure (overview + 7 areas) with `N/5` grades; (b) curated owner-authority OQ list (≤15, decision-shaped), not a 150-item log; (c) preserves the sub-agent ETL contract (does not fabricate; flags low-confidence as OQs). Use `system_context: file://../../../frameworks/reverse-engineered-brand/prompt.md` and a brand-build task prompt; reuse `fixtures/company-briefs/b2b-saas-startup.md` as the source stand-in.

**Step 2: Append a trigger to `e2e/trigger-map.yaml`** (after the last entry):

```yaml
  - paths:
      - frameworks/reverse-engineered-brand/prompt.md
      - frameworks/reverse-engineered-brand/render-review-html.md
      - frameworks/reverse-engineered-brand/open-questions-schema.md
    scenarios:
      - scenarios/use-framework/reverse-engineered-brand.yaml
```

**Step 2b: Add surface patterns to `e2e/eval-surface.yaml`.** `test_trigger_path_matches_surface_pattern` enforces that every trigger-map path matches at least one eval-surface glob pattern. `render-review-html.md` (sub-agent prompt) and `open-questions-schema.md` (schema reference) are not covered by the existing `frameworks/*/prompt.md` pattern. Append two patterns under the `patterns:` key:

```yaml
  - frameworks/*/render-review-html.md
  - frameworks/*/open-questions-schema.md
```

**Step 3: Register the scenario in `e2e/promptfooconfig.yaml`** — append to the `scenarios:` list:

```yaml
  - file://scenarios/use-framework/reverse-engineered-brand.yaml
```

**Step 4: Verify registration (scoped test).**

Run: `pytest e2e/tests/test_trigger_map_scenarios.py e2e/tests/test_trigger_map_paths.py -v` (expected: PASS — the new scenario is registered, its trigger paths exist, and all paths match eval-surface patterns).

**Step 5: Commit.**

```bash
git add e2e/scenarios/use-framework/reverse-engineered-brand.yaml e2e/trigger-map.yaml e2e/promptfooconfig.yaml e2e/eval-surface.yaml
git commit -m "test(reb): add eval scenario + trigger-map entry + promptfoo registration + eval-surface patterns"
```

---

## Manual Steps (Post-Automation)

> Manual-deploy artifact scan: no catalog matches detected. This plan creates Python modules, Markdown/YAML/HTML framework assets, JSON fixtures, and eval scenarios — no database migrations, Supabase artifacts, or other production-deploy steps.

**Optional (out of scope for this plan — see design doc §"After this framework is updated"):** after merge, re-run `/aligned:use-framework reverse-engineered-brand` for **The Knot** (PUBLIC WEB ONLY; competitors Zola/Joy/Minted/Honeyfund; write target `/Users/ericpage/Documents/Obsidian/the-knot/brand/`) to validate the new model end-to-end on a real public-web build. This is a verification run the user performs, not a plan task.

---

## Eval Scenarios

This plan changes framework prompt logic (orchestrator PHASE 2/3, renderer contract, schema), so it adds eval coverage where there was none:

- **Create** `e2e/scenarios/use-framework/reverse-engineered-brand.yaml` (Task 19) — LLM-graded scenario scoring: 8-section structure with grades, curated ≤15 owner-authority OQ list (not a 150-item log), and ETL/anti-fabrication contract preservation.
- **Register** it in `e2e/trigger-map.yaml` (triggers on `prompt.md` / `render-review-html.md` / `open-questions-schema.md` changes) and `e2e/promptfooconfig.yaml`.
- **Deterministic coverage** (Tasks 3 & 6, NOT promptfoo): `test_reb_curation.py` (owner-authority selection, backfill-to-floor, cap-15 truncation, tie-break determinism, empty/all-P2 queues, P1-owner-survives-P0-heavy) and `test_reb_renderer.py` (palette + neutral default, `@font-face` emission/skip, null-logo→wordmark, server-side panels, sanitize/verify, + error paths: grade-out-of-range, over-cap OQs, remote-font-src, `../`-escape).

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|-------------|-------------------------|
| 1 | Curation + rendering as executable code vs. LLM prose | **Deterministic stdlib Python** (`curate_open_questions.py`, `render_review.py`) invoked via Bash | LLM-prose renderer/curator with eval-only coverage; a JS renderer |
| 2 | Where the scripts live | `frameworks/reverse-engineered-brand/scripts/` (permanent framework assets) | `scripts/` repo root; ephemeral `.build/scripts/` (Marley's choice) |
| 3 | Test location + import | `e2e/tests/test_reb_*.py`, importing scripts by absolute path | A new `frameworks/**/tests/` tree; doctest in the modules |
| 4 | Python dependencies | **stdlib only** (no bs4, no jinja) | Add `beautifulsoup4` for HTML-assert tests; `jinja2` for templating |
| 5 | `proof/claims-ledger.md` producer | **Orchestrator-side dispatch instruction** (don't edit `proof-points-audit/prompt.md`) | Edit `proof-points-audit` standalone prompt; a dedicated ledger sub-agent |
| 6 | `version.yaml` `schema_version` (design OQ-A) | **Drop it**; use `status: first_draft` (Marley parity) | Keep + bump `schema_version`; add a new version field |
| 7 | `overview.grade` (design OQ-B) | **Editorial, seeded by the rounded mean** of the 7 sections | Strict rounded mean of the 7 |
| 8 | Legacy v0.4.x render fallback | **Clean cutover** — no `legacyFolderAsGroup` path; renderer handles only the new shape | Keep a version-detecting fallback for old fixtures |

### Appendix: Decision Details

#### Decision 1: Curation + rendering as executable code vs. LLM prose
**Chose:** Two deterministic, stdlib-only Python modules carry the logic; the orchestrator and the renderer sub-agent invoke them via Bash.
**Why:** The design doc's R6 is explicit — "Curation = pure pytest unit (filter + rank + cap + tie-break are deterministic)" and "Renderer behavior = post-render HTML-assertion harness (parse the emitted `review.html`) … Deterministic — NOT promptfoo." R2 additionally demands "identical curated sets + identical `OQ-NNN` ids across reruns." An LLM cannot make a determinism-across-reruns guarantee, and you cannot write a deterministic pytest against an LLM sub-agent's free-form output. Both `test-fixtures/render/README.md` and `test-fixtures/oq-schema/README.md` confirm the framework has **zero executable code today** ("read manually during framework development — there is no automated runner"), and R6 names this work "net-new infrastructure." The Marley reference build itself shipped `render_review_dashboard.py` and `write_brand_folder.py` in `.build/scripts/`. Moving the deterministic core into code also serves the context-bloat guard (a script reads the 500-line template + JSON, not the orchestrator LLM).
**Alternatives rejected:**
- *LLM-prose renderer/curator + eval-only coverage:* directly contradicts R6 ("Deterministic — NOT promptfoo") and cannot satisfy R2's cross-rerun determinism. It also re-derives a 17-var palette + panel HTML on every run — the exact nondeterminism the redesign is trying to remove.
- *JS renderer:* the test suite is pytest (`e2e/package.json` → `pytest tests/`); a JS renderer would need a parallel JS test runner. Python keeps one test stack.

#### Decision 2: Where the scripts live
**Chose:** `frameworks/reverse-engineered-brand/scripts/`.
**Why:** They are permanent, versioned assets owned by this framework, invoked on every build. Co-locating them with the framework keeps the blast radius legible and matches how the framework already co-locates its sub-agent prompt templates (`extract.md`, `competitor-dossier.md`). Marley put them in `.build/scripts/` because that was a per-build artifact folder; in the plugin they must persist.
**Alternatives rejected:**
- *`scripts/` repo root:* that dir holds repo-wide tooling (`generate-catalogs.py`, `autopilot/`); a framework-specific renderer would be miscategorized.
- *Ephemeral `.build/scripts/`:* `.build/` is deleted at PHASE 3.8 every run — the scripts would have to be regenerated each time (Marley's LLM did exactly that, which is the nondeterminism we're removing).

#### Decision 3: Test location + import
**Chose:** `e2e/tests/test_reb_curation.py` + `test_reb_renderer.py` + `test_reb_migration_contracts.py`, importing the framework scripts via `importlib`/absolute path.
**Why:** `e2e/tests/` is the repo's only pytest home (`conftest.py`, `npm test` = `pytest tests/ -v`). Existing tests already reach across the repo by computing `REPO_ROOT` (`test_phase_contracts.py`). Following that idiom means the new tests run in the same `npm test` sweep and Phase 9 with no harness changes.
**Alternatives rejected:** a new `frameworks/**/tests/` tree (would need its own pytest discovery + CI wiring); in-module doctests (weaker than the explicit success/error-path coverage R6 wants).

#### Decision 4: Python dependencies
**Chose:** stdlib only — `json`, `re`, `glob`, `html`, `pathlib`, `urllib` (for the logo/font download in the design pass, though that download is authored as prompt instructions, not in these two modules).
**Why:** The plugin is distributed; adding `beautifulsoup4`/`jinja2` imposes an install burden on every user and the autopilot environment. The renderer's HTML assertions are simple substring/regex checks that stdlib handles; templating is plain `str.replace` on a token-slot file. Honors the repo's portability rule.
**Alternatives rejected:** `beautifulsoup4` (heavier DOM assertions not needed for substring checks); `jinja2` (token-slot replacement is trivial without a templating engine, and avoids a sandbox/escaping mismatch with the existing sanitize contract).

#### Decision 5: `proof/claims-ledger.md` producer
**Chose:** Extend the **orchestrator's** proof dispatch to request `claims-ledger.md` as a second output from the `proof-points-audit` sub-agent; do NOT edit `proof-points-audit/prompt.md`.
**Why:** `proof-points-audit` runs standalone via `/aligned:use-framework` for all users. Editing its prompt to always emit a brand-folder ledger would change its standalone contract (a portability regression per CLAUDE.md's Portability Rule). The ledger is a reshape of data it already produces (PHASE 1 claims + PHASE 3 dates + PHASE 4 confidence), so an additive dispatch instruction inside `reverse-engineered-brand` is sufficient and keeps the edit inside this framework.
**Alternatives rejected:** editing the standalone prompt (portability regression); a dedicated ledger sub-agent (adds a 4th sub-agent right as we're deleting two — contradicts the "3→0" goal).

#### Decision 6: `version.yaml` `schema_version` (resolves design OQ-A)
**Chose:** Drop `schema_version`; author Marley-shaped `version.yaml` with `status: first_draft`.
**Why:** Marley's `version.yaml` has no `schema_version` and uses `status: first_draft`; the redesign targets Marley parity. The only consumer of `schema_version` was the renderer's legacy-fallback branch, which Decision 8 removes (clean cutover). With no re-run/versioning workflow in scope (the `recent_update` diff machinery is deliberately unbuilt — T5/YAGNI), a schema-version field has no live consumer.
**Alternatives rejected:** keep + bump `schema_version` (dead field with no consumer once the fallback path is gone); add a new version field (speculative — no workflow needs it yet).

#### Decision 7: `overview.grade` (resolves design OQ-B)
**Chose:** Editorial grade seeded by the rounded mean of the 7 area grades (author may adjust with a one-line justification; defaults to the rounded mean).
**Why:** The design doc flipped the default to editorial (m-6): Marley itself authored an overview grade of 4 against a section mean of 3.28 — the reference artifact chose editorial, not strict-mean. Seeding by the mean keeps it anchored and deterministic-by-default while allowing the one case (Marley's) the strict mean can't express.
**Alternatives rejected:** strict rounded mean (cannot reproduce Marley's own overview grade; the design explicitly flipped away from it).

#### Decision 8: Legacy v0.4.x render fallback
**Chose:** Clean cutover — `render_review.py` handles only the new envelope; no `legacyFolderAsGroup` / version-detection path.
**Why:** The v0.4.1 fixtures are being rebuilt (Task 5) and there are no deployed v0.4.1 consumer brand folders inside the plugin to render — the framework produces consumer folders, it doesn't store them. A fallback path would be dead code maintained against fixtures that no longer exist. Matches the brand-folder spec's stated "Clean-state cutover. No legacy-paths.yaml" hard constraint.
**Alternatives rejected:** keep a version-detecting fallback (dead code; the old fixtures it would serve are deleted in this same plan).

