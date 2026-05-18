---
---
# reverse-engineered-brand `review.html` v0.4.1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Ship review.html v0.4.1 — collapse the 9-tab build-taxonomy nav to 5 CEO-vocabulary tabs, drop dense `folders[].summary` paragraphs from rendering, render Sections-at-a-Glance as 4 group rows with `What we see:` / `What we're missing:` bullets, flatten Inputs Needed to a hyphen-bulleted doc-category checklist, and add the PHASE 3.2c validator extensions that keep authored text within shape budgets.

**Source Design Doc:** `docs/plans/2026-05-18-reverse-engineered-brand-review-fix-design.md`

**Mockups:** `docs/mockups/2026-05-18-reverse-engineered-brand-review-fix.html`

**Architecture:** Additive schema bump v0.4.0 → v0.4.1: new top-level `display_groups[]` array maps `folder_ids` into 4 CEO-vocabulary groups. Renderer becomes data-driven on `display_groups[]` with `legacyFolderAsGroup()` fallback for v0.4.0 fixtures. Group-level `headline_claim` + `thinnest_gap` (≤14 words) authored by 4 parallel sub-agents dispatched at PHASE 3.2 (honors the prompt.md context-bloat guard). Voice-rewrite sub-agent gains a Step 0 shape-transformation rule that converts methodology-textbook asks into noun-form doc categories on read — framework `prompt.md` frontmatters stay intact for standalone `/aligned:use-framework <name>` UX. PHASE 3.2c gate extends with word-cap (Check 4) and verb-form rejection / required-non-empty (Check 5).

**Tech Stack:** JS (no build step, vanilla DOM in `review-template.html`); Markdown spec files in `frameworks/reverse-engineered-brand/`; JSON test fixtures in `frameworks/reverse-engineered-brand/test-fixtures/`. No Node/npm pipeline — validation runs as LLM-read prompt logic at PHASE 3.2c; renderer tests are manual paste-and-open browser checks against the locked mockup.

---

## Prerequisites

None. Every step is local file editing in this repo. The end-to-end smoke run in Task 15 reads a brand folder the user already has on disk (`~/Documents/Obsidian/marley/brand/`); if that folder is unavailable, the executor marks Task 15 as `🔄 BLOCKED` and the autopilot auto-skips it after `MAX_BLOCKED_ITERATIONS`.

---

### Task 1: Renderer-only quick wins — drop ask-tab-tag chip, drop CSS, fix KB-141 em-dash

**Files:**
- Modify: `frameworks/reverse-engineered-brand/review-template.html` (the `iaMakeTierGroup` function, the `.ask-tab-tag` CSS rule, and the empty-state copy near the `renderPerTabCallouts` empty-asks branch)

**Why these three together:** All renderer-only, no schema dependency, single coherent commit. KB-141 piggy-backs because it sits in the same render path.

**Step 1: Verify current state**

Read `review-template.html` and confirm:
- `iaMakeTierGroup` builds an `<li>` containing a link plus a `<span class="ask-tab-tag">` (look for `className: 'ask-tab-tag'` inside `iaMakeTierGroup`).
- A `.ask-tab-tag` CSS rule exists (Grep for `.ask-tab-tag` in style block).
- Empty-asks copy contains the substring `coverage is sufficient` joined with an em-dash.

**Step 2: Write the pre-change spec note**

Read `review-template.html` and confirm by inspection that the pre-change state matches what we're about to remove:
- Grep `iaMakeTierGroup` and verify it contains `className: 'ask-tab-tag'` text.
- Grep `\.ask-tab-tag` in the `<style>` block and verify the rule exists.
- Read the empty-asks copy near `renderPerTabCallouts`'s zero-ask branch and confirm the literal `'This area has no outstanding asks — coverage is sufficient.'`.

These three reads are the pre-change baseline; the diff after Steps 3–5 below removes exactly these three sites.

**Step 3: Remove `.ask-tab-tag` CSS rule**

In `review-template.html`, find the `.ask-tab-tag` rule inside the `<style>` block. Delete the rule. (Grep for `\.ask-tab-tag` to locate; deletion of the whole rule including its `{ ... }` body.)

**Step 4: Remove the chip from `iaMakeTierGroup`**

In `iaMakeTierGroup`, delete these three lines:

```js
var tag = iaEl('span', { className: 'ask-tab-tag', text: it.folderLabel });
li.appendChild(link);
li.appendChild(tag);
```

Replace with:

```js
li.appendChild(link);
```

**Step 5: Fix KB-141 em-dash**

Find the line in `renderPerTabCallouts` containing the literal `'This area has no outstanding asks — coverage is sufficient.'`. Replace with `'Coverage is sufficient here.'`.

**Step 6: Verify mockup fidelity**

Read the mockup at `docs/mockups/2026-05-18-reverse-engineered-brand-review-fix.html`. Compare your implementation by reading the modified `review-template.html`:
- Confirm `iaMakeTierGroup` no longer constructs a `<span class="ask-tab-tag">`.
- Confirm the `.ask-tab-tag` CSS rule is absent (Grep returns zero matches).
- Confirm the empty-state literal reads `'Coverage is sufficient here.'` with no em-dash or en-dash.

Live browser verification is deferred to the post-automation visual-regression pass — see `## Manual Steps (Post-Automation)`.

If you intentionally deviate from the mockup, add a note below the task heading:
> MOCKUP DEVIATION: [what changed and why]

**Step 7: Commit**

```bash
git add frameworks/reverse-engineered-brand/review-template.html
git commit -m "fix(reverse-engineered-brand): drop ask-tab-tag chip + KB-141 em-dash"
```

---

### Task 2: Update open-questions-schema.md to v0.4.1 — document `display_groups[]`

**Files:**
- Modify: `frameworks/reverse-engineered-brand/open-questions-schema.md` (the `# Open Questions Schema v0.4.0` header, the `schema_version` row, the top-level table, and a new `## display_groups entry schema` section)

**Step 1: Bump the heading and version field**

Change `# Open Questions Schema v0.4.0` to `# Open Questions Schema v0.4.1`.

Change the `schema_version` row's `Notes` column from `Currently "0.4.0"` to `Currently "0.4.1". v0.4.0 fixtures still render via legacyFolderAsGroup() fallback (see renderer changes).`

**Step 2: Add `display_groups` to the top-level table**

Insert this row in the top-level structure table immediately after the `folders` row:

```
| `display_groups` | array | NEW v0.4.1. One entry per CEO-vocabulary group; renderer prefers this over `folders[]` for tab nav, Sections-at-a-Glance, and per-tab callouts. Absent in v0.4.0 fixtures — renderer falls back to deriving synthetic groups from `folders[]` 1:1 via `legacyFolderAsGroup()`. |
```

**Step 3: Add a `## display_groups entry schema` section**

Append this section immediately before the `## behavioral_alternatives entry schema` section:

```markdown
## `display_groups` entry schema (v0.4.1+)

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Stable group id (e.g., `"how-you-show-up"`, `"who-you-sell-to"`, `"who-you-sell-against"`, `"what-you-can-prove"`). For legacy v0.4.0 fixtures, synthetic ids are `"legacy-{folder-id}"`. |
| `label` | string | yes | CEO-vocabulary label (e.g., `"How you show up"`). |
| `folder_ids` | array | yes | Array of constituent folder ids. Renderer filters OQs by `display_groups[i].folder_ids.some(fid => oq.file.startsWith(fid + "/"))`. |
| `grade` | integer | yes | `1..5`. Rounded mean of constituent folder grades, capped at 5. |
| `headline_claim` | string | yes | ≤14 words. Declarative; no questions, no conditionals. Authored by per-group sub-agent at PHASE 3.2. PHASE 3.2c Check 4 hard-fails if longer; Check 5 hard-fails if empty after trim. |
| `thinnest_gap` | string | yes | ≤14 words. Same authorship + gate rules as `headline_claim`. Empty string permitted ONLY in `legacyFolderAsGroup()` synthetic output. |
| `provided_summary` | string | yes | ≤25 words. Group-level source inventory authored by voice-rewrite sub-agent at PHASE 3.2b. |
| `input_asks` | array | yes | Union of constituents' `input_asks`, deduped by case-insensitive trim, higher tier wins. Voice-rewrite sub-agent transforms each ask on read — noun-form, doc-category, ≤12 words. Each entry: `{ tier, ask }`. |

### Authoring path

1. Orchestrator constructs `display_groups[]` shells (id + label + folder_ids + grade aggregation) at PHASE 3.2.
2. Per-group sub-agents (4 in parallel, dispatched in one assistant message) author `headline_claim` + `thinnest_gap` from constituent slice drafts.
3. Voice-rewrite sub-agent at PHASE 3.2b authors group-level `provided_summary` and rewrites group-level `input_asks[].ask` to doc-category shape.
4. PHASE 3.2c gate validates all v0.4.1 fields (word caps, banned phrases, verb-form rejection, required-non-empty).
```

**Step 4: Verify**

Read the modified file end-to-end. Confirm the v0.4.0 fallback notes are present (renderer + schema both call this out).

**Step 5: Commit**

```bash
git add frameworks/reverse-engineered-brand/open-questions-schema.md
git commit -m "docs(reverse-engineered-brand): bump OQ schema doc to v0.4.1"
```

---

### Task 3: Add `display_groups[]` to render fixtures + author negative/edge fixtures

**Files:**
- Modify: `frameworks/reverse-engineered-brand/test-fixtures/render/fixture-tiny.json` (add top-level `display_groups[]`; bump `schema_version`)
- Modify: `frameworks/reverse-engineered-brand/test-fixtures/render/fixture-realistic.json` (same)
- Modify: `frameworks/reverse-engineered-brand/test-fixtures/render/fixture-stress.json` (same)
- Modify: `frameworks/reverse-engineered-brand/test-fixtures/render/README.md` (document the new fixtures + v0.4.0 legacy-fallback fixture intent)
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/invalid-headline-too-long.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/invalid-thinnest-gap-too-long.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/invalid-provided-summary-too-long.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/invalid-ask-too-long.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/invalid-ask-verb-form.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/valid-leading-whitespace.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/valid-dedupe-collision.json`
- Create: `frameworks/reverse-engineered-brand/test-fixtures/render/valid-legacy-v0.4.0.json`

**Step 0: Note about `valid-minimal.json`**

The pre-existing `test-fixtures/oq-schema/valid-minimal.json` (v0.4.0) intentionally stays at v0.4.0 per the design doc line 287. It verifies the renderer's `legacyFolderAsGroup()` fallback path without any changes. No edit to that file in this task.

**Step 1: Author `valid-legacy-v0.4.0.json`**

Copy `fixture-tiny.json` to `valid-legacy-v0.4.0.json` verbatim. Leave `schema_version: "0.4.0"`, leave `folders[].summary` populated, do NOT add `display_groups[]`. This is the legacy-fallback exemplar — the renderer must reduce it to synthetic groups via `legacyFolderAsGroup()`.

**Step 2: Bump `fixture-tiny.json` to v0.4.1 with `display_groups[]`**

In `fixture-tiny.json`:
- Change `"schema_version": "0.4.0"` to `"schema_version": "0.4.1"`.
- After the `folders` array (and before `behavioral_alternatives`), insert:

```json
  "display_groups": [
    {
      "id": "how-you-show-up",
      "label": "How you show up",
      "folder_ids": ["strategy"],
      "grade": 5,
      "headline_claim": "Manual spreadsheet dispatch is the working competitor; lead-attribute and category framing remain open.",
      "thinnest_gap": "Recent buyer notes on what they almost chose instead of you.",
      "provided_summary": "1 pitch deck and 2 sales call transcripts; no customer interviews or competitor dossiers.",
      "input_asks": [
        { "tier": "critical", "ask": "Recent buyer notes on what they almost chose" },
        { "tier": "recommended", "ask": "Past pitch decks or board memos" }
      ]
    }
  ],
```

Verify the resulting JSON parses (manual JSON.parse check by pasting into a JS console or jq).

**Step 3: Bump `fixture-realistic.json` to v0.4.1**

In `fixture-realistic.json`:
- Change `schema_version` to `"0.4.1"`.
- Insert a `display_groups[]` array with 4 entries:
  - `how-you-show-up` → `["strategy", "language", "design"]`
  - `who-you-sell-to` → `["audiences", "personas"]`
  - `who-you-sell-against` → `["market"]` (competitive folder doesn't exist in this fixture — confirm by Grep)
  - `what-you-can-prove` → `["proof"]`

For each entry: `grade` = rounded mean of constituent folders' grades (use existing values from the file); `headline_claim` and `thinnest_gap` are ≤14-word brand-specific strings drawn from the existing folder summaries (collapse, do not invent); `provided_summary` is ≤25 words aggregating the constituent folders' `provided_summary` strings; `input_asks` is the deduped union of constituents' asks transformed to ≤12-word doc-category noun-form.

**Step 4: Bump `fixture-stress.json` to v0.4.1**

Same procedure as Step 3. The stress fixture has 7 folders and ~130 OQs — `display_groups[]` is still 4 entries; each constituent folder's asks dedupe into the group-level array. Test the dedupe rule by including at least two collision cases (same-text ask appearing in two constituent folders with different tiers).

**Step 5: Author negative fixtures**

Each negative fixture is a minimal-viable JSON (clone `valid-legacy-v0.4.0.json` then add a single `display_groups[]` entry that violates one rule). Each must have `"schema_version": "0.4.1"`.

- `invalid-headline-too-long.json`: one `display_groups[].headline_claim` with exactly 15 words (one over cap).
- `invalid-thinnest-gap-too-long.json`: one `display_groups[].thinnest_gap` with exactly 15 words.
- `invalid-provided-summary-too-long.json`: one `display_groups[].provided_summary` with exactly 26 words.
- `invalid-ask-too-long.json`: one `display_groups[].input_asks[].ask` with exactly 13 words.
- `invalid-ask-verb-form.json`: one `display_groups[].input_asks[].ask` starting with `If you have…`.

**Step 6: Author positive edge-case fixtures**

- `valid-leading-whitespace.json`: a `display_groups[].headline_claim` of 14 words preceded by a single leading space. PASSES Check 4 because `trim().split(/\s+/).filter(Boolean).length === 14`.
- `valid-dedupe-collision.json`: two constituent folders with the same ask text (e.g., `"Recorded customer or prospect conversations"`) tagged `critical` in folder A and `recommended` in folder B. Result: a single entry in the group's `input_asks` with `tier: "critical"` (higher-tier wins). Also include a third pair using different case (`"recorded customer or prospect conversations"` and `"Recorded customer or prospect conversations"`) tagged `optional` / `recommended` to verify the dedupe key uses case-insensitive trim comparison.

**Step 7: Update fixtures README**

In `frameworks/reverse-engineered-brand/test-fixtures/render/README.md`, append rows for the 8 new fixtures using the existing table format. Add a paragraph noting that v0.4.0 legacy-fallback is exercised by `valid-legacy-v0.4.0.json`.

**Step 8: Verify**

For each fixture, run `python3 -c "import json; json.load(open('PATH'))"` to confirm valid JSON. Run on all 11 files (3 modified + 8 created).

**Step 9: Commit**

```bash
git add frameworks/reverse-engineered-brand/test-fixtures/render/
git commit -m "test(reverse-engineered-brand): v0.4.1 render fixtures (positive, negative, legacy)"
```

---

### Task 4: Add `legacyFolderAsGroup()` + data-driven tab nav to renderer

**Files:**
- Modify: `frameworks/reverse-engineered-brand/review-template.html` (the `<div class="tab-bar" id="main-tabs">` block, the `switchTab` function, and a new `legacyFolderAsGroup()` helper near the existing `folderGrade` helper)

**Step 1: Author the fail-first manual check**

Open `fixture-tiny.json` (now v0.4.1) in the renderer. Tab nav still shows the old 9 buttons (build-taxonomy). Expected after this task: 5 buttons (`Overview / How you show up / Who you sell to / Who you sell against / What you can prove`). Open `valid-legacy-v0.4.0.json` in the renderer (no `display_groups[]`): tab nav should still show synthetic buttons from `folders[]` 1:1.

**Step 2: Add `legacyFolderAsGroup()` helper**

After the `folderGrade` function (`review-template.html` near the `GRADE_TOOLTIP` block), add:

```js
function legacyFolderAsGroup(folder) {
  var summary = folder.summary || '';
  var parts = summary.trim().split(/\s+/).filter(Boolean);
  var headline = parts.length <= 14 ? parts.join(' ') : parts.slice(0, 14).join(' ') + '…';
  return {
    id: 'legacy-' + folder.id,
    label: folder.label || folder.id,
    folder_ids: [folder.id],
    grade: folderGrade(folder),
    headline_claim: headline,
    thinnest_gap: '',
    provided_summary: folder.provided_summary || '',
    input_asks: folder.input_asks || []
  };
}

function resolveDisplayGroups() {
  if (OPEN_QUESTIONS.display_groups && OPEN_QUESTIONS.display_groups.length) {
    return OPEN_QUESTIONS.display_groups;
  }
  return (OPEN_QUESTIONS.folders || []).map(legacyFolderAsGroup);
}
```

Em-dash stripping in the truncation path was dropped (per Round 1 critique L1/L2): mutating the legacy display text would be a renderer-as-source-fixer anti-pattern. If a folder.summary contains an em-dash, it survives truncation as-is; the user-facing dash style stays consistent with what was originally authored.

**Step 3: Replace the static tab nav with data-driven rendering**

Replace the entire `<div class="tab-bar" id="main-tabs"> ... </div>` block (the 9 buttons) with a single Overview button:

```html
<div class="tab-bar" id="main-tabs">
  <button class="tab-btn active" onclick="switchTab('overview')">Overview</button>
</div>
```

Then add a new helper called once at script start (right after the `OPEN_QUESTIONS` / `BRAND_FOLDER_PATH` / `ORG_NAME` constants near the top of the `<script>` block):

```js
function buildTabNav() {
  var bar = document.getElementById('main-tabs');
  if (!bar) return;
  if (bar.dataset.built === 'true') return; // idempotence: renderAll may fire twice (DOMContentLoaded + readyState fallback)
  var groups = resolveDisplayGroups();
  groups.forEach(function(g) {
    var btn = document.createElement('button');
    btn.className = 'tab-btn';
    btn.textContent = g.label;
    btn.setAttribute('onclick', "switchTab('" + g.id + "')");
    bar.appendChild(btn);
  });
  bar.dataset.built = 'true';
}
```

**Step 4: Call `buildTabNav()` from `renderAll`**

In `renderAll`, add `buildTabNav();` as the first call (before `assignDisplayIds`).

**Step 5: Spec-only verification**

Read the modified `review-template.html` and confirm:
- The `<div class="tab-bar" id="main-tabs">` contains only the Overview `<button>` statically; all other buttons are appended by `buildTabNav()`.
- `buildTabNav()` reads `resolveDisplayGroups()` and appends one button per group.
- `buildTabNav()` is idempotent (`bar.dataset.built === 'true'` early return).
- `legacyFolderAsGroup()` produces `id: 'legacy-{folder-id}'` and `thinnest_gap: ''`.

This task creates the buttons but does NOT yet create the panels they point to. Clicking a non-Overview button at this point will render an empty active state — that's expected. Panels arrive in Task 7. Live browser verification is deferred to the post-automation visual-regression pass.

**Step 6: Verify mockup fidelity**

Read the mockup. Confirm Frame 1's 5-button tab bar is the target end-state. The current task only matches partially (panels arrive later); document this as expected progress.

**Step 7: Commit**

```bash
git add frameworks/reverse-engineered-brand/review-template.html
git commit -m "feat(reverse-engineered-brand): data-driven tab nav with legacyFolderAsGroup fallback"
```

---

### Task 5: Refactor `renderSectionsAtAGlance` to group rows with N/5 grades and 2 bullets

**Files:**
- Modify: `frameworks/reverse-engineered-brand/review-template.html` (the `gradePill` function and the `renderSectionsAtAGlance` function; the `.section-list` CSS to add the bullets-cell label styling)

**Step 1: Update `gradePill` to render N/5**

Change the line in `gradePill`:

```js
el.appendChild(tx(String(grade)));
```

to:

```js
el.appendChild(tx(String(grade) + '/5'));
```

The `min-width: 36px` on `.grade` already accommodates the 2 extra characters (mockup CSS lines 39-44 confirm).

**Step 2: Rewrite `renderSectionsAtAGlance`**

Replace the function body to iterate `resolveDisplayGroups()` instead of `OPEN_QUESTIONS.folders`. Each row becomes:

```js
function renderSectionsAtAGlance() {
  var el = document.getElementById('sections-at-a-glance');
  if (!el) return;
  clearEl(el);
  var groups = resolveDisplayGroups();
  if (!groups.length) {
    el.appendChild(ap(sa(ce('p', 'description'), { style: 'color:var(--color-dimmed)' }), tx('No groups found.')));
    return;
  }
  var table = ce('table', 'section-list');
  var tbody = ce('tbody');
  groups.forEach(function(g) {
    var row = sa(ce('tr', 'section-row'), { role: 'link', tabindex: '0', 'data-group': g.id });
    row.addEventListener('click', function() { switchTab(g.id); window.scrollTo({ top: 0, behavior: 'smooth' }); });
    row.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); switchTab(g.id); window.scrollTo({ top: 0, behavior: 'smooth' }); }
    });

    var gradeCell = ce('td', 'section-grade-cell');
    gradeCell.appendChild(gradePill(g.grade));

    var areaCell = ce('td', 'section-area-cell');
    areaCell.appendChild(ap(ce('span', 'label section-link'), tx(g.label)));

    var bulletsCell = ce('td', 'section-summary-cell bullets-cell');
    if (g.headline_claim) {
      var b1 = ce('p', 'bullet');
      b1.appendChild(ap(ce('span', 'b-label'), tx('What we see: ')));
      b1.appendChild(tx(g.headline_claim));
      bulletsCell.appendChild(b1);
    }
    if (g.thinnest_gap) {
      var b2 = ce('p', 'bullet');
      b2.appendChild(ap(ce('span', 'b-label'), tx("What we're missing: ")));
      b2.appendChild(tx(g.thinnest_gap));
      bulletsCell.appendChild(b2);
    }
    // L10: faint clickability hint
    var caret = sa(ce('span', 'row-caret'), { 'aria-hidden': 'true' });
    caret.appendChild(tx(' ›'));
    bulletsCell.appendChild(caret);

    row.appendChild(gradeCell);
    row.appendChild(areaCell);
    row.appendChild(bulletsCell);
    tbody.appendChild(row);
  });
  table.appendChild(tbody);
  el.appendChild(table);
}
```

**Step 3: Add CSS for `.bullet` + `.b-label` + `.row-caret`**

In the `<style>` block, add (positioned with the other `.section-list` rules):

```css
.section-list .bullets-cell .bullet { font-size: 0.9rem; line-height: 1.55; color: var(--color-foreground); margin: 0 0 4px 0; }
.section-list .bullet .b-label { color: var(--color-dimmed); font-weight: 600; }
.section-list .bullet:last-child { margin-bottom: 0; }
.section-list .row-caret { color: var(--color-dimmed); float: right; font-size: 1.1rem; }
```

**Step 4: Spec-only verification**

Read the modified `review-template.html` and confirm:
- `gradePill` appends `tx(String(grade) + '/5')`, not bare `tx(String(grade))`.
- `renderSectionsAtAGlance` iterates `resolveDisplayGroups()`, not `OPEN_QUESTIONS.folders`.
- Each row builds `bulletsCell` with one `.bullet` per `headline_claim` and one per `thinnest_gap`, with `b-label` spans `What we see:` and `What we're missing:` respectively.
- `legacyFolderAsGroup` output renders correctly because `thinnest_gap: ''` produces NO second bullet (the `if (g.thinnest_gap)` guard skips empty strings).

Live browser verification is deferred to the post-automation visual-regression pass.

**Step 5: Verify mockup fidelity**

Read `docs/mockups/2026-05-18-reverse-engineered-brand-review-fix.html` Frame 2. Compare your rendered output:
- 4 rows for the realistic/stress fixtures.
- `N/5` grade pill formatting.
- Two-bullet structure with grey `What we see:` / `What we're missing:` labels.

**Step 6: Commit**

```bash
git add frameworks/reverse-engineered-brand/review-template.html
git commit -m "feat(reverse-engineered-brand): Sections at a Glance renders 4 group rows with N/5 + bullets"
```

---

### Task 6: Flatten Overview Inputs Needed + drop happy-talk intro + sub-tab label changes

**Files:**
- Modify: `frameworks/reverse-engineered-brand/review-template.html` (the Overview sub-tab buttons, the `<p class="description">` intro paragraph at the Inputs Needed sub-panel, the `renderInputAsks` function, and the `iaMakeTierGroup` function — drop the latter entirely now that asks are flat)

**Step 1: Rename Overview sub-tab buttons**

Change the existing Overview sub-tab buttons. From the current 3 buttons (`Executive Summary`, `Sections at a Glance`, `Inputs Needed`), drop Executive Summary and rename the other two:

```html
<div class="sub-tab-bar">
  <button class="sub-tab-btn active" onclick="switchSubTab('overview','overview-focus')">Your brand at a glance</button>
  <button class="sub-tab-btn" onclick="switchSubTab('overview','overview-inputs')">Send us any of these</button>
</div>
```

Confirm the existing `<div id="sub-overview-focus">` and `<div id="sub-overview-inputs">` ids match — they should already. Make `sub-overview-focus` the default active sub-panel (it gets the `active` class on its `<div>`); remove `active` from `sub-overview-summary` (which we'll convert to a `<details>` strip in the next step).

**Step 2: Convert Executive Summary block into an expandable `<details>` strip**

Replace the entire `<div id="sub-overview-summary" class="sub-panel active"> ... </div>` block with a `<details>` element positioned BELOW the Sections at a Glance content (i.e., move it inside `sub-overview-focus`, after `<div id="sections-at-a-glance"></div>`):

```html
<details class="overview-source-detail">
  <summary>About the source material we received</summary>
  <div class="overview-source-body">
    <div id="exec-snapshot"></div>
    <div class="exec-section">
      <h4>Raw material</h4>
      <p id="exec-raw-material"></p>
    </div>
    <hr class="exec-divider" />
    <div class="exec-section">
      <h4>Primary research</h4>
      <p id="exec-primary-research"></p>
    </div>
  </div>
</details>
```

Add CSS (in `<style>`):

```css
.overview-source-detail { margin-top: 16px; font-size: 0.85rem; color: var(--color-secondary); border-top: 1px solid var(--color-muted); padding-top: 12px; }
.overview-source-detail summary { cursor: pointer; color: var(--color-dimmed); font-weight: 500; }
.overview-source-detail .overview-source-body { margin-top: 8px; }
```

**Step 3: Drop the happy-talk intro paragraph**

In the `<div id="sub-overview-inputs">` block, delete this line entirely:

```html
<p class="description">If you'd like to strengthen this report, here's what would help — organized by impact. We pulled what we could from what you sent; this list names categories of raw material that would change the result on the tab noted next to each item.</p>
```

Replace the `<h2>Inputs Needed</h2>` with `<h2>Send us any of these</h2>`.

Also delete the three tier containers:

```html
<div id="inputs-needed-critical"></div>
<div id="inputs-needed-recommended"></div>
<div id="inputs-needed-optional"></div>
```

Replace with a single container:

```html
<div id="inputs-needed-flat"></div>
```

**Step 4: Rewrite `renderInputAsks`**

Replace the entire function body:

```js
function renderInputAsks() {
  var container = document.getElementById('inputs-needed-flat');
  if (!container) return;
  while (container.firstChild) container.removeChild(container.firstChild);
  var groups = resolveDisplayGroups();
  var seen = Object.create(null);
  var flat = [];
  groups.forEach(function(g) {
    (g.input_asks || []).forEach(function(a) {
      if (!a || !a.ask) return;
      var key = a.ask.trim().toLowerCase();
      if (seen[key]) return;
      seen[key] = true;
      flat.push(a.ask);
    });
  });
  if (!flat.length) {
    var empty = iaEl('p', { className: 'provided', text: 'No additional inputs requested.' });
    container.appendChild(empty);
    return;
  }
  var ul = iaEl('ul', { className: 'inputs-flat' });
  flat.forEach(function(ask) {
    var li = iaEl('li', { text: ask });
    ul.appendChild(li);
  });
  container.appendChild(ul);
}
```

**Step 5: Delete `iaMakeTierGroup`**

Delete the entire `iaMakeTierGroup` function from the script block. It has no remaining callers.

**Step 6: Add `.inputs-flat` CSS**

Append:

```css
.inputs-flat { list-style: none; padding: 0; margin: 0; }
.inputs-flat li { padding: 7px 0; font-size: 0.95rem; line-height: 1.5; border-bottom: 1px solid var(--color-muted); }
.inputs-flat li:last-child { border-bottom: none; }
.inputs-flat li::before { content: "- "; color: var(--color-foreground); font-weight: 500; margin-right: 6px; font-family: var(--font-mono); }
```

**Step 7: Spec-only verification**

Read the modified `review-template.html` and confirm:
- The Overview sub-tab bar contains exactly two `<button class="sub-tab-btn">` elements: `Your brand at a glance` (active) and `Send us any of these`.
- The `<div id="sub-overview-summary">` block has been removed; the exec-snapshot/raw-material/primary-research divs now live inside a `<details>` element under `sub-overview-focus`.
- `iaMakeTierGroup` function is gone (Grep for `iaMakeTierGroup` should return zero matches).
- `renderInputAsks` iterates `resolveDisplayGroups()` and renders a single `<ul class="inputs-flat">` with hyphen-prefix CSS.
- The happy-talk intro `<p class="description">If you'd like to strengthen this report…</p>` is deleted.
- Hyphen-prefix on `<li>` is from the `::before` CSS rule, NOT inline `-` text — but the CSS uses `content: "- "`, which IS copied along with selected list-item text in most browsers' clipboard.

Live browser verification (including copy-paste survival) is deferred to the post-automation visual-regression pass.

**Step 8: Verify mockup fidelity**

Read mockup Frames 2 and 3. Compare. The Frame 2 `<details>` placement matches; the Frame 3 flat hyphen list matches.

**Step 9: Commit**

```bash
git add frameworks/reverse-engineered-brand/review-template.html
git commit -m "feat(reverse-engineered-brand): flatten Inputs Needed + drop Exec Summary sub-tab"
```

---

### Task 7: Restructure HTML — 4 group panels, nested per-folder paste-backs, FOLDER_LABEL_BY_ID + FOLDER_TO_GROUP_TAB

**Files:**
- Modify: `frameworks/reverse-engineered-brand/review-template.html` (the 8 folder `<div class="tab-panel">` blocks → 4 group panels; introduce `FOLDER_LABEL_BY_ID` and `FOLDER_TO_GROUP_TAB`; refactor `FRAMEWORK_BY_FOLDER` / `FRAMEWORK_TARGET` usage; refactor `renderAll` and `rebuildAllPastebacks`)

**Step 1: Replace 8 folder panel blocks with 4 group panel blocks**

Delete the 8 existing `<div id="panel-{folder}">` blocks (competitive, strategy, language, audiences, personas, market, proof, design). Insert 4 group panel blocks AFTER the Overview panel:

```html
<div id="panel-how-you-show-up" class="tab-panel">
  <div class="folder-banner" id="banner-how-you-show-up"></div>
  <div class="input-callout" id="callout-how-you-show-up" style="display:none"></div>
  <div id="panel-how-you-show-up-oqs"></div>
  <div id="panel-how-you-show-up-pastebacks"></div>
</div>
<div id="panel-who-you-sell-to" class="tab-panel">
  <div class="folder-banner" id="banner-who-you-sell-to"></div>
  <div class="input-callout" id="callout-who-you-sell-to" style="display:none"></div>
  <div id="panel-who-you-sell-to-oqs"></div>
  <div id="panel-who-you-sell-to-pastebacks"></div>
</div>
<div id="panel-who-you-sell-against" class="tab-panel">
  <div class="folder-banner" id="banner-who-you-sell-against"></div>
  <div class="input-callout" id="callout-who-you-sell-against" style="display:none"></div>
  <h3 class="alt-section-heading">What customers do today (without you)</h3>
  <div id="behavioral-alternatives"></div>
  <h3 class="alt-section-heading alt-section-heading-secondary">Named competitors</h3>
  <div id="competitor-cards"></div>
  <div id="panel-who-you-sell-against-oqs"></div>
  <div id="panel-who-you-sell-against-pastebacks"></div>
</div>
<div id="panel-what-you-can-prove" class="tab-panel">
  <div class="folder-banner" id="banner-what-you-can-prove"></div>
  <div class="input-callout" id="callout-what-you-can-prove" style="display:none"></div>
  <div id="panel-what-you-can-prove-oqs"></div>
  <div id="panel-what-you-can-prove-pastebacks"></div>
</div>
```

For legacy v0.4.0 fixtures, the renderer's `buildGroupPanels()` step (added below) generates synthetic legacy panels at runtime.

**Step 2: Add `FOLDER_LABEL_BY_ID` and `FOLDER_TO_GROUP_TAB`**

After the existing `FOLDER_LABEL_TO_TAB` constant declaration, add:

```js
var FOLDER_LABEL_BY_ID = {
  strategy: 'Strategy',
  language: 'Language',
  audiences: 'Audiences',
  personas: 'Personas',
  market: 'Market',
  proof: 'Proof',
  design: 'Design',
  competitive: 'Competitive'
};

function buildFolderToGroupTab() {
  var map = {};
  resolveDisplayGroups().forEach(function(g) {
    (g.folder_ids || []).forEach(function(fid) {
      map[fid] = g.id;
    });
  });
  return map;
}
```

Note: `FOLDER_TO_GROUP_TAB` is built at render time (not a static const) because legacy fallback produces `legacy-{folder-id}` group ids dynamically.

**Step 3: Add `buildGroupPanels()` for legacy fallback**

Right after `buildTabNav` (declared in Task 4), add:

```js
function buildGroupPanels() {
  if (OPEN_QUESTIONS.display_groups && OPEN_QUESTIONS.display_groups.length) return;
  // Legacy fallback: synthesize panel divs for each synthetic group.
  // Idempotent: re-invocation skips groups whose panel already exists in the DOM.
  var groups = resolveDisplayGroups();
  var host = document.querySelector('body');
  groups.forEach(function(g) {
    if (document.getElementById('panel-' + g.id)) return; // idempotence guard
    var panel = document.createElement('div');
    panel.id = 'panel-' + g.id;
    panel.className = 'tab-panel';
    ['banner-', 'callout-', 'panel-{id}-oqs', 'panel-{id}-pastebacks'].forEach(function(tmpl) {
      var d = document.createElement('div');
      if (tmpl === 'banner-') { d.className = 'folder-banner'; d.id = 'banner-' + g.id; }
      else if (tmpl === 'callout-') { d.className = 'input-callout'; d.style.display = 'none'; d.id = 'callout-' + g.id; }
      else { d.id = tmpl.replace('{id}', g.id); }
      panel.appendChild(d);
    });
    host.appendChild(panel);
  });
}
```

Call `buildGroupPanels()` from `renderAll` immediately after `buildTabNav()` and before `assignDisplayIds()`.

**Step 4: Refactor `renderAll` — keep `renderFolderPanel` calls for now**

Replace the existing `renderAll` body with:

```js
function renderAll() {
  buildTabNav();
  buildGroupPanels();
  assignDisplayIds();
  renderExecNarrative();
  renderExecSnapshot();
  renderBehavioralAlternatives();
  renderCompetitorCards();
  renderSectionsAtAGlance();
  // Group-panel rendering swaps in at Task 8. For this intermediate commit,
  // keep the per-folder render loop; group panels are empty containers until then.
  ['strategy', 'language', 'audiences', 'personas', 'market', 'proof', 'design'].forEach(function(id) {
    if (document.getElementById('panel-' + id + '-content')) renderFolderPanel(id);
  });
}
```

Because the existing folder-panel DOM (the `panel-strategy-content` etc. divs) was deleted in Step 1, the `if (document.getElementById(...))` guard makes `renderFolderPanel` a no-op for the deleted folders — preventing runtime errors. This keeps the commit boot-clean; Task 8 replaces this loop with `renderGroupPanel(g)`.

**Step 5: Refactor `rebuildAllPastebacks`**

Replace with:

```js
function rebuildAllPastebacks() {
  resolveDisplayGroups().forEach(function(g) {
    (g.folder_ids || []).forEach(function(fid) {
      var ta = document.getElementById('pasteback-' + fid);
      if (ta) rebuildPasteBack(fid);
    });
  });
}
```

This still iterates per-folder because each constituent framework's paste-back is per-folder; the parent group is just the container.

**Step 6: Update `renderPerTabCallouts` (interim — full rewrite in Task 9)**

In this commit, change the `FOLDER_LABEL_TO_TAB[folder.label] || folder.id` lookup in `renderPerTabCallouts` so it routes to the group panel's callout container instead of the now-deleted per-folder callout. Use `buildFolderToGroupTab()` to map folder id → group id, then write into `callout-{group-id}`. Full structural callout rewrite (single heading + hyphen bullets) lands in Task 9; this commit just keeps the legacy callout rendering alive.

**Step 7: Audit paste-back binding code against the new DOM**

The existing `pasteback-{folder}` textareas were declared inside the now-deleted folder panel divs. The new nested per-folder paste-back DOM (with `textarea#pasteback-{fid}` inside each group panel) is built by `renderGroupPanel` in Task 8 — so for this commit, no `pasteback-{fid}` textareas exist yet, and `rebuildPasteBack(fid)` in Step 5's new `rebuildAllPastebacks` is a no-op due to the `if (ta)` guard.

Grep `review-template.html` for these symbols to confirm no other binding sites need updates:
- `copyPasteback(` — defined; takes a folder id; reads `pasteback-{folder}`. No change needed — folder ids stay in the textarea ids inside group panels (Task 8).
- `regeneratePasteback(` — same shape; no change.
- `rebuildPasteBack(` — same shape; uses `pasteback-{folder}` id; no change.
- `data-folder=` — OQ cards still carry `data-folder` for buildPasteBack to filter; verify `buildPasteBack(folder)` still works against group-rendered OQ cards (Task 8 ensures `data-folder` is set per OQ from `q.file.split('/')[0]`).
- `pasteback-` (literal prefix) — confirm no other ids depend on the per-folder DOM that was deleted.

Document any missing binding as a follow-up bullet at the bottom of this task body. Do not fix mid-task — the comprehensive paste-back DOM lives in Task 8.

**Step 8: Spec-only verification (machine-checkable)**

Re-read the modified script and confirm by spec inspection:
- `buildTabNav()` is called once at the top of `renderAll`.
- `buildGroupPanels()` is called after `buildTabNav()`.
- The `renderFolderPanel` loop guards on `document.getElementById('panel-' + id + '-content')` so deletions in Step 1 don't throw.
- `rebuildAllPastebacks` uses `if (ta) rebuildPasteBack(fid)` and never throws on missing textareas.

Live browser verification is deferred to the post-automation visual-regression pass — see `## Manual Steps (Post-Automation)`.

**Step 9: Verify mockup fidelity**

Read `docs/mockups/2026-05-18-reverse-engineered-brand-review-fix.html` Frame 4. The mockup's group-panel layout (banner + callout + OQ cards + nested paste-backs) is the target end-state. This task's intermediate commit creates the empty group panel shells; OQ cards + nested paste-backs are filled by Task 8.

If you intentionally deviate from the mockup (e.g., discovered a better approach during implementation), add a note below the task heading:
> MOCKUP DEVIATION: [what changed and why]

**Step 10: Commit**

```bash
git add frameworks/reverse-engineered-brand/review-template.html
git commit -m "refactor(reverse-engineered-brand): 4 group panels + folder→group routing helpers"
```

---

### Task 8: Implement `renderGroupPanel` — banner without bullets, OQ filter/sort, chip-area, nested per-folder paste-backs

**Files:**
- Modify: `frameworks/reverse-engineered-brand/review-template.html` (replace `renderFolderPanel` with `renderGroupPanel`; rename `renderFolderBanner` → `renderGroupBanner` and drop bullet rendering; add `chip-area` to `renderOQCard`; add CSS for `chip-area`)

**Step 1: Author `renderGroupBanner`**

Replace `renderFolderBanner` with:

```js
function renderGroupBanner(group, oqs) {
  if (!group) return null;
  var assumptions = oqs.filter(function(q) { return q.confidence !== 'low'; });
  var questions = oqs.filter(function(q) { return q.confidence === 'low'; });
  var highPriority = oqs.filter(function(q) { return q.impact === 'P0'; }).length;

  var banner = ce('div', 'folder-banner');
  banner.appendChild(ap(ce('div', 'banner-grade'), gradePill(group.grade)));

  var body = ce('div', 'banner-body');
  body.appendChild(ap(ce('h2'), tx(group.label)));

  var counts = ce('p', 'banner-counts');
  counts.appendChild(ap(ce('strong'), tx(String(assumptions.length))));
  counts.appendChild(tx(' assumptions, '));
  counts.appendChild(ap(ce('strong'), tx(String(questions.length))));
  counts.appendChild(tx(' questions, '));
  counts.appendChild(ap(ce('strong'), tx(String(highPriority))));
  counts.appendChild(tx(' high-priority'));
  body.appendChild(counts);

  banner.appendChild(body);
  return banner;
}
```

Note the explicit absence of `.banner-summary` / `.banner-bullet` — per Decision 6, the banner shows grade + label + counts only.

**Step 2: Author `renderGroupPanel`**

Replace `renderFolderPanel` with:

```js
function renderGroupPanel(group) {
  var bannerEl = document.getElementById('banner-' + group.id);
  var oqsEl = document.getElementById('panel-' + group.id + '-oqs');
  var pbEl = document.getElementById('panel-' + group.id + '-pastebacks');
  if (!bannerEl || !oqsEl || !pbEl) return;

  var oqs = (OPEN_QUESTIONS.open_questions || []).filter(function(q) {
    return (group.folder_ids || []).some(function(fid) {
      return q.file && q.file.indexOf(fid + '/') === 0;
    });
  });

  clearEl(bannerEl);
  var banner = renderGroupBanner(group, oqs);
  if (banner) bannerEl.appendChild(banner);

  // OQ sort: P0 → P1 → P2, then by file lexically
  var priOrder = { P0: 0, P1: 1, P2: 2 };
  oqs.sort(function(a, b) {
    var pa = priOrder[a.impact] != null ? priOrder[a.impact] : 9;
    var pb = priOrder[b.impact] != null ? priOrder[b.impact] : 9;
    if (pa !== pb) return pa - pb;
    return (a.file || '').localeCompare(b.file || '');
  });

  clearEl(oqsEl);
  if (!oqs.length) {
    oqsEl.appendChild(ap(ce('p', 'empty-group'), tx('Coverage is sufficient across this area.')));
  } else {
    oqs.forEach(function(q) {
      var folderId = (q.file || '').split('/')[0];
      oqsEl.appendChild(renderOQCard(q, folderId));
    });
  }

  // Nested per-folder paste-backs (one <details> per constituent folder).
  // Skip `competitive`: it has no on-disk slice files (behavioral_alternatives +
  // competitor_cards render at the top of the group panel; there is no
  // framework-dispatch paste-back target).
  clearEl(pbEl);
  (group.folder_ids || []).filter(function(fid) { return fid !== 'competitive'; }).forEach(function(fid) {
    var det = ce('details', 'group-pasteback');
    var sum = ce('summary');
    var fwid = FRAMEWORK_BY_FOLDER[fid];
    sum.appendChild(tx((FOLDER_LABEL_BY_ID[fid] || fid) + (fwid ? ' → ' + fwid : '')));
    det.appendChild(sum);
    var ta = ce('textarea');
    ta.id = 'pasteback-' + fid;
    ta.setAttribute('placeholder', 'Paste-back prompt will appear here after you triage the cards above...');
    det.appendChild(ta);
    var actions = ce('div', 'paste-back-actions');
    actions.appendChild(sa(ap(ce('button', 'btn'), tx('Copy prompt')), { onclick: "copyPasteback('" + fid + "')" }));
    actions.appendChild(sa(ap(ce('button', 'btn btn-primary'), tx('Regenerate')), { onclick: "regeneratePasteback('" + fid + "')" }));
    det.appendChild(actions);
    pbEl.appendChild(det);
  });
}
```

**Step 3: Add `chip-area` to `renderOQCard`**

In the `renderOQCard` function, inside the `hdr` build block, after the conf chip line (`hdr.appendChild(chip('conf: ' + confLabel, ...));`), insert:

```js
var areaLabel = FOLDER_LABEL_BY_ID[folderId] || folderId;
hdr.appendChild(chip(areaLabel, 'chip-area'));
```

**Step 4: Add CSS for `chip-area` + `empty-group` + `group-pasteback`**

```css
.chip-area { background: var(--color-surface); color: var(--color-secondary); font-family: var(--font-sans); }
.empty-group { font-size: 0.9rem; color: var(--color-dimmed); font-style: italic; margin: 12px 0; }
.group-pasteback { margin-bottom: 10px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 8px; padding: 10px 14px; }
.group-pasteback summary { cursor: pointer; font-size: 0.9rem; font-weight: 600; }
.group-pasteback textarea { width: 100%; min-height: 60px; margin-top: 8px; font-family: var(--font-mono); font-size: 0.78rem; border: 1px solid var(--color-border); border-radius: 4px; padding: 8px; }
.group-pasteback .paste-back-actions { margin-top: 8px; display: flex; gap: 8px; }
```

**Step 5: Spec-only verification**

Read the modified `review-template.html` and confirm:
- `renderGroupBanner` builds `.banner-grade`, `.banner-body > h2`, and `.banner-counts`. There is no `.banner-summary` or `.banner-bullet` construction.
- `renderGroupPanel` filters OQs via `(group.folder_ids || []).some(fid => q.file.indexOf(fid + '/') === 0)`.
- OQs are sorted: `priOrder = {P0:0, P1:1, P2:2}` first; then `localeCompare` on `file`.
- `renderOQCard` appends `chip(areaLabel, 'chip-area')` where `areaLabel = FOLDER_LABEL_BY_ID[folderId] || folderId`.
- Nested paste-back loop filters out `competitive` (Round 1 M3).
- Empty-group branch appends `<p class="empty-group">Coverage is sufficient across this area.</p>`.

Live browser verification is deferred to the post-automation visual-regression pass.

**Step 6: Add an empty-group fixture**

Create `frameworks/reverse-engineered-brand/test-fixtures/render/valid-empty-group.json`. Same shape as `fixture-tiny.json` but with `open_questions: []`. Verify the rendered group panel shows the `Coverage is sufficient across this area.` text under the callout.

**Step 7: Verify mockup fidelity**

Read mockup Frame 4. Compare your rendered output:
- Group banner shape (grade + label + counts).
- Group callout shape (`What we have, what would help` — full rewrite in next task; for now the legacy callout is acceptable).
- OQ cards with CEO-vocabulary area chips.
- Nested `<details>` paste-backs.

**Step 8: Commit**

```bash
git add frameworks/reverse-engineered-brand/review-template.html frameworks/reverse-engineered-brand/test-fixtures/render/valid-empty-group.json
git commit -m "feat(reverse-engineered-brand): group panel banner + OQ filter/sort + chip-area + nested paste-backs"
```

---

### Task 9: Rewrite `renderPerTabCallouts` for group level — single heading, hyphen bullets

**Files:**
- Modify: `frameworks/reverse-engineered-brand/review-template.html` (the `renderPerTabCallouts` function; the `SINGLE_INSTANCE_FOLDERS` constant — delete; the `DOMContentLoaded` listener that calls both `renderInputAsks` and `renderPerTabCallouts`)

**Step 1: Delete `SINGLE_INSTANCE_FOLDERS`**

This constant was used to gate which folders got a callout. With groups, every group gets a callout. Delete the entire `var SINGLE_INSTANCE_FOLDERS = { ... }` block.

**Step 2: Rewrite `renderPerTabCallouts`**

Replace the function body with:

```js
function renderPerTabCallouts() {
  var groups = resolveDisplayGroups();
  groups.forEach(function(g) {
    var container = document.getElementById('callout-' + g.id);
    if (!container) return;
    while (container.firstChild) container.removeChild(container.firstChild);
    var provided = g.provided_summary || '';
    var asks = g.input_asks || [];
    if (!provided && !asks.length) {
      container.style.display = 'none';
      return;
    }
    container.appendChild(iaEl('h3', { text: 'What we have, what would help' }));
    if (provided) {
      var p = iaEl('p', { className: 'provided' });
      p.appendChild(document.createTextNode('We received: ' + provided));
      container.appendChild(p);
    }
    if (asks.length) {
      container.appendChild(iaEl('p', { className: 'provided would-help-heading', text: 'Would help:' }));
      var list = iaEl('ul', { className: 'callout-list' });
      asks.forEach(function(a) {
        if (!a || !a.ask) return;
        var li = iaEl('li');
        // Hyphen bullet for copy-paste survival
        li.appendChild(document.createTextNode('- ' + a.ask));
        list.appendChild(li);
      });
      container.appendChild(list);
    }
    container.style.display = '';
  });
}
```

**Step 3: Move the bootstrap call into `renderAll`**

Find the standalone `DOMContentLoaded` listener:

```js
document.addEventListener('DOMContentLoaded', function() {
  renderInputAsks();
  renderPerTabCallouts();
});
```

Delete it. Add both calls to the end of `renderAll`:

```js
function renderAll() {
  buildTabNav();
  buildGroupPanels();
  assignDisplayIds();
  renderExecNarrative();
  renderExecSnapshot();
  renderBehavioralAlternatives();
  renderCompetitorCards();
  renderSectionsAtAGlance();
  resolveDisplayGroups().forEach(function(g) { renderGroupPanel(g); });
  renderInputAsks();
  renderPerTabCallouts();
}
```

This collapses the previous dual-bootstrap (one `DOMContentLoaded` for the main render, a separate one for Inputs Needed + callouts) into a single deterministic path. The existing already-loaded fallback (`if (document.readyState !== 'loading') { renderAll(); ... }`) now covers both.

**Step 4: Add CSS for `.would-help-heading` and `.callout-list`**

```css
.input-callout .would-help-heading { font-size: 0.88rem; color: var(--color-foreground); margin: 12px 0 6px 0; font-weight: 600; }
.input-callout .callout-list { list-style: none; padding: 0; margin: 0; }
.input-callout .callout-list li { font-size: 0.9rem; line-height: 1.6; padding: 3px 0; font-family: inherit; }
```

**Step 5: Spec-only verification**

Read the modified `review-template.html` and confirm:
- `renderPerTabCallouts` iterates `resolveDisplayGroups()`, not `OPEN_QUESTIONS.folders`.
- It calls `iaEl('h3', { text: 'What we have, what would help' })` exactly once per callout (single heading, not two).
- The `<p class="provided">` text starts with the literal `'We received: '` prefix.
- `Would help:` label is appended only when `asks.length > 0`.
- Each `<li>` appends a text node prefixed with `'- '` (inline hyphen, copy-paste survives without depending on CSS `::before`).
- When both `provided` is empty AND `asks.length === 0`, the container is hidden (`container.style.display = 'none'`).

Live browser verification is deferred to the post-automation visual-regression pass.

> **Side-effect note:** The bootstrap change in Step 3 (moving `renderInputAsks` + `renderPerTabCallouts` into `renderAll`) means the already-loaded fallback path (`if (document.readyState !== 'loading') { renderAll(); ... }`) now also runs them. Previously they only fired on `DOMContentLoaded`, which was missed when the script was injected after the load event. The new path covers both timings (Round 1 L6).

**Step 6: Verify mockup fidelity**

Read mockup Frame 4 callout structure. Confirm:
- One heading instead of two.
- Hyphen-prefixed list items.
- `We received: …` framing.

**Step 7: Commit**

```bash
git add frameworks/reverse-engineered-brand/review-template.html
git commit -m "feat(reverse-engineered-brand): group-level callout with single heading + hyphen bullets"
```

---

### Task 10: Update `voice-rewrite.md` — Step 0 shape transformation + group-level provided_summary

**Files:**
- Modify: `frameworks/reverse-engineered-brand/voice-rewrite.md` (insert Step 0; refactor Step 2 to per-group instead of per-folder; update input table and output JSON example)

> **Behavior change:** Step 0 shape transformation is not voice rewriting — it semantically compresses curated framework-frontmatter asks into generic noun-form doc categories. The sub-agent gains authoring authority over an artifact previously authored by framework owners. Framework owners (`5-components-positioning`, `brand-voice`, `buyer-persona`, etc.) should sanity-check the example transformations in Step 1 below before merge. The standalone `/aligned:use-framework <name>` UX is unaffected — the rewrite happens only on read by review.html, not on the framework `prompt.md` frontmatter source.

**Step 1: Rewrite the inputs table**

Replace the table with:

```markdown
| Placeholder | Description |
|---|---|
| `{ask-list-json}` | JSON array of `{group_id, index, tier, ask}` — every ask across all `display_groups[]`, post-aggregation |
| `{group-sources-json}` | JSON object keyed by `group_id`; value is the aggregated registry source list across constituent folders |
| `{brand-voice-content}` | Resolved brand voice file contents, or the literal string `PASS_THROUGH` if neither candidate path exists |
```

**Step 2: Insert Step 0 — Shape transformation**

Before the existing Step 1, insert:

```markdown
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
```

**Step 3: Update Step 1 to operate on group-tagged asks**

Replace the `(folder_id, index)` references in Step 1 with `(group_id, index)`. The five rule bullets are unchanged in content but the tuple keys move from folder to group.

**Step 4: Rewrite Step 2 for group-level provided_summary**

Replace Step 2 with:

```markdown
### Step 2: Author per-group provided_summary

For each `group_id` in `{group-sources-json}`, write one ≤25-word sentence inventorying the aggregated source material across the group's constituent folders. Use the union of source-type counts and signal-tag presence as evidence. Examples:

- `"3 marketing decks, 1 founder essay, 1 partial product brief; no recorded sales calls."`
- `"5 case study drafts, 1 outcome dashboard; no peer-reviewed citations or security correspondence."`

Same banned phrases as Step 1 (no em/en dashes; no AI buzzwords). Same digit/typed-noun preservation rules.
```

**Step 5: Update Step 3 — return JSON shape**

Replace the output example with:

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

Failure modes line gets the field set updated: `missing 'asks' key`, `missing 'provided_summaries' key`, `any ask entry missing 'group_id' or 'index'`.

**Step 6: Verify**

Read the file end-to-end. Confirm:
- Step 0 exists, runs before Step 1, contains the three shape rules and the regex callout.
- Step 1's tuple keys are `(group_id, index)`.
- Step 2 references per-group not per-folder.
- Step 3 example uses `group_id`.

**Step 7: Commit**

```bash
git add frameworks/reverse-engineered-brand/voice-rewrite.md
git commit -m "feat(reverse-engineered-brand): voice-rewrite Step 0 shape transformation + group-level provided_summary"
```

---

### Task 11: Create `group-bullets.md` sub-agent prompt template

**Files:**
- Create: `frameworks/reverse-engineered-brand/group-bullets.md`

**Step 1: Write the new prompt file**

Create `frameworks/reverse-engineered-brand/group-bullets.md` with the following content:

```markdown
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
```

**Step 2: Verify**

Read the file end-to-end. Confirm all 6 placeholders are documented, all 5 procedure steps are present, and the failure modes table maps cleanly to PHASE 3.2c gate checks 2/4/5.

**Step 3: Commit**

```bash
git add frameworks/reverse-engineered-brand/group-bullets.md
git commit -m "feat(reverse-engineered-brand): add group-bullets sub-agent prompt template"
```

---

### Task 12: Update `prompt.md` PHASE 3.2 — group-level synthesis via 4 parallel sub-agents

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (extend Step 3.2 with the new group-construction block and the parallel sub-agent dispatch instructions)

**Step 1: Insert the group-construction block at the end of Step 3.2**

After the existing "Write `provided_summary` placeholder" paragraph (which sets `folders[].provided_summary = null`), insert a new subsection:

```markdown
**Step 3.2-NEW: Build `display_groups[]` shells + dispatch group-bullets sub-agents.**

After `folders[]` is built, construct the `display_groups[]` array with exactly 4 entries in this order:

1. `id: "how-you-show-up"`, `label: "How you show up"`, `folder_ids: ["strategy", "language", "design"]`
2. `id: "who-you-sell-to"`, `label: "Who you sell to"`, `folder_ids: ["audiences", "personas"]`
3. `id: "who-you-sell-against"`, `label: "Who you sell against"`, `folder_ids: ["market", "competitive"]`
4. `id: "what-you-can-prove"`, `label: "What you can prove"`, `folder_ids: ["proof"]`

If any listed folder is absent from `folders[]` (e.g., `competitive` is a top-level synthetic folder, not a brand-folder subdirectory — gate behavior: include if behavioral_alternatives + competitors arrays are non-empty), filter `folder_ids` to actually-present folders before continuing.

For each group, compute the shell fields:
- `grade`: rounded mean of constituent folders' `grade` values; cap at 5.
- `input_asks`: union of constituent folders' `input_asks`, deduped by case-insensitive whitespace-trimmed `ask` text. Higher tier wins on collision (`critical` > `recommended` > `optional`). Within a tier, preserve first-seen order in `display_groups[i].folder_ids` order.
- `headline_claim`, `thinnest_gap`, `provided_summary`: temporarily set to `""` placeholders; sub-agents populate them next.

**Dispatch 4 sub-agents in PARALLEL** (single assistant message, 4 Task calls). Each uses `subagent_type: general-purpose` and the prompt template at `frameworks/reverse-engineered-brand/group-bullets.md`. Substitute the placeholders per group, including `{output-json-path}` = `{brand-folder-path}/.build/groups/{group-id}.json`.

The `{canonical-pre-synthesis-blob-path}` placeholder resolves to `{brand-folder-path}/.build/canonical-pre-synthesis-blob.md` — the 1-paragraph blob the orchestrator already authored at PHASE 2.2 from the Source Registry (org-name + brief positioning hypothesis + brief ICP hypothesis). The same blob is passed to every framework dispatch, so the group-bullets sub-agents share that baseline view. Sub-agents read it as orienting context; they do not modify it.

**After all 4 return:** Read each `.build/groups/{group-id}.json` file. Validate the JSON parses and contains `headline_claim` + `thinnest_gap` keys. Merge into the in-memory `display_groups[]` by `id`. If any file is missing or malformed: hard-fail with `group: {id}, failure: file_missing|malformed_json|missing_keys`.

**Resume semantics.** If a sub-agent succeeded on a previous run (its `.build/groups/{group-id}.json` is present and parses), skip re-dispatch for that group. This makes PHASE 3.2 idempotent across reruns and avoids re-paying PHASE 1+1.5+2 costs after a single-sub-agent failure.
```

**Step 2: Bump `version.yaml` template and `.open-questions.json` JSON example**

The disk-write step at PHASE 3.6/3.7 still emits `schema_version: "0.4.0"` (`prompt.md` line 479 — `version.yaml` template; line 497 — top-level JSON example). Without bumping these, the orchestrator emits v0.4.0 files even after `display_groups[]` is built in memory, the renderer never sees v0.4.1 content, and Check 5 never fires.

Two edits:

a. Find the `version.yaml` template line (Grep for `version.yaml` in `prompt.md`). Change `schema_version: "0.4.0"` to `schema_version: "0.4.1"`.

b. Find the `.open-questions.json` block (Grep for `.open-questions.json` in `prompt.md`). In the example JSON, change `"schema_version": "0.4.0"` to `"schema_version": "0.4.1"`, and insert a `display_groups[]` block immediately after the `folders[]` array (using the same shape as the design doc's Architecture section):

```json
  "display_groups": [
    {
      "id": "how-you-show-up",
      "label": "How you show up",
      "folder_ids": ["strategy", "language", "design"],
      "grade": 3,
      "headline_claim": "<≤14 words, brand-specific, declarative>",
      "thinnest_gap": "<≤14 words, brand-specific, declarative>",
      "provided_summary": "<≤25 words inventorying group-level source material>",
      "input_asks": [
        { "tier": "critical", "ask": "<≤12-word noun-form doc-category>" }
      ]
    }
  ],
```

**Step 3: Verify**

Read the modified prompt.md PHASE 3 section. Confirm:
- The 4 hard-coded groups match the design doc's mapping.
- "PARALLEL (single assistant message)" appears explicitly so a future LLM executor doesn't fan them out serially.
- Resume semantics are stated alongside dispatch.
- `version.yaml` template now says `"0.4.1"`.
- The `.open-questions.json` example shows `display_groups[]` as a top-level field.

**Step 4: Commit**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reverse-engineered-brand): PHASE 3.2 dispatches 4 parallel group-bullets sub-agents + schema bump"
```

---

### Task 13: Update `prompt.md` PHASE 3.2b — group-level voice rewrite + PHASE 3.2c gate extensions

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (PHASE 3.2b and PHASE 3.2c sections)

**Step 1: Rewrite PHASE 3.2b input construction**

In PHASE 3.2b, change the orchestrator-input description:
- Replace `(folder_id, index, tier)` with `(group_id, index, tier)` throughout.
- Replace "Per-folder lists of `(source_id, source_type, signal_tags)` tuples" with "Per-group aggregated registry tuples (union across the group's `folder_ids`)".

Update the merge step:
- Change `folders[folder_id].input_asks[index].ask` to `display_groups[group_id].input_asks[index].ask`.
- Change `folders[folder_id].provided_summary` to `display_groups[group_id].provided_summary`.

**Step 2: Update the sub-agent return-shape example**

Replace the JSON example in PHASE 3.2b with:

```json
{
  "asks": [
    {"group_id": "how-you-show-up", "index": 0, "tier": "critical", "ask": "<voice-revised, shape-transformed>"}
  ],
  "provided_summaries": {
    "how-you-show-up": "3 marketing decks, 1 founder essay; no recorded sales calls."
  }
}
```

**Step 3: Extend PHASE 3.2c Check 2 (banned-phrase regex)**

Update Check 2 to cover the new fields. Find the line beginning with `**Check 2 — Banned-phrase regex.**`. Change "every post-pass `ask` string AND every `provided_summary` string" to:

> every post-pass `ask` string AND every `provided_summary` string AND every `display_groups[].headline_claim` AND every `display_groups[].thinnest_gap`.

The 3 sub-regex patterns are unchanged (em/en-dash; `it's not X, it's Y`; AI buzzwords).

**Step 4: Add Check 4 (NEW — word-count caps)**

Append immediately after Check 3:

```markdown
**Check 4 — Word-count caps (NEW).** Use `trim().split(/\s+/).filter(Boolean).length` to compute the word count for each field below. Hard-fail with `field: {name}, scope: {group_id or folder_id}, count: {n}, cap: {c}, value: {string}` if `count > cap`:

| Field | Scope | Cap |
|---|---|---|
| `folders[].provided_summary` | per folder | 25 |
| `folders[].input_asks[].ask` | per folder, per ask | 12 |
| `display_groups[].headline_claim` | per group | 14 |
| `display_groups[].thinnest_gap` | per group | 14 |
| `display_groups[].provided_summary` | per group | 25 |
| `display_groups[].input_asks[].ask` | per group, per ask | 12 |

`folders[].headline_claim` and `folders[].thinnest_gap` are NOT capped because they DO NOT EXIST in the schema.
```

**Step 5: Add Check 5 (NEW — shape compliance)**

Append immediately after Check 4:

```markdown
**Check 5 — Shape compliance (NEW).**

a. **Verb-form rejection.** For every `ask` in `display_groups[].input_asks[]` AND `folders[].input_asks[]`, apply the case-insensitive regex `^\s*(if|ideally|when|where the buyer)\b`. On match: hard-fail with `field: input_asks.ask, scope: {group_id|folder_id}, index: {i}, matched: {pattern}, value: {string}`.

b. **Required-non-empty.** For every `display_groups[i]`, verify `headline_claim` and `thinnest_gap` are non-empty after `trim()`. On either empty: hard-fail with `field: {headline_claim|thinnest_gap}, group: {id}, reason: empty_or_whitespace_only`.

c. **Field presence.** For every `display_groups[i]`, verify the keys `id`, `label`, `folder_ids`, `grade`, `headline_claim`, `thinnest_gap`, `provided_summary`, `input_asks` are all present (`folder_ids` and `input_asks` may be empty arrays; the four required strings may NOT). On missing key: hard-fail with `field: {key}, group: {id}, reason: missing`.

Empty-string `thinnest_gap` IS permitted in the legacy-fallback path (`legacyFolderAsGroup()` produces it for v0.4.0 fixtures rendered without authoring). Check 5 is enforced ONLY on authored v0.4.1 output. The detection signal: `display_groups[i].id` does NOT start with `legacy-`. Synthetic legacy ids are generated only by the renderer's `legacyFolderAsGroup()` helper, never by the orchestrator's PHASE 3.2 authoring path. The gate at PHASE 3.2c runs against orchestrator output (in-memory `display_groups[]` immediately before `.open-questions.json` is written) — at that point no legacy ids exist, so the carveout is in practice a documentation safeguard, not a runtime branch.

**Behavior change note (Check 4 caps on `folders[].provided_summary` and `folders[].input_asks[].ask`):** These caps formalize an implicit constraint that already existed in the voice-rewrite sub-agent prompt ("1 sentence ≤25 words", "12-word cap" in Step 0). Existing v0.4.0 brand-folder rebuilds may hit the cap if previous runs produced over-budget text. Operator recovery is to delete the affected folder's `.build/voice-rewrite.json` and rerun PHASE 3.2b. No source-data modification is required.
```

**Step 6: Update Check 1 (array length parity)**

Find Check 1. Change "For each folder, the count of `input_asks` after Step 3.2b must equal the count before Step 3.2b" to:

> For each group, the count of `display_groups[i].input_asks` after Step 3.2b must equal the count before Step 3.2b (the orchestrator-aggregated count, pre-voice-rewrite).

**Step 7: Update Check 3 (tier preservation)**

Find Check 3. Change "For each folder, walk `input_asks` by index" to:

> For each group, walk `display_groups[i].input_asks` by index.

**Step 8: Verify**

Read PHASE 3.2c. Confirm 5 checks present (1, 2, 3, 4, 5), all 5 hard-fail, the field tables in Check 4 are complete, and the legacy-fallback carveout in Check 5 is explicit.

**Step 9: Commit**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "feat(reverse-engineered-brand): PHASE 3.2c gate adds Check 4 (word caps) + Check 5 (shape)"
```

---

### Task 14: Update PHASE 2.4 outcomes — `.build/` resume semantics for group-bullets and voice-rewrite

**Files:**
- Modify: `frameworks/reverse-engineered-brand/prompt.md` (PHASE 2.4 outcomes section — add resume-rule entries for the two new sub-agent dispatches)

**Step 1: Find the PHASE 2.4 outcomes section**

Grep for "PHASE 2.4" in `prompt.md`. Read the surrounding outcomes paragraph or list.

**Step 2: Append resume-rule entries**

Add bullets to the outcomes list (or section) describing the resume semantics for the two new sub-agent dispatches:

```markdown
**Resume semantics for PHASE 3 sub-agents (added v0.4.1):**

- **PHASE 3.2 group-bullets sub-agents.** Each writes `{brand-folder-path}/.build/groups/{group-id}.json`. On rerun, if the file is present and parses as JSON containing both `headline_claim` and `thinnest_gap` non-empty after trim, skip re-dispatch for that group. To force re-dispatch, delete the file.
- **PHASE 3.2b voice-rewrite sub-agent.** Writes `{brand-folder-path}/.build/voice-rewrite.json`. On rerun, if the file is present and parses with both `asks` and `provided_summaries` keys, skip re-dispatch. To force re-dispatch, delete the file.

These resume rules avoid re-paying PHASE 1 + 1.5 + 2 costs when a single sub-agent fails. The PHASE 3.2c gate runs unconditionally on the merged output regardless of which path produced it (fresh dispatch vs. resumed cache).
```

**Step 3: Verify**

Read PHASE 2.4. Confirm both resume entries are present and reference the exact file paths.

**Step 4: Commit**

```bash
git add frameworks/reverse-engineered-brand/prompt.md
git commit -m "docs(reverse-engineered-brand): PHASE 2.4 documents .build resume semantics for v0.4.1 sub-agents"
```

---

### Task 15: End-to-end smoke test against existing brand corpus (deferred-skip if absent)

**Files:**
- Read-only: `~/Documents/Obsidian/marley/brand/` (if present); rerun the framework against it
- Modify: `docs/plans/2026-05-18-reverse-engineered-brand-review-fix.md` (mark task ✅ after; nothing else)

**Step 1: Pre-check**

Read `~/Documents/Obsidian/marley/brand/CLAUDE.md` (or any file under that path).

If the directory does not exist, mark this task `🔄 BLOCKED` and exit. The autopilot's BLOCKED retry path will auto-skip after `MAX_BLOCKED_ITERATIONS` and move on; the operator can complete the smoke test manually later. Do not fabricate a brand folder.

**Step 2: Run the framework**

If the brand folder is present:

```bash
# In an interactive Claude session, NOT inside the autopilot loop:
# /aligned:use-framework reverse-engineered-brand
# (auto-mode against ~/Documents/Obsidian/marley/brand)
```

Because this requires an interactive Claude session and explicit user invocation of `/aligned:use-framework`, the autopilot cannot perform Step 2 unattended. The autopilot's role is to mark the task `🔄 BLOCKED` and exit; the operator runs the smoke test manually after merge.

**Step 3: Validation criteria (operator-only, post-merge)**

When the operator runs the framework:
- Confirm `.open-questions.json` has `schema_version: "0.4.1"`.
- Confirm `display_groups[]` has 4 entries (or fewer if a folder is genuinely missing — `who-you-sell-against` may be 1 folder if there's no `competitive` data).
- Each `display_groups[i].headline_claim` and `thinnest_gap` are non-empty and ≤14 words.
- Each `display_groups[i].provided_summary` is ≤25 words.
- Each ask in `display_groups[].input_asks[].ask` is ≤12 words and starts with a noun.
- No em-dashes anywhere in the JSON.
- Open the produced `review.html` in a browser; verify:
  - 5-button tab nav (Overview + 4 groups).
  - Sections at a Glance shows 4 rows with `N/5` grades + two bullets each.
  - Overview → `Send us any of these` is a single flat hyphen-bulleted list with no folder chips.
  - Each group panel shows banner (no bullets) + callout (one heading) + sorted OQ cards (P0 first) with CEO-vocabulary chips + nested per-folder paste-back `<details>` blocks.
  - KB-141 empty-state copy reads `Coverage is sufficient here.` for any folder that has no asks.

**Step 4: Commit the task-completion marker**

Whether the smoke test ran or was BLOCKED, commit the plan-file update:

```bash
git add docs/plans/2026-05-18-reverse-engineered-brand-review-fix.md
git commit -m "test(reverse-engineered-brand): mark end-to-end smoke test task complete"
```

---

## Manual Steps (Post-Automation)

The autopilot cannot run `/aligned:use-framework reverse-engineered-brand` against a real brand folder unattended (the framework has interactive WAIT gates and reads user-owned source material outside this repo). After autopilot completes, the operator should:

1. **Visual regression pass** — paste each fixture from `frameworks/reverse-engineered-brand/test-fixtures/render/` into the `{open-questions-json}` substitution point in `review-template.html` and open the resulting file in a browser. For each, visually compare against the mockup at `docs/mockups/2026-05-18-reverse-engineered-brand-review-fix.html`:
   - `fixture-tiny.json` → 1 group (How you show up); 2-bullet row in Sections at a Glance; flat hyphen-bulleted Inputs list; no folder chips; `Coverage is sufficient here.` for any zero-ask folder.
   - `fixture-realistic.json` → 4 group rows; banner shows grade `N/5` only (no bullets); single `What we have, what would help` callout heading; chip-area in CEO vocabulary (e.g., `Strategy`).
   - `fixture-stress.json` → same as realistic but with ~130 OQs across groups; verify OQ sort P0 → P1 → P2 then file order; verify nested per-folder paste-back `<details>` blocks render.
   - `valid-legacy-v0.4.0.json` → 1:1 synthetic groups; second bullet absent (legacyFolderAsGroup sets `thinnest_gap = ''`); if the fixture's `folders[].summary` exceeds 14 words, the first bullet shows an ellipsis (`…`) — otherwise no ellipsis.
   - `valid-empty-group.json` → `Coverage is sufficient across this area.` empty-group line under callout.
2. **End-to-end framework run** — run `/aligned:use-framework reverse-engineered-brand` in an interactive Claude session against `~/Documents/Obsidian/marley/brand/` per Task 15 Step 3 acceptance criteria.
3. **Visual-compare** the rendered `review.html` against `docs/mockups/2026-05-18-reverse-engineered-brand-review-fix.html`.
4. **File KB entries** for any drift not already captured in this plan.

No production deploys, no migrations, no DNS, no OAuth — all changes are local to this plugin repo and take effect on the next `/aligned:use-framework reverse-engineered-brand` invocation.

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | How to split the work across commits | 15 tasks following the design's 7-step implementation order, each task = 1 commit | 7 coarse tasks (one per design phase); 25 fine tasks (one per spec change) |
| 2 | TDD discipline given no automated render tests | Fixture-first TDD: positive + negative fixtures land in Task 3 before the renderer/validator changes consume them | Add a headless-browser test harness as a prereq; defer fixture authorship to the consuming task |
| 3 | Whether to write fixtures + helpers in the renderer commit or upstream | Fixtures land in Task 3 as a single commit; renderer helpers (`legacyFolderAsGroup`, `resolveDisplayGroups`, `buildTabNav`, `buildGroupPanels`, `buildFolderToGroupTab`) land in Task 4 with the data-driven tab nav | Bundle fixtures into each consuming task; centralize all helpers into a separate "renderer foundations" commit |
| 4 | How to handle the v0.4.0 → v0.4.1 transition risk | Additive schema with `legacyFolderAsGroup()` fallback; renderer always derives from `display_groups[]` (synthesizing if absent) | Hard cutover; dual-render paths (one for v0.4.0, one for v0.4.1) |
| 5 | Where the group-bullets sub-agent prompt lives | `frameworks/reverse-engineered-brand/group-bullets.md` (sibling of `voice-rewrite.md`) | Inline in `prompt.md`; under `agents/`; under a new `sub-agents/` subdir |
| 6 | Whether Task 15 (smoke test) is autopilot-executable | Marked `🔄 BLOCKED` in the autopilot — the operator runs it post-merge | Skip mentioning the smoke test in the plan; include a Prerequisites entry that requires a marley folder before Task 1 |
| 7 | How OQ filter routes folder ids to groups at render time | Build `FOLDER_TO_GROUP_TAB` lazily at render time via `buildFolderToGroupTab()` — supports legacy synthetic group ids | Static const FOLDER_TO_GROUP_TAB; require all fixtures to declare display_groups before render |
| 8 | Whether Check 5 enforces non-empty `thinnest_gap` on legacy-fallback output | Legacy fallback exempt — Check 5 runs only on orchestrator-authored v0.4.1 output | Enforce uniformly; require v0.4.0 fixtures to declare `thinnest_gap = ""` explicitly |
| 9 | Whether v0.4.0 fixtures render as 1:1 synthetic legacy buttons or remap into 4 CEO tabs | 1:1 synthetic tabs — each legacy folder becomes its own group | Hardcoded folder→group fallback map applied to v0.4.0 fixtures |
| 10 | Whether to author executable error-path assertions or rely on negative fixtures | Negative fixtures only; spec + fixture JSON IS the executable spec given no automated runner | Author Markdown assertion table per negative fixture; build a JSON-schema validator harness as a side task |

### Appendix: Decision Details

#### Decision 1: How to split the work across commits

**Chose:** 15 tasks, each task = 1 commit, following the design's 7-step order.

**Why:** The design doc already establishes the dependency order (renderer-only quick wins → validator spec → schema/fixtures → renderer changes → sub-agent prompts → orchestration → smoke test). Mapping each phase to 2-3 tasks preserves logical commit grouping while keeping each commit reviewable in <15 minutes. Fewer tasks would hide significant edits behind a single commit message; more tasks would create commits that don't independently compile/render.

**Alternatives rejected:**
- 7 coarse tasks (one per design phase): some phases (renderer changes, sub-agent prompts) cover ~200 lines of HTML + multiple JS function rewrites. A single commit at that size is hard to review and harder to bisect on regression.
- 25 fine tasks (one per spec change): introduces commits like "add one negative fixture" that have no semantic value on their own. The bundle in Task 3 — all v0.4.1 fixtures and all negative/edge cases in one commit — is one coherent "fixtures matching the v0.4.1 spec" change.

#### Decision 2: TDD discipline given no automated render tests

**Chose:** Fixture-first TDD. Task 3 lands all positive + negative + edge-case fixtures before any consuming task. Each subsequent task (4 onward) starts with a manual paste-and-open verification, then implements, then re-verifies.

**Why:** This codebase has no automated browser test harness (see `frameworks/reverse-engineered-brand/test-fixtures/render/README.md` line 4: "There is no automated runner"). Standing one up would be a 1-2 day side quest. The fixtures themselves are the executable artifact: they encode the spec and force the renderer to handle each case. Manual paste-and-open is a real validation pass even if it's not automated.

**Alternatives rejected:**
- Standing up Puppeteer/Playwright as a prereq: out of scope for this plan and a large independent effort. Adding it here would balloon the plan from 15 tasks to 25+ and shift the focus from the user-visible fix to test infrastructure.
- Deferring fixture authorship to each consuming task: causes ordering friction — the legacy-fallback fixture is needed by Task 4, the verb-form-reject fixture by Task 13. Centralizing them in Task 3 means each consuming task references existing files instead of producing new ones mid-flow.

#### Decision 3: Where helpers live

**Chose:** Fixtures in Task 3; renderer helpers (`legacyFolderAsGroup`, `resolveDisplayGroups`, `buildTabNav`, `buildGroupPanels`, `buildFolderToGroupTab`) in Task 4 alongside the tab nav refactor. (Task 4 originally added a standalone `truncateAndStripDashes` helper; Round 1 L1/L2 critique correctly identified it as a single-caller utility that also mutated legacy text — the truncation logic now lives inline inside `legacyFolderAsGroup`, and em-dash stripping was dropped.)

**Why:** Task 4 introduces the first renderer change that needs these helpers (the data-driven tab nav). Splitting helpers into a standalone "renderer foundations" commit creates a dead commit (no observable change in the rendered HTML) that's hard to validate. Bundling them with the first consumer means Task 4's manual paste-and-open is the verification.

**Alternatives rejected:**
- "Renderer foundations" commit landing all helpers first: dead commit problem; can't validate without a consumer.
- Inline helpers in each task's first-use site: causes duplicate code as later tasks (Task 5 `renderSectionsAtAGlance`, Task 7 `renderAll`) all need `resolveDisplayGroups`. Centralizing once in Task 4 means all later tasks just call it.

#### Decision 4: v0.4.0 → v0.4.1 transition

**Chose:** Additive schema. Renderer always normalizes via `resolveDisplayGroups()` — returns `display_groups[]` if present, otherwise derives synthetic groups via `legacyFolderAsGroup()`. Single decision tree, no per-fixture switch.

**Why:** This matches the v0.3.0 → v0.4.0 transition pattern (`render-review-html.md:35` shape-warning fallback). It also means existing brand-folder rebuilds against a v0.4.0 `.open-questions.json` don't break — the renderer reduces them to the 5-tab layout automatically (1 folder per synthetic group, second bullet empty).

**Alternatives rejected:**
- Hard cutover (v0.4.1 fixtures only): would break any brand folder built before this lands. The marley corpus is the obvious affected case.
- Dual-render paths: two code paths means two test surfaces. Higher maintenance, more places to drift.

#### Decision 5: Sub-agent prompt location

**Chose:** `frameworks/reverse-engineered-brand/group-bullets.md`, sibling to `voice-rewrite.md`.

**Why:** Matches the established convention. `voice-rewrite.md` is a sub-agent prompt with the same dispatch pattern (Task call with placeholder substitution) and lives in this directory. New `group-bullets.md` follows the same pattern so future readers find both in one place.

**Alternatives rejected:**
- Inline in `prompt.md`: would inflate the orchestrator prompt with sub-agent content the orchestrator never reads. Sub-agents need their own files for substitution.
- `agents/` namespace: per memory `feedback_agents_vs_framework_helpers.md`, single-caller sub-agent prompts live inside the framework folder, not in `agents/`. The `agents/` namespace is for standalone or shared things.

#### Decision 6: Task 15 (smoke test) execution model

**Chose:** Task 15 marks itself `🔄 BLOCKED` when running unattended (autopilot loop) and is performed by the operator post-merge.

**Why:** The smoke test requires running `/aligned:use-framework reverse-engineered-brand` against a real brand folder, which has interactive WAIT gates and reads user-owned source material (`~/Documents/Obsidian/marley/brand/`). The autopilot's `claude -p` invocation cannot interactively step through the framework. The honest path is to surface the obligation in `Manual Steps (Post-Automation)` and let the operator complete it.

**Alternatives rejected:**
- Skip Task 15 entirely: drops the end-to-end validation that catches integration bugs not visible in fixture-only checks.
- Add the marley folder as a Prerequisite: makes the plan unrunnable for anyone without that specific corpus on disk.

#### Decision 7: Folder→group routing at render time

**Chose:** Build `FOLDER_TO_GROUP_TAB` lazily via `buildFolderToGroupTab()` each render pass.

**Why:** The legacy-fallback path produces synthetic group ids (`legacy-strategy`, `legacy-language`, …) at render time. A static const cannot anticipate these. Building lazily means one normalization path handles both v0.4.1 authored output and v0.4.0 legacy fixtures.

**Alternatives rejected:**
- Static const + require all fixtures to declare `display_groups[]`: breaks the v0.4.0 fallback contract.

#### Decision 8: Check 5 carveout for legacy-fallback output

**Chose:** Check 5 (required-non-empty + field-presence) enforced ONLY when the orchestrator authored `display_groups[]` itself. The renderer's `legacyFolderAsGroup()` is exempt. Detection signal: `display_groups[i].id` does NOT start with `legacy-` (synthetic legacy ids are unique to `legacyFolderAsGroup()`).

**Why:** `legacyFolderAsGroup()` deliberately emits empty `thinnest_gap` strings (no thinnest-gap data exists in v0.4.0 fixtures). Enforcing Check 5 against this output would make every v0.4.0 fixture hard-fail. The intent is to validate the orchestrator's authoring, not the renderer's fallback synthesis. In practice the carveout is documentation: PHASE 3.2c runs against orchestrator output (in-memory `display_groups[]` before disk write), where no legacy ids exist.

**Alternatives rejected:**
- Enforce uniformly + require v0.4.0 fixtures to declare `thinnest_gap = ""`: that's authoring it, not falling back; defeats the legacy-compat point.
- Enforce uniformly + delete the legacy-fallback path: ships a hard cutover under another name. Rejected for the same reason as Decision 4.

#### Decision 9: Legacy v0.4.0 rendering — 1:1 synthetic tabs

**Chose:** Each v0.4.0 folder becomes its own synthetic group via `legacyFolderAsGroup()`. A v0.4.0 fixture renders 7 + 1 (Overview + 7 legacy-folder tabs), not the new 5-tab CEO layout.

**Why:** The design doc's Decision 16 is internally ambiguous — line 60 says the renderer "always builds tab nav from `display_groups[]`" with v0.4.0 falling through `legacyFolderAsGroup()`, but the prose also references "v0.4.0 fixtures render under the new 5-button nav layout." The plan picks the safer interpretation: 1:1 synthetic tabs preserve all legacy folder data without inventing a folder→group map that v0.4.0 authors did not provide. The 5-CEO-tab consolidation requires authoring `headline_claim` + `thinnest_gap` per group, which only exists in v0.4.1+.

**Alternatives rejected:**
- Hardcoded folder→group fallback map for v0.4.0 fixtures: would render correct tab vocabulary but with `thinnest_gap = ''` across every group and no `headline_claim` continuity across the constituents. The result is the right LABEL but worse CONTENT than 1:1 tabs.
- Reject v0.4.0 fixtures at render time: breaks brand folders generated before this lands.

#### Decision 10: Error-path test specs vs negative fixtures only

**Chose:** Negative fixtures only. Each negative fixture's JSON content + the PHASE 3.2c spec text together ARE the executable spec — a future executor reads the fixture, runs the validator logic mentally (or in a future automated runner), and confirms the expected hard-fail occurs.

**Why:** This codebase has no automated runner for PHASE 3.2c validation (see `test-fixtures/oq-schema/README.md`: "There is no automated runner"). The validation is executed by the LLM agent during PHASE 3.2c. Authoring a separate Markdown assertion table per negative fixture would duplicate information already encoded in (a) the fixture JSON itself and (b) the PHASE 3.2c spec. Adding a JSON-schema validator harness is a separate side task whose scope exceeds this fix.

**Alternatives rejected:**
- Markdown assertion table per fixture: would duplicate the spec; risks drift when the spec changes.
- Build a JSON-schema validator harness as a prereq: out of scope; adds 1-2 days of test-infrastructure work for a deliverable focused on user-visible review.html quality.
